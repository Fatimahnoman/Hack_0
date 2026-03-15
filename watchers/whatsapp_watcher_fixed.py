"""
WhatsApp Watcher - Silver Tier (Fixed v5 - FINAL)
=================================================
Monitors WhatsApp Web for unread messages with specific keywords.
Uses Playwright for browser automation with persistent session.

Based on actual WhatsApp Web structure analysis:
- Chat list: #pane-side
- Chat items: [role="row"] (67 rows)
- Each row has 3 gridcells: [role="gridcell"]
  - Cell 0: Full content
  - Cell 1: Contact name + time
  - Cell 2: Unread count (if unread) - class "_ak8i"
- Unread detection: Cell 2 has a number (e.g., "32", "11", "45")
- Read messages: Cell 2 is empty

Install: pip install playwright
         playwright install chromium
Run: python watchers/whatsapp_watcher_fixed.py
"""

import os
import re
import sys
import time
import logging
from datetime import datetime
from pathlib import Path

# Check for Playwright
try:
    from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout
except ImportError as e:
    print(f"[ERROR] Missing required dependency: {e}")
    print("[INFO] Please install required packages:")
    print("       pip install playwright")
    print("       playwright install chromium")
    sys.exit(1)
except OSError as e:
    print(f"[ERROR] Playwright dependency error: {e}")
    print("TRY THESE FIXES:")
    print("  1. pip install --upgrade greenlet playwright")
    print("  2. playwright install chromium")
    sys.exit(1)

# Configuration
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SESSION_PATH = os.path.join(PROJECT_ROOT, "session", "whatsapp")
NEEDS_ACTION_FOLDER = os.path.join(PROJECT_ROOT, "Needs_Action")
LOGS_FOLDER = os.path.join(PROJECT_ROOT, "Logs")
CHECK_INTERVAL = 30  # seconds
WHATSAPP_URL = "https://web.whatsapp.com"

# Keywords to monitor (case-insensitive)
IMPORTANT_KEYWORDS = ["urgent", "invoice", "payment", "sales"]

# Track processed messages
processed_messages = set()


def setup_logging():
    """Setup logging to file and console."""
    if not os.path.exists(LOGS_FOLDER):
        os.makedirs(LOGS_FOLDER)

    log_file = os.path.join(LOGS_FOLDER, "watcher.log")

    logger = logging.getLogger("WhatsAppWatcher")
    logger.setLevel(logging.DEBUG)
    logger.handlers = []

    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setLevel(logging.DEBUG)
    file_format = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
    file_handler.setFormatter(file_format)
    logger.addHandler(file_handler)

    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_format = logging.Formatter("[%(levelname)s] %(message)s")
    console_handler.setFormatter(console_format)
    logger.addHandler(console_handler)

    return logger


def get_priority(message: str) -> str:
    """Determine priority based on keywords."""
    text = message.lower()
    if "urgent" in text:
        return "high"
    elif "invoice" in text or "payment" in text:
        return "medium"
    elif "sales" in text:
        return "normal"
    return "low"


def create_needs_action_file(contact: str, message: str, timestamp: str, logger: logging.Logger) -> str:
    """Create .md file in Needs_Action folder with YAML frontmatter."""
    priority = get_priority(message)
    file_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    safe_contact = re.sub(r"[^a-zA-Z0-9]", "_", contact[:20])
    filename = f"WHATSAPP_{safe_contact}_{file_timestamp}.md"
    filepath = os.path.join(NEEDS_ACTION_FOLDER, filename)

    yaml_content = f"""---
type: whatsapp_message
from: {contact}
message: {message}
priority: {priority}
status: pending
---

## Message Content

{message}

---
*Imported by WhatsApp Watcher on {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}*
"""

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(yaml_content)

    logger.info(f"Created: {filename}")
    return filename


def check_important_message(message: str) -> bool:
    """Check if message contains important keywords."""
    text = message.lower()
    return any(keyword in text for keyword in IMPORTANT_KEYWORDS)


def scan_chats(page, logger: logging.Logger):
    """
    Scan chat list for unread messages with keywords.
    
    WhatsApp Web structure (verified):
    - Container: #pane-side
    - Chat rows: [role="row"] 
    - Each row has 3 gridcells: [role="gridcell"]
      - Cell 0: Full content
      - Cell 1: Contact name + time  
      - Cell 2: Unread count (if unread) - number like "32", "11", "45"
    - Read messages have empty Cell 2
    - Unread messages have number in Cell 2
    """
    global processed_messages
    
    try:
        # Get chat container
        chat_container = page.query_selector('#pane-side')
        
        if not chat_container:
            logger.debug("No chat container found (#pane-side)")
            return True, 0, 0
        
        # Get all chat rows
        chats = page.query_selector_all('#pane-side [role="row"]')
        
        if not chats:
            logger.debug("No [role='row'] elements found")
            return True, 0, 0
        
        total_chats = len(chats)
        total_unread = 0
        important_found = 0
        
        logger.debug(f"Processing {total_chats} chat rows...")
        
        for i, chat in enumerate(chats):
            try:
                # Get all 3 gridcells
                gridcells = chat.query_selector_all('[role="gridcell"]')
                
                if len(gridcells) < 3:
                    continue  # Skip incomplete rows
                
                # Cell 2 (third gridcell) contains unread count if unread
                cell_2 = gridcells[2]
                cell_2_text = cell_2.inner_text().strip()
                
                # Check if Cell 2 has a number (indicates unread)
                if not cell_2_text or not cell_2_text.isdigit():
                    continue  # Read message - skip
                
                unread_count = int(cell_2_text)
                if unread_count == 0:
                    continue  # No unread
                
                total_unread += 1
                
                # Get contact name from Cell 1
                cell_1 = gridcells[1]
                contact = "Unknown"
                
                # Try span[dir="auto"] first
                name_elem = cell_1.query_selector('span[dir="auto"]')
                if name_elem:
                    contact = name_elem.inner_text() or "Unknown"
                
                # Fallback to span[title]
                if contact == "Unknown":
                    name_elem = cell_1.query_selector('span[title]')
                    if name_elem:
                        contact = name_elem.get_attribute('title') or "Unknown"
                
                # Get message preview from Cell 0
                cell_0 = gridcells[0]
                message = ""
                
                # Look for the message content span
                msg_elem = cell_0.query_selector('span[data-testid="last-message-content"]')
                if msg_elem:
                    message = msg_elem.inner_text()
                
                # Fallback: get all spans and find the longest text
                if not message:
                    spans = cell_0.query_selector_all('span')
                    for span in spans:
                        try:
                            text = span.inner_text()
                            if text and len(text) > len(message):
                                message = text
                        except:
                            continue
                
                # Skip if no message content
                if not message.strip():
                    continue
                
                # Create unique ID
                msg_id = f"{contact}:{message[:50]}"
                
                # Skip if already processed
                if msg_id in processed_messages:
                    continue
                
                logger.debug(f"Unread #{total_unread}: {contact} | Count: {unread_count} | {message[:50]}...")
                
                # Check for important keywords
                if check_important_message(message):
                    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    filename = create_needs_action_file(contact, message, timestamp, logger)
                    processed_messages.add(msg_id)
                    important_found += 1
                    
                    logger.info(f"✅ IMPORTANT: {contact} | Unread: {unread_count} | Priority: {get_priority(message)}")
                    logger.info(f"   File: {filename}")
                    logger.info(f"   Msg: {message[:100]}...")
                else:
                    processed_messages.add(msg_id)
                    
            except Exception as e:
                logger.debug(f"Error processing chat {i}: {e}")
                continue
        
        return True, total_chats, total_unread
        
    except Exception as e:
        logger.error(f"Scan error: {e}")
        return False, 0, 0


def monitor_whatsapp(logger: logging.Logger):
    """Monitor WhatsApp Web for new important messages."""

    with sync_playwright() as p:
        logger.info("Launching browser with persistent session...")
        logger.info(f"Session path: {SESSION_PATH}")

        context = p.chromium.launch_persistent_context(
            user_data_dir=SESSION_PATH,
            headless=False,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
                "--disable-dev-shm-usage",
                "--disable-gpu"
            ]
        )

        page = context.pages[0]
        page.set_default_timeout(30000)

        logger.info("Navigating to WhatsApp Web...")
        
        try:
            page.goto(WHATSAPP_URL, wait_until="domcontentloaded", timeout=60000)
            page.wait_for_load_state("networkidle", timeout=30000)
            
            logger.info("Waiting for WhatsApp to load (scan QR code if first time)...")
            
            try:
                page.wait_for_selector('#pane-side, [data-testid="intro"]', timeout=120000)
                logger.info("WhatsApp page loaded")
            except PlaywrightTimeout:
                logger.warning("Timeout waiting for page elements")
                
        except PlaywrightTimeout:
            logger.warning("Navigation timeout - continuing...")
        except Exception as e:
            logger.error(f"Navigation error: {e}")

        logger.info("-" * 60)
        logger.info(f"Monitoring started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info(f"Check interval: {CHECK_INTERVAL} seconds")
        logger.info("Press Ctrl+C to stop")
        logger.info("-" * 60)

        consecutive_failures = 0
        max_failures = 5

        try:
            while True:
                try:
                    # Show ONLINE status
                    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    print(f"\n[{current_time}] ONLINE - Checking for unread messages...")
                    logger.info("ONLINE")
                    
                    # Verify page is valid
                    current_url = page.url
                    if "web.whatsapp.com" not in current_url:
                        logger.warning(f"Wrong URL: {current_url} - reloading...")
                        page.goto(WHATSAPP_URL, timeout=30000)
                        time.sleep(5)
                        continue
                    
                    # Scan for chats
                    success, total_chats, total_unread = scan_chats(page, logger)
                    
                    if success:
                        consecutive_failures = 0
                        logger.info(f"Scan: {total_chats} chats, {total_unread} unread")
                    else:
                        consecutive_failures += 1
                        logger.warning(f"Scan failed ({consecutive_failures}/{max_failures})")
                        
                        if consecutive_failures >= max_failures:
                            logger.info("Refreshing page...")
                            page.reload()
                            page.wait_for_load_state("networkidle", timeout=30000)
                            consecutive_failures = 0
                    
                    # Wait before next check
                    time.sleep(CHECK_INTERVAL)
                    
                except PlaywrightTimeout as e:
                    consecutive_failures += 1
                    logger.error(f"Timeout ({consecutive_failures}/{max_failures})")
                    if consecutive_failures >= max_failures:
                        try:
                            page.reload()
                            page.wait_for_load_state("networkidle", timeout=30000)
                        except:
                            pass
                        consecutive_failures = 0
                    time.sleep(5)
                    
                except Exception as e:
                    consecutive_failures += 1
                    logger.error(f"Error ({consecutive_failures}/{max_failures}): {e}")
                    if consecutive_failures >= max_failures:
                        try:
                            page.reload()
                            page.wait_for_load_state("networkidle", timeout=30000)
                        except:
                            pass
                        consecutive_failures = 0
                    time.sleep(5)

        except KeyboardInterrupt:
            logger.info("Stopping WhatsApp watcher...")

        finally:
            context.close()
            logger.info("Browser closed.")


def ensure_directories(logger: logging.Logger):
    """Ensure required directories exist."""
    if not os.path.exists(NEEDS_ACTION_FOLDER):
        os.makedirs(NEEDS_ACTION_FOLDER)
        logger.info(f"Created: {NEEDS_ACTION_FOLDER}")

    if not os.path.exists(SESSION_PATH):
        os.makedirs(SESSION_PATH)
        logger.info(f"Created session: {SESSION_PATH}")
    
    if not os.path.exists(LOGS_FOLDER):
        os.makedirs(LOGS_FOLDER)
        logger.info(f"Created logs: {LOGS_FOLDER}")


def main():
    """Main function to start WhatsApp watcher."""
    print("=" * 60)
    print("WhatsApp Watcher - Silver Tier (Fixed v5 - FINAL)")
    print("=" * 60)
    print(f"Monitoring: WhatsApp Web")
    print(f"Keywords: {', '.join(IMPORTANT_KEYWORDS)}")
    print(f"Destination: {NEEDS_ACTION_FOLDER}")
    print(f"Session: {SESSION_PATH}")
    print(f"Interval: {CHECK_INTERVAL} seconds")
    print("=" * 60)

    logger = setup_logging()
    ensure_directories(logger)

    logger.info("NOTE: First run requires QR code scan to login.")
    logger.info("      Session saved for subsequent runs.")

    try:
        monitor_whatsapp(logger)
    except Exception as e:
        logger.error(f"Fatal error: {e}")

    logger.info("WhatsApp watcher stopped.")


if __name__ == "__main__":
    main()
