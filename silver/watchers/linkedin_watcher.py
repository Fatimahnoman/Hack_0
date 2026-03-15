"""
LinkedIn Watcher - Silver Tier
===============================
Monitors LinkedIn for notifications and messages with specific keywords.
Uses Playwright for browser automation with persistent session.

Install: pip install playwright
         playwright install chromium
Setup:
  1. Run script once to login to LinkedIn
  2. Session saved to /session/linkedin for persistent login
Run: python watchers/linkedin_watcher.py

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
SESSION_PATH = os.path.join(PROJECT_ROOT, "session", "linkedin")
NEEDS_ACTION_FOLDER = os.path.join(PROJECT_ROOT, "Needs_Action")
CHECK_INTERVAL = 60  # seconds
LINKEDIN_URL = "https://www.linkedin.com"
LINKEDIN_MESSAGES_URL = "https://www.linkedin.com/messaging/"

# Keywords to monitor (case-insensitive)
IMPORTANT_KEYWORDS = ["urgent", "invoice", "payment", "sales"]

# Track processed notifications/messages
processed_items = set()


def get_priority(content: str) -> str:
    """Determine priority based on keywords."""
    text = content.lower()
    if "urgent" in text:
        return "high"
    elif "invoice" in text or "payment" in text:
        return "medium"
    elif "sales" in text:
        return "normal"
    return "low"


def create_needs_action_file(
    item_type: str, sender: str, subject: str, content: str, timestamp: str
) -> str:
    """Create .md file in Needs_Action folder with YAML frontmatter."""
    priority = get_priority(content)
    file_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Sanitize filename
    safe_sender = re.sub(r"[^a-zA-Z0-9]", "_", sender[:20])
    filename = f"LINKEDIN_{item_type.upper()}_{safe_sender}_{file_timestamp}.md"
    filepath = os.path.join(NEEDS_ACTION_FOLDER, filename)
    
    yaml_content = f"""---
type: linkedin_{item_type}
from: {sender}
subject: {subject}
received: {timestamp}
priority: {priority}
status: pending
---

## Content

{content}

---
*Imported by LinkedIn Watcher on {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}*
"""
    
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(yaml_content)
    
    return filename


def check_important_content(content: str) -> bool:
    """Check if content contains important keywords."""
    text = content.lower()
    return any(keyword in text for keyword in IMPORTANT_KEYWORDS)


def check_messages(page) -> int:
    """Check LinkedIn messages for new important content."""
    new_count = 0
    
    try:
        # Navigate to messages
        page.goto(LINKEDIN_MESSAGES_URL, wait_until="domcontentloaded", timeout=30000)
        time.sleep(3)  # Wait for content to load
        
        # Look for conversation items
        conversations = page.query_selector_all('div.conversation-card')
        
        for conv in conversations:
            try:
                # Get sender name
                sender_elem = conv.query_selector('span.entity-result__title-line')
                if not sender_elem:
                    continue
                sender = sender_elem.inner_text().strip()
                
                # Get message preview
                msg_elem = conv.query_selector('span.t-14')
                if not msg_elem:
                    continue
                message = msg_elem.inner_text().strip()
                
                # Check for unread indicator
                unread = conv.query_selector('span.notification-badge')
                if not unread:
                    continue
                
                # Create unique ID
                item_id = f"msg:{sender}:{message[:50]}"
                
                if item_id in processed_items:
                    continue
                
                # Check for important keywords
                if check_important_content(message):
                    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    filename = create_needs_action_file(
                        "message", sender, f"LinkedIn Message from {sender}", message, timestamp
                    )
                    processed_items.add(item_id)
                    
                    print(f"\n[{timestamp}] New important message!")
                    print(f"  -> Created: {filename}")
                    print(f"     From: {sender}")
                    print(f"     Priority: {get_priority(message)}")
                    print(f"     Content: {message[:100]}...")
                    new_count += 1
                else:
                    processed_items.add(item_id)
            
            except Exception as e:
                continue
    
    except Exception as e:
        print(f"[ERROR] Checking messages: {e}")
    
    return new_count


def check_notifications(page) -> int:
    """Check LinkedIn notifications for important content."""
    new_count = 0
    
    try:
        # Navigate to notifications
        page.goto(f"{LINKEDIN_URL}/notifications/", wait_until="domcontentloaded", timeout=30000)
        time.sleep(3)  # Wait for content to load
        
        # Look for notification items
        notifications = page.query_selector_all('li.notification-item')
        
        for notif in notifications:
            try:
                # Get notification content
                content_elem = notif.query_selector('span.update-components-text')
                if not content_elem:
                    continue
                content = content_elem.inner_text().strip()
                
                # Get sender if available
                sender_elem = notif.query_selector('a.actor-name')
                sender = sender_elem.inner_text().strip() if sender_elem else "Unknown"
                
                # Create unique ID
                item_id = f"notif:{sender}:{content[:50]}"
                
                if item_id in processed_items:
                    continue
                
                # Check for important keywords
                if check_important_content(content):
                    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    filename = create_needs_action_file(
                        "notification", sender, f"LinkedIn Notification", content, timestamp
                    )
                    processed_items.add(item_id)
                    
                    print(f"\n[{timestamp}] New important notification!")
                    print(f"  -> Created: {filename}")
                    print(f"     From: {sender}")
                    print(f"     Priority: {get_priority(content)}")
                    print(f"     Content: {content[:100]}...")
                    new_count += 1
                else:
                    processed_items.add(item_id)
            
            except Exception as e:
                continue
    
    except Exception as e:
        print(f"[ERROR] Checking notifications: {e}")
    
    return new_count


def monitor_linkedin():
    """Monitor LinkedIn for new important messages and notifications."""
    
    with sync_playwright() as p:
        # Launch browser with persistent context
        print("[INFO] Launching browser with persistent session...")
        print(f"[INFO] Session path: {SESSION_PATH}")
        
        context = p.chromium.launch_persistent_context(
            user_data_dir=SESSION_PATH,
            headless=False,  # Show browser for login on first run
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
                "--disable-dev-shm-usage"
            ]
        )
        
        page = context.pages[0]
        
        print("[INFO] Navigating to LinkedIn...")
        page.goto(LINKEDIN_URL)
        
        # Wait for LinkedIn to load
        try:
            print("[INFO] Waiting for LinkedIn to load (login if first time)...")
            page.wait_for_selector('div#global-nav', timeout=120000)
            print("[INFO] LinkedIn loaded successfully!")
        except PlaywrightTimeout:
            print("[WARNING] LinkedIn did not load within timeout. Continuing anyway...")
        
        print("-" * 60)
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Monitoring started...")
        print(f"Checking every {CHECK_INTERVAL} seconds")
        print("Press Ctrl+C to stop")
        print("-" * 60)
        
        try:
            while True:
                try:
                    # Check messages
                    msg_count = check_messages(page)
                    
                    # Check notifications
                    notif_count = check_notifications(page)
                    
                    total_new = msg_count + notif_count
                    
                    if total_new > 0:
                        print(f"  -> {total_new} new important item(s) processed")
                    else:
                        print(f"  -> No new important items")
                    
                    # Wait before next check
                    time.sleep(CHECK_INTERVAL)
                
                except Exception as e:
                    print(f"[ERROR] During monitoring: {e}")
                    time.sleep(5)
        
        except KeyboardInterrupt:
            print("\n[INFO] Stopping LinkedIn watcher...")
        
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
    """Main function to start LinkedIn watcher."""
    print("=" * 60)
    print("LinkedIn Watcher - Silver Tier")
    print("=" * 60)
    print(f"Monitoring: LinkedIn Messages & Notifications")
    print(f"Keywords: {', '.join(IMPORTANT_KEYWORDS)}")
    print(f"Destination: {NEEDS_ACTION_FOLDER}")
    print(f"Session: {SESSION_PATH}")
    print(f"Check interval: {CHECK_INTERVAL} seconds")
    print("-" * 60)
    
    # Ensure directories exist
    ensure_directories()
    
    print("NOTE: First run requires manual login to LinkedIn.")
    print("      Subsequent runs will use saved session.")
    print("=" * 60)
    
    try:
        monitor_linkedin()
    except Exception as e:
        print(f"[ERROR] Fatal error: {e}")
    
    print("[INFO] LinkedIn watcher stopped.")


if __name__ == "__main__":
    main()
