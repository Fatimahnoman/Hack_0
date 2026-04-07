"""
WhatsApp Watcher - Silver Tier (Dual Mode)
=============================================
Mode 1: File Drop (100% Reliable)
  - Copy WhatsApp message → drop in silver/Inbox/
  - Watcher detects and creates Needs_Action file

Mode 2: Browser Automation (Playwright)
  - Monitors WhatsApp Web for unread messages
  - Uses JavaScript injection for DOM extraction

Install: pip install watchdog playwright
         playwright install chromium
Run: python silver/watchers/whatsapp_watcher.py
"""

import os
import re
import sys
import time
import json
from datetime import datetime
from pathlib import Path

# Check for watchdog
try:
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler
except ImportError as e:
    print(f"[ERROR] Missing watchdog: {e}")
    print("[INFO] Run: pip install watchdog")
    sys.exit(1)

# Check for Playwright (optional)
PLAYWRIGHT_AVAILABLE = False
try:
    from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    pass

# Configuration
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SILVER_DIR = PROJECT_ROOT
INBOX_FOLDER = os.path.join(PROJECT_ROOT, "Inbox")
NEEDS_ACTION_FOLDER = os.path.join(SILVER_DIR, "Needs_Action")
LOGS_FOLDER = os.path.join(SILVER_DIR, "Logs")
SESSION_PATH = os.path.join(PROJECT_ROOT, "session", "whatsapp")
CHECK_INTERVAL = 30  # seconds

# Keywords to monitor (case-insensitive)
IMPORTANT_KEYWORDS = ["urgent", "invoice", "payment", "sales"]

# Track processed messages
processed_messages = set()

# Ensure directories exist
os.makedirs(INBOX_FOLDER, exist_ok=True)
os.makedirs(NEEDS_ACTION_FOLDER, exist_ok=True)
os.makedirs(LOGS_FOLDER, exist_ok=True)
os.makedirs(SESSION_PATH, exist_ok=True)


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


def create_needs_action_file(contact: str, message: str, source: str = "file_drop") -> str:
    """Create .md file in Needs_Action folder with YAML frontmatter."""
    priority = get_priority(message)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # Sanitize filename
    safe_contact = re.sub(r"[^a-zA-Z0-9]", "_", contact[:30]) or "Unknown"
    filename = f"WHATSAPP_{safe_contact}_{timestamp}.md"
    filepath = os.path.join(NEEDS_ACTION_FOLDER, filename)

    yaml_content = f"""---
type: whatsapp_message
from: "{contact}"
to: "{contact}"
subject: WhatsApp Message from {contact}
received: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
priority: {priority}
status: pending
source: {source}
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


# =============================================================================
# MODE 1: FILE DROP WATCHER (100% Reliable)
# =============================================================================

class WhatsAppFileHandler(FileSystemEventHandler):
    """Monitors Inbox folder for WhatsApp message files."""

    def __init__(self):
        super().__init__()
        self.processed_files = set()

    def on_created(self, event):
        """Called when a file is created in Inbox."""
        if event.is_directory:
            return

        file_path = event.src_path

        # Skip if already processed
        if file_path in self.processed_files:
            return

        self.processed_files.add(file_path)
        print(f"[{datetime.now().strftime('%H:%M:%S')}] File detected: {os.path.basename(file_path)}")

        try:
            self.process_file(file_path)
        except Exception as e:
            print(f"[ERROR] Failed to process file: {e}")

    def process_file(self, file_path: str):
        """Process a WhatsApp message file."""
        time.sleep(0.5)  # Wait for file to be fully written

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read().strip()

            if not content:
                print("  -> Empty file, skipping")
                return

            # Extract contact name from filename or content
            filename = os.path.basename(file_path)
            contact = filename.replace("WHATSAPP_", "").replace(".txt", "").replace(".md", "")
            contact = contact.replace("_", " ").strip()

            # If contact name is generic, try to extract from content
            if not contact or contact in ["message", "whatsapp", "msg"]:
                # Try to find a name in first line
                first_line = content.split("\n")[0]
                if first_line and len(first_line) < 50:
                    contact = first_line
                    content = "\n".join(content.split("\n")[1:])

            if not contact:
                contact = "WhatsApp Contact"

            # Check for important keywords
            if check_important_message(content):
                filename = create_needs_action_file(contact, content, "file_drop")
                print(f"  -> Created: {filename}")
                print(f"     From: {contact}")
                print(f"     Priority: {get_priority(content)}")
                print(f"     Message: {content[:100]}...")
            else:
                print(f"  -> Not important, skipping")

        except Exception as e:
            print(f"[ERROR] Error processing file: {e}")


# =============================================================================
# MODE 2: BROWSER AUTOMATION (Playwright)
# =============================================================================

def monitor_whatsapp_browser():
    """Monitor WhatsApp Web using Playwright browser automation."""
    if not PLAYWRIGHT_AVAILABLE:
        print("[WARN] Playwright not available, skipping browser mode")
        return

    print("[INFO] Starting browser automation mode...")
    print("[INFO] Scan QR code on first run.")

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(
                headless=False,
                args=["--no-sandbox", "--disable-dev-shm-usage"]
            )
            context = browser.new_context(
                viewport={"width": 1280, "height": 800},
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            )
            page = context.new_page()

            print("[INFO] Navigating to WhatsApp Web...")
            page.goto("https://web.whatsapp.com", wait_until="domcontentloaded", timeout=60000)

            try:
                page.wait_for_selector('div[data-testid="chat-list"]', timeout=180000)
                print("[INFO] WhatsApp loaded!")
            except PlaywrightTimeout:
                print("[ERROR] WhatsApp did not load. Skipping browser mode.")
                browser.close()
                return

            print("[INFO] Browser monitoring started...")

            while True:
                try:
                    chats_data = page.evaluate("""
                        () => {
                            const chats = [];
                            const chatItems = document.querySelectorAll('div[role="gridcell"]');
                            for (const item of chatItems) {
                                try {
                                    let contact = '';
                                    const titleEl = item.querySelector('h2, span[title]');
                                    if (titleEl) contact = titleEl.getAttribute('title') || titleEl.textContent || '';
                                    contact = contact.trim();
                                    if (!contact || contact.length < 2) continue;
                                    
                                    let message = '';
                                    const msgEl = item.querySelector('span[data-testid="last-message-content"]');
                                    if (msgEl) message = msgEl.textContent.trim();
                                    if (!message) continue;
                                    
                                    let unread = 0;
                                    const unreadEl = item.querySelector('span[data-testid="unread-count"]');
                                    if (unreadEl) {
                                        const count = parseInt(unreadEl.textContent);
                                        unread = isNaN(count) ? 1 : count;
                                    }
                                    
                                    chats.push({ contact: contact.substring(0, 50), message: message.substring(0, 300), unread });
                                } catch (e) { continue; }
                            }
                            return chats;
                        }
                    """)

                    if chats_data:
                        for chat in chats_data:
                            contact = chat.get('contact', '')
                            message = chat.get('message', '')
                            unread = chat.get('unread', 0)

                            if not contact or not message or unread == 0:
                                continue

                            msg_id = f"{contact}:{message[:50]}"
                            if msg_id in processed_messages:
                                continue

                            if check_important_message(message):
                                filename = create_needs_action_file(contact, message, "browser")
                                processed_messages.add(msg_id)
                                print(f"[{datetime.now().strftime('%H:%M:%S')}] WhatsApp message detected: {contact}")
                                print(f"  -> Created: {filename}")
                            else:
                                processed_messages.add(msg_id)

                except Exception as e:
                    print(f"[ERROR] Browser monitoring error: {e}")

                time.sleep(CHECK_INTERVAL)

    except Exception as e:
        print(f"[ERROR] Browser automation failed: {e}")
        print("[INFO] Falling back to file drop mode...")


# =============================================================================
# MAIN
# =============================================================================

def main():
    """Main function - runs both modes."""
    print("=" * 60)
    print("WhatsApp Watcher - Silver Tier (Dual Mode)")
    print("=" * 60)
    print(f"Mode 1: File Drop - Monitoring {INBOX_FOLDER}")
    print(f"Mode 2: Browser Automation - WhatsApp Web")
    print(f"Keywords: {', '.join(IMPORTANT_KEYWORDS)}")
    print(f"Destination: {NEEDS_ACTION_FOLDER}")
    print(f"Check interval: {CHECK_INTERVAL} seconds")
    print("-" * 60)
    print("USAGE:")
    print("  1. File Drop: Copy WhatsApp message → save as .txt in Inbox/")
    print("  2. Browser: WhatsApp Web will open for monitoring")
    print("-" * 60)

    # Start File Drop Watcher
    print("[INFO] Starting file drop watcher...")
    event_handler = WhatsAppFileHandler()
    observer = Observer()
    observer.schedule(event_handler, INBOX_FOLDER, recursive=False)
    observer.start()
    print(f"[{datetime.now().strftime('%H:%M:%S')}] File drop watcher started!")

    # Start Browser Automation (runs in parallel)
    print("[INFO] Starting browser automation...")

    try:
        # Run browser monitoring in a simple loop alongside file watcher
        monitor_whatsapp_browser()
    except KeyboardInterrupt:
        print("\n[INFO] Stopping WhatsApp watcher...")
    finally:
        observer.stop()
        observer.join()
        print("[INFO] WhatsApp watcher stopped.")


if __name__ == "__main__":
    main()
