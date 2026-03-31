"""
Gmail Watcher - SIMPLE VERSION (Guaranteed to Work)
====================================================
This is a simplified version that works reliably.

Run: python watchers/gmail_watcher_simple.py
"""

import time
from datetime import datetime
from pathlib import Path
from playwright.sync_api import sync_playwright

# Configuration
PROJECT_ROOT = Path(__file__).resolve().parent.parent
SESSION_PATH = PROJECT_ROOT / "session" / "gmail"
NEEDS_ACTION_FOLDER = PROJECT_ROOT / "Needs_Action"
LOGS_FOLDER = PROJECT_ROOT / "Logs"
DEBUG_SCREENSHOTS = PROJECT_ROOT / "debug_gmail"

# Create folders
for folder in [SESSION_PATH, NEEDS_ACTION_FOLDER, LOGS_FOLDER, DEBUG_SCREENSHOTS]:
    folder.mkdir(parents=True, exist_ok=True)

# Keywords to monitor
IMPORTANT_KEYWORDS = [
    "urgent", "sales", "payment", "invoice", "deal", "order",
    "client", "customer", "quotation", "proposal", "overdue",
    "follow up", "meeting", "booking", "asap"
]

def take_screenshot(page, name: str):
    """Take screenshot for debugging."""
    try:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        screenshot_path = DEBUG_SCREENSHOTS / f"{name}_{timestamp}.png"
        page.screenshot(path=str(screenshot_path), full_page=True)
        print(f"[SCREENSHOT] {screenshot_path.name}")
    except Exception as e:
        print(f"[SCREENSHOT ERROR] {e}")

def check_keywords(text: str) -> bool:
    """Check if text contains important keywords."""
    if not text:
        return False
    text_lower = text.lower()
    return any(kw in text_lower for kw in IMPORTANT_KEYWORDS)

def create_needs_action_file(sender: str, subject: str, content: str) -> str:
    """Create .md file in Needs_Action folder."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_sender = "".join(c if c.isalnum() else "_" for c in sender[:20])
    safe_subject = "".join(c if c.isalnum() else "_" for c in subject[:30])
    filename = f"GMAIL_{safe_sender}_{safe_subject}_{timestamp}.md"
    filepath = NEEDS_ACTION_FOLDER / filename
    
    md_content = f"""---
type: email
from: {sender}
subject: {subject}
received: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
priority: high
status: pending
---

## Content

{content}

---
*Imported by Gmail Watcher*
"""
    
    with open(filepath, "w", encoding='utf-8') as f:
        f.write(md_content)
    
    print(f"✓ Created: {filename}")
    return filename

def main():
    print("=" * 70)
    print("GMAIL WATCHER - SIMPLE VERSION")
    print("=" * 70)
    print(f"Session: {SESSION_PATH}")
    print(f"Keywords: {', '.join(IMPORTANT_KEYWORDS)}")
    print(f"Debug: {DEBUG_SCREENSHOTS}")
    print("=" * 70)
    print()
    print("INSTRUCTIONS:")
    print("1. Browser will open")
    print("2. Login to Gmail if not already logged in")
    print("3. Wait for inbox to fully load")
    print("4. Watcher will automatically check for emails with keywords")
    print("5. Press Ctrl+C to stop")
    print()
    print("=" * 70)
    print()

    with sync_playwright() as p:
        print("Launching browser...")
        
        # Launch browser with persistent session
        context = p.chromium.launch_persistent_context(
            user_data_dir=str(SESSION_PATH),
            headless=False,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
                "--disable-dev-shm-usage",
                "--window-size=1366,768"
            ],
            viewport={"width": 1366, "height": 768},
            timeout=120000
        )
        
        page = context.pages[0] if context.pages else context.new_page()
        
        # Navigate to Gmail
        print("Navigating to Gmail...")
        page.goto("https://mail.google.com/mail/u/0/#inbox", wait_until="domcontentloaded")
        take_screenshot(page, "01_gmail_opened")
        
        print()
        print("=" * 70)
        print("WAIT FOR GMAIL TO LOAD COMPLETELY")
        print("=" * 70)
        print()
        print("You should see:")
        print("  ✓ Your inbox")
        print("  ✓ Email list")
        print("  ✓ Search bar at top")
        print()
        print("If you see login page:")
        print("  → Login to your Gmail account")
        print()
        print("Waiting 30 seconds for you to login/load Gmail...")
        print()
        
        # Wait for user to login/load
        for i in range(30, 0, -1):
            print(f"\r  Time remaining: {i} seconds", end="")
            time.sleep(1)
        
        print("\n")
        take_screenshot(page, "02_after_wait")
        
        # Check if logged in
        current_url = page.url
        print(f"Current URL: {current_url}")
        
        if "mail.google.com" not in current_url:
            print()
            print("⚠️  Not on Gmail yet!")
            print("Please login manually, then press ENTER to continue...")
            input("> Press ENTER when logged in...")
            page.goto("https://mail.google.com/mail/u/0/#inbox")
            time.sleep(5)
            take_screenshot(page, "03_after_login")
        
        print()
        print("=" * 70)
        print("GMAIL LOADED - STARTING MONITORING")
        print("=" * 70)
        print()
        
        processed_emails = set()
        check_count = 0
        
        try:
            while True:
                check_count += 1
                print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Check #{check_count}")
                
                # Take screenshot every 5 checks
                if check_count % 5 == 0:
                    take_screenshot(page, f"check_{check_count}")
                
                # Get all email rows
                try:
                    # Wait for email rows to appear
                    page.wait_for_selector('tr[role="row"]', timeout=10000)
                    email_rows = page.query_selector_all('tr[role="row"]')
                    print(f"  Found {len(email_rows)} email rows")
                    
                    for email in email_rows[:10]:  # Check first 10 emails
                        try:
                            text = email.inner_text().lower()
                            
                            # Skip if already processed
                            email_id = hash(text[:100])
                            if email_id in processed_emails:
                                continue
                            
                            # Check keywords
                            if not check_keywords(text):
                                processed_emails.add(email_id)
                                continue
                            
                            # Extract sender and subject
                            sender = "Unknown"
                            subject = "No subject"
                            
                            try:
                                sender_elem = email.query_selector('span.bV, [data-email]')
                                if sender_elem:
                                    sender = sender_elem.inner_text().strip()
                            except:
                                pass
                            
                            try:
                                subject_elem = email.query_selector('span.bog, span.y6')
                                if subject_elem:
                                    subject = subject_elem.inner_text().strip()
                            except:
                                pass
                            
                            # Create needs action file
                            filename = create_needs_action_file(sender, subject, text)
                            processed_emails.add(email_id)
                            
                            print(f"  ✓ IMPORTANT: {sender} - {subject[:50]}")
                            take_screenshot(page, "important_email")
                            
                        except Exception as e:
                            print(f"  [DEBUG] Email error: {e}")
                            continue
                    
                    print(f"  ✓ Monitoring... ({len(processed_emails)} emails checked)")
                    
                except Exception as e:
                    print(f"  [ERROR] Check error: {e}")
                
                # Wait before next check
                time.sleep(30)
                
        except KeyboardInterrupt:
            print("\n\nStopped by user")
        finally:
            print("Closing browser...")
            take_screenshot(page, "final_shutdown")
            context.close()
            print("Gmail Watcher stopped")

if __name__ == "__main__":
    main()
