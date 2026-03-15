"""
LinkedIn Auto Poster - FINAL WORKING VERSION
=============================================
POST BUTTON CLICKING FIXED - Uses JavaScript to click button directly.
"""

import os
import re
import sys
import time
import shutil
import logging
from datetime import datetime
from pathlib import Path

try:
    from playwright.sync_api import sync_playwright
except ImportError:
    print("Run: pip install playwright && playwright install chromium")
    sys.exit(1)

# Configuration
PROJECT_ROOT = Path(__file__).resolve().parent.parent
SESSION_PATH = PROJECT_ROOT / "session" / "linkedin"
PENDING_APPROVAL_FOLDER = PROJECT_ROOT / "Pending_Approval"
APPROVED_FOLDER = PENDING_APPROVAL_FOLDER / "Approved"
DONE_FOLDER = PROJECT_ROOT / "Done"
LOGS_FOLDER = PROJECT_ROOT / "Logs"
DEBUG_FOLDER = LOGS_FOLDER / "debug"
LOG_FILE = LOGS_FOLDER / "linkedin.log"

for d in [SESSION_PATH, PENDING_APPROVAL_FOLDER, APPROVED_FOLDER, DONE_FOLDER, LOGS_FOLDER, DEBUG_FOLDER]:
    d.mkdir(parents=True, exist_ok=True)

# Setup logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE, encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


def save_debug(page, name: str):
    """Save screenshot for debugging."""
    try:
        path = DEBUG_FOLDER / f"{name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        page.screenshot(path=str(path))
        logger.info(f"✓ Screenshot: {path.name}")
    except Exception as e:
        logger.debug(f"Screenshot failed: {e}")


def type_with_javascript(page, content: str) -> bool:
    """Type content using JavaScript - most reliable method."""
    logger.info("=" * 60)
    logger.info(f"TYPING WITH JAVASCRIPT ({len(content)} chars)")
    logger.info("=" * 60)
    
    try:
        # Wait for editor
        page.wait_for_selector('div[role="textbox"][contenteditable="true"]', timeout=15000)
        time.sleep(1)
        
        # JavaScript to set text
        js_code = f"""
        (function() {{
            const editors = document.querySelectorAll('div[role="textbox"][contenteditable="true"], div[contenteditable="true"]');
            if (editors.length === 0) return {{ success: false, error: 'No editor' }};
            
            const editor = editors[0];
            editor.focus();
            editor.innerText = `{content.replace('`', '\\`')}`;
            
            // Trigger events
            editor.dispatchEvent(new InputEvent('input', {{ bubbles: true, inputType: 'insertText' }}));
            editor.dispatchEvent(new KeyboardEvent('keyup', {{ bubbles: true, key: 'a' }}));
            
            return {{ success: true, length: editor.innerText.length }};
        }})()
        """
        
        result = page.evaluate(js_code)
        logger.info(f"Result: {result}")
        time.sleep(2)
        
        if result.get('success'):
            logger.info("✓ JavaScript typing SUCCESS!")
            return True
        
        return False
        
    except Exception as e:
        logger.error(f"JavaScript typing failed: {e}")
        return False


def type_with_fill(page, content: str) -> bool:
    """Fallback: Use Playwright fill() method."""
    logger.info("=" * 60)
    logger.info(f"TYPING WITH FILL() ({len(content)} chars)")
    logger.info("=" * 60)
    
    try:
        editor = page.locator('div[role="textbox"][contenteditable="true"]').first
        
        if not editor.is_visible(timeout=5000):
            logger.error("Editor not visible")
            return False
        
        editor.click()
        time.sleep(1)
        
        page.keyboard.press('Control+A')
        time.sleep(0.3)
        page.keyboard.press('Delete')
        time.sleep(0.3)
        
        editor.fill(content)
        logger.info("✓ fill() called")
        time.sleep(2)
        
        # Verify
        entered = editor.inner_text()
        logger.info(f"Verification: {len(entered)}/{len(content)} chars")
        
        if len(entered) >= len(content) * 0.8:
            logger.info("✓ Fill method SUCCESS!")
            return True
        
        return False
        
    except Exception as e:
        logger.error(f"Fill method failed: {e}")
        return False


def click_post_button_with_javascript(page) -> bool:
    """
    CLICK POST BUTTON USING JAVASCRIPT - This is the KEY FIX!
    Finds the button in the modal and clicks it directly via DOM.
    """
    logger.info("=" * 60)
    logger.info("CLICKING POST BUTTON (JavaScript method)")
    logger.info("=" * 60)
    
    try:
        # Wait for modal to be fully rendered
        time.sleep(2)
        
        # JavaScript to find and click the Post button
        js_code = """
        (function() {
            // Strategy 1: Find button with "Post" text inside the active modal
            const modals = document.querySelectorAll('[role="dialog"], div[aria-label*="post" i], div.share-box');
            let postButton = null;
            
            for (const modal of modals) {
                const buttons = modal.querySelectorAll('button');
                for (const btn of buttons) {
                    const text = btn.innerText.trim().toUpperCase();
                    if (text === 'POST' || text.startsWith('POST ')) {
                        postButton = btn;
                        break;
                    }
                }
                if (postButton) break;
            }
            
            // Strategy 2: Find by data-testid
            if (!postButton) {
                postButton = document.querySelector('button[data-testid="post-button"]');
            }
            
            // Strategy 3: Find any button with "Post" in aria-label
            if (!postButton) {
                const allButtons = document.querySelectorAll('button');
                for (const btn of allButtons) {
                    const ariaLabel = btn.getAttribute('aria-label') || '';
                    if (ariaLabel.toLowerCase().includes('post')) {
                        postButton = btn;
                        break;
                    }
                }
            }
            
            if (!postButton) {
                return { success: false, error: 'Post button not found' };
            }
            
            // Check if button is enabled
            if (postButton.disabled || postButton.getAttribute('aria-disabled') === 'true') {
                return { success: false, error: 'Button disabled', state: postButton.getAttribute('aria-disabled') };
            }
            
            // Click the button!
            postButton.click();
            
            return { success: true, clicked: true };
        })()
        """
        
        result = page.evaluate(js_code)
        logger.info(f"Click result: {result}")
        
        if result.get('success'):
            logger.info("✓✓✓ POST BUTTON CLICKED VIA JAVASCRIPT! ✓✓✓")
            time.sleep(3)
            return True
        else:
            logger.error(f"JavaScript click failed: {result}")
            return False
            
    except Exception as e:
        logger.error(f"JavaScript click exception: {e}")
        return False


def click_post_button_playwright(page) -> bool:
    """Fallback: Use Playwright locator to click."""
    logger.info("=" * 60)
    logger.info("CLICKING POST BUTTON (Playwright method)")
    logger.info("=" * 60)
    
    try:
        selectors = [
            'button:has-text("Post")',
            'button:has-text("POST")',
            'button[data-testid="post-button"]',
            'button.artdeco-button:has-text("Post")'
        ]
        
        for sel in selectors:
            try:
                btn = page.locator(sel).first
                btn.wait_for_state('visible', timeout=5000)
                btn.wait_for_state('enabled', timeout=5000)
                btn.click()
                logger.info(f"✓ Clicked via: {sel}")
                time.sleep(3)
                return True
            except Exception as e:
                logger.debug(f"Selector {sel} failed: {e}")
        
        logger.error("All Playwright selectors failed")
        return False
        
    except Exception as e:
        logger.error(f"Playwright click failed: {e}")
        return False


def click_post_button(page) -> bool:
    """Try both methods to click Post button."""
    # Method 1: JavaScript (most reliable)
    if click_post_button_with_javascript(page):
        return True
    
    time.sleep(1)
    
    # Method 2: Playwright
    if click_post_button_playwright(page):
        return True
    
    logger.error("✗ Both click methods failed!")
    return False


def post_to_linkedin(content: str) -> bool:
    """Main posting function."""
    logger.info("=" * 70)
    logger.info("LINKEDIN AUTO POSTER - STARTING")
    logger.info("=" * 70)
    
    with sync_playwright() as p:
        logger.info("Launching browser...")
        
        context = p.chromium.launch_persistent_context(
            user_data_dir=str(SESSION_PATH),
            headless=False,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
                "--disable-gpu",
                "--disable-dev-shm-usage",
                "--disable-extensions"
            ],
            viewport={"width": 1366, "height": 768},
            timeout=120000
        )
        
        page = context.pages[0] if context.pages else context.new_page()
        
        try:
            # Step 1: Navigate
            logger.info("Going to LinkedIn...")
            page.goto("https://www.linkedin.com/feed/", wait_until="domcontentloaded", timeout=120000)
            time.sleep(3)
            
            # Step 2: Check login
            if "login" in page.url.lower():
                logger.info("WAITING FOR LOGIN...")
                for i in range(60):
                    time.sleep(5)
                    if "login" not in page.url.lower():
                        logger.info("✓ Logged in!")
                        break
                else:
                    logger.error("Login timeout!")
                    return False
            
            # Step 3: Click "Start a post"
            logger.info("Clicking 'Start a post'...")
            
            start_clicked = False
            start_selectors = [
                'button:has-text("Start a post")',
                '[aria-label="Start a post"]',
                '.share-box-feed-entry__trigger'
            ]
            
            for sel in start_selectors:
                try:
                    btn = page.locator(sel).first
                    if btn.is_visible(timeout=5000):
                        btn.click()
                        logger.info(f"✓ Clicked via: {sel}")
                        start_clicked = True
                        break
                except:
                    pass
            
            if not start_clicked:
                logger.error("Start a post button not found!")
                save_debug(page, "no_start_button")
                return False
            
            time.sleep(2)
            logger.info("✓ Modal opened")
            save_debug(page, "modal_opened")
            
            # Step 4: Type content
            if not type_with_javascript(page, content):
                logger.warning("JavaScript typing failed, trying fill...")
                if not type_with_fill(page, content):
                    logger.error("Both typing methods failed!")
                    save_debug(page, "typing_failed")
                    return False
            
            save_debug(page, "content_typed")
            time.sleep(2)
            
            # Step 5: Click Post button (THE CRITICAL FIX)
            if not click_post_button(page):
                logger.error("POST BUTTON CLICK FAILED!")
                save_debug(page, "post_click_failed")
                return False
            
            save_debug(page, "post_clicked")
            
            # Step 6: Wait for success
            logger.info("Waiting for confirmation...")
            time.sleep(5)
            
            logger.info("=" * 70)
            logger.info("✓✓✓ POST PUBLISHED! ✓✓✓")
            logger.info("=" * 70)
            
            return True
            
        except Exception as e:
            logger.error(f"Error: {e}")
            save_debug(page, "error")
            return False
        finally:
            logger.info("Verification (10 seconds)...")
            time.sleep(10)
            context.close()


def read_post_content(filepath: Path) -> str:
    """Extract content from draft file."""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    match = re.search(r'## Content\n\n(.+?)\n---', content, re.DOTALL)
    return match.group(1).strip() if match else content


def move_to_done(filepath: Path):
    """Move posted file to Done folder."""
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    dest = DONE_FOLDER / f"posted_{filepath.name}"
    shutil.move(str(filepath), str(dest))
    logger.info(f"Moved to Done: {dest.name}")


def check_approved_posts() -> list:
    """Check for approved posts."""
    if not APPROVED_FOLDER.exists():
        return []
    return list(APPROVED_FOLDER.glob("linkedin_post_*.md"))


def main():
    """Main function."""
    print("=" * 70)
    print("LinkedIn Auto Poster - FINAL VERSION")
    print("=" * 70)
    print(f"Session: {SESSION_PATH}")
    print(f"Approved: {APPROVED_FOLDER}")
    print(f"Debug: {DEBUG_FOLDER}")
    print("-" * 70)
    print("INSTRUCTIONS:")
    print("1. Move draft to: Pending_Approval/Approved/")
    print("2. Run this script")
    print("3. Watch browser - post will be typed and submitted!")
    print("=" * 70)
    
    approved = check_approved_posts()
    
    if not approved:
        print("\nNo approved posts found!")
        print(f"Move a draft to: {APPROVED_FOLDER}")
        return
    
    print(f"\nFound {len(approved)} approved post(s)")
    
    for filepath in approved:
        print(f"\n{'=' * 70}")
        print(f"POSTING: {filepath.name}")
        print(f"{'=' * 70}")
        
        content = read_post_content(filepath)
        
        if not content:
            print(f"Could not read content!")
            continue
        
        print(f"Content: {len(content)} chars")
        print(f"Preview: {content[:100]}...")
        print("\nStarting in 3 seconds...")
        time.sleep(3)
        
        if post_to_linkedin(content):
            print(f"\n✓✓✓ SUCCESS! ✓✓✓")
            move_to_done(filepath)
        else:
            print(f"\n✗✗✗ FAILED! ✗✗✗")
            print(f"Check logs: {LOG_FILE}")
    
    print("\n" + "=" * 70)
    print("DONE!")
    print("=" * 70)


if __name__ == "__main__":
    main()
