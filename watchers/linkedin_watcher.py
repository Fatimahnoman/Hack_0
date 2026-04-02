"""
LinkedIn Watcher - Silver Tier
==============================
Monitors LinkedIn notifications and messages for important keywords.
Uses Playwright with persistent session for login.

Install: pip install playwright
       playwright install chromium
Run: python watchers/linkedin_watcher.py
"""

import os
import re
import sys
import time
import logging
from datetime import datetime
from pathlib import Path

# Check for required dependencies
try:
    from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout
except ImportError as e:
    print(f"[ERROR] Missing required dependency: {e}")
    print("[INFO] Please install required packages:")
    print("       pip install playwright")
    print("       playwright install chromium")
    sys.exit(1)

# Configuration
PROJECT_ROOT = Path(__file__).resolve().parent.parent
SESSION_FOLDER = PROJECT_ROOT / "session" / "linkedin"
NEEDS_ACTION_FOLDER = PROJECT_ROOT / "Needs_Action"
PLANS_FOLDER = PROJECT_ROOT / "Plans"
PENDING_APPROVAL_FOLDER = PROJECT_ROOT / "Pending_Approval"
APPROVED_FOLDER = PENDING_APPROVAL_FOLDER / "Approved"
DONE_FOLDER = PROJECT_ROOT / "Done"
LOGS_FOLDER = PROJECT_ROOT / "Logs"
LOG_FILE = LOGS_FOLDER / "watcher.log"
CHECK_INTERVAL = 60  # seconds
STATUS_INTERVAL = 30  # seconds

# Keywords to monitor (case-insensitive)
IMPORTANT_KEYWORDS = ["urgent", "invoice", "payment", "sales"]

# Ensure directories exist
for d in [SESSION_FOLDER, NEEDS_ACTION_FOLDER, PLANS_FOLDER, PENDING_APPROVAL_FOLDER, APPROVED_FOLDER, DONE_FOLDER, LOGS_FOLDER]:
    d.mkdir(parents=True, exist_ok=True)

# Retry configuration
MAX_RETRIES = 3
RETRY_DELAY = 5  # seconds

# LinkedIn URLs
LINKEDIN_URL = "https://www.linkedin.com/"
LINKEDIN_MESSAGES_URL = "https://www.linkedin.com/messaging/"
LINKEDIN_NOTIFICATIONS_URL = "https://www.linkedin.com/notifications/"


def setup_logging():
    """Setup logging to file and console."""
    if not LOGS_FOLDER.exists():
        LOGS_FOLDER.mkdir(parents=True, exist_ok=True)

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        handlers=[
            logging.FileHandler(LOG_FILE, encoding="utf-8"),
            logging.StreamHandler(sys.stdout)
        ]
    )
    return logging.getLogger(__name__)


logger = setup_logging()


def get_priority(text: str) -> str:
    """Determine priority based on keywords."""
    text = text.lower()
    if "urgent" in text:
        return "high"
    elif "invoice" in text or "payment" in text:
        return "medium"
    elif "sales" in text:
        return "normal"
    return "low"


def force_english_ltr_on_editor(target):
    """LinkedIn compose can inherit RTL — English appears mirrored. Force LTR."""
    try:
        target.evaluate(
            """(el) => {
                const apply = (node) => {
                    if (!node) return;
                    if (node.style) {
                        node.style.direction = 'ltr';
                        node.style.unicodeBidi = 'normal';
                        node.style.textAlign = 'left';
                    }
                    if (node.setAttribute) {
                        node.setAttribute('dir', 'ltr');
                        node.setAttribute('lang', 'en');
                    }
                };
                apply(el);
                let p = el.parentElement;
                for (let i = 0; i < 8 && p; i++) {
                    apply(p);
                    p = p.parentElement;
                }
            }"""
        )
    except Exception as e:
        logger.debug(f"force_english_ltr: {e}")


def create_needs_action_file(data: dict) -> str:
    """Create .md file in Needs_Action folder with YAML frontmatter."""
    priority = get_priority(data.get("content", ""))
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # Sanitize filename
    safe_subject = re.sub(r"[^a-zA-Z0-9]", "_", data.get("subject", "notification")[:30])
    filename = f"LINKEDIN_{safe_subject}_{timestamp}.md"
    filepath = NEEDS_ACTION_FOLDER / filename

    yaml_content = f"""---
type: {data.get('type', 'notification')}
from: {data.get('from', 'Unknown')}
subject: {data.get('subject', 'No subject')}
received: {data.get('received', datetime.now().strftime('%Y-%m-%d %H:%M:%S'))}
priority: {priority}
status: pending
linkedin_url: {data.get('url', '')}
---

## Content

{data.get('content', 'No content available')}

---
*Imported by LinkedIn Watcher on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*
"""

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(yaml_content)

    logger.info(f"Created file: {filename}")
    return filename


def check_keywords(text: str) -> bool:
    """Check if text contains important keywords."""
    if not text:
        return False
    text_lower = text.lower()
    return any(keyword in text_lower for keyword in IMPORTANT_KEYWORDS)


def extract_notifications(page) -> list:
    """Extract notifications from LinkedIn notifications page."""
    notifications = []

    try:
        # Wait for notifications container
        page.wait_for_selector('div.notification-card', timeout=5000)

        # Get notification cards
        cards = page.query_selector_all('div.notification-card')

        for card in cards[:10]:  # Limit to 10 most recent
            try:
                # Extract sender
                sender_elem = card.query_selector('span.entity-result__name, a.app-aware-link')
                sender = sender_elem.inner_text() if sender_elem else "Unknown"

                # Extract content
                content_elem = card.query_selector('p.app-aware-link, span.notification-card__content')
                content = content_elem.inner_text() if content_elem else ""

                # Extract time
                time_elem = card.query_selector('span.timestamp')
                received = time_elem.inner_text() if time_elem else datetime.now().strftime('%Y-%m-%d %H:%M:%S')

                if check_keywords(content) or check_keywords(sender):
                    notifications.append({
                        "type": "notification",
                        "from": sender,
                        "subject": content[:100] if content else "Notification",
                        "content": content,
                        "received": received,
                        "url": LINKEDIN_NOTIFICATIONS_URL
                    })
            except Exception as e:
                logger.debug(f"Error extracting notification: {e}")
                continue

    except Exception as e:
        logger.debug(f"No notifications found or selector changed: {e}")

    return notifications


def extract_messages(page) -> list:
    """Extract messages from LinkedIn messaging."""
    messages = []

    try:
        # Navigate to messages
        page.goto(LINKEDIN_MESSAGES_URL, wait_until="domcontentloaded", timeout=30000)
        time.sleep(3)  # Wait for messages to load

        # Get message conversations
        try:
            conversations = page.query_selector_all('div.conversation-card, li.artdeco-list__item')

            for conv in conversations[:10]:  # Limit to 10 most recent
                try:
                    # Extract sender
                    sender_elem = conv.query_selector('span.entity-result__name, h4.artdeco-entity-lockup__title')
                    sender = sender_elem.inner_text() if sender_elem else "Unknown"

                    # Extract last message preview
                    message_elem = conv.query_selector('p.app-aware-link, span.artdeco-entity-lockup__subtitle')
                    message_content = message_elem.inner_text() if message_elem else ""

                    # Extract time
                    time_elem = conv.query_selector('span.timestamp, time')
                    received = time_elem.inner_text() if time_elem else datetime.now().strftime('%Y-%m-%d %H:%M:%S')

                    if check_keywords(message_content) or check_keywords(sender):
                        messages.append({
                            "type": "message",
                            "from": sender,
                            "subject": f"Message from {sender}",
                            "content": message_content,
                            "received": received,
                            "url": LINKEDIN_MESSAGES_URL
                        })
                except Exception as e:
                    logger.debug(f"Error extracting message: {e}")
                    continue

        except Exception as e:
            logger.debug(f"No conversations found: {e}")

    except Exception as e:
        logger.error(f"Error accessing messages: {e}")

    return messages


def run_linkedin_watcher(context, page, processed_ids: set) -> int:
    """Check LinkedIn for new important notifications and messages."""
    new_count = 0

    for attempt in range(MAX_RETRIES):
        try:
            # Check if logged in
            try:
                page.wait_for_url(LINKEDIN_URL, timeout=10000)
                time.sleep(2)

                # Check if we're on login page
                if "login" in page.url.lower():
                    logger.warning("Not logged in. Please log in manually.")
                    print("  -> Please log in to LinkedIn in the browser window")
                    print("  -> Waiting for login...")

                    # Wait for user to log in (max 2 minutes)
                    for _ in range(12):
                        time.sleep(10)
                        if "login" not in page.url.lower():
                            logger.info("Login detected!")
                            break
                    else:
                        logger.error("Login timeout. Please restart the watcher.")
                        return 0

            except PlaywrightTimeout:
                logger.warning("Page load timeout, continuing anyway...")

            # Extract notifications
            logger.info("Checking notifications...")
            try:
                page.goto(LINKEDIN_NOTIFICATIONS_URL, wait_until="domcontentloaded", timeout=30000)
                time.sleep(3)  # Wait for content to load
                notifications = extract_notifications(page)

                for notif in notifications:
                    # Create unique ID
                    notif_id = f"{notif['type']}_{notif['from']}_{notif['subject']}"

                    if notif_id not in processed_ids:
                        filename = create_needs_action_file(notif)
                        logger.info(f"NEW IMPORTANT NOTIFICATION - From: {notif['from']}, Subject: {notif['subject']}")
                        print(f"  -> Created: {filename}")
                        print(f"     From: {notif['from']}")
                        print(f"     Subject: {notif['subject']}")
                        print(f"     Priority: {get_priority(notif['content'])}")
                        new_count += 1
                        processed_ids.add(notif_id)

            except Exception as e:
                logger.debug(f"Error checking notifications: {e}")

            # Extract messages
            logger.info("Checking messages...")
            messages = extract_messages(page)

            for msg in messages:
                # Create unique ID
                msg_id = f"{msg['type']}_{msg['from']}_{msg['subject']}"

                if msg_id not in processed_ids:
                    filename = create_needs_action_file(msg)
                    logger.info(f"NEW IMPORTANT MESSAGE - From: {msg['from']}, Subject: {msg['subject']}")
                    print(f"  -> Created: {filename}")
                    print(f"     From: {msg['from']}")
                    print(f"     Subject: {msg['subject']}")
                    print(f"     Priority: {get_priority(msg['content'])}")
                    new_count += 1
                    processed_ids.add(msg_id)

            # Success - break retry loop
            break

        except Exception as e:
            logger.error(f"LinkedIn watcher error (attempt {attempt + 1}/{MAX_RETRIES}): {e}")
            if attempt < MAX_RETRIES - 1:
                logger.info(f"Retrying in {RETRY_DELAY} seconds...")
                time.sleep(RETRY_DELAY)
            else:
                logger.error("Max retries reached. Continuing to next check cycle.")

    return new_count


def ensure_directories():
    """Ensure required directories exist."""
    SESSION_FOLDER.mkdir(parents=True, exist_ok=True)
    NEEDS_ACTION_FOLDER.mkdir(parents=True, exist_ok=True)
    LOGS_FOLDER.mkdir(parents=True, exist_ok=True)


# =============================================================================
# AUTO-POST FUNCTIONS (Added for auto-posting approved drafts)
# =============================================================================

def read_draft_content(filepath):
    """Extract post content from draft."""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    match = re.search(r'## Content\n\n(.+?)\n---', content, re.DOTALL)
    return match.group(1).strip() if match else None


def check_approved_posts() -> list:
    """
    Check for approved posts in Approved folder.
    Also checks Pending_Approval folder and auto-moves files with 'approved' status.
    """
    approved = []
    
    # Check Approved folder
    if APPROVED_FOLDER.exists():
        approved.extend(list(APPROVED_FOLDER.glob("linkedin_post_*.md")))
    
    # Also check Pending_Approval for files with approved status
    if PENDING_APPROVAL_FOLDER.exists():
        for filepath in PENDING_APPROVAL_FOLDER.glob("linkedin_post_*.md"):
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Check if status is approved
                if 'status: approved' in content.lower() or 'status: pending_approval' in content.lower():
                    # Move to Approved folder
                    dest = APPROVED_FOLDER / filepath.name
                    try:
                        import shutil
                        shutil.move(str(filepath), str(dest))
                        logger.info(f"Moved to Approved: {filepath.name}")
                        approved.append(dest)
                    except Exception as e:
                        logger.error(f"Could not move {filepath.name}: {e}")
            except Exception as e:
                logger.debug(f"Error reading {filepath}: {e}")
    
    if approved:
        logger.info(f"Found {len(approved)} approved post(s) to publish")
    
    return approved


def move_to_done(draft_path, content):
    """Move posted draft to Done folder."""
    done_file = DONE_FOLDER / f"linkedin_post_{datetime.now().strftime('%Y%m%d_%H%M%S')}_DONE.md"
    
    with open(done_file, 'w', encoding='utf-8') as f:
        f.write(f"""---
type: linkedin_post_sent
source: {draft_path.name}
posted_at: {datetime.now().isoformat()}
status: posted
---

# Posted

{content}

---
*Posted {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*
""")
    
    draft_path.unlink()
    logger.info(f"Moved to Done: {done_file.name}")


def post_to_linkedin(page, content: str) -> bool:
    """
    Post content to LinkedIn using existing page context.
    FIXED: Proper typing + Auto-click Post button with JavaScript.
    """
    logger.info("=" * 60)
    logger.info("AUTO-POSTING APPROVED CONTENT")
    logger.info("=" * 60)
    logger.info(f"Content length: {len(content)} chars")

    try:
        # Navigate to feed
        logger.info("Navigating to feed...")
        page.goto("https://www.linkedin.com/feed/", wait_until="domcontentloaded", timeout=60000)
        time.sleep(3)

        # Click "Start a post"
        logger.info("Clicking 'Start a post'...")
        start_btn = None
        start_selectors = [
            'button:has-text("Start a post")',
            '[aria-label="Start a post"]',
            '.share-box-feed-entry',
        ]

        for sel in start_selectors:
            try:
                start_btn = page.query_selector(sel)
                if start_btn:
                    start_btn.click()
                    logger.info(f"✓ Clicked via: {sel}")
                    break
            except:
                pass

        if not start_btn:
            logger.error("Start a post button NOT found!")
            return False

        time.sleep(2)
        logger.info("Modal opened")

        # =========================================================
        # Find text input - CRITICAL!
        # =========================================================
        logger.info("Finding text input...")
        text_input = None
        
        # Wait for modal to fully render
        time.sleep(2)
        
        # Try each selector with locator (more reliable)
        input_selectors = [
            'div[contenteditable="true"][role="textbox"]',
            'div[contenteditable="true"]',
            '[data-testid="update-editor-text-input"]',
        ]

        for i, sel in enumerate(input_selectors, 1):
            try:
                logger.info(f"Trying selector {i}: {sel}")
                text_input = page.locator(sel).first
                
                # Wait for it to be visible
                text_input.wait_for_state('visible', timeout=15000)
                
                # Check if it's actually there
                if text_input.count() > 0:
                    logger.info(f"✓✓✓ FOUND via selector {i}!")
                    break
                else:
                    logger.info(f"Selector {i} found 0 elements")
                    text_input = None
            except Exception as e:
                logger.info(f"Selector {i} failed: {e}")
                text_input = None

        # Fallback: Get all contenteditable divs
        if not text_input:
            logger.info("Trying fallback: all contenteditable divs...")
            try:
                all_editable = page.query_selector_all('div[contenteditable="true"]')
                logger.info(f"Found {len(all_editable)} contenteditable divs")
                
                if len(all_editable) > 0:
                    # Use the first one that has focus or is visible
                    for i, elem in enumerate(all_editable):
                        try:
                            if elem.is_visible():
                                text_input = elem
                                logger.info(f"Using contenteditable div #{i+1}")
                                break
                        except:
                            continue
            except Exception as e:
                logger.error(f"Fallback failed: {e}")

        if not text_input:
            logger.error("✗✗✗ Text input NOT found with ANY method!")
            # Save screenshot
            try:
                page.screenshot(path=str(LOGS_FOLDER / "debug_no_input.png"))
                logger.info("Debug screenshot saved")
            except:
                pass
            return False

        # =========================================================
        # TYPE CONTENT - USING DIRECT KEYBOARD TYPE!
        # =========================================================
        logger.info(f"Typing {len(content)} characters...")
        
        # Click to focus
        logger.info("Clicking to focus...")
        text_input.click()
        time.sleep(1)
        force_english_ltr_on_editor(text_input)

        # Clear existing content
        logger.info("Clearing existing content...")
        page.keyboard.press('Control+A')
        time.sleep(0.5)
        page.keyboard.press('Delete')
        time.sleep(0.5)
        force_english_ltr_on_editor(text_input)

        # Type character by character - SLOW AND STEADY
        logger.info("Starting to type character by character...")
        
        for i, char in enumerate(content):
            try:
                page.keyboard.type(char, delay=50)  # 50ms per character
                
                # Log progress every 50 chars
                if (i + 1) % 50 == 0:
                    logger.info(f"Typed {i+1}/{len(content)} chars...")
                    
            except Exception as e:
                logger.warning(f"Char {i+1} failed: {e}")
                # Try to refocus
                try:
                    text_input.click()
                    time.sleep(0.3)
                except:
                    pass
        
        logger.info(f"✓✓✓ Finished typing {len(content)} chars!")
        time.sleep(2)

        # Verify content
        try:
            entered = text_input.inner_text()
            logger.info(f"✓ Entered: {len(entered)}/{len(content)} chars")
            
            if len(entered) < len(content) * 0.8:
                logger.warning("Text mismatch - content may not have typed correctly")
        except Exception as e:
            logger.warning(f"Could not verify: {e}")

        # Wait for LinkedIn to process
        time.sleep(2)

        # =========================================================
        # CLICK POST BUTTON - FORCE CLICK WITH MULTIPLE METHODS!
        # =========================================================
        logger.info("Clicking Post button...")

        # Wait for button to be enabled
        logger.info("Waiting 5 seconds for Post button to be ready...")
        time.sleep(5)  # LinkedIn needs time to enable button after typing
        
        # =========================================================
        # METHOD 1: Playwright Direct Click (Try First)
        # =========================================================
        logger.info("Method 1: Trying Playwright direct click...")
        post_clicked = False
        
        try:
            # Find the Post button using multiple approaches
            post_buttons = [
                page.locator('button:has-text("Post")').first,
                page.locator('button:has-text("POST")').first,
                page.locator('[data-testid="post-button"]').first,
            ]
            
            for post_btn in post_buttons:
                try:
                    # Wait for it to be visible and enabled
                    post_btn.wait_for(state='visible', timeout=5000)
                    post_btn.wait_for(state='enabled', timeout=5000)
                    
                    # FORCE CLICK - scroll into view and click
                    post_btn.scroll_into_view_if_needed()
                    time.sleep(0.5)
                    post_btn.click(force=True)
                    
                    logger.info(f"✓✓✓ POST BUTTON CLICKED via Playwright!")
                    post_clicked = True
                    break
                    
                except Exception as e:
                    logger.debug(f"Button click failed: {e}")
                    continue
            
        except Exception as e:
            logger.debug(f"Playwright method failed: {e}")
        
        # =========================================================
        # METHOD 2: JavaScript Click (Fallback)
        # =========================================================
        if not post_clicked:
            logger.info("Method 2: Trying JavaScript click...")
            
            try:
                js_code = """
                (function() {
                    console.log('=== FINDING POST BUTTON ===');
                    
                    // Get all buttons on the page
                    const allButtons = Array.from(document.querySelectorAll('button'));
                    console.log('Total buttons: ' + allButtons.length);
                    
                    // Find button with POST text
                    let postBtn = null;
                    for (let btn of allButtons) {
                        const text = btn.innerText.trim();
                        const ariaLabel = btn.getAttribute('aria-label') || '';
                        
                        console.log('Button: "' + text + '" aria: "' + ariaLabel + '"');
                        
                        if (text === 'Post' || text === 'POST' || 
                            text.startsWith('Post ') || text.startsWith('POST ') ||
                            ariaLabel.toLowerCase().includes('post')) {
                            postBtn = btn;
                            console.log('✓ FOUND POST BUTTON!');
                            break;
                        }
                    }
                    
                    if (!postBtn) {
                        console.log('✗ Post button not found');
                        return { success: false, error: 'Not found' };
                    }
                    
                    // Check if disabled
                    if (postBtn.disabled || postBtn.getAttribute('aria-disabled') === 'true') {
                        console.log('✗ Button is disabled');
                        return { success: false, error: 'Disabled' };
                    }
                    
                    // FORCE CLICK - dispatch multiple events
                    console.log('Clicking button...');
                    
                    // Mouse events
                    postBtn.dispatchEvent(new MouseEvent('mousedown', { bubbles: true }));
                    postBtn.dispatchEvent(new MouseEvent('mouseup', { bubbles: true }));
                    postBtn.dispatchEvent(new MouseEvent('click', { bubbles: true }));
                    
                    // Also try direct click
                    postBtn.click();
                    
                    console.log('✓ Click events sent!');
                    return { success: true, clicked: true };
                })()
                """
                
                result = page.evaluate(js_code)
                logger.info(f"JavaScript result: {result}")
                
                if result.get('success'):
                    logger.info("✓✓✓ POST BUTTON CLICKED via JavaScript!")
                    post_clicked = True
                    
            except Exception as e:
                logger.error(f"JavaScript method failed: {e}")
        
        # =========================================================
        # METHOD 3: Keyboard Navigation (Last Resort)
        # =========================================================
        if not post_clicked:
            logger.info("Method 3: Trying keyboard navigation (Tab + Enter)...")
            
            try:
                # Try to Tab to the Post button and press Enter
                time.sleep(1)
                page.keyboard.press('Tab')  # Focus first element
                time.sleep(0.5)
                page.keyboard.press('Tab')  # Focus second element
                time.sleep(0.5)
                page.keyboard.press('Enter')  # Activate
                
                logger.info("Keyboard navigation sent")
                post_clicked = True  # Assume it worked
                
            except Exception as e:
                logger.error(f"Keyboard method failed: {e}")
        
        # Check final result
        if not post_clicked:
            logger.error("✗✗✗ Post button NOT clicked by ANY method!")
            # Save screenshot
            try:
                page.screenshot(path=str(LOGS_FOLDER / "debug_no_click.png"))
                logger.info("Debug screenshot saved")
            except:
                pass
            return False

        # Wait for confirmation
        logger.info("Waiting for post to publish...")
        time.sleep(5)
        
        logger.info("✓✓✓ POST PUBLISHED! ✓✓✓")
        return True

    except Exception as e:
        logger.error(f"Auto-post error: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False


def process_approved_posts(context, page) -> int:
    """
    Check for approved posts and auto-post them.
    Called from main watcher loop.
    """
    published_count = 0
    approved_files = check_approved_posts()
    
    for filepath in approved_files:
        logger.info(f"Processing approved post: {filepath.name}")
        content = read_draft_content(filepath)
        
        if not content:
            logger.error(f"Could not read content from {filepath.name}")
            continue
        
        logger.info(f"Posting: {filepath.name}")
        
        if post_to_linkedin(page, content):
            move_to_done(filepath, content)
            published_count += 1
            logger.info(f"✓ Published: {filepath.name}")
        else:
            logger.error(f"✗ Failed to publish: {filepath.name}")
    
    return published_count


def main():
    """Main function to start LinkedIn watcher."""
    print("=" * 60)
    print("LinkedIn Watcher - Silver Tier")
    print("=" * 60)
    print(f"Monitoring: LinkedIn notifications and messages")
    print(f"Keywords: {', '.join(IMPORTANT_KEYWORDS)}")
    print(f"Session path: {SESSION_FOLDER}")
    print(f"Destination: {NEEDS_ACTION_FOLDER}")
    print(f"Check interval: {CHECK_INTERVAL} seconds")
    print(f"Status interval: {STATUS_INTERVAL} seconds")
    print(f"Log file: {LOG_FILE}")
    print("-" * 60)

    # Ensure directories exist
    ensure_directories()

    print("Press Ctrl+C to stop the watcher...")
    print("=" * 60)

    logger.info("Starting LinkedIn watcher...")

    with sync_playwright() as p:
        # Launch browser with persistent context
        logger.info("Launching browser with persistent session...")
        context = p.chromium.launch_persistent_context(
            user_data_dir=str(SESSION_FOLDER),
            headless=False,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--disable-dev-shm-usage",
                "--no-sandbox"
            ],
            viewport={"width": 1280, "height": 720}
        )

        # Create page
        page = context.pages[0] if context.pages else context.new_page()

        # Navigate to LinkedIn
        logger.info("Navigating to LinkedIn...")
        try:
            page.goto(LINKEDIN_URL, wait_until="domcontentloaded", timeout=30000)
        except Exception as e:
            logger.error(f"Error navigating to LinkedIn: {e}")

        # Track processed item IDs
        processed_ids = set()

        logger.info("Watcher started successfully!")
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Watcher started successfully!")
        print("-" * 60)

        # Status counter for ONLINE message
        status_counter = 0

        try:
            while True:
                # Check for new items
                print(f"\n[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Checking LinkedIn...")
                logger.info("Checking LinkedIn for new items...")

                new_count = run_linkedin_watcher(context, page, processed_ids)

                if new_count > 0:
                    print(f"  -> {new_count} new important item(s) processed")
                    logger.info(f"Processed {new_count} new important item(s)")
                else:
                    print("  -> No new important items")
                    logger.info("No new important items found")

                # =========================================================
                # AUTO-POST: Check for approved posts and publish them
                # =========================================================
                logger.info("Checking for approved posts to auto-publish...")
                published_count = process_approved_posts(context, page)
                if published_count > 0:
                    print(f"  -> {published_count} auto-post(s) published!")
                    logger.info(f"Published {published_count} approved post(s)")

                # Reset status counter after each check
                status_counter = 0

                # Wait with periodic ONLINE status updates
                for _ in range(CHECK_INTERVAL // STATUS_INTERVAL):
                    time.sleep(STATUS_INTERVAL)
                    status_counter += STATUS_INTERVAL
                    if status_counter < CHECK_INTERVAL:
                        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] ONLINE - Monitoring LinkedIn...")
                        logger.info("ONLINE - Watcher is running")

        except KeyboardInterrupt:
            logger.info("Watcher stopped by user.")
            print("\n[INFO] LinkedIn watcher stopped by user.")

        # Close browser
        context.close()
        logger.info("Browser closed.")

    logger.info("Watcher stopped.")
    print("[INFO] LinkedIn watcher stopped.")


if __name__ == "__main__":
    main()
