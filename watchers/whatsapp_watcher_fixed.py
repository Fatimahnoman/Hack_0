"""
WhatsApp Watcher - Gold Tier (Fixed v9 - Better Scanning)
==========================================================
Monitors WhatsApp Web for unread messages with specific keywords.
Uses Playwright with CHROME browser.

FIXES:
1. Better chat scanning logic
2. Logs every message for debugging
3. Creates files in gold/needs_action/ folder
4. Handles session properly

Install: pip install playwright && playwright install chrome
Run: python watchers/whatsapp_watcher_fixed.py
"""

import os
import re
import sys
import time
import logging
from datetime import datetime
from pathlib import Path

try:
    from playwright.sync_api import sync_playwright
except ImportError as e:
    print(f"[ERROR] Missing: {e}")
    print("Run: pip install playwright && playwright install chrome")
    sys.exit(1)

# =============================================================================
# CONFIGURATION
# =============================================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent
GOLD_DIR = PROJECT_ROOT / "gold"

# Gold Tier folders
NEEDS_ACTION_FOLDER = GOLD_DIR / "needs_action"
LOGS_FOLDER = GOLD_DIR / "logs"
SESSION_PATH = PROJECT_ROOT / "session" / "whatsapp_chrome"

# Ensure folders exist
NEEDS_ACTION_FOLDER.mkdir(parents=True, exist_ok=True)
LOGS_FOLDER.mkdir(parents=True, exist_ok=True)
SESSION_PATH.mkdir(parents=True, exist_ok=True)

# Settings
CHECK_INTERVAL = 30  # seconds
WHATSAPP_URL = "https://web.whatsapp.com"

# Keywords (case-insensitive)
IMPORTANT_KEYWORDS = [
    "urgent", "sales", "payment", "invoice", "deal", "order",
    "client", "customer", "quotation", "proposal", "overdue",
    "follow up", "meeting", "booking", "asap", "test", "hi",
    "hello", "paid", "receive", "price", "cost", "quote",
    "contract", "agreement", "confirm", "approval", "budget",
    "help", "service", "product", "buy", "purchase"
]

# Track processed
processed_messages = set()
PROCESSED_FILE = SESSION_PATH / "processed.txt"

# =============================================================================
# LOGGING
# =============================================================================

def setup_logging():
    log_file = LOGS_FOLDER / f"whatsapp_{datetime.now().strftime('%Y%m%d')}.log"
    
    logger = logging.getLogger("WhatsAppWatcher")
    logger.setLevel(logging.DEBUG)
    logger.handlers = []
    
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
    logger.addHandler(file_handler)
    
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(logging.Formatter("[%(levelname)s] %(message)s"))
    logger.addHandler(console_handler)
    
    return logger

logger = setup_logging()

# =============================================================================
# MESSAGE PROCESSING
# =============================================================================

def load_processed():
    global processed_messages
    if PROCESSED_FILE.exists():
        try:
            with open(PROCESSED_FILE, 'r', encoding='utf-8') as f:
                processed_messages = set(line.strip() for line in f if line.strip())
            logger.info(f"✓ Loaded {len(processed_messages)} processed messages")
        except:
            pass

def save_processed(msg_id: str):
    processed_messages.add(msg_id)
    try:
        with open(PROCESSED_FILE, 'a', encoding='utf-8') as f:
            f.write(f"{msg_id}\n")
    except:
        pass

def get_priority(message: str) -> str:
    text = message.lower()
    if "urgent" in text or "asap" in text:
        return "high"
    if "invoice" in text or "payment" in text or "order" in text:
        return "medium"
    return "normal"

def create_needs_action_file(contact: str, message: str) -> Path:
    """Create file in gold/needs_action/ folder"""
    priority = get_priority(message)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_contact = re.sub(r"[^a-zA-Z0-9]", "_", contact[:20]) or "Unknown"
    filename = f"WHATSAPP_{safe_contact}_{timestamp}.md"
    filepath = NEEDS_ACTION_FOLDER / filename
    
    content = f"""---
type: whatsapp_message
from: {contact}
message: {message}
priority: {priority}
status: pending
created_at: {datetime.now().isoformat()}
---

## Message Content

{message}

---
*WhatsApp Watcher - Gold Tier*
"""
    
    with open(filepath, "w", encoding='utf-8') as f:
        f.write(content)
    
    logger.info(f"✅ CREATED: {filename}")
    return filepath

# =============================================================================
# SCANNING
# =============================================================================

def scan_chats(page):
    """Scan WhatsApp Web for messages with keywords."""
    try:
        # Wait for chat list
        try:
            page.wait_for_selector('#pane-side', timeout=5000)
        except:
            logger.warning("Chat list not found")
            return 0, 0
        
        # Get all chats
        chats = page.query_selector_all('#pane-side [role="row"]')
        
        if not chats:
            logger.debug("No chats found")
            return 0, 0
        
        logger.info(f"📊 Found {len(chats)} chats")
        
        new_tasks = 0
        messages_checked = 0
        
        # Check each chat
        for i, chat in enumerate(chats[:20]):  # Check first 20 chats
            try:
                # Get absolute raw text of the entire chat row
                row_text = chat.inner_text()
                if not row_text:
                    continue
                
                # Split by newlines and clean up
                parts = [p.strip() for p in row_text.split('\\n') if p.strip()]
                
                # First valid line is usually the contact name
                contact = parts[0] if parts else "Unknown"
                
                # Join all text to form the message blob for guaranteed keyword finding
                message = " | ".join(parts)
                
                if len(message) < 3:
                    continue
                
                messages_checked += 1
                
                # Log message for debugging
                if i < 10:  # Log first 10 messages
                    logger.debug(f"💬 {contact[:20]}: {message[:60]}...")
                
                # Check if processed
                msg_id = f"{contact}:{message[:50]}"
                if msg_id in processed_messages:
                    continue
                
                # Check keywords
                message_lower = message.lower()
                found_keywords = [kw for kw in IMPORTANT_KEYWORDS if kw in message_lower]
                
                if found_keywords:
                    logger.info(f"🎯 KEYWORDS FOUND: {found_keywords}")
                    logger.info(f"📍 Contact: {contact}")
                    logger.info(f"📄 Message: {message[:100]}...")
                    
                    create_needs_action_file(contact, message)
                    save_processed(msg_id)
                    new_tasks += 1
                elif i < 5:
                    logger.debug(f"⚪ No keywords in: {message[:50]}...")
                    
            except Exception as e:
                logger.debug(f"Error processing chat {i}: {e}")
                continue
        
        logger.info(f"✓ Checked {messages_checked} messages, {new_tasks} new tasks")
        return len(chats), new_tasks
        
    except Exception as e:
        logger.error(f"❌ Scan error: {e}")
        return 0, 0

# =============================================================================
# MAIN
# =============================================================================

def main():
    logger.info("=" * 70)
    logger.info("WHATSAPP WATCHER - GOLD TIER (CHROME)")
    logger.info("=" * 70)
    logger.info(f"Session: {SESSION_PATH}")
    logger.info(f"Tasks folder: {NEEDS_ACTION_FOLDER}")
    logger.info(f"Keywords: {len(IMPORTANT_KEYWORDS)}")
    logger.info("=" * 70)
    
    load_processed()
    
    with sync_playwright() as p:
        context = None
        
        try:
            # Launch Chrome
            logger.info("Launching Chrome...")
            context = p.chromium.launch_persistent_context(
                user_data_dir=str(SESSION_PATH),
                headless=False,
                channel="chrome",
                args=[
                    "--disable-gpu",
                    "--no-sandbox",
                    "--window-size=1280,720",
                    "--disable-notifications",
                    "--disable-blink-features=AutomationControlled",
                    "--remote-debugging-port=9223"
                ],
                timeout=60000
            )
            
            logger.info("✓ Chrome launched")
            
            page = context.pages[0] if context.pages else context.new_page()
            
            logger.info(f"Navigating to WhatsApp...")
            page.goto(WHATSAPP_URL, timeout=300000)
            
            logger.info("Waiting for WhatsApp to load (scan QR code if needed)...")
            logger.info("⚠️  KEEP BROWSER OPEN - Do not close!")
            
            # Wait for load
            try:
                page.wait_for_selector('#pane-side', timeout=300000)
                logger.info("✓ WhatsApp loaded!")
                time.sleep(2)  # Wait for messages to load
            except:
                logger.warning("⚠️  Timeout - please login manually")
            
            logger.info("Starting monitoring loop...")
            consecutive_errors = 0
            
            while True:
                try:
                    total, new_tasks = scan_chats(page)
                    
                    if total > 0:
                        consecutive_errors = 0
                        
                        if new_tasks > 0:
                            logger.info(f"🎉 Created {new_tasks} task(s)!")
                        else:
                            logger.info(f"⏳ Monitoring... ({total} chats)")
                    else:
                        consecutive_errors += 1
                        if consecutive_errors > 5:
                            logger.warning("⚠️  No chats found - reloading...")
                            page.reload()
                            time.sleep(5)
                            consecutive_errors = 0
                    
                    time.sleep(CHECK_INTERVAL)
                    
                except Exception as e:
                    logger.error(f"Loop error: {e}")
                    consecutive_errors += 1
                    if consecutive_errors > 5:
                        logger.error("Too many errors - reloading")
                        page.reload()
                        time.sleep(5)
                        consecutive_errors = 0
                    time.sleep(CHECK_INTERVAL)
                    
        except KeyboardInterrupt:
            logger.info("\n👋 Stopping...")
        except Exception as e:
            logger.error(f"❌ Fatal: {e}")
            import traceback
            logger.error(traceback.format_exc())
        finally:
            if context:
                try:
                    context.close()
                    logger.info("Browser closed")
                except:
                    pass

if __name__ == "__main__":
    main()
