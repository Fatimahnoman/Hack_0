"""
LinkedIn Auto Poster - Gold Tier (IMPROVED & FIXED)
====================================================
Posts content to LinkedIn automatically using Chrome.
Monitors gold/pending_approval/approved/ folder.

IMPROVEMENTS:
1. Better modal detection with multiple waits
2. Improved editor finding with keyboard navigation
3. Direct DOM manipulation fallback
4. Better screenshot debugging
5. Enhanced error handling
"""

import os
import re
import sys
import time
import shutil
import logging
import argparse
from datetime import datetime
from pathlib import Path
from playwright.sync_api import sync_playwright, Page, TimeoutError as PlaywrightTimeout

# =============================================================================
# CONFIGURATION
# =============================================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SESSION_PATH = PROJECT_ROOT / "session" / "linkedin_chrome"
DEBUG_FOLDER = PROJECT_ROOT / "debug_linkedin"
GOLD_DIR = PROJECT_ROOT / "gold"
APPROVED_FOLDER = GOLD_DIR / "pending_approval" / "approved"
DONE_FOLDER = GOLD_DIR / "done"
LOGS_FOLDER = GOLD_DIR / "logs"

# Ensure folders exist
for folder in [DEBUG_FOLDER, APPROVED_FOLDER, DONE_FOLDER, LOGS_FOLDER, SESSION_PATH]:
    folder.mkdir(parents=True, exist_ok=True)

# Setup Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOGS_FOLDER / f"linkedin_poster_{datetime.now().strftime('%Y%m%d')}.log", encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# =============================================================================
# UTILITIES
# =============================================================================

def take_screenshot(page: Page, name: str):
    """Save debug screenshot."""
    try:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        path = DEBUG_FOLDER / f"{name}_{timestamp}.png"
        page.screenshot(path=str(path), full_page=True)
        logger.info(f"[SCREENSHOT] {path.name}")
    except Exception as e:
        logger.warning(f"Screenshot error: {e}")

# =============================================================================
# CORE POSTING LOGIC - IMPROVED
# =============================================================================

def wait_for_modal_ready(page: Page, timeout: int = 20000) -> bool:
    """Wait for LinkedIn compose modal to be fully loaded and ready."""
    logger.info("Waiting for modal to be ready...")
    
    try:
        # Wait for dialog to exist (may be hidden initially)
        dialog = page.locator('div[role="dialog"]').first
        dialog.wait_for(state='attached', timeout=timeout)
        logger.info("✓ Modal dialog attached")
        
        # Wait for it to become visible (LinkedIn animates it)
        try:
            dialog.wait_for(state='visible', timeout=10000)
            logger.info("✓ Modal dialog visible")
        except:
            logger.info("Modal may be animating, continuing...")
        
        # Give extra time for LinkedIn animations
        time.sleep(2)
        
        # Wait for "What do you want to talk about?" text or similar
        modal_texts = [
            "What do you want to talk about?",
            "Start a post",
            "Create a post",
            "Post",
        ]
        
        for text in modal_texts:
            try:
                locator = page.get_by_text(text, exact=False)
                if locator.count() > 0:
                    locator.first.wait_for(state='visible', timeout=3000)
                    logger.info(f"✓ Modal text found: '{text}'")
                    return True
            except:
                continue
        
        # If no text found, check for any dialog with contenteditable
        try:
            page.locator('div[contenteditable="true"]').first.wait_for(state='visible', timeout=3000)
            logger.info("✓ ContentEditable found in modal")
            return True
        except:
            pass
        
        # Last resort: check if dialog exists and has content
        try:
            dialog_content = dialog.inner_text(timeout=3000)
            if len(dialog_content) > 10:
                logger.info(f"✓ Modal has content ({len(dialog_content)} chars)")
                return True
        except:
            pass
        
        logger.info("Modal appears to be open")
        return True  # Assume modal is open even if we can't find specific elements
        
    except Exception as e:
        logger.warning(f"Modal ready check failed: {e}")
        return False

def find_editor_element(page: Page):
    """Find the LinkedIn editor element using multiple strategies."""
    logger.info("Searching for editor element...")
    
    # Strategy 1: Try standard selectors
    selectors = [
        'div.ql-editor[contenteditable="true"]',
        'div[role="textbox"][contenteditable="true"]',
        'div[contenteditable="true"]',
        '.share-creation-state__text-editor',
        'div.update-v2__editor',
    ]
    
    for selector in selectors:
        try:
            locator = page.locator(selector).first
            if locator.is_visible(timeout=2000):
                logger.info(f"✓ Found editor with selector: {selector}")
                return locator
        except:
            continue
    
    # Strategy 2: Find any contenteditable in dialog
    try:
        dialog = page.locator('div[role="dialog"]').first
        editor = dialog.locator('[contenteditable="true"]').first
        if editor.is_visible(timeout=2000):
            logger.info("✓ Found contenteditable in dialog")
            return editor
    except:
        pass
    
    # Strategy 3: Use keyboard navigation to focus editor
    logger.info("Trying keyboard navigation to find editor...")
    try:
        # Press Tab multiple times to reach editor
        for i in range(10):
            page.keyboard.press('Tab')
            time.sleep(0.3)
            
            # Check if something is focused
            focused = page.evaluate('() => document.activeElement')
            if focused and (focused.get('contentEditable') == 'true' or focused.get('role') == 'textbox'):
                logger.info(f"✓ Found editor via keyboard navigation (Tab {i+1})")
                return page.locator(':focus')
    except:
        pass
    
    # Strategy 4: Click on "Start a post" area
    try:
        logger.info("Trying to click on post creation area...")
        page.mouse.click(400, 300)
        time.sleep(1)
        
        # Try to find contenteditable after click
        editor = page.locator('[contenteditable="true"]').first
        if editor.is_visible(timeout=2000):
            logger.info("✓ Found editor after click")
            return editor
    except:
        pass
    
    logger.warning("✗ Could not find editor element")
    return None

def type_post_content(page: Page, content: str) -> bool:
    """Type post content into LinkedIn compose box using improved methods."""
    logger.info("=" * 70)
    logger.info(f"TYPING POST ({len(content)} characters)")
    logger.info("=" * 70)
    
    for attempt in range(3):
        try:
            logger.info(f"Attempt {attempt + 1}/3: Finding editor...")
            
            # Find editor element
            editor = find_editor_element(page)
            
            if editor is None:
                logger.warning(f"Editor not found (attempt {attempt + 1})")
                take_screenshot(page, f"no_editor_att_{attempt + 1}")
                time.sleep(2)
                continue
            
            # Strategy 1: Click and type normally
            try:
                logger.info("Strategy 1: Click and type...")
                editor.click()
                time.sleep(0.5)
                
                # Clear any existing content
                page.keyboard.press('Control+A')
                time.sleep(0.3)
                page.keyboard.press('Delete')
                time.sleep(0.3)
                
                # Type content
                editor.type(content, delay=10)
                time.sleep(1)
                
                # Verify content was typed
                typed_content = editor.inner_text(timeout=2000)
                if len(typed_content) > len(content) * 0.8:
                    logger.info(f"✓ Content typed successfully ({len(typed_content)} chars)")
                    take_screenshot(page, "content_typed")
                    return True
                else:
                    logger.warning(f"Content incomplete: {len(typed_content)}/{len(content)}")
            except Exception as e:
                logger.warning(f"Strategy 1 failed: {e}")
            
            # Strategy 2: Direct DOM manipulation
            try:
                logger.info("Strategy 2: DOM manipulation...")
                
                # Convert newlines to paragraphs
                html_content = content.replace('\n', '</p><p>')
                html_content = f'<p>{html_content}</p>'
                
                result = page.evaluate(f"""
                    () => {{
                        const editor = document.querySelector('div[contenteditable="true"]');
                        if (editor) {{
                            editor.innerHTML = `{html_content}`;
                            editor.dispatchEvent(new Event('input', {{ bubbles: true }}));
                            editor.dispatchEvent(new Event('change', {{ bubbles: true }}));
                            return true;
                        }}
                        return false;
                    }}
                """)
                
                if result:
                    logger.info("✓ DOM manipulation successful")
                    time.sleep(1)
                    take_screenshot(page, "content_dom")
                    return True
            except Exception as e:
                logger.warning(f"Strategy 2 failed: {e}")
            
            # Strategy 3: Paste from clipboard
            try:
                logger.info("Strategy 3: Clipboard paste...")
                
                # Copy to clipboard
                page.evaluate(f"""
                    navigator.clipboard.writeText(`{content}`)
                """)
                
                # Click editor and paste
                editor.click()
                time.sleep(0.5)
                page.keyboard.press('Control+V')
                time.sleep(1)
                
                # Verify
                typed_content = editor.inner_text(timeout=2000)
                if len(typed_content) > len(content) * 0.8:
                    logger.info("✓ Clipboard paste successful")
                    take_screenshot(page, "content_clipboard")
                    return True
            except Exception as e:
                logger.warning(f"Strategy 3 failed: {e}")
            
            take_screenshot(page, f"type_failed_att_{attempt + 1}")
            time.sleep(2)
            
        except Exception as e:
            logger.error(f"Typing error (Attempt {attempt+1}): {e}")
            take_screenshot(page, f"type_error_att_{attempt + 1}")
            time.sleep(2)
    
    logger.error("✗ All typing strategies failed")
    return False

def submit_post(page: Page) -> bool:
    """Click Post button and wait for submission."""
    logger.info("=" * 70)
    logger.info("SUBMITTING POST")
    logger.info("=" * 70)
    
    for attempt in range(3):
        try:
            logger.info(f"Attempt {attempt + 1}/3: Finding Post button...")
            
            # Try multiple button selectors
            post_btn = None
            
            # Strategy 1: Get by role
            try:
                post_btn = page.get_by_role("button", name="Post", exact=True).first
                if post_btn.is_visible(timeout=2000) and post_btn.is_enabled():
                    logger.info("✓ Found Post button (role)")
                    post_btn.click()
                    break
            except:
                pass
            
            # Strategy 2: Get by text
            try:
                post_btn = page.get_by_text("Post", exact=True).first
                if post_btn.is_visible(timeout=2000):
                    logger.info("✓ Found Post button (text)")
                    post_btn.click()
                    break
            except:
                pass
            
            # Strategy 3: Find button with "Post" in text
            try:
                post_btn = page.locator('button:has-text("Post")').first
                if post_btn.is_visible(timeout=2000) and post_btn.is_enabled():
                    logger.info("✓ Found Post button (locator)")
                    post_btn.click()
                    break
            except:
                pass
            
            # Strategy 4: JavaScript click
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
                    logger.info("✓ Clicked Post button via JS")
                    break
            except:
                pass
            
            logger.warning(f"Post button not found (attempt {attempt + 1})")
            take_screenshot(page, f"no_post_btn_att_{attempt + 1}")
            time.sleep(2)
            
        except Exception as e:
            logger.error(f"Submit error (Attempt {attempt+1}): {e}")
            time.sleep(2)
    
    # Wait for modal to close (post submitted)
    try:
        logger.info("Waiting for post submission...")
        page.locator('div[role="dialog"]').first.wait_for(state='hidden', timeout=15000)
        logger.info("✓ Modal closed - Post successful")
        return True
    except:
        # Check if dialog is gone or we're back to feed
        try:
            if page.is_visible('div.ember-view.feed', timeout=3000):
                logger.info("✓ Back to feed - Post likely successful")
                return True
        except:
            pass
        
        logger.warning("Could not confirm post submission")
        return False

def open_linkedin_compose(page: Page) -> bool:
    """Open LinkedIn post compose modal."""
    logger.info("=" * 70)
    logger.info("OPENING LINKEDIN COMPOSE")
    logger.info("=" * 70)
    
    try:
        # Check if already on LinkedIn
        if "linkedin.com" not in page.url:
            logger.info("Navigating to LinkedIn...")
            page.goto("https://www.linkedin.com/feed/", wait_until="domcontentloaded", timeout=60000)
            time.sleep(3)
        
        # Check for login
        if "login" in page.url or "checkpoint" in page.url:
            logger.info("=" * 60)
            logger.info("MANUAL LOGIN REQUIRED")
            logger.info("=" * 60)
            logger.info("Please login to LinkedIn. Script will wait...")
            while "login" in page.url or "checkpoint" in page.url:
                time.sleep(2)
            logger.info("✓ Login detected!")
            time.sleep(3)
        
        # Check if modal is already open
        try:
            if page.locator('div[role="dialog"]').first.is_visible(timeout=2000):
                logger.info("✓ Modal already open")
                return wait_for_modal_ready(page)
        except:
            pass
        
        # Find and click "Start a post" button
        logger.info("Locating 'Start a post' button...")
        
        clicked = False
        
        # Try multiple selectors
        start_selectors = [
            'button:has-text("Start a post")',
            'div[role="button"]:has-text("Start a post")',
            'div.ember-view:has-text("Start a post")',
        ]
        
        for selector in start_selectors:
            try:
                btn = page.locator(selector).first
                if btn.is_visible(timeout=2000):
                    btn.click()
                    clicked = True
                    logger.info(f"✓ Clicked 'Start a post' ({selector})")
                    break
            except:
                continue
        
        if not clicked:
            # Try coordinate click as fallback
            logger.info("Trying coordinate click...")
            page.mouse.click(500, 200)
            clicked = True
        
        time.sleep(2)
        
        # Wait for modal
        return wait_for_modal_ready(page)
        
    except Exception as e:
        logger.error(f"Error opening compose: {e}")
        take_screenshot(page, "open_compose_error")
        return False

# =============================================================================
# MAIN EXECUTION
# =============================================================================

def post_to_linkedin(content: str) -> bool:
    """Main function to post to LinkedIn."""
    with sync_playwright() as p:
        browser = None
        context = None
        page = None
        
        try:
            # 1. Try connect existing (Gold method - Port 9222)
            logger.info("Connecting to Port 9222...")
            try:
                browser = p.chromium.connect_over_cdp("http://127.0.0.1:9222")
                logger.info("[OK] Connected to Port 9222")
                context = browser.contexts[0] if browser.contexts else None
                
                if context:
                    # Find LinkedIn page
                    for p_obj in context.pages:
                        if "linkedin.com" in p_obj.url:
                            page = p_obj
                            break
                    
                    if not page:
                        page = context.new_page()
                else:
                    page = context.new_page()
                    
            except Exception as e:
                logger.warning(f"Connection failed: {e}")
                # 2. Fallback to new browser
                logger.info("Launching NEW browser instance...")
                context = p.chromium.launch_persistent_context(
                    user_data_dir=str(SESSION_PATH),
                    headless=False,
                    channel="chrome",
                    args=[
                        "--disable-blink-features=AutomationControlled",
                        "--no-sandbox",
                        "--disable-gpu"
                    ]
                )
                browser = context.browser
                page = context.pages[0] if context.pages else context.new_page()
            
            # Bring page to front
            page.bring_to_front()
            logger.info(f"Using: {page.title()} ({page.url})")
            
            # Take initial screenshot
            take_screenshot(page, "initial_state")
            
            # Execute post flow
            if not open_linkedin_compose(page):
                logger.error("Failed to open compose modal")
                return False
            
            time.sleep(1)
            
            if not type_post_content(page, content):
                logger.error("Failed to type content")
                return False
            
            time.sleep(2)
            
            if not submit_post(page):
                logger.error("Failed to submit post")
                return False
            
            logger.info("=" * 70)
            logger.info("[OK] POST PUBLISHED!")
            logger.info("=" * 70)
            return True
            
        except Exception as e:
            logger.error(f"[FATAL] {e}")
            import traceback
            logger.error(traceback.format_exc())
            return False
        finally:
            if browser and browser.is_connected():
                try:
                    # Don't close browser - keep session alive
                    # browser.disconnect()
                    pass
                except:
                    pass

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--content", type=str, help="Content to post")
    args = parser.parse_args()
    
    if args.content:
        success = post_to_linkedin(args.content)
        sys.exit(0 if success else 1)
    else:
        print("Usage: python linkedin_auto_poster_improved.py --content 'Your post text'")
        sys.exit(1)

if __name__ == "__main__":
    main()
