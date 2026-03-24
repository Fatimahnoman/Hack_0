"""
WhatsApp Watcher - Silver Tier
===============================
Monitors WhatsApp Web for unread messages with specific keywords.
Uses Playwright for browser automation with persistent session.

Install: pip install playwright
         playwright install chromium
Setup:
  1. Run script once to scan QR code and login
  2. Session saved to /session/whatsapp for persistent login
Run: python watchers/whatsapp_watcher.py

NOTE: If you get greenlet DLL errors, this is a Python 3.14 compatibility issue.
      Try: pip install --upgrade greenlet playwright
           playwright install chromium
"""

import os
import re
import sys
import time
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
    print(f"[ERROR] Playwright dependency error (likely greenlet DLL issue): {e}")
    print("")
    print("This is a known Python 3.14 compatibility issue.")
    print("TRY THESE FIXES:")
    print("  1. pip install --upgrade greenlet playwright")
    print("  2. playwright install chromium")
    print("  3. Use Python 3.11 or 3.12 for this watcher")
    print("  4. See WATCHERS_SETUP.md for details")
    sys.exit(1)

# Configuration
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SESSION_PATH = os.path.join(PROJECT_ROOT, "session", "whatsapp")
NEEDS_ACTION_FOLDER = os.path.join(PROJECT_ROOT, "Needs_Action")
CHECK_INTERVAL = 30  # seconds
WHATSAPP_URL = "https://web.whatsapp.com"

# Keywords to monitor (case-insensitive)
IMPORTANT_KEYWORDS = ["urgent", "invoice", "payment", "sales"]

# Track processed messages
processed_messages = set()


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


def create_needs_action_file(contact: str, message: str, timestamp: str) -> str:
    """Create .md file in Needs_Action folder with YAML frontmatter."""
    priority = get_priority(message)
    file_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Sanitize filename
    safe_contact = re.sub(r"[^a-zA-Z0-9]", "_", contact[:20])
    filename = f"WHATSAPP_{safe_contact}_{file_timestamp}.md"
    filepath = os.path.join(NEEDS_ACTION_FOLDER, filename)
    
    yaml_content = f"""---
type: whatsapp_message
from: {contact}
subject: WhatsApp Message from {contact}
received: {timestamp}
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
    
    return filename


def check_important_message(message: str) -> bool:
    """Check if message contains important keywords."""
    text = message.lower()
    return any(keyword in text for keyword in IMPORTANT_KEYWORDS)


def monitor_whatsapp():
    """Monitor WhatsApp Web for new important messages."""
    
    with sync_playwright() as p:
        # Launch browser with persistent context
        print("[INFO] Launching browser with persistent session...")
        print(f"[INFO] Session path: {SESSION_PATH}")
        
        context = p.chromium.launch_persistent_context(
            user_data_dir=SESSION_PATH,
            headless=False,  # Show browser for QR code scan on first run
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
                "--disable-dev-shm-usage"
            ]
        )
        
        page = context.pages[0]
        
        print("[INFO] Navigating to WhatsApp Web...")
        page.goto(WHATSAPP_URL)
        
        # Wait for WhatsApp to load
        try:
            print("[INFO] Waiting for WhatsApp to load (scan QR code if first time)...")
            page.wait_for_selector('div[data-testid="default-user"]', timeout=120000)
            print("[INFO] WhatsApp loaded successfully!")
        except PlaywrightTimeout:
            print("[WARNING] WhatsApp did not load within timeout. Continuing anyway...")
        
        print("-" * 60)
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Monitoring started...")
        print(f"Checking every {CHECK_INTERVAL} seconds")
        print("Press Ctrl+C to stop")
        print("-" * 60)
        
        try:
            while True:
                try:
                    # Look for chat items with unread indicators
                    # WhatsApp Web structure may vary, adjust selectors as needed
                    chats = page.query_selector_all('div[data-testid="chat"]')
                    
                    for chat in chats:
                        try:
                            # Get chat name/contact
                            name_elem = chat.query_selector('span[dir="auto"]')
                            if not name_elem:
                                continue
                            
                            contact = name_elem.inner_text()
                            
                            # Check for unread indicator
                            unread_badge = chat.query_selector('span[data-testid="unread-count"]')
                            if not unread_badge:
                                continue
                            
                            # Get last message preview
                            msg_elem = chat.query_selector('span[data-testid="last-message-content"]')
                            if not msg_elem:
                                continue
                            
                            message = msg_elem.inner_text()
                            
                            # Create unique ID for message
                            msg_id = f"{contact}:{message[:50]}"
                            
                            # Skip if already processed
                            if msg_id in processed_messages:
                                continue
                            
                            # Check for important keywords
                            if check_important_message(message):
                                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                                filename = create_needs_action_file(contact, message, timestamp)
                                processed_messages.add(msg_id)
                                
                                print(f"\n[{timestamp}] New important message!")
                                print(f"  -> Created: {filename}")
                                print(f"     From: {contact}")
                                print(f"     Priority: {get_priority(message)}")
                                print(f"     Message: {message[:100]}...")
                            
                            else:
                                processed_messages.add(msg_id)
                        
                        except Exception as e:
                            # Skip individual chat errors
                            continue
                    
                    # Wait before next check
                    time.sleep(CHECK_INTERVAL)
                
                except Exception as e:
                    print(f"[ERROR] During monitoring: {e}")
                    time.sleep(5)
        
        except KeyboardInterrupt:
            print("\n[INFO] Stopping WhatsApp watcher...")
        
        finally:
            context.close()
            print("[INFO] Browser closed.")


def ensure_directories():
    """Ensure required directories exist."""
    if not os.path.exists(NEEDS_ACTION_FOLDER):
        os.makedirs(NEEDS_ACTION_FOLDER)
        print(f"[INFO] Created directory: {NEEDS_ACTION_FOLDER}")
    
    if not os.path.exists(SESSION_PATH):
        os.makedirs(SESSION_PATH)
        print(f"[INFO] Created session directory: {SESSION_PATH}")


def main():
    """Main function to start WhatsApp watcher."""
    print("=" * 60)
    print("WhatsApp Watcher - Silver Tier")
    print("=" * 60)
    print(f"Monitoring: WhatsApp Web")
    print(f"Keywords: {', '.join(IMPORTANT_KEYWORDS)}")
    print(f"Destination: {NEEDS_ACTION_FOLDER}")
    print(f"Session: {SESSION_PATH}")
    print(f"Check interval: {CHECK_INTERVAL} seconds")
    print("-" * 60)
    
    # Ensure directories exist
    ensure_directories()
    
    print("NOTE: First run requires QR code scan to login.")
    print("      Subsequent runs will use saved session.")
    print("=" * 60)
    
    try:
        monitor_whatsapp()
    except Exception as e:
        print(f"[ERROR] Fatal error: {e}")
    
    print("[INFO] WhatsApp watcher stopped.")


if __name__ == "__main__":
    main()
