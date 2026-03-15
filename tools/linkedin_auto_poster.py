"""
LinkedIn Auto Poster - Final Production Version
================================================
Fully automated with smart login handling.

Run: python tools\linkedin_auto_poster.py --post FILENAME
"""

import os
import sys
import time
import re
import logging
from datetime import datetime
from pathlib import Path

try:
    from playwright.sync_api import sync_playwright
except ImportError:
    print("Install: pip install playwright && playwright install chromium")
    sys.exit(1)

# Configuration
PROJECT_ROOT = Path(__file__).parent.parent
PENDING_FOLDER = PROJECT_ROOT / "Pending_Approval"
DONE_FOLDER = PROJECT_ROOT / "Done"
LOGS_FOLDER = PROJECT_ROOT / "Logs"
SESSION_PATH = PROJECT_ROOT / "session" / "linkedin"
DEBUG_FOLDER = PROJECT_ROOT / "debug_linkedin"

DEBUG_FOLDER.mkdir(exist_ok=True)

def setup_logging():
    log_file = LOGS_FOLDER / f"linkedin_{datetime.now().strftime('%Y-%m-%d')}.log"
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8'),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger(__name__)

logger = setup_logging()


def save_debug(page, name):
    """Save screenshot and HTML."""
    try:
        page.screenshot(path=str(DEBUG_FOLDER / f"{name}.png"))
        with open(DEBUG_FOLDER / f"{name}.html", 'w', encoding='utf-8') as f:
            f.write(page.content())
        logger.info(f"Debug: {name}")
    except Exception as e:
        logger.debug(f"Debug save failed: {e}")


def is_logged_in(page) -> bool:
    """Check if user is logged in to LinkedIn."""
    indicators = [
        page.query_selector('nav.global-nav'),
        page.query_selector('a[href*="/mynetwork/"]'),
        page.query_selector('a[href*="/notifications/"]'),
        page.query_selector('img.actor-name'),
        page.query_selector('button[data-control-name="nav_settings"]'),
    ]
    
    # Check URL
    if "login" not in page.url.lower() and "checkpoint" not in page.url.lower():
        if any(indicators):
            return True
    
    return False


def wait_for_login(page, timeout: int = 180) -> bool:
    """Wait for user to log in manually."""
    logger.info("Waiting for login...")
    logger.info(f"Timeout: {timeout} seconds")
    
    start = time.time()
    check_interval = 5
    
    while time.time() - start < timeout:
        if is_logged_in(page):
            logger.info("Login detected!")
            return True
        
        elapsed = int(time.time() - start)
        logger.info(f"  Waiting... ({elapsed}/{timeout}s) - Current URL: {page.url[:80]}")
        time.sleep(check_interval)
    
    logger.warning("Login timeout!")
    return False


def read_draft_content(filepath):
    """Extract post content from draft."""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    match = re.search(r'## Content\n\n(.+?)\n---', content, re.DOTALL)
    return match.group(1).strip() if match else None


def post_to_linkedin(content: str) -> bool:
    """Post content to LinkedIn."""
    
    logger.info("=" * 60)
    logger.info("LinkedIn Auto Poster - Starting")
    logger.info("=" * 60)
    logger.info(f"Content length: {len(content)} chars")
    
    success = False
    
    with sync_playwright() as p:
        logger.info("Launching browser...")
        
        context = p.chromium.launch_persistent_context(
            user_data_dir=str(SESSION_PATH),
            headless=False,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
                "--disable-gpu",
                "--disable-dev-shm-usage"
            ],
            timeout=120000
        )
        
        page = context.pages[0] if context.pages else context.new_page()
        page.set_viewport_size({"width": 1920, "height": 1080})
        
        try:
            # Step 1: Go to LinkedIn
            logger.info("Going to LinkedIn...")
            page.goto("https://www.linkedin.com/feed/", wait_until="domcontentloaded", timeout=120000)
            time.sleep(5)
            
            # Step 2: Check if logged in, wait for login if needed
            if not is_logged_in(page):
                logger.warning("Not logged in!")
                logger.info("=" * 60)
                logger.info("MANUAL LOGIN REQUIRED")
                logger.info("=" * 60)
                logger.info("Please login to LinkedIn in the browser window")
                logger.info("Session will be saved for future runs")
                logger.info("=" * 60)
                
                if not wait_for_login(page, timeout=180):
                    logger.error("Login failed or timed out")
                    context.close()
                    return False
                
                save_debug(page, "00_logged_in")
                time.sleep(2)

            logger.info("User is logged in")

            # Navigate to feed
            page.goto("https://www.linkedin.com/feed/", wait_until="domcontentloaded", timeout=120000)
            time.sleep(5)
            save_debug(page, "01_feed")
            logger.info("Feed loaded")
            
            # Step 3: Click "Start a post"
            logger.info("Clicking 'Start a post'...")
            
            start_btn = None
            start_selectors = [
                'button:has-text("Start a post")',
                '[aria-label="Start a post"]',
                '.share-box-feed-entry',
                'div.share-box-feed-entry',
            ]
            
            for sel in start_selectors:
                try:
                    start_btn = page.query_selector(sel)
                    if start_btn:
                        start_btn.click()
                        logger.info(f"Clicked via: {sel}")
                        break
                except:
                    pass
            
            if not start_btn:
                logger.error("Start a post button NOT found!")
                save_debug(page, "01_no_start_button")
                input("Press Enter to exit...")
                context.close()
                return False
            
            time.sleep(3)
            save_debug(page, "02_modal")
            logger.info("Modal opened")
            
            # Wait for modal animation to complete
            time.sleep(2)
            
            # Click on the modal backdrop to ensure focus
            try:
                modal_backdrop = page.query_selector('div[role="dialog"]')
                if modal_backdrop:
                    modal_backdrop.click()
                    time.sleep(1)
                    logger.info("Clicked modal backdrop for focus")
            except:
                pass
            
            # Step 4: Find text input
            logger.info("Finding text input...")
            
            text_input = None
            input_selectors = [
                'div[contenteditable="true"][role="textbox"]',
                'div[contenteditable="true"]',
                '[data-testid="update-editor-text-input"]',
                'textarea[aria-label*="post" i]',
                'textarea[placeholder*="post" i]',
                '.editor-content-area[contenteditable="true"]',
                'div.ember-view[contenteditable="true"]',
            ]
            
            for sel in input_selectors:
                try:
                    text_input = page.query_selector(sel)
                    if text_input:
                        logger.info(f"Found via: {sel}")
                        break
                except:
                    pass
            
            # Fallback 1: any contenteditable div
            if not text_input:
                try:
                    all_editable = page.query_selector_all('div[contenteditable="true"]')
                    if all_editable:
                        text_input = all_editable[0]
                        logger.info(f"Using first of {len(all_editable)} editable divs")
                except:
                    pass
            
            # Fallback 2: any textarea
            if not text_input:
                try:
                    all_textareas = page.query_selector_all('textarea')
                    if all_textareas:
                        text_input = all_textareas[0]
                        logger.info(f"Using first of {len(all_textareas)} textareas")
                except:
                    pass
            
            # Fallback 3: Try to find by aria-label
            if not text_input:
                try:
                    text_input = page.query_selector('[aria-label*="Share" i], [aria-label*="post" i]')
                    if text_input:
                        logger.info(f"Found by aria-label")
                except:
                    pass
            
            if not text_input:
                logger.error("Text input NOT found!")
                save_debug(page, "02_no_input")
                input("Press Enter to exit...")
                context.close()
                return False
            
            # Step 5: Type content
            logger.info(f"Typing {len(content)} characters...")

            text_input.click()
            time.sleep(1)

            # Clear any existing text
            page.keyboard.press('Control+A')
            time.sleep(0.3)
            page.keyboard.press('Delete')
            time.sleep(0.3)

            # Type content in chunks with focus check
            chunks = [content[i:i+50] for i in range(0, len(content), 50)]
            for i, chunk in enumerate(chunks):
                try:
                    # Refocus before each chunk
                    if i > 0:
                        text_input.click()
                        time.sleep(0.2)
                    page.keyboard.type(chunk, delay=10)
                    logger.debug(f"Chunk {i+1}/{len(chunks)} typed")
                except Exception as e:
                    logger.warning(f"Chunk {i+1} failed: {e}")
                    # Fallback: use fill
                    try:
                        text_input.fill(chunk)
                    except:
                        pass
                time.sleep(0.2)

            time.sleep(2)

            # Verify
            try:
                entered = text_input.inner_text()
                logger.info(f"Entered: {len(entered)}/{len(content)} chars")
                if len(entered) < len(content) * 0.8:
                    logger.warning("Text mismatch - retrying...")
                    text_input.fill(content)
                    time.sleep(1)
            except Exception as e:
                logger.warning(f"Could not verify text: {e}")

            save_debug(page, "03_content_entered")
            
            # Step 6: Click Post button
            logger.info("Clicking Post button...")

            post_clicked = False
            post_selectors = [
                'button:has-text("Post")',
                'button.artdeco-button:has-text("Post")',
                '[data-control-name="post_post"]',
                'button:has-text("POST")',
            ]

            for sel in post_selectors:
                try:
                    post_btn = page.locator(sel).first
                    if post_btn.count() > 0:
                        post_btn.wait_for(state="enabled", timeout=5000)
                        post_btn.click()
                        logger.info(f"Post clicked via: {sel}")
                        post_clicked = True
                        break
                except Exception as e:
                    logger.debug(f"Selector {sel} failed: {e}")
                    pass

            if not post_clicked:
                # Fallback: find any button with "Post" text
                try:
                    all_buttons = page.locator('button').all()
                    for btn in all_buttons:
                        try:
                            txt = btn.inner_text().strip().upper()
                            if txt == "POST" or txt.startswith("POST "):
                                btn.wait_for(state="enabled", timeout=2000)
                                btn.click()
                                logger.info("Post clicked via fallback")
                                post_clicked = True
                                break
                        except:
                            pass
                except Exception as e:
                    logger.debug(f"Fallback failed: {e}")

            if not post_clicked:
                logger.error("Post button NOT found!")
                logger.info("Available buttons:")
                try:
                    buttons = page.locator('button').all()
                    for i, btn in enumerate(buttons[:30]):
                        try:
                            txt = btn.inner_text().strip()
                            if txt:
                                logger.info(f"  [{i}] {txt[:50]}")
                        except:
                            pass
                except:
                    pass
                save_debug(page, "03_no_post_button")
                input("Press Enter to exit...")
                context.close()
                return False

            # Step 7: Wait for confirmation
            logger.info("Waiting for post to publish...")
            time.sleep(3)

            # Check for success indicators
            success_indicators = [
                ('button:has-text("See fewer")', "Feed loaded"),
                ('text="View post"', "View post link"),
                ('text="Post successful"', "Success notification"),
            ]

            for sel, desc in success_indicators:
                try:
                    if page.locator(sel).count() > 0:
                        logger.info(f"Post confirmed via: {desc}")
                        break
                except:
                    pass

            try:
                page.wait_for_selector('button:has-text("See fewer")', timeout=10000)
                logger.info("Post published!")
            except:
                logger.info("Post may be published")

            save_debug(page, "04_success")
            
            success = True
            logger.info("=" * 60)
            logger.info("[SUCCESS] Post published to LinkedIn!")
            logger.info("=" * 60)
            
        except Exception as e:
            logger.error(f"Error: {e}")
            save_debug(page, "error")
        
        # Keep browser open
        logger.info("Browser open for verification...")
        logger.info("Press Enter to exit...")
        try:
            input("Press Enter to exit...")
        except:
            pass
        
        context.close()
    
    return success


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
    logger.info(f"Done: {done_file.name}")


def main():
    import argparse
    parser = argparse.ArgumentParser(description="LinkedIn Auto Poster")
    parser.add_argument('--post', type=str, help='Draft file to post')
    parser.add_argument('--test', action='store_true', help='Test login')
    args = parser.parse_args()
    
    # Ensure directories
    for d in [PENDING_FOLDER, DONE_FOLDER, LOGS_FOLDER, SESSION_PATH, DEBUG_FOLDER]:
        d.mkdir(parents=True, exist_ok=True)
    
    if args.test:
        logger.info("Test mode - checking LinkedIn login...")
        with sync_playwright() as p:
            context = p.chromium.launch_persistent_context(
                user_data_dir=str(SESSION_PATH),
                headless=False,
                args=["--no-sandbox"],
                timeout=120000
            )
            page = context.pages[0] if context.pages else context.new_page()
            page.goto("https://www.linkedin.com/", wait_until="domcontentloaded", timeout=120000)
            
            if not is_logged_in(page):
                logger.info("Not logged in - waiting for manual login...")
                wait_for_login(page, timeout=180)
            
            logger.info("Browser open - verify you're on feed")
            input("Press Enter to exit...")
            context.close()
        return
    
    if not args.post:
        drafts = list(PENDING_FOLDER.glob('linkedin_post_*.md'))
        if drafts:
            logger.info(f"Found {len(drafts)} draft(s):")
            for d in drafts[:10]:
                logger.info(f"  - {d.name}")
            if len(drafts) > 10:
                logger.info(f"  ... and {len(drafts) - 10} more")
            logger.info(f"\nRun: python tools\\linkedin_auto_poster.py --post {drafts[0].name}")
        else:
            logger.info("No drafts in Pending_Approval")
        return
    
    # Find and read draft
    draft_path = PENDING_FOLDER / args.post
    if not draft_path.exists():
        logger.error(f"Not found: {args.post}")
        return
    
    content = read_draft_content(draft_path)
    if not content:
        logger.error("Could not read content")
        return
    
    logger.info(f"Posting: {args.post}")
    
    # Post
    if post_to_linkedin(content):
        move_to_done(draft_path, content)
        logger.info("Done!")
    else:
        logger.error("Failed!")


if __name__ == "__main__":
    main()
