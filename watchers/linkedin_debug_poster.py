"""
LinkedIn Auto Poster - DEBUG VERSION
=====================================
This version will show EXACTLY what's happening step by step.
Run this and share the output so we can fix the exact issue.
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
LOG_FILE = LOGS_FOLDER / "linkedin_debug.log"

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

# =============================================================================
# DEBUG FUNCTIONS
# =============================================================================

def save_debug_info(page, step_name: str):
    """Save screenshot and page HTML for debugging."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    try:
        # Screenshot
        screenshot_path = DEBUG_FOLDER / f"{timestamp}_{step_name}.png"
        page.screenshot(path=str(screenshot_path))
        logger.info(f"✓ Screenshot saved: {screenshot_path}")
        
        # HTML
        html_path = DEBUG_FOLDER / f"{timestamp}_{step_name}.html"
        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(page.content())
        logger.info(f"✓ HTML saved: {html_path}")
        
        # Console logs
        console_path = DEBUG_FOLDER / f"{timestamp}_{step_name}_console.txt"
        with open(console_path, 'w', encoding='utf-8') as f:
            f.write(f"URL: {page.url}\n")
            f.write(f"Title: {page.title()}\n")
        logger.info(f"✓ Console info saved: {console_path}")
        
    except Exception as e:
        logger.error(f"Debug save failed: {e}")


def find_all_editors(page):
    """Find ALL possible text input elements and log them."""
    logger.info("=" * 70)
    logger.info("SEARCHING FOR ALL POSSIBLE TEXT INPUTS...")
    logger.info("=" * 70)
    
    selectors = [
        'div[role="textbox"][contenteditable="true"]',
        '[data-testid="post-creation-textarea"]',
        'div[contenteditable="true"]',
        'textarea',
        '.editor-content-area',
        'div.share-box-feed-entry',
        '[aria-label*="post" i]',
        '[placeholder*="post" i]',
    ]
    
    found_elements = []
    
    for i, selector in enumerate(selectors, 1):
        try:
            elements = page.query_selector_all(selector)
            if elements:
                logger.info(f"\n[{i}] Selector: {selector}")
                logger.info(f"    Found {len(elements)} element(s)")
                
                for j, elem in enumerate(elements):
                    try:
                        tag = elem.evaluate('el => el.tagName')
                        text = elem.inner_text()[:100] if elem.inner_text() else "(empty)"
                        visible = elem.is_visible()
                        logger.info(f"    Element {j+1}: tag={tag}, visible={visible}, text_len={len(text)}")
                        logger.info(f"               text preview: {text[:50]}...")
                        
                        found_elements.append({
                            'selector': selector,
                            'element': elem,
                            'tag': tag,
                            'visible': visible,
                            'text': text
                        })
                    except Exception as e:
                        logger.debug(f"    Element {j+1} error: {e}")
        except Exception as e:
            logger.debug(f"Selector {selector} error: {e}")
    
    logger.info("=" * 70)
    logger.info(f"TOTAL FOUND: {len(found_elements)} input elements")
    logger.info("=" * 70)
    
    return found_elements


def try_type_method_1(page, content: str) -> bool:
    """Method 1: Direct fill()"""
    logger.info("\n" + "=" * 70)
    logger.info("TRYING METHOD 1: Direct fill()")
    logger.info("=" * 70)
    
    try:
        # Find the main editor
        editor = page.locator('div[role="textbox"][contenteditable="true"]').first
        
        if not editor.is_visible(timeout=5000):
            logger.error("Editor not visible!")
            return False
        
        logger.info("✓ Editor found and visible")
        
        # Click to focus
        editor.click()
        logger.info("✓ Clicked to focus")
        time.sleep(1)
        
        # Clear existing
        page.keyboard.press('Control+A')
        time.sleep(0.3)
        page.keyboard.press('Delete')
        time.sleep(0.3)
        logger.info("✓ Cleared existing content")
        
        # Use fill() - most reliable
        editor.fill(content)
        logger.info(f"✓ fill() called with {len(content)} chars")
        
        time.sleep(2)
        
        # Verify
        entered = editor.inner_text()
        logger.info(f"Verification: {len(entered)} chars entered (expected {len(content)})")
        
        if len(entered) >= len(content) * 0.8:
            logger.info("✓✓✓ METHOD 1 SUCCESSFUL! ✓✓✓")
            return True
        else:
            logger.warning("Method 1 partial success")
            return False
            
    except Exception as e:
        logger.error(f"Method 1 failed: {e}")
        return False


def try_type_method_2(page, content: str) -> bool:
    """Method 2: JavaScript innerText"""
    logger.info("\n" + "=" * 70)
    logger.info("TRYING METHOD 2: JavaScript innerText")
    logger.info("=" * 70)
    
    try:
        js_code = f"""
        (function() {{
            const editors = document.querySelectorAll('div[role="textbox"][contenteditable="true"]');
            if (editors.length === 0) {{
                return {{ success: false, error: 'No editor found' }};
            }}
            
            const editor = editors[0];
            editor.focus();
            editor.innerText = `{content.replace('`', '\\`')}`;
            
            // Trigger events
            editor.dispatchEvent(new InputEvent('input', {{ bubbles: true }}));
            editor.dispatchEvent(new KeyboardEvent('keyup', {{ bubbles: true }}));
            
            return {{ 
                success: true, 
                length: editor.innerText.length
            }};
        }})()
        """
        
        result = page.evaluate(js_code)
        logger.info(f"JavaScript result: {result}")
        
        time.sleep(2)
        
        if result.get('success'):
            # Verify
            editor = page.locator('div[role="textbox"][contenteditable="true"]').first
            entered = editor.inner_text()
            logger.info(f"Verification: {len(entered)} chars (expected {len(content)})")
            
            if len(entered) >= len(content) * 0.8:
                logger.info("✓✓✓ METHOD 2 SUCCESSFUL! ✓✓✓")
                return True
        
        return False
        
    except Exception as e:
        logger.error(f"Method 2 failed: {e}")
        return False


def try_type_method_3(page, content: str) -> bool:
    """Method 3: Keyboard type character by character"""
    logger.info("\n" + "=" * 70)
    logger.info("TRYING METHOD 3: Keyboard type (slow)")
    logger.info("=" * 70)
    
    try:
        editor = page.locator('div[role="textbox"][contenteditable="true"]').first
        
        if not editor.is_visible(timeout=5000):
            logger.error("Editor not visible!")
            return False
        
        editor.click()
        time.sleep(1)
        
        page.keyboard.press('Control+A')
        time.sleep(0.3)
        page.keyboard.press('Delete')
        time.sleep(0.3)
        
        logger.info(f"Typing {len(content)} characters one by one...")
        
        # Type in chunks
        for i in range(0, len(content), 10):
            chunk = content[i:i+10]
            for char in chunk:
                page.keyboard.type(char, delay=100)
            time.sleep(0.5)
            logger.info(f"Typed {min(i+10, len(content))}/{len(content)} chars")
        
        time.sleep(2)
        
        # Verify
        entered = editor.inner_text()
        logger.info(f"Verification: {len(entered)} chars (expected {len(content)})")
        
        if len(entered) >= len(content) * 0.8:
            logger.info("✓✓✓ METHOD 3 SUCCESSFUL! ✓✓✓")
            return True
        
        return False
        
    except Exception as e:
        logger.error(f"Method 3 failed: {e}")
        return False


def type_content_with_all_methods(page, content: str) -> bool:
    """Try ALL methods until one works."""
    logger.info("=" * 70)
    logger.info("STARTING POST TYPING - WILL TRY ALL METHODS")
    logger.info(f"Content length: {len(content)} characters")
    logger.info("=" * 70)
    
    # First, show what elements are available
    find_all_editors(page)
    
    # Try each method
    if try_type_method_1(page, content):
        logger.info("SUCCESS with Method 1 (fill)")
        save_debug_info(page, "success_method_1")
        return True
    
    time.sleep(1)
    save_debug_info(page, "after_method_1")
    
    if try_type_method_2(page, content):
        logger.info("SUCCESS with Method 2 (JavaScript)")
        save_debug_info(page, "success_method_2")
        return True
    
    time.sleep(1)
    save_debug_info(page, "after_method_2")
    
    if try_type_method_3(page, content):
        logger.info("SUCCESS with Method 3 (keyboard)")
        save_debug_info(page, "success_method_3")
        return True
    
    save_debug_info(page, "all_methods_failed")
    logger.error("=" * 70)
    logger.error("ALL METHODS FAILED!")
    logger.error("Check debug folder for screenshots and HTML")
    logger.error("=" * 70)
    return False


def click_post_button(page) -> bool:
    """Click the Post button."""
    logger.info("=" * 70)
    logger.info("CLICKING POST BUTTON")
    logger.info("=" * 70)
    
    try:
        # Find button
        btn = page.locator('button:has-text("Post")').first
        btn.wait_for_state('visible', timeout=10000)
        btn.wait_for_state('enabled', timeout=5000)
        
        logger.info("✓ Post button found and enabled")
        
        btn.click()
        logger.info("✓ Post button clicked!")
        
        time.sleep(3)
        
        # Check for success
        if page.query_selector('button:has-text("See fewer")'):
            logger.info("✓ Post published successfully!")
        
        return True
        
    except Exception as e:
        logger.error(f"Post button click failed: {e}")
        save_debug_info(page, "post_button_failed")
        return False


def post_to_linkedin(content: str) -> bool:
    """Main posting function with full debug."""
    logger.info("=" * 70)
    logger.info("LINKEDIN AUTO POSTER - DEBUG VERSION")
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
            save_debug_info(page, "01_feed_loaded")
            
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
            
            save_debug_info(page, "02_logged_in")
            
            # Step 3: Click "Start a post"
            logger.info("Clicking 'Start a post'...")
            
            start_selectors = [
                'button:has-text("Start a post")',
                '[aria-label="Start a post"]',
                '.share-box-feed-entry__trigger'
            ]
            
            start_clicked = False
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
                logger.error("Could not click 'Start a post'!")
                save_debug_info(page, "03_no_start_button")
                return False
            
            time.sleep(2)
            save_debug_info(page, "04_modal_opened")
            logger.info("✓ Compose modal opened")
            
            # Step 4: TYPE CONTENT (with all methods)
            if not type_content_with_all_methods(page, content):
                logger.error("TYPING FAILED!")
                return False
            
            time.sleep(2)
            save_debug_info(page, "05_content_typed")
            
            # Step 5: Click Post
            if not click_post_button(page):
                logger.error("POST BUTTON CLICK FAILED!")
                return False
            
            time.sleep(3)
            save_debug_info(page, "06_post_clicked")
            
            logger.info("=" * 70)
            logger.info("✓✓✓ POST SUCCESSFUL! ✓✓✓")
            logger.info("=" * 70)
            
            return True
            
        except Exception as e:
            logger.error(f"Error: {e}")
            save_debug_info(page, "error")
            return False
        finally:
            logger.info("Browser open for 10 seconds for verification...")
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
    dest = DONE_FOLDER / f"posted_{filepath.name}"
    shutil.move(str(filepath), str(dest))
    logger.info(f"Moved to Done: {dest.name}")


def check_approved_posts() -> list:
    """Check for approved posts."""
    if not APPROVED_FOLDER.exists():
        return []
    return list(APPROVED_FOLDER.glob("linkedin_post_*.md"))


def main():
    """Main function - check for approved posts and post them."""
    print("=" * 70)
    print("LinkedIn Auto Poster - DEBUG VERSION")
    print("=" * 70)
    print(f"Session: {SESSION_PATH}")
    print(f"Approved: {APPROVED_FOLDER}")
    print(f"Debug: {DEBUG_FOLDER}")
    print("-" * 70)
    print("INSTRUCTIONS:")
    print("1. Move a draft file to Pending_Approval/Approved/ folder")
    print("2. Run this script")
    print("3. Watch the browser and console output")
    print("4. Check Logs/debug/ folder for screenshots")
    print("=" * 70)
    
    # Check for approved posts
    approved = check_approved_posts()
    
    if not approved:
        print("\nNo approved posts found!")
        print(f"Please move a draft to: {APPROVED_FOLDER}")
        print("\nOr test with a sample post? (y/n): ", end='')
        
        if input().lower() != 'y':
            return
        
        # Create test post
        test_content = f"""🧪 TEST POST

This is a test post to verify the auto-posting system is working.

Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

#Test #Automation
"""
        
        # Save as approved
        test_file = APPROVED_FOLDER / f"test_post_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        with open(test_file, 'w', encoding='utf-8') as f:
            f.write(f"""---
type: test_post
created: {datetime.now().isoformat()}
---

## Content

{test_content}
---
""")
        
        approved = [test_file]
        print(f"Created test post: {test_file.name}")
    
    print(f"\nFound {len(approved)} approved post(s)")
    
    # Post each approved file
    for filepath in approved:
        print(f"\n{'=' * 70}")
        print(f"POSTING: {filepath.name}")
        print(f"{'=' * 70}")
        
        content = read_post_content(filepath)
        
        if not content:
            print(f"Could not read content from {filepath.name}")
            continue
        
        print(f"Content length: {len(content)} chars")
        print(f"Content preview: {content[:100]}...")
        print("\nStarting in 3 seconds...")
        time.sleep(3)
        
        if post_to_linkedin(content):
            print(f"\n✓✓✓ SUCCESS! Post published!")
            move_to_done(filepath)
        else:
            print(f"\n✗✗✗ FAILED! Check logs in {LOG_FILE}")
            print(f"Debug screenshots in: {DEBUG_FOLDER}")
    
    print("\n" + "=" * 70)
    print("DONE!")
    print("=" * 70)


if __name__ == "__main__":
    main()
