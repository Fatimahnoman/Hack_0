"""
Unified LinkedIn Poster & Watcher - Gold Tier
=============================================
Combines Monitoring (Eyes) and Posting (Hands) into one robust script.
Prevents session conflicts by managing a single browser instance.

FEATURES:
✓ Integrated Watcher (--watch) for sales leads
✓ Robust Auto-Poster (--content or --file)
✓ Stable Selectors (LinkedIn 2026 Compatible)
✓ Automatic Overlay Handling (Post Settings, etc.)
✓ Shadow DOM and Iframe Piercing
✓ natural human-like typing
✓ Comprehensive Screenshot Debugging

USAGE:
  1. Watcher mode: python gold/watchers/unified_linkedin_poster.py --watch
  2. Post mode:    python gold/watchers/unified_linkedin_poster.py --content "Hello!"
"""

import os
import re
import sys
import time
import shutil
import logging
import argparse
import random
from datetime import datetime
from pathlib import Path
from playwright.sync_api import sync_playwright, Page, TimeoutError as PlaywrightTimeout

# =============================================================================
# CONFIGURATION - GOLD TIER PATHS
# =============================================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
GOLD_DIR = PROJECT_ROOT / "gold"
SESSION_PATH = PROJECT_ROOT / "session" / "linkedin"
DEBUG_FOLDER = PROJECT_ROOT / "debug_linkedin"
LOG_DIR = GOLD_DIR / "logs"
NEEDS_ACTION = GOLD_DIR / "needs_action"

# Ensure all folders exist
for folder in [SESSION_PATH, DEBUG_FOLDER, LOG_DIR, NEEDS_ACTION]:
    folder.mkdir(parents=True, exist_ok=True)

# Setup Logging
log_file = LOG_DIR / f"linkedin_unified_{datetime.now().strftime('%Y%m%d')}.log"
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file, encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("LinkedInUnified")

# Settings
LINKEDIN_URL = "https://www.linkedin.com/feed/"
CHECK_INTERVAL = 60  # seconds for lead scanning
TYPE_DELAY = 120    # ms per character for natural typing
MAX_RETRIES = 3

# Lead Detection Keywords
SALES_KEYWORDS = [
    "looking for", "need", "require", "seeking", "hire",
    "developer", "service", "help", "project", "budget",
    "urgent", "asap", "recommend", "suggestion"
]

# Track processed items
processed_ids = set()

# =============================================================================
# BROWSER UTILITIES
# =============================================================================

def take_debug_screenshot(page: Page, name: str):
    """Save a timestamped screenshot for debugging."""
    try:
        ts = datetime.now().strftime("%H%M%S")
        filepath = DEBUG_FOLDER / f"{name}_{ts}.png"
        page.screenshot(path=str(filepath), full_page=False)
        logger.info(f"[SCREENSHOT] Saved: {filepath.name}")
    except Exception as e:
        logger.warning(f"Screenshot failed: {e}")

def get_browser_context(p, session_path: Path):
    """Connect to existing Chrome on Port 9222 or launch new."""
    try:
        # Attempt connection to existing instance (watcher)
        logger.info("Connecting to Port 9222...")
        browser = p.chromium.connect_over_cdp("http://127.0.0.1:9222", timeout=5000)
        logger.info("✓ Connected to existing browser instance")
        return browser, browser.contexts[0]
    except Exception:
        logger.info("Launching NEW persistent browser instance...")
        # Clean locks if any
        lock_file = session_path / "SingletonLock"
        if lock_file.exists():
            try: lock_file.unlink()
            except: pass
            
        context = p.chromium.launch_persistent_context(
            user_data_dir=str(session_path),
            headless=False,
            channel="chrome",
            args=[
                "--disable-gpu",
                "--no-sandbox",
                "--window-size=1280,720",
                "--remote-debugging-port=9222",
                "--disable-blink-features=AutomationControlled"
            ],
            timeout=60000
        )
        return context.browser, context

# =============================================================================
# UI INTERACTION (HANDS)
# =============================================================================

def handle_overlays(page: Page):
    """Detect and close common LinkedIn popups/overlays."""
    try:
        # 1. "Post settings" overlay
        # We use a more specific selector to avoid strict mode violations
        done_btn = page.locator('button.share-box-footer__primary-btn:has-text("Done")').first
        if done_btn.is_visible(timeout=2000):
            logger.info("Overlay detected: 'Post settings'. Clicking Done...")
            if not done_btn.is_enabled():
                # Sometimes 'Done' is disabled until a selector is clicked
                anyone_btn = page.locator('button:has-text("Anyone")').first
                if anyone_btn.is_visible(): anyone_btn.click()
                time.sleep(1)
            done_btn.click()
            time.sleep(1)
            
        # 2. "Got it" / Cookie banners
        got_it = page.locator('button:has-text("Got it")').first
        if got_it.is_visible(timeout=1000):
            got_it.click()
            
    except Exception as e:
        logger.debug(f"Overlay check error: {e}")

def open_compose_modal(page: Page) -> bool:
    """Clicks 'Start a post' and waits for modal."""
    logger.info("Opening LinkedIn compose modal...")
    take_debug_screenshot(page, "before_start_post")
    
    # Selectors for 'Start a post' button
    start_selectors = [
        'button:has-text("Start a post")',
        'div[role="button"]:has-text("Start a post")',
        '.share-box-feed-entry__trigger',
        'button.artdeco-button--tertiary:has-text("Start a post")',
        'span:has-text("Start a post")'
    ]
    
    for attempt in range(2):
        handle_overlays(page)
        for selector in start_selectors:
            try:
                # Find all matching elements and try the first visible one
                locators = page.locator(selector)
                count = locators.count()
                for i in range(count):
                    btn = locators.nth(i)
                    if btn.is_visible(timeout=2000):
                        logger.info(f"✓ Found visible button with '{selector}'. Clicking...")
                        btn.click()
                        time.sleep(3)
                        break
                else: continue
                break
            except: continue
        else:
            # Try coordinate click if all fail
            logger.info("Coordinate click (fallback) on top-center post area...")
            page.mouse.click(500, 200)
            time.sleep(3)
            
        # Verify modal - use broader selectors
        modal_selectors = [
            'div[role="dialog"]',
            '.share-creation-state',
            '.artdeco-modal',
            'div[aria-labelledby*="share-to-linkedin"]'
        ]
        
        for m_sel in modal_selectors:
            if page.locator(m_sel).first.is_visible(timeout=3000):
                logger.info(f"✓ Compose modal opened (detected by {m_sel})")
                take_debug_screenshot(page, "modal_opened")
                return True
            
        logger.warning(f"Modal not found yet, checking handle_overlays... (Attempt {attempt+1})")
        take_debug_screenshot(page, f"modal_not_found_att_{attempt+1}")
        handle_overlays(page)
        
    return False

def find_editor(page: Page):
    """Finds the contenteditable editor element."""
    selectors = [
        'div[contenteditable="true"][role="textbox"]',
        'div.ql-editor[contenteditable="true"]',
        '[data-testid="post-creation-textarea"]',
        'div[aria-label*="talk about"]'
    ]
    for sel in selectors:
        try:
            elem = page.locator(sel).first
            if elem.is_visible(timeout=2000):
                return elem
        except: continue
    return None

def post_content(page: Page, content: str) -> bool:
    """Types content and clicks Post."""
    try:
        # Close any blocking overlays first
        handle_overlays(page)
        
        editor = find_editor(page)
        if not editor:
            logger.error("Could not locate editor element")
            take_debug_screenshot(page, "error_no_editor")
            return False
            
        logger.info("Focusing and typing...")
        editor.focus()
        time.sleep(1)
        
        # Clear existing
        page.keyboard.press("Control+A")
        page.keyboard.press("Backspace")
        
        # Type naturally
        page.keyboard.type(content, delay=TYPE_DELAY)
        time.sleep(2)
        
        # Click Post - use multiple strategies
        post_btn = None
        
        # Strategy 1: Role-based (Most robust)
        try:
            btn = page.get_by_role("button", name=re.compile(r"^Post$", re.IGNORECASE)).first
            if btn.is_visible(timeout=3000) and btn.is_enabled():
                post_btn = btn
                logger.info("✓ Found Post button via get_by_role")
        except: pass
        
        # Strategy 2: Scoped selectors
        if not post_btn:
            dialog = page.locator('div[role="dialog"], .share-creation-state, .artdeco-modal').first
            post_btn_selectors = [
                'button.share-actions__primary-action',
                'button:has-text("Post")',
                'button.artdeco-button--primary:has-text("Post")',
                '[data-testid="post-button"]'
            ]
            for sel in post_btn_selectors:
                try:
                    btn = dialog.locator(sel).first
                    if btn.is_visible(timeout=2000) and btn.is_enabled():
                        post_btn = btn
                        logger.info(f"✓ Found Post button via scoped selector: {sel}")
                        break
                except: continue
        
        # Strategy 3: Global text search
        if not post_btn:
            try:
                btn = page.get_by_text("Post", exact=True).first
                if btn.is_visible(timeout=2000):
                    post_btn = btn
                    logger.info("✓ Found Post button via global get_by_text")
            except: pass

        if post_btn:
            post_btn.click()
            logger.info("✓ Clicked Post button")
        else:
            # Strategy 4: JS-based exhaustive search
            logger.info("Trying JS-based exhaustive search for Post button...")
            success = page.evaluate("""
                () => {
                    const buttons = Array.from(document.querySelectorAll('button'));
                    const postBtn = buttons.find(b => 
                        (b.innerText.trim() === 'Post' || b.getAttribute('aria-label') === 'Post') &&
                        !b.disabled
                    );
                    if (postBtn) {
                        postBtn.click();
                        return true;
                    }
                    return false;
                }
            """)
            if success:
                logger.info("✓ Found and clicked Post button via JS")
            else:
                logger.error("Post button not found after all strategies")
                take_debug_screenshot(page, "error_post_button_final_fail")
                return False

        # Wait for modal to close
        try:
            page.locator('div[role="dialog"], .share-creation-state').first.wait_for(state="hidden", timeout=15000)
            logger.info("✓ Modal closed - successfully posted")
            return True
        except:
            logger.warning("Modal didn't close, verifying success...")
            if page.is_visible('div.feed', timeout=3000): return True
            
    except Exception as e:
        logger.error(f"Posting failed: {e}")
        take_debug_screenshot(page, "error_full_stack")
        
    return False

# =============================================================================
# SCANNING LOGIC (EYES)
# =============================================================================

def scan_for_leads(page: Page):
    """Scans feed for leads and matches keywords."""
    logger.info("Scanning LinkedIn feed for leads...")
    try:
        # Wait for any post-like structure - extremely generic
        post_selectors = [
            'div.feed-shared-update-v2',
            'div.feed-shared-update-v4',
            '[data-urn*="urn:li:activity"]',
            '[data-id*="urn:li:activity"]',
            '.search-content__result',
            '.artdeco-card'
        ]
        
        posts = []
        for sel in post_selectors:
            try:
                found = page.query_selector_all(sel)
                # Filter for elements that actually have some content
                found = [f for f in found if len(f.inner_text().strip()) > 50]
                if found:
                    posts = found
                    logger.debug(f"✓ Found {len(found)} posts with selector: {sel}")
                    break
            except: continue
            
        if not posts:
            logger.warning("No posts found in feed yet. Waiting for scroll...")
            take_debug_screenshot(page, "error_scan_no_posts")
            # Try to log some helpful element names
            try:
                tags = page.evaluate("() => Array.from(document.querySelectorAll('div[id^=\"ember\"]')).slice(0, 5).map(e => e.className)")
                logger.debug(f"Sample ember div classes: {tags}")
            except: pass
            page.evaluate("window.scrollBy(0, 500)")
            return 0
            
        new_leads = 0
        for post in posts[:15]:
            try:
                # Try to get a unique ID
                post_id = post.get_attribute('data-id') or post.get_attribute('data-urn')
                if not post_id:
                    # Fallback to unique text hash if no ID
                    txt = post.inner_text()[:50]
                    post_id = f"hash_{hash(txt)}"
                
                if post_id in processed_ids: continue
                
                content_elem = post.query_selector('.update-components-text')
                if not content_elem: continue
                content = content_elem.inner_text().strip().lower()
                
                # Keyword check
                if any(kw in content for kw in SALES_KEYWORDS):
                    author = "User"
                    author_elem = post.query_selector('span[dir="auto"] span')
                    if author_elem: author = author_elem.inner_text().strip()
                    
                    # Create lead file
                    filename = f"LINKEDIN_LEAD_{re.sub(r'[^a-zA-Z0-9]', '_', author[:15])}_{int(time.time())}.md"
                    filepath = NEEDS_ACTION / filename
                    
                    md_content = f"---\ntype: linkedin_lead\nfrom: {author}\npriority: medium\nstatus: pending\nsource: linkedin\n---\n\n## LinkedIn Lead\n\n{content}\n"
                    filepath.write_text(md_content, encoding='utf-8')
                    
                    logger.info(f"📍 LEAD DETECTED: {author} - {filename}")
                    processed_ids.add(post_id)
                    new_leads += 1
                else:
                    processed_ids.add(post_id)
                    
            except Exception: continue
            
        return new_leads
    except Exception as e:
        logger.warning(f"Scan error: {e}")
        return 0

# =============================================================================
# MAIN ORCHESTRATION
# =============================================================================

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--watch", action="store_true", help="Run in monitoring mode")
    parser.add_argument("--content", type=str, help="Post content")
    parser.add_argument("--file", type=str, help="Approved MD file to post")
    args = parser.parse_args()

    with sync_playwright() as p:
        browser, context = get_browser_context(p, SESSION_PATH)
        page = context.pages[0] if context.pages else context.new_page()
        
        try:
            logger.info(f"Navigating to LinkedIn...")
            page.goto(LINKEDIN_URL, wait_until="domcontentloaded", timeout=60000)
            time.sleep(3)
            
            # Check login
            if "login" in page.url:
                logger.info("Login required. Waiting for manual login...")
                try: page.wait_for_url("**/feed/", timeout=120000)
                except: 
                    logger.error("Login timeout"); return
            
            # MODE: POSTING
            post_text = args.content
            if args.file:
                path = Path(args.file)
                if path.exists():
                    raw = path.read_text(encoding='utf-8')
                    # Strip frontmatter
                    post_text = re.split(r'---\s*\n', raw, 2)[-1].split('## LinkedIn Post Draft')[-1].strip()
            
            if post_text:
                if open_compose_modal(page):
                    if post_content(page, post_text):
                        logger.info("✓ POST SUCCESS")
                        if args.file:
                            # Move to done
                            done_file = GOLD_DIR / "done" / Path(args.file).name
                            shutil.move(args.file, str(done_file))
                    else: logger.error("✗ POST FAILED")
                else: logger.error("✗ COULD NOT OPEN MODAL")
            
            # MODE: WATCHING
            if args.watch:
                logger.info("Starting lead monitor loop (Ctrl+C to stop)...")
                while True:
                    scan_for_leads(page)
                    time.sleep(CHECK_INTERVAL)
                    # Stay on feed
                    if "feed" not in page.url: page.goto(LINKEDIN_URL)
                    
        except KeyboardInterrupt:
            logger.info("Stopping...")
        finally:
            # browser.close() # Usually keep open if persistent
            pass

if __name__ == "__main__":
    main()
