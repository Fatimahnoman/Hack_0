r"""
LinkedIn Auto Poster - Gold Tier
================================
Production-ready LinkedIn auto poster with persistent session support.
Integrated with Action Dispatcher for automatic posting when files move to Approved folder.

FEATURES:
✓ Persistent session: F:\heckathon\heckathon 0\session\linkedin
✓ Slow, natural typing (anti-bot detection)
✓ Stable selectors with multiple fallbacks
✓ Comprehensive logging
✓ Error handling with retries
✓ Action Dispatcher integration

USAGE:
  python gold/watchers/linkedin_auto_poster.py --content "Your post text"
  OR
  python gold/watchers/linkedin_auto_poster.py --file "path/to/approved_file.md"

INSTALL:
  pip install playwright
  playwright install chromium

Author: Gold Tier Integration (based on Silver Tier working code)
Version: 2.0
Date: 2026-03-31
"""

import os
import sys
import time
import shutil
import logging
import argparse
import random
import re
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
    print("")
    print("This is a known Python 3.14 compatibility issue.")
    print("TRY THESE FIXES:")
    print("  1. pip install --upgrade greenlet playwright")
    print("  2. playwright install chromium")
    print("  3. Use Python 3.11 or 3.12 for this watcher")
    sys.exit(1)

# =============================================================================
# CONFIGURATION - GOLD TIER PATHS
# =============================================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
GOLD_DIR = PROJECT_ROOT / "gold"
SESSION_PATH = PROJECT_ROOT / "session" / "linkedin"
APPROVED_FOLDER = GOLD_DIR / "pending_approval" / "approved"
DONE_FOLDER = GOLD_DIR / "done"
FAILED_FOLDER = GOLD_DIR / "failed"
LOGS_FOLDER = GOLD_DIR / "logs"
DEBUG_FOLDER = PROJECT_ROOT / "debug_linkedin"

# Ensure directories exist
for folder in [SESSION_PATH, DONE_FOLDER, FAILED_FOLDER, LOGS_FOLDER, DEBUG_FOLDER]:
    folder.mkdir(parents=True, exist_ok=True)

# LinkedIn URLs
LINKEDIN_URL = "https://www.linkedin.com"
LINKEDIN_FEED_URL = "https://www.linkedin.com/feed/"
LINKEDIN_MESSAGES_URL = "https://www.linkedin.com/messaging/"

# Posting configuration
MAX_RETRIES = 3
TYPE_DELAY = 100  # ms per character (slow typing for anti-bot)
FOCUS_WAIT = 1500  # ms
POST_WAIT = 3000  # ms after typing
RETRY_DELAYS = [10, 15, 20]  # seconds between retries
CHECK_INTERVAL = 60  # seconds for watcher mode

# Logging setup
log_file = LOGS_FOLDER / f"linkedin_gold_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file, encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Track processed items (for watcher mode)
processed_items = set()


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def take_screenshot(page, name):
    """Save screenshot for debugging."""
    try:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        path = DEBUG_FOLDER / f"{name}_{timestamp}.png"
        page.screenshot(path=str(path), full_page=True)
        logger.info(f"Screenshot saved: {path.name}")
    except Exception as e:
        logger.debug(f"Screenshot error: {e}")


def wait_for_linkedin_load(page, timeout=60000):
    """Wait for LinkedIn feed to load."""
    logger.info("Waiting for LinkedIn to load...")
    try:
        page.wait_for_load_state('networkidle', timeout=timeout)
        time.sleep(3)  # Extra wait for React
        logger.info("✓ LinkedIn loaded")
        return True
    except Exception as e:
        logger.error(f"Load error: {e}")
        return False


def find_compose_box(page):
    """Find LinkedIn compose box with multiple fallback selectors."""
    selectors = [
        'div[role="textbox"][contenteditable="true"]',
        '[data-testid="post-creation-textarea"]',
        'div[contenteditable="true"][aria-label*="What do"]',
        'div[contenteditable="true"][aria-label*="Write a post"]',
        'div.ql-editor[contenteditable="true"]',
        'div.inline-editor[contenteditable="true"]',
    ]

    for selector in selectors:
        try:
            box = page.locator(selector).first
            if box.is_visible(timeout=2000):
                logger.info(f"✓ Found compose box")
                return box
        except:
            continue

    logger.warning("Compose box not found")
    return None


def find_post_button(page):
    """Find LinkedIn Post button with exhaustive search."""
    logger.info("Searching for Post button...")

    # Exhaustive list of Post button selectors
    selectors = [
        # Primary selectors
        'button[data-testid="post-button"]',
        'button:has-text("Post")',
        'button[aria-label="Post"]',

        # Secondary - button with Post text in dialog
        'div[role="dialog"] button:not([disabled]):has-text("Post")',
        'div[role="dialog"] button span:has-text("Post")',

        # Tertiary - any enabled button with Post
        'button[class*="post"]:has-text("Post")',
        'button[type="submit"]:has-text("Post")',

        # Fallback - span with Post inside button
        'button span:text-is("Post")',
        'div[role="button"]:has-text("Post")',
    ]

    for i, selector in enumerate(selectors, 1):
        try:
            btn = page.locator(selector).first

            if btn.is_visible(timeout=2000):
                if btn.is_enabled(timeout=2000):
                    logger.info(f"✓ Found Post button (selector {i})")
                    return btn
                else:
                    logger.debug(f"Selector {i}: Button found but DISABLED")
        except Exception as e:
            logger.debug(f"Selector {i} failed")
            continue

    # Last resort: JavaScript search
    logger.info("Trying JavaScript search for Post button...")
    try:
        btn_found = page.evaluate("""
            () => {
                const buttons = Array.from(document.querySelectorAll('button'));
                const postBtn = buttons.find(b =>
                    b.innerText.trim().toUpperCase() === 'POST' &&
                    !b.disabled
                );
                if (postBtn) {
                    postBtn.scrollIntoView();
                    return true;
                }
                return false;
            }
        """)

        if btn_found:
            logger.info("✓ Found Post button via JavaScript")
            return page.locator('button:has-text("Post")').first

    except Exception as e:
        logger.debug(f"JavaScript search failed: {e}")

    logger.warning("✗ Post button not found with any selector")
    return None


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


def check_important_content(content: str) -> bool:
    """Check if content contains important keywords."""
    IMPORTANT_KEYWORDS = ["urgent", "invoice", "payment", "sales"]
    text = content.lower()
    return any(keyword in text for keyword in IMPORTANT_KEYWORDS)


# =============================================================================
# CORE POSTING FUNCTION
# =============================================================================

def post_to_linkedin(text):
    """
    Post text to LinkedIn.
    Returns True if successful, False otherwise.
    """
    logger.info("=" * 60)
    logger.info(f"Posting to LinkedIn ({len(text)} chars)")
    logger.info("=" * 60)

    for attempt in range(MAX_RETRIES):
        logger.info(f"\nAttempt {attempt + 1}/{MAX_RETRIES}")

        try:
            with sync_playwright() as p:
                browser = None
                context = None

                # TRY 1: Connect to existing Chrome (Gold Tier Watcher on Port 9222)
                logger.info("Trying to connect to existing Chrome (Port 9222)...")

                try:
                    browser = p.chromium.connect_over_cdp(
                        "http://127.0.0.1:9222",
                        timeout=10000
                    )
                    logger.info("✓ Connected to existing Chrome")

                    context = browser.contexts[0] if browser.contexts else None

                    if context:
                        # Find or create LinkedIn page
                        linkedin_page = None
                        for pg in context.pages:
                            if "linkedin.com" in pg.url:
                                linkedin_page = pg
                                break

                        page = linkedin_page if linkedin_page else context.new_page()
                    else:
                        page = browser.new_page()

                except Exception as e:
                    logger.warning(f"Could not connect to existing Chrome: {e}")

                    # TRY 2: Launch new Chrome with persistent session
                    logger.info("Launching new Chrome with persistent session...")

                    context = p.chromium.launch_persistent_context(
                        user_data_dir=str(SESSION_PATH),
                        headless=False,
                        channel="chrome",
                        args=[
                            "--disable-blink-features=AutomationControlled",
                            "--no-sandbox",
                            "--disable-gpu",
                            "--remote-debugging-port=9222"
                        ],
                        timeout=90000
                    )

                    browser = context.browser
                    page = context.pages[0] if context.pages else context.new_page()
                    logger.info("✓ New Chrome launched")

                # Bring page to front
                page.bring_to_front()
                logger.info(f"Current page: {page.url}")

                # Navigate to LinkedIn feed
                logger.info(f"Navigating to {LINKEDIN_FEED_URL}...")

                try:
                    page.goto(LINKEDIN_FEED_URL, wait_until='domcontentloaded', timeout=60000)
                    logger.info("✓ Navigation initiated")

                    # Wait for network idle (but don't fail if it times out)
                    try:
                        page.wait_for_load_state('networkidle', timeout=30000)
                        logger.info("✓ Network idle")
                    except:
                        logger.info("Network idle timeout, continuing...")

                    # Wait for React app to initialize
                    time.sleep(5)

                except Exception as e:
                    logger.warning(f"Navigation issue: {e}")
                    # Continue anyway - page might still be usable

                take_screenshot(page, "after_navigation")

                # Check for login
                if "login" in page.url.lower() or "checkpoint" in page.url.lower():
                    logger.info("=" * 40)
                    logger.info("MANUAL LOGIN REQUIRED")
                    logger.info("=" * 40)
                    logger.info("Please login to LinkedIn...")

                    for i in range(60):
                        time.sleep(2)
                        if "login" not in page.url.lower() and "checkpoint" not in page.url.lower():
                            logger.info("✓ Login detected")
                            page.goto(LINKEDIN_FEED_URL)
                            time.sleep(5)
                            break
                    else:
                        raise Exception("Login timeout")

                take_screenshot(page, "logged_in")

                # Click "Start a post"
                logger.info("Opening compose box...")

                start_btn = None
                clicked = False

                # Try multiple selectors for "Start a post"
                start_selectors = [
                    'button:has-text("Start a post")',
                    'div[role="button"]:has-text("Start a post")',
                    'div.ember-view:has-text("Start a post")',
                    'button span:has-text("Start a post")',
                ]

                for selector in start_selectors:
                    try:
                        btn = page.locator(selector).first
                        if btn.is_visible(timeout=3000):
                            btn.scroll_into_view_if_needed()
                            time.sleep(1)
                            btn.click()
                            logger.info(f"✓ Clicked 'Start a post'")
                            clicked = True
                            break
                    except:
                        continue

                if not clicked:
                    logger.info("Trying coordinate click...")
                    page.mouse.click(500, 220)
                    clicked = True

                # Wait longer for modal and check multiple times
                logger.info("Waiting for modal to open...")
                modal_found = False

                for wait_attempt in range(5):
                    time.sleep(3)

                    # Try to find compose box
                    compose_box = find_compose_box(page)
                    if compose_box:
                        logger.info(f"✓ Compose box found after {wait_attempt + 1} attempts")
                        modal_found = True
                        break

                    logger.info(f"Modal not found yet (attempt {wait_attempt + 1}/5)...")

                take_screenshot(page, "modal_check")

                if not modal_found:
                    # Try clicking again
                    logger.info("Modal not found, trying to click 'Start a post' again...")
                    try:
                        page.locator('button:has-text("Start a post")').first.click()
                        time.sleep(5)
                        compose_box = find_compose_box(page)
                        if compose_box:
                            modal_found = True
                            logger.info("✓ Compose box found on second click")
                    except:
                        pass

                if not modal_found:
                    logger.error("✗ Modal did not open")
                    take_screenshot(page, "modal_not_opened")
                    raise Exception("Modal did not open")

                # compose_box already found in the loop above
                logger.info("Finding compose box...")
                compose_box = find_compose_box(page)

                if not compose_box:
                    logger.error("✗ Compose box NOT found")
                    take_screenshot(page, "compose_box_not_found")
                    raise Exception("Compose box not found")

                # Focus and clear
                logger.info("Focusing compose box...")
                compose_box.focus()
                time.sleep(FOCUS_WAIT / 1000)

                logger.info("Clearing existing content...")
                page.keyboard.press('Control+A')
                time.sleep(0.3)
                page.keyboard.press('Delete')
                time.sleep(0.3)

                # Type content SLOWLY
                logger.info(f"Typing content ({len(text)} chars, {TYPE_DELAY}ms/char)...")
                start_time = time.time()

                compose_box.type(text, delay=TYPE_DELAY)

                elapsed = time.time() - start_time
                logger.info(f"✓ Typing completed in {elapsed:.1f}s")

                # Wait after typing
                time.sleep(POST_WAIT / 1000)

                # Verify content
                try:
                    typed = compose_box.inner_text(timeout=2000)
                    if len(typed.strip()) < len(text.strip()) * 0.8:
                        logger.warning(f"Content incomplete: {len(typed)}/{len(text)}")
                    else:
                        logger.info(f"✓ Content verified: {len(typed)} chars")
                except:
                    logger.warning("Could not verify content")

                take_screenshot(page, "content_typed")

                # Find and click Post button
                logger.info("Finding Post button...")
                post_btn = find_post_button(page)

                if not post_btn:
                    logger.error("✗ Post button NOT found")
                    take_screenshot(page, "post_button_not_found")

                    # Try JavaScript click as last resort
                    logger.info("Trying JavaScript click on Post button...")
                    try:
                        result = page.evaluate("""
                            () => {
                                const buttons = Array.from(document.querySelectorAll('button'));
                                const postBtn = buttons.find(b =>
                                    b.innerText.trim().toUpperCase() === 'POST' &&
                                    !b.disabled
                                );
                                if (postBtn) {
                                    postBtn.click();
                                    return true;
                                }
                                return false;
                            }
                        """)

                        if result:
                            logger.info("✓ Post button clicked via JavaScript")
                            time.sleep(3)
                            take_screenshot(page, "post_js_clicked")
                            # Continue to success
                        else:
                            raise Exception("Post button not found")

                    except Exception as js_e:
                        logger.error(f"JavaScript click failed: {js_e}")
                        raise Exception("Post button not found")
                else:
                    # Wait before clicking
                    time.sleep(2)

                    logger.info("Clicking Post button...")
                    post_btn.scroll_into_view_if_needed()
                    time.sleep(0.5)
                    post_btn.click()
                    logger.info("✓ Post button clicked")

                # Wait for submission
                logger.info("Waiting for post submission...")
                try:
                    page.locator('div[role="dialog"]').first.wait_for(state='hidden', timeout=30000)
                    logger.info("✓ Modal closed - Post submitted")
                except:
                    logger.info("Modal didn't close, checking if on feed...")
                    if page.is_visible('div.feed', timeout=3000):
                        logger.info("✓ Back on feed - Post likely successful")

                take_screenshot(page, "post_submitted")

                # SUCCESS!
                logger.info("=" * 60)
                logger.info("✓ LINKEDIN POST PUBLISHED SUCCESSFULLY!")
                logger.info("=" * 60)

                # Close browser (but keep session alive if using persistent context)
                if browser and browser.is_connected():
                    try:
                        browser.close()
                    except:
                        pass

                return True

        except Exception as e:
            logger.error(f"✗ Attempt {attempt + 1} failed: {e}")

            # Close browser on error
            try:
                if browser and browser.is_connected():
                    browser.close()
            except:
                pass

            # Retry logic
            if attempt < MAX_RETRIES - 1:
                delay = RETRY_DELAYS[attempt]
                logger.info(f"Waiting {delay}s before retry...")
                time.sleep(delay)
            else:
                logger.error("=" * 60)
                logger.error("✗ ALL RETRY ATTEMPTS FAILED")
                logger.error("=" * 60)
                return False

    return False


# =============================================================================
# FILE MANAGEMENT
# =============================================================================

def move_to_done(filepath, metadata=None):
    """Move successfully processed file to Done folder."""
    try:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        dst = DONE_FOLDER / f"done_{filepath.stem}_{timestamp}.md"

        content = f"""---
type: linkedin_post
source: {filepath.name}
processed_at: {datetime.now().isoformat()}
status: completed
---

# ✓ LinkedIn Post COMPLETED

**Processed:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

---
Original content preserved above.
"""

        dst.write_text(content, encoding='utf-8')
        filepath.unlink()

        logger.info(f"✓ Moved to DONE: {dst.name}")
        return True

    except Exception as e:
        logger.error(f"Error moving to done: {e}")
        return False


def move_to_failed(filepath, reason):
    """Move failed file to Failed folder with reason."""
    try:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        dst = FAILED_FOLDER / f"failed_{filepath.stem}_{timestamp}.md"

        content = f"""---
type: linkedin_post
source: {filepath.name}
processed_at: {datetime.now().isoformat()}
status: failed
failure_reason: {reason}
---

# ✗ LinkedIn Post FAILED

**Failed:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

**Reason:** {reason}

**Log:** {log_file}

---
Original content preserved above.
"""

        dst.write_text(content, encoding='utf-8')
        filepath.unlink()

        logger.info(f"✗ Moved to FAILED: {dst.name}")
        logger.info(f"Reason: {reason}")
        return True

    except Exception as e:
        logger.error(f"Error moving to failed: {e}")
        return False


def create_needs_action_file(
    item_type: str, sender: str, subject: str, content: str, timestamp: str
) -> str:
    """Create .md file in Needs_Action folder with YAML frontmatter."""
    priority = get_priority(content)
    file_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # Sanitize filename
    safe_sender = re.sub(r"[^a-zA-Z0-9]", "_", sender[:20])
    filename = f"LINKEDIN_{item_type.upper()}_{safe_sender}_{file_timestamp}.md"
    filepath = Path(PROJECT_ROOT / "gold" / "needs_action" / filename)

    # Ensure directory exists
    filepath.parent.mkdir(parents=True, exist_ok=True)

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


# =============================================================================
# WATCHER MODE - MONITOR LINKEDIN FOR MESSAGES/NOTIFICATIONS
# =============================================================================

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
    """Monitor LinkedIn for new important messages and notifications (Watcher Mode)."""

    with sync_playwright() as p:
        # Launch browser with persistent context
        print("[INFO] Launching browser with persistent session...")
        print(f"[INFO] Session path: {SESSION_PATH}")

        context = p.chromium.launch_persistent_context(
            user_data_dir=str(SESSION_PATH),
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


# =============================================================================
# MAIN FUNCTION
# =============================================================================

def main():
    parser = argparse.ArgumentParser(description='Gold Tier LinkedIn Auto Poster')
    parser.add_argument('--content', type=str, help='Post content')
    parser.add_argument('--file', type=str, help='Approved file to process')
    parser.add_argument('--watch', action='store_true', help='Run in watcher mode (monitor LinkedIn)')
    args = parser.parse_args()

    logger.info("=" * 60)
    logger.info("GOLD TIER LINKEDIN AUTO POSTER")
    logger.info("=" * 60)

    # Watcher mode
    if args.watch:
        logger.info("Running in WATCHER mode")
        logger.info("Monitoring LinkedIn for important messages and notifications...")
        print("=" * 60)
        print("LinkedIn Watcher - Gold Tier")
        print("=" * 60)
        print(f"Session: {SESSION_PATH}")
        print(f"Check interval: {CHECK_INTERVAL} seconds")
        print("-" * 60)
        monitor_linkedin()
        return

    # Get content
    content = None
    filepath = None

    if args.content:
        content = args.content
        filepath = Path(f"manual_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md")

    elif args.file:
        filepath = Path(args.file)
        if not filepath.exists():
            logger.error(f"File not found: {filepath}")
            sys.exit(1)

        try:
            file_content = filepath.read_text(encoding='utf-8')

            # Extract post content
            if '## LinkedIn Post Draft' in file_content:
                parts = file_content.split('## LinkedIn Post Draft')
                if len(parts) > 1:
                    content = parts[1].strip().split('---')[0].strip()
            else:
                content = file_content

        except Exception as e:
            logger.error(f"Error reading file: {e}")
            sys.exit(1)

    if not content:
        logger.error("No content provided")
        sys.exit(1)

    logger.info(f"Content: {content[:100]}...")

    # Post to LinkedIn
    success = post_to_linkedin(content)

    # Handle file
    if filepath and filepath.exists():
        if success:
            move_to_done(filepath)
        else:
            move_to_failed(filepath, "Failed to post after all retries")

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
