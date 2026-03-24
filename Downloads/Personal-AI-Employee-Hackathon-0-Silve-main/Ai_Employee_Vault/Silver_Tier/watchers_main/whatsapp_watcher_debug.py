"""
WhatsApp Watcher - Debug Version
=================================
Monitors WhatsApp Web for unread messages with specific keywords.
Enhanced version with better selectors and detailed logging.

Run: python watchers/whatsapp_watcher_debug.py
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

# Configuration
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SESSION_PATH = os.path.join(PROJECT_ROOT, "session", "whatsapp")
NEEDS_ACTION_FOLDER = os.path.join(PROJECT_ROOT, "Needs_Action")
CHECK_INTERVAL = 15  # Reduced for faster testing
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


def save_page_screenshot(page, filename: str):
    """Save screenshot for debugging."""
    try:
        screenshot_path = os.path.join(PROJECT_ROOT, "Logs", filename)
        page.screenshot(path=screenshot_path, full_page=False)
        print(f"[DEBUG] Screenshot saved: {screenshot_path}")
    except Exception as e:
        print(f"[DEBUG] Could not save screenshot: {e}")


def monitor_whatsapp():
    """Monitor WhatsApp Web for new important messages."""

    with sync_playwright() as p:
        # Launch browser with persistent context
        print("[INFO] Launching browser with persistent session...")
        print(f"[INFO] Session path: {SESSION_PATH}")

        context = p.chromium.launch_persistent_context(
            user_data_dir=SESSION_PATH,
            headless=False,  # Show browser for QR code scan
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
            print("[INFO] You have 120 seconds to scan QR code if needed")
            page.wait_for_selector('div[data-testid="default-user"], div[data-testid="chat-list"]', timeout=120000)
            print("[INFO] WhatsApp loaded successfully!")
        except PlaywrightTimeout:
            print("[WARNING] WhatsApp did not load within timeout. Continuing anyway...")

        # Save initial screenshot
        try:
            os.makedirs(os.path.join(PROJECT_ROOT, "Logs"), exist_ok=True)
            save_page_screenshot(page, "whatsapp_initial.png")
        except:
            pass

        print("-" * 60)
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Monitoring started...")
        print(f"Checking every {CHECK_INTERVAL} seconds")
        print("Press Ctrl+C to stop")
        print("-" * 60)

        try:
            iteration = 0
            while True:
                iteration += 1
                try:
                    # Debug: Check page URL and title
                    current_url = page.url
                    print(f"\n{'='*50}")
                    print(f"[ITERATION {iteration}] {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                    print(f"[DEBUG] Current URL: {current_url}")
                    
                    # Check if we're on WhatsApp Web
                    if "web.whatsapp.com" not in current_url:
                        print("[WARNING] Not on WhatsApp Web! Redirecting...")
                        page.goto(WHATSAPP_URL)
                        time.sleep(5)
                        continue
                    
                    # Get page title
                    page_title = page.title()
                    print(f"[DEBUG] Page title: {page_title}")
                    
                    # Look for chat list container
                    chat_list = page.query_selector('div[data-testid="chat-list"]')
                    if not chat_list:
                        print("[DEBUG] Chat list not found - may not be logged in")
                        save_page_screenshot(page, "whatsapp_no_chatlist.png")
                        time.sleep(CHECK_INTERVAL)
                        continue
                    
                    print("[DEBUG] Chat list found!")
                    
                    # Look for chat items with unread indicators
                    # Try multiple selector strategies
                    chats_with_unread = []
                    
                    # Strategy 1: Find all chat items and check for unread badges
                    all_chats = page.query_selector_all('div[role="listitem"]')
                    print(f"[DEBUG] Found {len(all_chats)} total chat items")
                    
                    for idx, chat in enumerate(all_chats):
                        try:
                            # Get chat name/contact
                            contact = "Unknown"
                            name_elem = chat.query_selector('span[dir="auto"][title]')
                            if name_elem:
                                contact = name_elem.get_attribute('title')
                            else:
                                name_elem = chat.query_selector('div[title]')
                                if name_elem:
                                    contact = name_elem.get_attribute('title')
                            
                            # Check for unread badge
                            unread_badge = chat.query_selector('span[data-testid="unread-count-badge"]')
                            if not unread_badge:
                                # Try alternative selectors
                                unread_badge = chat.query_selector('span[class*="unread"]')
                            if not unread_badge:
                                # Try any span with a number
                                badge_spans = chat.query_selector_all('span')
                                for span in badge_spans:
                                    try:
                                        text = span.inner_text().strip()
                                        if text and text.isdigit() and int(text) > 0:
                                            unread_badge = span
                                            break
                                    except:
                                        continue
                            
                            if not unread_badge:
                                continue
                            
                            # Get unread count
                            try:
                                unread_count = unread_badge.inner_text().strip()
                            except:
                                unread_count = "?"
                            
                            # Get last message preview
                            message = ""
                            msg_elem = chat.query_selector('span[data-testid="last-message-content"]')
                            if msg_elem:
                                message = msg_elem.inner_text().strip()
                            else:
                                # Try to find message in any span
                                spans = chat.query_selector_all('span')
                                for span in spans:
                                    try:
                                        text = span.inner_text().strip()
                                        if len(text) > 5 and len(text) < 200:
                                            message = text
                                            break
                                    except:
                                        continue
                            
                            if not message:
                                message = "[No message preview available]"
                            
                            chats_with_unread.append({
                                'contact': contact,
                                'unread_count': unread_count,
                                'message': message
                            })
                            
                            print(f"\n[DEBUG] Unread chat found:")
                            print(f"  Contact: {contact}")
                            print(f"  Unread: {unread_count}")
                            print(f"  Message: {message[:80]}...")
                            
                        except Exception as e:
                            print(f"[DEBUG] Error processing chat {idx}: {e}")
                            continue
                    
                    # Process unread chats
                    if not chats_with_unread:
                        print("[DEBUG] No unread messages found")
                    else:
                        print(f"\n[DEBUG] Total unread chats: {len(chats_with_unread)}")
                        
                        for chat_data in chats_with_unread:
                            contact = chat_data['contact']
                            message = chat_data['message']
                            
                            # Create unique ID for message
                            msg_id = f"{contact}:{message[:50]}"
                            
                            # Skip if already processed
                            if msg_id in processed_messages:
                                print(f"[DEBUG] Already processed: {contact}")
                                continue
                            
                            # Check for important keywords
                            if check_important_message(message):
                                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                                filename = create_needs_action_file(contact, message, timestamp)
                                processed_messages.add(msg_id)
                                
                                print(f"\n[{timestamp}] ✅ NEW IMPORTANT MESSAGE!")
                                print(f"  -> Created: {filename}")
                                print(f"     From: {contact}")
                                print(f"     Priority: {get_priority(message)}")
                                print(f"     Keywords: {[kw for kw in IMPORTANT_KEYWORDS if kw in message.lower()]}")
                                print(f"     Message: {message[:100]}...")
                            else:
                                processed_messages.add(msg_id)
                                print(f"[DEBUG] Skipped (no keywords): {contact}")
                    
                    # Save screenshot periodically
                    if iteration % 5 == 0:
                        try:
                            save_page_screenshot(page, f"whatsapp_iter_{iteration}.png")
                        except:
                            pass
                    
                    print(f"\n[DEBUG] Scan complete. Waiting {CHECK_INTERVAL}s...")
                    # Wait before next check
                    time.sleep(CHECK_INTERVAL)

                except Exception as e:
                    print(f"[ERROR] During monitoring: {e}")
                    import traceback
                    traceback.print_exc()
                    time.sleep(5)

        except KeyboardInterrupt:
            print("\n[INFO] Stopping WhatsApp watcher...")

        finally:
            context.close()
            print("[INFO] Browser closed.")


def ensure_directories():
    """Ensure required directories exist."""
    for folder in [NEEDS_ACTION_FOLDER, SESSION_PATH]:
        if not os.path.exists(folder):
            os.makedirs(folder)
            print(f"[INFO] Created directory: {folder}")


def main():
    """Main function to start WhatsApp watcher."""
    print("=" * 60)
    print("WhatsApp Watcher - Debug Version")
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
        import traceback
        traceback.print_exc()

    print("[INFO] WhatsApp watcher stopped.")


if __name__ == "__main__":
    main()
