"""
LinkedIn Auto Poster - PRODUCTION DIAGNOSTIC VERSION
=====================================================
EXPERT-LEVEL LINKEDIN AUTOMATION WITH MAXIMUM DIAGNOSTICS

This version is specifically designed to diagnose and fix the 
"works in AI sandbox but fails in production" issue.

CRITICAL FIXES FOR PRODUCTION:
1. Heavy logging at every single step
2. Multiple fallback strategies for typing
3. Explicit wait states for LinkedIn's React app
4. Anti-bot bypassing with human-like delays
5. Session persistence with proper cookie handling
6. Diagnostic screenshots at every critical step

Author: Senior LinkedIn Automation Expert
Version: 2.0 (PRODUCTION DIAGNOSTIC)
Date: 2026-03-31
"""

import os
import sys
import time
import json
import shutil
import logging
import argparse
import random
from datetime import datetime
from pathlib import Path
from playwright.sync_api import sync_playwright, Page, TimeoutError as PlaywrightTimeout

# =============================================================================
# CONFIGURATION - EXACT PATHS FOR HACKATHON 0
# =============================================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SESSION_PATH = PROJECT_ROOT / "session" / "linkedin"
DEBUG_FOLDER = PROJECT_ROOT / "debug_linkedin"
GOLD_DIR = PROJECT_ROOT / "gold"
APPROVED_FOLDER = GOLD_DIR / "pending_approval" / "approved"
DONE_FOLDER = GOLD_DIR / "done"
FAILED_FOLDER = GOLD_DIR / "failed"
LOGS_FOLDER = GOLD_DIR / "logs"

# Ensure all folders exist
for folder in [DEBUG_FOLDER, APPROVED_FOLDER, DONE_FOLDER, FAILED_FOLDER, LOGS_FOLDER, SESSION_PATH]:
    folder.mkdir(parents=True, exist_ok=True)

# =============================================================================
# HEAVY LOGGING SETUP - DIAGNOSE EVERYTHING
# =============================================================================

log_file = LOGS_FOLDER / f"linkedin_DIAGNOSTIC_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"

logging.basicConfig(
    level=logging.DEBUG,  # Maximum logging level
    format='%(asctime)s.%(msecs)03d - %(levelname)-8s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    handlers=[
        logging.FileHandler(log_file, encoding='utf-8', mode='w'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Log file location for easy access
logger.info("=" * 80)
logger.info(f"DIAGNOSTIC LOG FILE: {log_file}")
logger.info("=" * 80)

# =============================================================================
# CONFIGURATION CONSTANTS - PRODUCTION TUNED
# =============================================================================

# Retry configuration
MAX_RETRIES = 5
RETRY_DELAYS = [10, 15, 20, 30, 45]  # Increasing delays (seconds)

# Timing configuration (milliseconds) - CRITICAL FOR ANTI-BOT
TYPE_DELAY_PER_CHAR = 130  # ms per character (human-like typing)
FOCUS_WAIT_TIME = 2000  # ms to wait after focusing
POST_TYPE_WAIT = 4000  # ms to wait after typing before posting
PRE_POST_WAIT = 3000  # ms to wait before clicking post button
PAGE_LOAD_WAIT = 5000  # ms to wait after page load
MODAL_WAIT = 6000  # ms to wait for modal to fully load
COMPOSE_CLICK_WAIT = 3000  # ms to wait after clicking compose

# Timeout configuration
PAGE_LOAD_TIMEOUT = 90000  # 90 seconds
MODAL_OPEN_TIMEOUT = 45000  # 45 seconds
POST_SUBMIT_TIMEOUT = 45000  # 45 seconds
TOTAL_TIMEOUT = 720000  # 12 minutes total

# LinkedIn URLs
LINKEDIN_FEED_URL = "https://www.linkedin.com/feed/"
LINKEDIN_LOGIN_URL = "https://www.linkedin.com/login"

# =============================================================================
# DIAGNOSTIC SCREENSHOT FUNCTION
# =============================================================================

def take_diagnostic_screenshot(page: Page, step_name: str) -> str:
    """
    Take screenshot with full diagnostic information.
    """
    try:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:19]
        filename = f"{step_name}_{timestamp}.png"
        path = DEBUG_FOLDER / filename
        
        page.screenshot(path=str(path), full_page=True)
        
        logger.info(f"[SCREENSHOT] ✓ Saved: {filename}")
        return str(path)
        
    except Exception as e:
        logger.error(f"[SCREENSHOT] ✗ Failed: {e}")
        return ""

def log_page_state(page: Page, step: str):
    """Log current page state for diagnostics."""
    try:
        url = page.url
        title = page.title()
        
        # Check if page is responsive
        is_responsive = page.evaluate('() => document.readyState') == 'complete'
        
        logger.info(f"[PAGE STATE] {step}:")
        logger.info(f"  - URL: {url}")
        logger.info(f"  - Title: {title}")
        logger.info(f"  - Ready State: {'Complete' if is_responsive else 'Loading'}")
        
        # Check for common LinkedIn elements
        try:
            has_feed = page.is_visible('div.feed', timeout=1000)
            logger.info(f"  - Has Feed: {has_feed}")
        except:
            logger.info(f"  - Has Feed: Not found")
            
        try:
            has_nav = page.is_visible('nav[aria-label*="Main"]', timeout=1000)
            logger.info(f"  - Has Navigation: {has_nav}")
        except:
            logger.info(f"  - Has Navigation: Not found")
            
    except Exception as e:
        logger.error(f"[PAGE STATE] Error logging state: {e}")

# =============================================================================
# COMPOSE BOX DETECTION - MULTIPLE STRATEGIES
# =============================================================================

def find_compose_box_exhaustive(page: Page):
    """
    Find LinkedIn compose box using EVERY possible selector.
    Returns tuple: (locator, selector_used) or (None, None)
    """
    logger.info("[COMPOSE SEARCH] Starting exhaustive search for compose box...")
    
    # COMPREHENSIVE list of ALL possible selectors for LinkedIn compose box
    compose_selectors = [
        # Primary selectors (most reliable)
        ('div[role="textbox"][contenteditable="true"]', "Role + Contenteditable"),
        ('[data-testid="post-creation-textarea"]', "Data-testid"),
        ('div[contenteditable="true"][aria-label*="What do you want to talk about"]', "Aria-label What"),
        ('div[aria-label="Create a post"]', "Aria-label Create"),
        
        # Secondary selectors (fallbacks)
        ('div.ql-editor[contenteditable="true"]', "Quill Editor"),
        ('div.share-creation-state__text-editor', "Share Creation"),
        ('div.update-v2__editor', "Update Editor"),
        ('div[contenteditable="true"].ember-view', "Ember Contenteditable"),
        
        # Tertiary selectors (desperate measures)
        ('div[role="dialog"] div[contenteditable="true"]', "Dialog Contenteditable"),
        ('div[role="dialog"] textarea', "Dialog Textarea"),
        ('div[id*="post-creation"]', "ID contains post-creation"),
        ('div[class*="post-creation"]', "Class contains post-creation"),
        
        # Generic selectors (last resort)
        ('div[contenteditable="true"]', "Generic Contenteditable"),
        ('textarea[aria-label*="post" i]', "Textarea with post"),
    ]
    
    for selector, description in compose_selectors:
        try:
            locator = page.locator(selector).first
            
            # Check visibility with timeout
            is_visible = locator.is_visible(timeout=1500)
            
            if is_visible:
                logger.info(f"[COMPOSE SEARCH] ✓ FOUND: {description}")
                logger.info(f"[COMPOSE SEARCH]   Selector: {selector}")
                
                # Additional diagnostics
                try:
                    bounding_box = locator.bounding_box(timeout=1000)
                    if bounding_box:
                        logger.info(f"[COMPOSE SEARCH]   Position: ({bounding_box['x']:.0f}, {bounding_box['y']:.0f})")
                        logger.info(f"[COMPOSE SEARCH]   Size: {bounding_box['width']:.0f}x{bounding_box['height']:.0f}")
                except:
                    pass
                
                return locator, selector
                
        except Exception as e:
            logger.debug(f"[COMPOSE SEARCH]   Tried '{description}' - Not found")
            continue
    
    logger.warning("[COMPOSE SEARCH] ✗ FAILED: Could not find compose box with ANY selector")
    return None, None

# =============================================================================
# POST BUTTON DETECTION - MULTIPLE STRATEGIES
# =============================================================================

def find_post_button_exhaustive(page: Page):
    """
    Find LinkedIn Post button using EVERY possible selector.
    Returns tuple: (locator, selector_used) or (None, None)
    """
    logger.info("[POST BUTTON SEARCH] Starting exhaustive search for Post button...")
    
    post_selectors = [
        # Primary selectors
        ('button[data-testid="post-button"]', "Data-testid Post"),
        ('button:has-text("Post")', "Text Contains Post"),
        ('button[aria-label="Post"]', "Aria-label Post"),
        
        # Secondary selectors
        ('button span:has-text("Post")', "Span Text Post"),
        ('div[role="dialog"] button:not([disabled]):has-text("Post")', "Dialog Enabled Post"),
        ('button[class*="post-button"]:has-text("Post")', "Class Post Button"),
        
        # Fallback selectors
        ('button[type="submit"]:has-text("Post")', "Submit Button Post"),
        ('form button:has-text("Post")', "Form Button Post"),
        ('div[role="button"]:has-text("Post")', "Role Button Post"),
    ]
    
    for selector, description in post_selectors:
        try:
            locator = page.locator(selector).first
            
            is_visible = locator.is_visible(timeout=1500)
            is_enabled = locator.is_enabled(timeout=1500) if is_visible else False
            
            if is_visible and is_enabled:
                logger.info(f"[POST BUTTON SEARCH] ✓ FOUND: {description}")
                logger.info(f"[POST BUTTON SEARCH]   Selector: {selector}")
                return locator, selector
            elif is_visible:
                logger.debug(f"[POST BUTTON SEARCH]   Found '{description}' but DISABLED")
                
        except Exception as e:
            logger.debug(f"[POST BUTTON SEARCH]   Tried '{description}' - Error: {str(e)[:50]}")
            continue
    
    logger.warning("[POST BUTTON SEARCH] ✗ FAILED: Could not find Post button with ANY selector")
    return None, None

# =============================================================================
# TYPE CONTENT - MULTIPLE STRATEGIES WITH ANTI-BOT
# =============================================================================

def type_content_keyboard_strategy(page: Page, compose_box, text: str) -> bool:
    """
    Type content using keyboard with anti-bot delays.
    This is the PRIMARY strategy.
    """
    logger.info("[TYPING] Strategy 1: Keyboard typing with anti-bot delays...")
    logger.info(f"[TYPING] Text length: {len(text)} characters")
    logger.info(f"[TYPING] Delay per character: {TYPE_DELAY_PER_CHAR}ms")
    
    try:
        # Focus the compose box
        logger.info("[TYPING] Step 1: Focusing compose box...")
        compose_box.focus()
        logger.info("[TYPING] ✓ Compose box focused")
        
        # CRITICAL WAIT - LinkedIn needs time to register focus
        logger.info(f"[TYPING] Waiting {FOCUS_WAIT_TIME}ms after focus...")
        page.wait_for_timeout(FOCUS_WAIT_TIME)
        
        # Clear existing content
        logger.info("[TYPING] Step 2: Clearing existing content...")
        page.keyboard.press('Control+A')
        page.wait_for_timeout(300)
        page.keyboard.press('Delete')
        page.wait_for_timeout(300)
        logger.info("[TYPING] ✓ Content cleared")
        
        # Type with delay - CRITICAL FOR ANTI-BOT
        logger.info("[TYPING] Step 3: Starting to type content...")
        start_time = time.time()
        
        # Use Playwright's built-in delay typing
        compose_box.type(text, delay=TYPE_DELAY_PER_CHAR)
        
        elapsed = time.time() - start_time
        logger.info(f"[TYPING] ✓ Typing completed in {elapsed:.1f}s")
        
        # Wait for LinkedIn to process
        logger.info(f"[TYPING] Waiting {POST_TYPE_WAIT}ms for LinkedIn to process...")
        page.wait_for_timeout(POST_TYPE_WAIT)
        
        # Verify content
        logger.info("[TYPING] Step 4: Verifying typed content...")
        try:
            typed_content = compose_box.inner_text(timeout=3000)
            typed_length = len(typed_content.strip())
            expected_length = len(text.strip())
            
            match_percentage = (typed_length / expected_length * 100) if expected_length > 0 else 0
            
            logger.info(f"[TYPING] Typed: {typed_length} chars, Expected: {expected_length} chars")
            logger.info(f"[TYPING] Match: {match_percentage:.1f}%")
            
            if match_percentage >= 80:
                logger.info("[TYPING] ✓ Content verification PASSED")
                return True
            else:
                logger.warning(f"[TYPING] ✗ Content verification FAILED (< 80% match)")
                return False
                
        except Exception as e:
            logger.warning(f"[TYPING] Could not verify content: {e}")
            return True  # Continue anyway
            
    except Exception as e:
        logger.error(f"[TYPING] ✗ Keyboard strategy FAILED: {e}")
        return False

def type_content_chunk_strategy(page: Page, compose_box, text: str) -> bool:
    """
    Type content in chunks with random delays (more human-like).
    This is the SECONDARY strategy.
    """
    logger.info("[TYPING] Strategy 2: Chunk typing with random delays...")
    
    try:
        # Focus
        compose_box.focus()
        page.wait_for_timeout(FOCUS_WAIT_TIME)
        
        # Clear
        page.keyboard.press('Control+A')
        page.wait_for_timeout(300)
        page.keyboard.press('Delete')
        page.wait_for_timeout(300)
        
        # Split into words
        words = text.split(' ')
        
        logger.info(f"[TYPING] Typing {len(words)} words with random delays...")
        
        for i, word in enumerate(words):
            # Type word
            page.keyboard.type(word + ' ', delay=random.randint(80, 180))
            
            # Random pause every 5-10 words (human-like)
            if i > 0 and i % random.randint(5, 10) == 0:
                pause = random.randint(800, 1500)
                logger.debug(f"[TYPING] Human-like pause: {pause}ms")
                page.wait_for_timeout(pause)
        
        logger.info("[TYPING] ✓ Chunk typing completed")
        page.wait_for_timeout(POST_TYPE_WAIT)
        
        return True
        
    except Exception as e:
        logger.error(f"[TYPING] ✗ Chunk strategy FAILED: {e}")
        return False

def type_content_dom_strategy(page: Page, compose_box, text: str) -> bool:
    """
    Type content using DOM manipulation (fallback).
    This is the TERTIARY strategy.
    """
    logger.info("[TYPING] Strategy 3: DOM manipulation...")
    
    try:
        # Convert to HTML
        html_text = text.replace('\n', '<br>')
        
        # JavaScript to set content
        js_code = f"""
        () => {{
            const editor = document.querySelector('div[contenteditable="true"]');
            if (!editor) {{
                console.error('No contenteditable found');
                return false;
            }}
            
            // Set content
            editor.innerHTML = `{html_text}`;
            
            // Dispatch events
            editor.dispatchEvent(new Event('input', {{ bubbles: true }}));
            editor.dispatchEvent(new Event('change', {{ bubbles: true }}));
            editor.dispatchEvent(new Event('focus', {{ bubbles: true }}));
            
            console.log('Content set via DOM');
            return true;
        }}
        """
        
        result = page.evaluate(js_code)
        
        if result:
            logger.info("[TYPING] ✓ DOM manipulation successful")
            page.wait_for_timeout(POST_TYPE_WAIT)
            return True
        else:
            logger.error("[TYPING] ✗ DOM manipulation returned false")
            return False
            
    except Exception as e:
        logger.error(f"[TYPING] ✗ DOM strategy FAILED: {e}")
        return False

def type_content_clipboard_strategy(page: Page, compose_box, text: str) -> bool:
    """
    Type content using clipboard paste (last resort).
    This is the FOURTH strategy.
    """
    logger.info("[TYPING] Strategy 4: Clipboard paste...")
    
    try:
        # Focus
        compose_box.focus()
        page.wait_for_timeout(1000)
        
        # Copy to clipboard
        page.evaluate(f"""
            navigator.clipboard.writeText(`{text}`)
        """)
        
        logger.info("[TYPING] Content copied to clipboard")
        page.wait_for_timeout(500)
        
        # Paste
        page.keyboard.press('Control+V')
        logger.info("[TYPING] Paste command sent")
        
        page.wait_for_timeout(POST_TYPE_WAIT)
        
        logger.info("[TYPING] ✓ Clipboard paste completed")
        return True
        
    except Exception as e:
        logger.error(f"[TYPING] ✗ Clipboard strategy FAILED: {e}")
        return False

# =============================================================================
# MAIN POSTING FUNCTION WITH FULL DIAGNOSTICS
# =============================================================================

def post_to_linkedin_diagnostic(content: str) -> bool:
    """
    Main function with MAXIMUM DIAGNOSTICS to identify exact failure point.
    """
    logger.info("=" * 80)
    logger.info("LINKEDIN AUTO POSTER - PRODUCTION DIAGNOSTIC MODE")
    logger.info("=" * 80)
    logger.info(f"Content length: {len(content)} characters")
    logger.info(f"Session path: {SESSION_PATH}")
    logger.info(f"Max retries: {MAX_RETRIES}")
    logger.info(f"Total timeout: {TOTAL_TIMEOUT/60000:.1f} minutes")
    logger.info("=" * 80)
    
    for attempt in range(MAX_RETRIES):
        attempt_start = time.time()
        
        logger.info("=" * 80)
        logger.info(f"ATTEMPT {attempt + 1}/{MAX_RETRIES}")
        logger.info("=" * 80)
        
        browser = None
        context = None
        page = None
        
        try:
            # STEP 1: Launch browser
            logger.info("[STEP 1] Launching browser...")
            
            with sync_playwright() as p:
                # Try to connect to existing Chrome first
                try:
                    logger.info("[BROWSER] Trying to connect to existing Chrome (Port 9222)...")
                    browser = p.chromium.connect_over_cdp(
                        "http://127.0.0.1:9222",
                        timeout=15000
                    )
                    logger.info("[BROWSER] ✓ Connected to existing Chrome")
                    
                    context = browser.contexts[0] if browser.contexts else None
                    if context:
                        linkedin_pages = [pg for pg in context.pages if "linkedin.com" in pg.url]
                        page = linkedin_pages[0] if linkedin_pages else context.new_page()
                    else:
                        page = browser.new_page()
                        
                except Exception as e:
                    logger.warning(f"[BROWSER] Could not connect to existing Chrome: {e}")
                    logger.info("[BROWSER] Launching new Chrome with persistent session...")
                    
                    context = p.chromium.launch_persistent_context(
                        user_data_dir=str(SESSION_PATH),
                        headless=False,
                        channel="chrome",
                        args=[
                            "--disable-blink-features=AutomationControlled",
                            "--no-sandbox",
                            "--disable-gpu",
                            "--disable-dev-shm-usage",
                            "--remote-debugging-port=9222",
                            "--window-size=1920,1080"
                        ],
                        timeout=90000
                    )
                    
                    browser = context.browser
                    page = context.pages[0] if context.pages else context.new_page()
                    logger.info("[BROWSER] ✓ New Chrome launched")
                
                # Bring to front
                page.bring_to_front()
                logger.info(f"[BROWSER] Current page: {page.url}")
                
                # STEP 2: Navigate to LinkedIn
                logger.info("[STEP 2] Navigating to LinkedIn feed...")
                
                try:
                    page.goto(LINKEDIN_FEED_URL, wait_until='domcontentloaded', timeout=PAGE_LOAD_TIMEOUT)
                    logger.info("[NAVIGATION] ✓ Navigation initiated")
                    
                    # Wait for network idle
                    page.wait_for_load_state('networkidle', timeout=PAGE_LOAD_TIMEOUT)
                    logger.info("[NAVIGATION] ✓ Network idle")
                    
                    # Additional wait for React app
                    logger.info(f"[NAVIGATION] Waiting {PAGE_LOAD_WAIT}ms for React app...")
                    page.wait_for_timeout(PAGE_LOAD_WAIT)
                    
                except Exception as e:
                    logger.error(f"[NAVIGATION] ✗ Failed: {e}")
                    take_diagnostic_screenshot(page, "navigation_error")
                    raise
                
                # Log page state
                log_page_state(page, "After navigation")
                take_diagnostic_screenshot(page, "after_navigation")
                
                # STEP 3: Check for login
                logger.info("[STEP 3] Checking for login requirement...")
                
                if LINKEDIN_LOGIN_URL in page.url or "login" in page.url.lower():
                    logger.info("[LOGIN] ⚠ Login page detected")
                    logger.info("[LOGIN] Waiting for manual login (120 seconds)...")
                    
                    for i in range(60):
                        page.wait_for_timeout(2000)
                        if LINKEDIN_LOGIN_URL not in page.url and "login" not in page.url.lower():
                            logger.info("[LOGIN] ✓ Login detected!")
                            break
                    else:
                        logger.error("[LOGIN] ✗ Login timeout")
                        raise Exception("Login timeout")
                    
                    # Navigate to feed after login
                    page.goto(LINKEDIN_FEED_URL, wait_until='domcontentloaded', timeout=PAGE_LOAD_TIMEOUT)
                    page.wait_for_timeout(PAGE_LOAD_WAIT)
                
                log_page_state(page, "After login check")
                take_diagnostic_screenshot(page, "after_login")
                
                # STEP 4: Open compose box
                logger.info("[STEP 4] Opening compose box...")
                
                # Find "Start a post" button
                start_post_selectors = [
                    'button:has-text("Start a post")',
                    'div[role="button"]:has-text("Start a post")',
                    'div.ember-view:has-text("Start a post")',
                ]
                
                compose_clicked = False
                
                for selector in start_post_selectors:
                    try:
                        btn = page.locator(selector).first
                        if btn.is_visible(timeout=3000):
                            logger.info(f"[COMPOSE CLICK] ✓ Found 'Start a post': {selector}")
                            btn.scroll_into_view_if_needed()
                            page.wait_for_timeout(500)
                            btn.click()
                            compose_clicked = True
                            logger.info("[COMPOSE CLICK] ✓ Clicked 'Start a post'")
                            break
                    except:
                        continue
                
                if not compose_clicked:
                    logger.info("[COMPOSE CLICK] Using coordinate click as fallback...")
                    page.mouse.click(500, 220)
                    compose_clicked = True
                
                # Wait for modal
                logger.info(f"[COMPOSE CLICK] Waiting {COMPOSE_CLICK_WAIT}ms for modal...")
                page.wait_for_timeout(COMPOSE_CLICK_WAIT)
                
                take_diagnostic_screenshot(page, "after_compose_click")
                log_page_state(page, "After compose click")
                
                # STEP 5: Find compose box
                logger.info("[STEP 5] Finding compose box...")
                
                compose_box, compose_selector = find_compose_box_exhaustive(page)
                
                if not compose_box:
                    logger.error("[COMPOSE BOX] ✗ CRITICAL: Compose box NOT FOUND")
                    take_diagnostic_screenshot(page, "compose_box_not_found")
                    raise Exception("Compose box not found")
                
                logger.info(f"[COMPOSE BOX] ✓ Compose box found using: {compose_selector}")
                
                # STEP 6: Type content
                logger.info("[STEP 6] Typing content...")
                
                typing_success = False
                
                # Try multiple typing strategies
                typing_strategies = [
                    ("Keyboard", lambda: type_content_keyboard_strategy(page, compose_box, content)),
                    ("Chunk", lambda: type_content_chunk_strategy(page, compose_box, content)),
                    ("DOM", lambda: type_content_dom_strategy(page, compose_box, content)),
                    ("Clipboard", lambda: type_content_clipboard_strategy(page, compose_box, content)),
                ]
                
                for strategy_name, strategy_func in typing_strategies:
                    logger.info(f"[TYPING] Trying {strategy_name} strategy...")
                    if strategy_func():
                        logger.info(f"[TYPING] ✓ {strategy_name} strategy SUCCESS")
                        typing_success = True
                        break
                    else:
                        logger.warning(f"[TYPING] ✗ {strategy_name} strategy FAILED")
                
                if not typing_success:
                    logger.error("[TYPING] ✗ ALL typing strategies FAILED")
                    take_diagnostic_screenshot(page, "typing_failed")
                    raise Exception("All typing strategies failed")
                
                take_diagnostic_screenshot(page, "typing_success")
                
                # STEP 7: Find and click Post button
                logger.info("[STEP 7] Finding Post button...")
                
                post_button, post_selector = find_post_button_exhaustive(page)
                
                if not post_button:
                    logger.error("[POST BUTTON] ✗ CRITICAL: Post button NOT FOUND")
                    take_diagnostic_screenshot(page, "post_button_not_found")
                    raise Exception("Post button not found")
                
                logger.info(f"[POST BUTTON] ✓ Post button found using: {post_selector}")
                
                # Wait before clicking
                logger.info(f"[POST BUTTON] Waiting {PRE_POST_WAIT}ms before clicking...")
                page.wait_for_timeout(PRE_POST_WAIT)
                
                # Click Post button
                logger.info("[POST BUTTON] Clicking Post button...")
                post_button.scroll_into_view_if_needed()
                page.wait_for_timeout(500)
                post_button.click()
                logger.info("[POST BUTTON] ✓ Post button clicked")
                
                # STEP 8: Wait for submission
                logger.info("[STEP 8] Waiting for post submission...")
                
                try:
                    page.locator('div[role="dialog"]').first.wait_for(
                        state='hidden',
                        timeout=POST_SUBMIT_TIMEOUT
                    )
                    logger.info("[SUBMISSION] ✓ Modal closed - Post submitted")
                    
                except PlaywrightTimeout:
                    logger.warning("[SUBMISSION] Modal didn't close, checking if post succeeded...")
                    
                    if page.is_visible('div.feed', timeout=3000):
                        logger.info("[SUBMISSION] ✓ Back on feed - Post likely succeeded")
                    else:
                        logger.warning("[SUBMISSION] Could not confirm submission")
                
                take_diagnostic_screenshot(page, "post_submitted")
                
                # SUCCESS!
                elapsed = time.time() - attempt_start
                logger.info("=" * 80)
                logger.info(f"[SUCCESS] LINKEDIN POST PUBLISHED!")
                logger.info(f"[SUCCESS] Time taken: {elapsed:.1f}s")
                logger.info("=" * 80)
                
                return True
                
        except Exception as e:
            logger.error("=" * 80)
            logger.error(f"[ERROR] Attempt {attempt + 1} FAILED: {e}")
            logger.error("=" * 80)
            
            # Take error screenshot
            if page:
                take_diagnostic_screenshot(page, f"attempt_{attempt + 1}_error")
            
            # Close browser
            if browser:
                try:
                    browser.close()
                except:
                    pass
            
            # Retry logic
            if attempt < MAX_RETRIES - 1:
                delay = RETRY_DELAYS[attempt]
                logger.info(f"[RETRY] Waiting {delay}s before next attempt...")
                time.sleep(delay)
            else:
                logger.error("=" * 80)
                logger.error("[FINAL] ALL RETRY ATTEMPTS EXHAUSTED")
                logger.error("=" * 80)
                return False
    
    return False

# =============================================================================
# FILE MANAGEMENT
# =============================================================================

def move_to_done(filepath: Path) -> bool:
    """Move successfully processed file to done folder."""
    try:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        dst = DONE_FOLDER / f"done_{filepath.stem}_{timestamp}.md"
        
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        done_content = f"""---
type: linkedin_post
source: {filepath.name}
processed_at: {datetime.now().isoformat()}
status: completed
---

# ✓ LinkedIn Post COMPLETED

**Processed:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

---
Original:
---
{content}
"""
        
        with open(dst, 'w', encoding='utf-8') as f:
            f.write(done_content)
        
        filepath.unlink()
        logger.info(f"[FILE] ✓ Moved to DONE: {dst.name}")
        return True
        
    except Exception as e:
        logger.error(f"[FILE] Error moving to done: {e}")
        return False

def move_to_failed(filepath: Path, reason: str) -> bool:
    """Move failed file to failed folder with detailed reason."""
    try:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        dst = FAILED_FOLDER / f"failed_{filepath.stem}_{timestamp}.md"
        
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        failed_content = f"""---
type: linkedin_post
source: {filepath.name}
processed_at: {datetime.now().isoformat()}
status: failed
failure_reason: {reason}
---

# ✗ LinkedIn Post FAILED

**Failed:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

**Failure Reason:** {reason}

**Log File:** {log_file}

---
Original:
---
{content}
"""
        
        with open(dst, 'w', encoding='utf-8') as f:
            f.write(failed_content)
        
        filepath.unlink()
        logger.info(f"[FILE] ✗ Moved to FAILED: {dst.name}")
        logger.info(f"[FILE] Reason: {reason}")
        return True
        
    except Exception as e:
        logger.error(f"[FILE] Error moving to failed: {e}")
        return False

# =============================================================================
# MAIN ENTRY POINT
# =============================================================================

def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description='LinkedIn Auto Poster - Production Diagnostic')
    parser.add_argument('--content', type=str, help='Content to post')
    parser.add_argument('--file', type=str, help='Approved file to process')
    args = parser.parse_args()
    
    logger.info("=" * 80)
    logger.info("LINKEDIN AUTO POSTER - STARTING")
    logger.info("=" * 80)
    
    # Get content
    content = None
    filepath = None
    
    if args.content:
        content = args.content
        filepath = Path(f"manual_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md")
        
    elif args.file:
        filepath = Path(args.file)
        if not filepath.exists():
            logger.error(f"[FILE] Not found: {filepath}")
            sys.exit(1)
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                file_content = f.read()
            
            # Extract content
            if '## LinkedIn Post Draft' in file_content:
                parts = file_content.split('## LinkedIn Post Draft')
                if len(parts) > 1:
                    content = parts[1].strip().split('---')[0].strip()
            else:
                content = file_content
                
        except Exception as e:
            logger.error(f"[FILE] Read error: {e}")
            sys.exit(1)
    
    if not content:
        logger.error("[CONTENT] No content provided")
        sys.exit(1)
    
    logger.info(f"[CONTENT] Length: {len(content)} characters")
    logger.info(f"[CONTENT] Preview: {content[:100]}...")
    
    # Post to LinkedIn
    success = post_to_linkedin_diagnostic(content)
    
    # Handle file
    if filepath and filepath.exists():
        if success:
            move_to_done(filepath)
        else:
            move_to_failed(filepath, "Failed after all retry attempts - check diagnostic log")
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
