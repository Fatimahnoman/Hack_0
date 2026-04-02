r"""
LinkedIn Auto Poster - Gold Tier
================================
Production-ready LinkedIn auto poster with persistent session support.
Integrated with Action Dispatcher for automatic posting when files move to Approved folder.

FEATURES:
✓ Persistent session: <project_root>/session/linkedin (see SESSION_PATH in this file)
✓ Slow, natural typing (anti-bot detection)
✓ Stable selectors with multiple fallbacks
✓ Comprehensive logging
✓ Error handling with retries
✓ Action Dispatcher integration

USAGE:
  python gold/watchers/linkedin_auto_poster.py --content "Your post text"
  OR
  python gold/watchers/linkedin_auto_poster.py --file "path/to/approved_file.md"
  OR
  python gold/watchers/linkedin_auto_poster.py --watch
  (--watch runs unified_linkedin_poster.py --watch: feed + leads -> gold/needs_action)

INSTALL:
  pip install playwright
  playwright install chromium

Author: Gold Tier Integration (based on Silver Tier working code)
Version: 2.0
Date: 2026-03-31
"""

import os
import re
import sys
import time
import shutil
import logging
import subprocess
import argparse
import random
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

# Posting configuration
MAX_RETRIES = 3
TYPE_DELAY = 120  # ms per character (slow typing for anti-bot; higher = fewer React dropouts)
FOCUS_WAIT = 1500  # ms
POST_WAIT = 3500  # ms after typing (let LinkedIn enable Post button)
RETRY_DELAYS = [10, 15, 20]  # seconds between retries

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
    """Wait for LinkedIn feed — avoid networkidle (LinkedIn rarely goes idle; can break flows)."""
    logger.info("Waiting for LinkedIn to load...")
    try:
        page.wait_for_load_state("domcontentloaded", timeout=timeout)
        time.sleep(2)
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


def dismiss_linkedin_overlays(page):
    """Close popups that steal focus or dismiss the composer (Got it, cookies, etc.)."""
    try:
        done_btn = page.locator('button.share-box-footer__primary-btn:has-text("Done")').first
        if done_btn.is_visible(timeout=1500):
            logger.info("Closing 'Post settings' overlay...")
            if not done_btn.is_enabled():
                anyone_btn = page.locator('button:has-text("Anyone")').first
                if anyone_btn.is_visible(timeout=1000):
                    anyone_btn.click()
                    time.sleep(0.8)
            done_btn.click()
            time.sleep(0.8)
    except Exception:
        pass
    for label in ("Got it", "Not now", "Dismiss"):
        try:
            b = page.locator(f'button:has-text("{label}")').first
            if b.is_visible(timeout=600):
                b.click()
                time.sleep(0.4)
        except Exception:
            pass


def safe_navigate_to_feed(page):
    """
    Avoid full page.reload when already on feed — reload often logs user out or
    closes the compose modal mid-flow when sharing Chrome with the watcher (CDP).
    """
    u = page.url.lower()
    if "linkedin.com" in u and "/feed" in u and "login" not in u and "checkpoint" not in u:
        logger.info("Already on LinkedIn feed — skipping goto (prevents session/modal loss)")
        try:
            page.wait_for_load_state("domcontentloaded", timeout=10000)
        except Exception:
            pass
        time.sleep(2)
        return
    logger.info(f"Navigating to {LINKEDIN_FEED_URL}...")
    page.goto(LINKEDIN_FEED_URL, wait_until="domcontentloaded", timeout=60000)
    time.sleep(2)


def force_english_ltr_on_editor(compose_box):
    """
    LinkedIn sometimes inherits RTL / unicode-bidi on the editor — English looks mirrored.
    Force LTR on the editor and a few ancestors.
    """
    try:
        compose_box.evaluate(
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
        logger.debug(f"force_english_ltr_on_editor: {e}")


def _normalize_for_keyboard(s: str) -> str:
    """Reduce Unicode issues with Playwright key events (smart quotes, etc.)."""
    return (
        s.replace("\u2019", "'")
        .replace("\u2018", "'")
        .replace("\u201c", '"')
        .replace("\u201d", '"')
        .replace("\u2014", "--")
        .replace("\u2013", "-")
    )


def paste_full_text_into_editor(compose_box, text: str) -> bool:
    """
    Insert entire post at once via DOM (avoids long keyboard.type stopping mid-text).
    LinkedIn's editor accepts execCommand insertText / InputEvent.
    """
    try:
        compose_box.evaluate(
            """(el, txt) => {
                el.focus();
                try {
                  el.innerHTML = '';
                } catch (e) {}
                if (document.execCommand && document.execCommand('insertText', false, txt)) {
                  return 'exec';
                }
                el.textContent = txt;
                el.dispatchEvent(new InputEvent('input', { bubbles: true, inputType: 'insertText', data: txt }));
                return 'fallback';
            }""",
            text,
        )
        return True
    except Exception as e:
        logger.warning(f"paste_full_text_into_editor: {e}")
        return False


def type_text_in_composer(page, compose_box, text: str):
    """
    Prefer one-shot DOM insert for long/Unicode text; fall back to chunked keyboard if short.
    """
    compose_box.click()
    time.sleep(0.5)
    force_english_ltr_on_editor(compose_box)
    page.keyboard.press("Control+A")
    time.sleep(0.15)
    page.keyboard.press("Backspace")
    time.sleep(0.25)
    force_english_ltr_on_editor(compose_box)

    if paste_full_text_into_editor(compose_box, text):
        time.sleep(1.5)
        try:
            got = (compose_box.inner_text(timeout=8000) or "").strip()
            need = len(text.strip())
            # Allow some UI loss vs source length
            ok = need < 80 or len(got) >= max(need * 0.4, need - 300)
            if ok:
                logger.info(f"✓ Compose filled via DOM (~{len(got)} chars visible, source {need})")
                return
            logger.warning(
                f"DOM insert looks short ({len(got)} vs {need} chars) — keyboard fallback"
            )
        except Exception as e:
            logger.warning(f"Could not verify DOM insert: {e}")

    # Fallback: chunked typing (ASCII-normalized)
    norm = _normalize_for_keyboard(text)
    delay = max(TYPE_DELAY, 80)
    chunk_size = 120
    for i in range(0, len(norm), chunk_size):
        part = norm[i : i + chunk_size]
        page.keyboard.type(part, delay=delay)
        time.sleep(0.08)
        u = page.url.lower()
        if "login" in u or "checkpoint" in u:
            raise RuntimeError("LinkedIn redirected to login/checkpoint during typing (session lost)")


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
        browser = None
        used_cdp = False

        try:
            with sync_playwright() as p:
                context = None

                # TRY 1: Connect to existing Chrome (Gold Tier Watcher on Port 9222)
                logger.info("Trying to connect to existing Chrome (Port 9222)...")

                try:
                    browser = p.chromium.connect_over_cdp(
                        "http://127.0.0.1:9222",
                        timeout=10000
                    )
                    used_cdp = True
                    logger.info("✓ Connected to existing Chrome (CDP — will NOT close browser when done)")

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

                dismiss_linkedin_overlays(page)
                safe_navigate_to_feed(page)
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

                dismiss_linkedin_overlays(page)

                # Click "Start a post"
                logger.info("Opening compose box...")

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

                logger.info("Focusing compose box...")
                compose_box.focus()
                time.sleep(FOCUS_WAIT / 1000)
                dismiss_linkedin_overlays(page)

                logger.info(f"Typing content ({len(text)} chars, ~{TYPE_DELAY}ms/char, keyboard API)...")
                start_time = time.time()

                type_text_in_composer(page, compose_box, text)

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

                # NEVER close Chrome when we attached via CDP — that disconnects the watcher
                # and looks like "session out" / compose closing on the next run.
                if browser and browser.is_connected() and not used_cdp:
                    try:
                        browser.close()
                    except Exception:
                        pass
                elif used_cdp:
                    logger.info("Leaving Chrome running (CDP session preserved for LinkedIn watcher)")

                return True

        except Exception as e:
            logger.error(f"✗ Attempt {attempt + 1} failed: {e}")

            try:
                if browser and browser.is_connected() and not used_cdp:
                    browser.close()
            except Exception:
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

    if args.watch:
        unified = PROJECT_ROOT / "gold" / "watchers" / "unified_linkedin_poster.py"
        if not unified.exists():
            logger.error(f"Missing {unified}")
            sys.exit(1)
        print("=" * 60)
        print("LinkedIn --watch → unified_linkedin_poster.py --watch")
        print("  Feed + leads → gold/needs_action | gold/logs/linkedin_unified_*.log")
        print("=" * 60)
        rc = subprocess.call(
            [sys.executable, str(unified), "--watch"],
            cwd=str(PROJECT_ROOT),
        )
        raise SystemExit(rc)

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

            # Extract post — never split on first '---' (truncates markdown / bullets in body)
            if "## LinkedIn Post Draft" in file_content:
                m = re.search(
                    r"## LinkedIn Post Draft\s*\n+([\s\S]+)",
                    file_content,
                    re.IGNORECASE,
                )
                if m:
                    content = m.group(1).strip()
                    content = re.sub(
                        r"\n?---\s*\n+\*[^\n]+\*\s*$",
                        "",
                        content,
                        flags=re.DOTALL,
                    )
                    content = re.sub(r"\n?---\s*$", "", content).strip()
                else:
                    content = file_content
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
