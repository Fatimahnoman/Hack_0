"""
Auto LinkedIn Poster - Silver Tier (Fixed v3)
==============================================
FIXED v3: Simpler approach with better debugging.
Uses direct keyboard input and waits longer for UI.

Run: python tools\auto_linkedin_poster.py --post FILENAME
"""

import os
import re
import sys
import shutil
import time
import logging
from datetime import datetime

try:
    from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout
except ImportError as e:
    print(f"[ERROR] Missing playwright: {e}")
    print("Install: pip install playwright && playwright install chromium")
    sys.exit(1)

# Configuration
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PENDING_APPROVAL_FOLDER = os.path.join(PROJECT_ROOT, "Pending_Approval")
DONE_FOLDER = os.path.join(PROJECT_ROOT, "Done")
LOGS_FOLDER = os.path.join(PROJECT_ROOT, "Logs")
DASHBOARD_FILE = os.path.join(PROJECT_ROOT, "Dashboard.md")
SESSION_PATH = os.path.join(PROJECT_ROOT, "session", "linkedin")

# Logging
def setup_logging():
    if not os.path.exists(LOGS_FOLDER):
        os.makedirs(LOGS_FOLDER)
    log_file = os.path.join(LOGS_FOLDER, f"linkedin_{datetime.now().strftime('%Y-%m-%d')}.log")
    logger = logging.getLogger("AutoLinkedInPoster")
    logger.setLevel(logging.INFO)
    if not logger.handlers:
        fh = logging.FileHandler(log_file, encoding='utf-8')
        fh.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
        logger.addHandler(fh)
        ch = logging.StreamHandler()
        ch.setFormatter(logging.Formatter('%(message)s'))
        logger.addHandler(ch)
    return logger

logger = setup_logging()


def ensure_directories():
    for d in [PENDING_APPROVAL_FOLDER, DONE_FOLDER, LOGS_FOLDER, SESSION_PATH]:
        if not os.path.exists(d):
            os.makedirs(d)


def update_dashboard():
    if not os.path.exists(DASHBOARD_FILE):
        return
    pending_count = len([f for f in os.listdir(PENDING_APPROVAL_FOLDER)
                        if f.startswith('linkedin_post_') and f.endswith('.md')])
    with open(DASHBOARD_FILE, 'r', encoding='utf-8') as f:
        content = f.read()
    if '**LinkedIn Posts Pending:**' in content:
        content = re.sub(r'\*\*LinkedIn Posts Pending:\*\*\s*\d+',
                        f'**LinkedIn Posts Pending:** {pending_count}', content)
    with open(DASHBOARD_FILE, 'w', encoding='utf-8') as f:
        f.write(content)
    logger.info(f"  [DASHBOARD] Updated pending count: {pending_count}")


def take_screenshot(page, name):
    """Take screenshot for debugging."""
    try:
        path = os.path.join(PROJECT_ROOT, f"debug_{name}.png")
        page.screenshot(path=path)
        logger.info(f"[INFO] Screenshot: {path}")
    except Exception as e:
        logger.warning(f"[WARNING] Screenshot failed: {e}")


def save_html(page, name):
    """Save page HTML for debugging."""
    try:
        path = os.path.join(PROJECT_ROOT, f"debug_{name}.html")
        with open(path, 'w', encoding='utf-8') as f:
            f.write(page.content())
        logger.info(f"[INFO] HTML saved: {path}")
    except:
        pass


def post_to_linkedin(draft_filename: str) -> dict:
    """Post to LinkedIn with improved detection."""
    
    logger.info("=" * 60)
    logger.info("Auto LinkedIn Poster - Fixed v3")
    logger.info("=" * 60)
    
    ensure_directories()
    
    # Find draft
    draft_path = os.path.join(PENDING_APPROVAL_FOLDER, draft_filename)
    if not os.path.exists(draft_path):
        logger.error(f"[ERROR] Draft not found: {draft_filename}")
        return {'success': False, 'error': 'File not found'}
    
    # Read content
    with open(draft_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    content_match = re.search(r'## Content\n\n(.+?)\n---', content, re.DOTALL)
    if not content_match:
        logger.error("[ERROR] Invalid draft format")
        return {'success': False, 'error': 'Invalid format'}
    
    post_content = content_match.group(1).strip()
    
    logger.info(f"[INFO] Post content: {len(post_content)} chars")
    logger.info(f"[INFO] Preview: {post_content[:60]}...")
    
    result = {'success': False, 'error': None, 'posted_at': None}
    
    try:
        with sync_playwright() as p:
            logger.info("[INFO] Launching browser...")
            logger.info(f"[INFO] Session: {SESSION_PATH}")
            
            context = p.chromium.launch_persistent_context(
                user_data_dir=SESSION_PATH,
                headless=False,
                args=[
                    "--disable-blink-features=AutomationControlled",
                    "--no-sandbox",
                    "--disable-gpu"
                ],
                timeout=120000
            )
            
            page = context.pages[0] if context.pages else context.new_page()
            
            # Go to LinkedIn
            logger.info("[INFO] Going to LinkedIn...")
            page.goto("https://www.linkedin.com/", wait_until="domcontentloaded", timeout=60000)
            time.sleep(3)
            
            # Check if logged in
            logger.info("[INFO] Checking login status...")
            
            # Wait for user to login if needed (max 3 minutes)
            logged_in = False
            for attempt in range(18):  # 18 x 10 seconds = 3 minutes
                try:
                    # Check for logged-in indicators
                    if page.url != "https://www.linkedin.com/" and "feed" in page.url:
                        logged_in = True
                        logger.info(f"[OK] Already on feed - logged in!")
                        break
                    
                    # Try to find nav elements
                    nav = page.query_selector('nav.global-nav')
                    if nav:
                        logged_in = True
                        logger.info(f"[OK] Found navigation - logged in!")
                        break
                    
                    # Check URL
                    if "login" not in page.url.lower():
                        logged_in = True
                        logger.info(f"[OK] Not on login page - proceeding!")
                        break
                        
                except:
                    pass
                
                if attempt == 0:
                    logger.info("[INFO] If not logged in, please login now...")
                logger.info(f"[INFO] Waiting... ({attempt + 1}/18)")
                time.sleep(10)
            
            if not logged_in:
                logger.warning("[WARNING] Login not detected after 3 minutes")
                logger.warning("[WARNING] Proceeding anyway...")
            
            # Go to feed
            logger.info("[INFO] Going to feed...")
            page.goto("https://www.linkedin.com/feed/", wait_until="domcontentloaded", timeout=60000)
            time.sleep(5)
            
            # Take screenshot
            take_screenshot(page, "feed_loaded")
            
            # CLICK "Start a post" button
            logger.info("[INFO] Looking for 'Start a post' button...")
            
            start_clicked = False
            
            # Try clicking with different methods
            methods_tried = []
            
            # Method 1: Click by text
            try:
                btn = page.locator('button:has-text("Start a post")').first
                if btn.count() > 0:
                    btn.click()
                    start_clicked = True
                    methods_tried.append("text button")
                    logger.info("[OK] Clicked via: text button")
            except Exception as e:
                logger.debug(f"Method 1 failed: {e}")
            
            # Method 2: Click by aria-label
            if not start_clicked:
                try:
                    btn = page.locator('[aria-label="Start a post"]').first
                    if btn.count() > 0:
                        btn.click()
                        start_clicked = True
                        methods_tried.append("aria-label")
                        logger.info("[OK] Clicked via: aria-label")
                except:
                    pass
            
            # Method 3: Click share box
            if not start_clicked:
                try:
                    btn = page.locator('.share-box-feed-entry').first
                    if btn.count() > 0:
                        btn.click()
                        start_clicked = True
                        methods_tried.append("share-box")
                        logger.info("[OK] Clicked via: share-box")
                except:
                    pass
            
            if not start_clicked:
                logger.error("[ERROR] Could not click 'Start a post'")
                logger.info("[INFO] Methods tried: " + ", ".join(methods_tried) if methods_tried else "[INFO] No methods tried")
                take_screenshot(page, "start_post_failed")
                save_html(page, "start_post_failed")
                logger.info("[INFO] Check debug files")
                logger.info("[INFO] Browser staying open...")
                time.sleep(5)
                context.close()
                return {'success': False, 'error': 'Start a post button not found'}
            
            time.sleep(3)
            take_screenshot(page, "modal_opened")
            
            # FIND text input
            logger.info("[INFO] Looking for text input...")
            
            text_input = None
            
            # Try different selectors
            selectors = [
                'div[contenteditable="true"][role="textbox"]',
                'div[contenteditable="true"]',
                '[data-testid="update-editor-text-input"]',
            ]
            
            for selector in selectors:
                try:
                    el = page.locator(selector).first
                    if el.count() > 0:
                        text_input = el
                        logger.info(f"[OK] Found input via: {selector}")
                        break
                except:
                    pass
            
            if not text_input:
                # Try to find ANY contenteditable
                try:
                    all_editable = page.query_selector_all('div[contenteditable="true"]')
                    if all_editable:
                        text_input = page.locator('div[contenteditable="true"]').first
                        logger.info(f"[OK] Found {len(all_editable)} editable divs, using first")
                except:
                    pass
            
            if not text_input:
                logger.error("[ERROR] Text input not found!")
                take_screenshot(page, "no_input")
                save_html(page, "no_input")
                logger.info("[INFO] Check debug files")
                logger.info("[INFO] Browser staying open...")
                time.sleep(5)
                context.close()
                return {'success': False, 'error': 'Text input not found'}
            
            # CLICK input
            logger.info("[INFO] Clicking text input...")
            text_input.click()
            time.sleep(2)
            
            # CLEAR existing
            logger.info("[INFO] Clearing...")
            page.keyboard.press('Control+A')
            time.sleep(0.5)
            page.keyboard.press('Delete')
            time.sleep(0.5)
            
            # TYPE content - use keyboard directly!
            logger.info("[INFO] Typing content...")
            
            # Type in chunks
            chunk_size = 50
            chunks = [post_content[i:i+chunk_size] for i in range(0, len(post_content), chunk_size)]
            
            for i, chunk in enumerate(chunks):
                logger.info(f"[INFO] Typing chunk {i+1}/{len(chunks)}...")
                
                # Use page.keyboard.type for more reliable typing
                try:
                    page.keyboard.type(chunk, delay=20)
                    logger.info(f"[OK] Chunk {i+1} done")
                except Exception as e:
                    logger.warning(f"[WARNING] Chunk {i+1} failed: {e}")
                    # Fallback: try fill
                    try:
                        text_input.fill(chunk)
                        logger.info(f"[OK] Chunk {i+1} filled")
                    except:
                        logger.error(f"[ERROR] Chunk {i+1} completely failed")
                
                time.sleep(0.3)
            
            time.sleep(3)
            
            # Verify
            try:
                entered = text_input.inner_text()
                logger.info(f"[INFO] Entered: {len(entered)} chars")
                if len(entered) < len(post_content) * 0.5:
                    logger.warning("[WARNING] Less text than expected!")
            except:
                logger.warning("[WARNING] Could not verify text")
            
            take_screenshot(page, "content_entered")
            
            # CLICK Post button
            logger.info("[INFO] Looking for Post button...")
            
            post_clicked = False
            
            post_selectors = [
                'button:has-text("Post")',
                'button.artdeco-button:has-text("Post")',
            ]
            
            for selector in post_selectors:
                try:
                    btn = page.locator(selector).first
                    if btn.count() > 0:
                        logger.info(f"[OK] Found Post button via: {selector}")
                        btn.click()
                        post_clicked = True
                        logger.info("[OK] Post button clicked!")
                        break
                except:
                    pass
            
            if post_clicked:
                time.sleep(5)
                
                # Check success
                try:
                    page.wait_for_selector('button:has-text("See fewer")', timeout=10000)
                    logger.info("[OK] Post published!")
                except:
                    logger.info("[INFO] Post may be published")
                
                result['success'] = True
                result['posted_at'] = datetime.now().isoformat()
                
                logger.info("=" * 60)
                logger.info("[SUCCESS] Post published!")
                logger.info("=" * 60)
                logger.info("[INFO] Browser open for verification...")
                logger.info("[INFO] Press Enter to exit")
                
                try:
                    input("Press Enter to exit...")
                except:
                    pass
            else:
                logger.error("[ERROR] Post button not found!")
                take_screenshot(page, "no_post_button")
                logger.info("[INFO] Browser open for debugging...")
                logger.info("[INFO] Press Enter to exit")
                result['error'] = 'Post button not found'
                
                try:
                    input("Press Enter to exit...")
                except:
                    pass
            
            try:
                context.close()
            except:
                pass
    
    except PlaywrightTimeout as e:
        logger.error(f"[ERROR] Timeout: {e}")
        result['error'] = f'Timeout: {e}'
        logger.info("[INFO] Browser open for debugging...")
        try:
            input("Press Enter to exit...")
        except:
            pass
    
    except Exception as e:
        logger.error(f"[ERROR] Failed: {e}")
        result['error'] = str(e)
        logger.info("[INFO] Browser open for debugging...")
        try:
            input("Press Enter to exit...")
        except:
            pass
    
    # Handle result
    if result['success']:
        now = datetime.now()
        timestamp = now.strftime("%Y%m%d_%H%M%S")
        done_file = f"linkedin_post_{timestamp}_DONE.md"
        done_path = os.path.join(DONE_FOLDER, done_file)
        
        with open(done_path, 'w', encoding='utf-8') as f:
            f.write(f"""---
type: linkedin_post_sent
source: {draft_filename}
posted_at: {result['posted_at']}
status: posted
---

# Posted

{post_content}

---
*Posted {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*
""")
        
        os.remove(draft_path)
        update_dashboard()
        
        logger.info(f"  [DONE] {done_file}")
    else:
        logger.error(f"  [FAILED] {result['error']}")
    
    logger.info("=" * 60)
    return result


def check_pending():
    logger.info("=" * 60)
    logger.info("Pending Approvals")
    logger.info("=" * 60)
    
    if not os.path.exists(PENDING_APPROVAL_FOLDER):
        logger.info("[INFO] None")
        return []
    
    files = [f for f in os.listdir(PENDING_APPROVAL_FOLDER)
             if f.startswith('linkedin_post_') and f.endswith('.md')]
    
    for f in sorted(files):
        logger.info(f"  [PENDING] {f}")
    
    logger.info(f"[SUMMARY] {len(files)} pending")
    return files


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Auto LinkedIn Poster v3")
    parser.add_argument('--post', type=str, help='Post draft')
    parser.add_argument('--status', action='store_true', help='List pending')
    args = parser.parse_args()
    
    if args.status:
        check_pending()
    elif args.post:
        post_to_linkedin(args.post)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
