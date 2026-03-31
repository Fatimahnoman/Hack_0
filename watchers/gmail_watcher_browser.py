"""
Gmail Watcher - Browser-Based Version (FIXED v2)
==============================================
Monitors Gmail for unread messages with specific keywords in a visible browser.

Fixes:
1. Ensures headless=False for visible browser
2. Handles Google login/redirect properly
3. Uses better selectors for Gmail elements
4. Adds proper wait states and error handling
5. Takes screenshots for debugging

Install: pip install playwright && playwright install chromium
Run: python watchers/gmail_watcher_browser.py
"""

import os
import re
import time
from datetime import datetime
from pathlib import Path
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout

# Configuration
PROJECT_ROOT = Path(__file__).resolve().parent.parent
GOLD_DIR = PROJECT_ROOT / "gold"
SESSION_PATH = PROJECT_ROOT / "session" / "gmail"
NEEDS_ACTION_FOLDER = GOLD_DIR / "needs_action"
LOGS_FOLDER = GOLD_DIR / "logs"
DEBUG_SCREENSHOTS = PROJECT_ROOT / "debug_gmail"

# Create debug folder
DEBUG_SCREENSHOTS.mkdir(parents=True, exist_ok=True)

# Keywords to monitor (case-insensitive) - ENFORCED KEYWORDS
IMPORTANT_KEYWORDS = [
    "urgent", "sales", "payment", "invoice", "deal", "order",
    "client", "customer", "quotation", "proposal", "overdue",
    "follow up", "meeting", "booking", "asap"
]

# Timing
CHECK_INTERVAL = 30  # seconds
LOGIN_TIMEOUT = 120  # seconds
ACTION_DELAY = 2

def ensure_directories():
    for d in [SESSION_PATH, NEEDS_ACTION_FOLDER, LOGS_FOLDER, DEBUG_SCREENSHOTS]:
        d.mkdir(parents=True, exist_ok=True)

def take_screenshot(page, name: str):
    """Take a screenshot for debugging."""
    try:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        screenshot_path = DEBUG_SCREENSHOTS / f"{name}_{timestamp}.png"
        page.screenshot(path=str(screenshot_path), full_page=True)
        print(f"[SCREENSHOT] Saved: {screenshot_path.name}")
    except Exception as e:
        print(f"[SCREENSHOT ERROR] {e}")

def is_logged_in(page) -> bool:
    """Check if user is logged into Gmail."""
    try:
        url = page.url.lower()
        # If we're on the inbox page, we're logged in
        if "mail.google.com" in url and "#inbox" in url:
            return True
        # Check for login page
        if "accounts.google.com" in url or "signin" in url or "ServiceLogin" in url:
            return False
        # Check for inbox elements
        inbox_indicators = [
            '[aria-label="Inbox"]',
            '[data-tooltip="Inbox"]',
            'a[href="#inbox"]',
            '[role="main"]',  # Gmail main content area
            'div[aria-label="Side panel"]',
            'div[aria-label="Gmail"]',
            'input[aria-label="Search mail"]'  # Search bar only visible when logged in
        ]
        for selector in inbox_indicators:
            try:
                if page.query_selector(selector):
                    return True
            except:
                pass
        return False
    except Exception as e:
        print(f"[DEBUG] Login check error: {e}")
        return False

def wait_for_inbox_load(page, timeout: int = 30) -> bool:
    """Wait for inbox to fully load."""
    print("[WAIT] Waiting for inbox to load...")
    start = time.time()
    
    while time.time() - start < timeout:
        try:
            # Check for inbox container
            inbox = page.query_selector('div[aria-label="Inbox"], div[role="main"]')
            if inbox:
                # Check for email rows
                email_rows = page.query_selector_all('tr[role="row"], tr[data-legacy-message-id]')
                if email_rows:
                    print(f"[SUCCESS] Inbox loaded with {len(email_rows)} emails")
                    return True
                print(f"[WAIT] Found inbox but no emails yet...")
            time.sleep(1)
        except Exception as e:
            print(f"[DEBUG] Wait error: {e}")
            time.sleep(1)
    
    print("[ERROR] Inbox load timeout!")
    return False

def wait_for_login(page, timeout: int = LOGIN_TIMEOUT) -> bool:
    """Wait for user to log in to Google."""
    print("=" * 60)
    print("MANUAL LOGIN REQUIRED - Please log in to Gmail")
    print("=" * 60)
    print("1. If you see the Google sign-in page, enter your credentials")
    print("2. If you see a QR code prompt, scan it with your phone")
    print("3. Wait for the inbox to load")
    print("=" * 60)
    
    start = time.time()
    last_url = ""
    screenshot_count = 0
    
    while time.time() - start < timeout:
        try:
            current_url = page.url
            # Detect navigation
            if current_url != last_url:
                print(f"[{int(time.time() - start)}s] URL: {current_url[:80]}")
                last_url = current_url
                
                # Take screenshot on URL change
                screenshot_count += 1
                if screenshot_count <= 5:  # Limit screenshots
                    take_screenshot(page, f"login_step_{screenshot_count}")
            
            if is_logged_in(page):
                print("✓ Login detected!")
                # Wait for inbox to load
                if wait_for_inbox_load(page, timeout=30):
                    return True
            
            time.sleep(3)
        except Exception as e:
            print(f"[DEBUG] Wait error: {e}")
            time.sleep(2)
    
    print("✗ Login timeout!")
    take_screenshot(page, "login_timeout_final")
    return False

def check_keywords(text: str) -> bool:
    """Check if text contains important keywords."""
    if not text:
        return False
    text_lower = text.lower()
    return any(kw in text_lower for kw in IMPORTANT_KEYWORDS)

def get_priority(text: str) -> str:
    """Determine priority based on keywords."""
    text_lower = text.lower()
    if "urgent" in text_lower or "asap" in text_lower:
        return "high"
    elif "invoice" in text_lower or "payment" in text_lower or "overdue" in text_lower:
        return "medium"
    elif "sales" in text_lower or "deal" in text_lower or "order" in text_lower:
        return "normal"
    return "low"

def create_needs_action_file(sender: str, subject: str, content: str, logger=None) -> str:
    """Create .md file in Needs_Action folder with YAML frontmatter."""
    priority = get_priority(content)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Sanitize filename
    safe_sender = re.sub(r'[^a-zA-Z0-9]', '_', sender[:20])
    safe_subject = re.sub(r'[^a-zA-Z0-9]', '_', subject[:30])
    filename = f"GMAIL_{safe_sender}_{safe_subject}_{ts}.md"
    filepath = NEEDS_ACTION_FOLDER / filename
    
    yaml_content = f"""---
type: email
from: {sender}
subject: {subject}
received: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
priority: {priority}
status: pending
---

## Content

{content}

---
*Imported by Gmail Watcher on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*
"""
    
    with open(filepath, "w", encoding='utf-8') as f:
        f.write(yaml_content)
    
    if logger:
        logger.info(f"Created: {filename}")
    else:
        print(f"✓ Created: {filename}")
    
    return filename

def main():
    ensure_directories()
    print("=" * 60)
    print("Gmail Browser Watcher - Starting (FIXED v2)")
    print("=" * 60)
    print(f"Session Path: {SESSION_PATH}")
    print(f"Monitoring Keywords: {', '.join(IMPORTANT_KEYWORDS)}")
    print(f"Check Interval: {CHECK_INTERVAL} seconds")
    print(f"Debug Screenshots: {DEBUG_SCREENSHOTS}")
    print("=" * 60)

    with sync_playwright() as p:
        print("Launching Firefox browser with visible window...")
        
        # Launch with persistent context to save login session
        context = p.firefox.launch_persistent_context(
            user_data_dir=str(SESSION_PATH),
            headless=False,
            args=[],
            viewport={"width": 1366, "height": 768},
            timeout=120000
        )
        
        page = context.pages[0] if context.pages else context.new_page()
        page.set_default_timeout(60000)
        
        # Navigate to Gmail
        print("Navigating to Gmail...")
        try:
            page.goto("https://mail.google.com/mail/u/0/#inbox", 
                     wait_until="domcontentloaded", 
                     timeout=60000)
            page.wait_for_load_state('networkidle', timeout=60000)
            take_screenshot(page, "initial_navigation")
        except Exception as e:
            print(f"[WARNING] Initial navigation issue: {e}")
            take_screenshot(page, "navigation_error")
        
        # Check if logged in
        if not is_logged_in(page):
            print("Not logged in to Gmail")
            take_screenshot(page, "not_logged_in")
            if not wait_for_login(page):
                print("Login failed or timed out. Please restart the watcher.")
                context.close()
                return
        
        # Ensure we're on the inbox page
        if "#inbox" not in page.url:
            print("Navigating to inbox...")
            page.goto("https://mail.google.com/mail/u/0/#inbox", 
                     wait_until="domcontentloaded",
                     timeout=30000)
            time.sleep(ACTION_DELAY)
        
        # Wait for inbox to fully load
        print("Waiting for inbox to fully load...")
        if not wait_for_inbox_load(page, timeout=30):
            print("[ERROR] Inbox did not load properly!")
            take_screenshot(page, "inbox_load_failure")
        else:
            take_screenshot(page, "inbox_loaded_success")
        
        print("=" * 60)
        print("✓ Gmail Watcher is now monitoring your inbox")
        print("✓ Checking for unread emails with important keywords")
        print("✓ Press Ctrl+C to stop")
        print("=" * 60)
        
        # Track processed emails to avoid duplicates
        processed_emails = set()

        try:
            while True:
                try:
                    # Verify we're still on Gmail
                    if "mail.google.com" not in page.url:
                        print("[WARNING] Navigated away from Gmail, returning...")
                        page.goto("https://mail.google.com/mail/u/0/#inbox",
                                 wait_until="domcontentloaded",
                                 timeout=30000)
                        time.sleep(ACTION_DELAY)
                    
                    # Wait for inbox to load
                    try:
                        page.wait_for_selector('div[aria-label="Inbox"]', timeout=10000)
                    except:
                        print("[WARNING] Inbox not fully loaded, waiting...")
                        time.sleep(3)
                        continue
                    
                    # Take periodic screenshot
                    screenshot_counter = 0
                    screenshot_counter += 1
                    if screenshot_counter % 10 == 0:  # Every 10 checks
                        take_screenshot(page, "monitoring_check")
                    
                    # Find unread emails - Gmail uses various selectors
                    # Primary: tr.zE (unread), also try [aria-label="Inbox"] rows
                    unread_selectors = [
                        'tr.zE',  # Classic Gmail unread
                        'tr[aria-level][aria-selected="false"]',  # New Gmail
                        'div[role="row"][aria-level]',  # Alternative
                        'tr[data-legacy-message-id]'  # Fallback
                    ]
                    
                    unread_emails = []
                    for selector in unread_selectors:
                        try:
                            emails = page.query_selector_all(selector)
                            if emails:
                                print(f"[DEBUG] Found {len(emails)} emails via {selector}")
                                unread_emails = emails
                                break
                        except Exception as e:
                            print(f"[DEBUG] Selector {selector} failed: {e}")
                    
                    if not unread_emails:
                        # Try broader selector
                        email_rows = page.query_selector_all('tr[data-legacy-message-id], tr[role="row"]')
                        print(f"[DEBUG] Found {len(email_rows)} total email rows")
                        unread_emails = email_rows[:20]  # Check first 20
                    
                    for email in unread_emails:
                        try:
                            # Get email text content
                            text = email.inner_text().lower()
                            
                            # Skip if already processed
                            email_id = hash(text[:100])
                            if email_id in processed_emails:
                                continue
                            
                            # Check for keywords
                            if not check_keywords(text):
                                processed_emails.add(email_id)
                                continue
                            
                            # Extract sender and subject
                            sender = "Unknown"
                            subject = "No subject"
                            
                            # Try various Gmail selectors
                            try:
                                sender_elem = email.query_selector('span.bV, span[email], [data-email]')
                                if sender_elem:
                                    sender = sender_elem.inner_text().strip() or sender
                            except:
                                pass
                            
                            try:
                                subject_elem = email.query_selector('span.bog, span.y6, [data-thread-id]')
                                if subject_elem:
                                    subject = subject_elem.inner_text().strip() or subject
                            except:
                                pass
                            
                            # Create needs action file
                            filename = create_needs_action_file(sender, subject, text)
                            processed_emails.add(email_id)
                            print(f"✓ IMPORTANT EMAIL FOUND: {sender} - {subject[:50]}")
                            take_screenshot(page, "important_email_found")
                            
                            # Mark as read by clicking it
                            try:
                                email.click()
                                time.sleep(1)
                                # Go back to inbox
                                page.goto("https://mail.google.com/mail/u/0/#inbox",
                                         wait_until="domcontentloaded",
                                         timeout=30000)
                                time.sleep(ACTION_DELAY)
                            except Exception as e:
                                print(f"[DEBUG] Error marking as read: {e}")
                            
                            break  # Process one email at a time
                            
                        except Exception as e:
                            print(f"[DEBUG] Error processing email: {e}")
                            continue
                    
                    # Status update
                    current_time = datetime.now().strftime("%H:%M:%S")
                    print(f"[{current_time}] Monitoring Gmail... ({len(processed_emails)} emails checked)")
                    time.sleep(CHECK_INTERVAL)
                    
                except PlaywrightTimeout as e:
                    print(f"[WARNING] Timeout: {e}")
                    take_screenshot(page, "timeout_error")
                    time.sleep(5)
                except Exception as e:
                    print(f"[ERROR] Monitoring error: {e}")
                    take_screenshot(page, "monitoring_error")
                    time.sleep(5)
                    
        except KeyboardInterrupt:
            print("\nStopped by user")
        finally:
            print("Closing browser...")
            take_screenshot(page, "final_shutdown")
            context.close()
            print("Gmail Watcher stopped")

if __name__ == "__main__":
    main()
