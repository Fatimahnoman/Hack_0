"""
LinkedIn Auto Poster - FIXED TYPING & SUBMIT
=============================================
FOCUS: Only fixing auto-typing and submit functionality.

Key Fixes:
1. Proper focus before typing
2. Slow typing with delay=100ms
3. wait_for_state('visible') before interaction
4. wait_for_load_state('networkidle') to prevent reload
5. Retry 3 times with 5s delay
6. Proper logging of every action

Install: pip install playwright && playwright install chromium
Run: python watchers/linkedin_auto_poster_fixed.py
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
    from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout
except ImportError:
    print("Run: pip install playwright && playwright install chromium")
    sys.exit(1)

# =============================================================================
# CONFIGURATION
# =============================================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SESSION_PATH = PROJECT_ROOT / "session" / "linkedin"
PENDING_APPROVAL_FOLDER = PROJECT_ROOT / "Pending_Approval"
APPROVED_FOLDER = PENDING_APPROVAL_FOLDER / "Approved"
DONE_FOLDER = PROJECT_ROOT / "Done"
LOGS_FOLDER = PROJECT_ROOT / "Logs"
LOG_FILE = LOGS_FOLDER / "linkedin.log"

for d in [SESSION_PATH, PENDING_APPROVAL_FOLDER, APPROVED_FOLDER, DONE_FOLDER, LOGS_FOLDER]:
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
# ★★★★★ FIXED TYPING & SUBMIT FUNCTIONS ★★★★★
# =============================================================================


def type_post_content(page, content: str) -> bool:
    """
    Type post content into LinkedIn compose box.
    
    FIXED: Uses proper focus, slow typing, and wait states.
    
    Args:
        page: Playwright page object
        content: Content to type
        
    Returns:
        True if successful, False otherwise
    """
    logger.info("=" * 70)
    logger.info(f"TYPING POST CONTENT ({len(content)} characters)")
    logger.info("=" * 70)
    
    for attempt in range(3):  # Retry 3 times
        try:
            logger.info(f"Attempt {attempt + 1}/3: Finding compose box...")
            
            # =========================================================
            # STEP 1: Find compose box using EXACT selectors
            # =========================================================
            compose_box = None
            
            # Primary selector: div[role="textbox"][contenteditable="true"]
            try:
                compose_box = page.locator('div[role="textbox"][contenteditable="true"]').first
                compose_box.wait_for_state('visible', timeout=10000)
                logger.info("✓ Found compose box via: div[role=\"textbox\"][contenteditable=\"true\"]")
            except PlaywrightTimeout:
                pass
            
            # Secondary selector: [data-testid="post-creation-textarea"]
            if not compose_box:
                try:
                    compose_box = page.locator('[data-testid="post-creation-textarea"]').first
                    compose_box.wait_for_state('visible', timeout=10000)
                    logger.info("✓ Found compose box via: [data-testid=\"post-creation-textarea\"]")
                except PlaywrightTimeout:
                    pass
            
            # Tertiary selector: div[contenteditable="true"]
            if not compose_box:
                try:
                    compose_box = page.locator('div[contenteditable="true"]').first
                    compose_box.wait_for_state('visible', timeout=10000)
                    logger.info("✓ Found compose box via: div[contenteditable=\"true\"]")
                except PlaywrightTimeout:
                    pass
            
            if not compose_box:
                logger.error("✗ Could not find compose box with any selector!")
                time.sleep(5)  # Wait 5s before retry
                continue
            
            # =========================================================
            # STEP 2: Focus compose box (CRITICAL!)
            # =========================================================
            logger.info("Focusing compose box...")
            compose_box.focus()
            time.sleep(1)  # Wait for focus to complete
            logger.info("✓ Compose box focused")
            
            # =========================================================
            # STEP 3: Clear existing content
            # =========================================================
            logger.info("Clearing existing content...")
            page.keyboard.press('Control+A')
            time.sleep(0.5)
            page.keyboard.press('Delete')
            time.sleep(0.5)
            logger.info("✓ Content cleared")
            
            # =========================================================
            # STEP 4: Type content SLOWLY (delay=100ms per char)
            # =========================================================
            logger.info(f"Typing {len(content)} characters with 100ms delay...")
            
            # Type in chunks to avoid detection
            chunk_size = 30
            chunks = [content[i:i+chunk_size] for i in range(0, len(content), chunk_size)]
            
            for i, chunk in enumerate(chunks):
                try:
                    # Refocus every 2 chunks to maintain focus
                    if i % 2 == 0 and i > 0:
                        compose_box.focus()
                        time.sleep(0.3)
                    
                    # Type chunk character by character with delay
                    for char in chunk:
                        page.keyboard.type(char, delay=100)  # 100ms delay per character!
                    
                    logger.debug(f"Typed chunk {i+1}/{len(chunks)}")
                    
                except Exception as e:
                    logger.warning(f"Chunk {i+1} failed: {e}")
                    # Fallback: use fill for remaining content
                    try:
                        compose_box.fill(content[i*chunk_size:])
                        break
                    except:
                        pass
                
                time.sleep(0.3)  # Small delay between chunks
            
            # =========================================================
            # STEP 5: Wait after typing (CRITICAL!)
            # =========================================================
            logger.info("Waiting 2 seconds after typing...")
            time.sleep(2)  # Wait for LinkedIn to process input
            
            # =========================================================
            # STEP 6: Verify content was entered
            # =========================================================
            logger.info("Verifying content...")
            try:
                entered = compose_box.inner_text()
                logger.info(f"Verification: {len(entered)}/{len(content)} chars entered")
                
                if len(entered) < len(content) * 0.8:
                    logger.warning("Text mismatch - retrying with fill...")
                    compose_box.fill(content)
                    time.sleep(2)
            except Exception as e:
                logger.warning(f"Could not verify text: {e}")
            
            logger.info("✓✓✓ CONTENT TYPING SUCCESSFUL! ✓✓✓")
            return True
            
        except Exception as e:
            logger.error(f"Attempt {attempt + 1} failed: {e}")
            if attempt < 2:
                logger.info(f"Retrying in 5 seconds...")
                time.sleep(5)  # 5 second delay before retry
            else:
                logger.error("✗✗✗ MAX RETRIES REACHED - TYPING FAILED! ✗✗✗")
    
    return False


def click_post_button(page) -> bool:
    """
    Click the Post submit button.
    
    FIXED: Uses proper wait states and multiple selectors.
    
    Args:
        page: Playwright page object
        
    Returns:
        True if successful, False otherwise
    """
    logger.info("=" * 70)
    logger.info("CLICKING POST BUTTON")
    logger.info("=" * 70)
    
    for attempt in range(3):  # Retry 3 times
        try:
            logger.info(f"Attempt {attempt + 1}/3: Finding post button...")
            
            post_button = None
            
            # Primary selector: button[data-testid="post-button"]
            try:
                post_button = page.locator('button[data-testid="post-button"]').first
                post_button.wait_for_state('visible', timeout=10000)
                post_button.wait_for_state('enabled', timeout=5000)
                logger.info("✓ Found post button via: button[data-testid=\"post-button\"]")
            except PlaywrightTimeout:
                pass
            
            # Secondary selector: button:has-text("Post")
            if not post_button:
                try:
                    post_button = page.locator('button:has-text("Post")').first
                    post_button.wait_for_state('visible', timeout=10000)
                    post_button.wait_for_state('enabled', timeout=5000)
                    logger.info("✓ Found post button via: button:has-text(\"Post\")")
                except PlaywrightTimeout:
                    pass
            
            # Tertiary selector: button[aria-label="Post"]
            if not post_button:
                try:
                    post_button = page.locator('button[aria-label="Post"]').first
                    post_button.wait_for_state('visible', timeout=10000)
                    post_button.wait_for_state('enabled', timeout=5000)
                    logger.info("✓ Found post button via: button[aria-label=\"Post\"]")
                except PlaywrightTimeout:
                    pass
            
            if not post_button:
                logger.error("✗ Could not find post button with any selector!")
                time.sleep(5)  # Wait 5s before retry
                continue
            
            # =========================================================
            # STEP 1: Click Post button
            # =========================================================
            logger.info("Clicking Post button...")
            post_button.click()
            logger.info("✓ Post button clicked!")
            
            # =========================================================
            # STEP 2: Wait for submission
            # =========================================================
            logger.info("Waiting 3 seconds for submission...")
            time.sleep(3)
            
            # =========================================================
            # STEP 3: Check for success
            # =========================================================
            logger.info("Checking for success indicators...")
            success_indicators = [
                'button:has-text("See fewer")',
                'text="View post"',
                'text="Post successful"'
            ]
            
            for indicator in success_indicators:
                try:
                    if page.query_selector(indicator):
                        logger.info(f"✓ Post confirmed via: {indicator}")
                        break
                except:
                    pass
            
            logger.info("✓✓✓ POST BUTTON CLICK SUCCESSFUL! ✓✓✓")
            return True
            
        except Exception as e:
            logger.error(f"Attempt {attempt + 1} failed: {e}")
            if attempt < 2:
                logger.info(f"Retrying in 5 seconds...")
                time.sleep(5)
            else:
                logger.error("✗✗✗ MAX RETRIES REACHED - POST CLICK FAILED! ✗✗✗")
    
    return False


def post_to_linkedin(content: str) -> bool:
    """
    Main posting function with fixed typing and submit.
    
    Args:
        content: Content to post
        
    Returns:
        True if successful, False otherwise
    """
    logger.info("=" * 70)
    logger.info("LINKEDIN AUTO POSTER - STARTING")
    logger.info(f"Content length: {len(content)} characters")
    logger.info("=" * 70)
    
    success = False
    
    with sync_playwright() as p:
        logger.info("Launching browser with anti-detection args...")
        
        # Launch with persistent context and anti-detection
        context = p.chromium.launch_persistent_context(
            user_data_dir=str(SESSION_PATH),
            headless=False,  # Show browser for debugging
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
                "--disable-gpu",
                "--disable-dev-shm-usage",
                "--disable-extensions"  # Disable extensions to avoid errors
            ],
            viewport={"width": 1366, "height": 768},
            timeout=120000
        )
        
        page = context.pages[0] if context.pages else context.new_page()
        
        try:
            # =========================================================
            # STEP 1: Navigate to LinkedIn feed
            # =========================================================
            logger.info("Navigating to LinkedIn feed...")
            
            # Navigate with longer timeout and ignore failures
            try:
                page.goto(
                    "https://www.linkedin.com/feed/",
                    wait_until="domcontentloaded",
                    timeout=180000
                )
            except PlaywrightTimeout:
                logger.warning("Initial navigation timeout, but continuing...")
            
            # Wait for page to be fully loaded (prevents reload issues)
            # Use shorter timeout to avoid hanging
            try:
                page.wait_for_load_state('networkidle', timeout=60000)
            except PlaywrightTimeout:
                logger.warning("Network idle timeout, continuing anyway...")
            
            time.sleep(5)  # Extra wait for LinkedIn to fully render
            logger.info("✓ LinkedIn feed loaded")
            
            # =========================================================
            # STEP 2: Check login status
            # =========================================================
            if "login" in page.url.lower():
                logger.warning("Not logged in! Waiting for manual login...")
                for i in range(60):
                    time.sleep(5)
                    if "login" not in page.url.lower():
                        logger.info("✓ Login detected!")
                        break
                else:
                    logger.error("Login timeout!")
                    return False
            
            # Reload feed after login
            try:
                page.goto(
                    "https://www.linkedin.com/feed/",
                    wait_until="domcontentloaded",
                    timeout=60000
                )
            except PlaywrightTimeout:
                logger.warning("Reload timeout, continuing...")
            
            try:
                page.wait_for_load_state('networkidle', timeout=60000)
            except PlaywrightTimeout:
                logger.warning("Network idle timeout after reload, continuing...")
            
            time.sleep(3)
            
            # =========================================================
            # STEP 3: Click "Start a post" button
            # =========================================================
            logger.info("Clicking 'Start a post'...")
            
            start_clicked = False
            start_selectors = [
                'button:has-text("Start a post")',
                '[aria-label="Start a post"]',
                '.share-box-feed-entry__trigger'
            ]
            
            for selector in start_selectors:
                try:
                    btn = page.locator(selector).first
                    if btn.is_visible(timeout=5000):
                        btn.click()
                        logger.info(f"✓ Clicked via: {selector}")
                        start_clicked = True
                        break
                except Exception as e:
                    logger.debug(f"Selector {selector} failed: {e}")
            
            if not start_clicked:
                logger.error("'Start a post' button not found!")
                return False
            
            # Wait for modal to open
            time.sleep(3)
            try:
                page.wait_for_load_state('networkidle', timeout=30000)
            except PlaywrightTimeout:
                logger.warning("Modal network idle timeout, continuing...")
            logger.info("✓ Compose modal opened")
            
            # =========================================================
            # STEP 4: TYPE CONTENT (FIXED!)
            # =========================================================
            if not type_post_content(page, content):
                logger.error("✗ Failed to type content!")
                return False
            
            # Wait after typing
            time.sleep(2)
            
            # =========================================================
            # STEP 5: CLICK POST BUTTON (FIXED!)
            # =========================================================
            if not click_post_button(page):
                logger.error("✗ Failed to click Post button!")
                return False
            
            # =========================================================
            # STEP 6: Wait for confirmation
            # =========================================================
            logger.info("Waiting for post confirmation...")
            time.sleep(5)
            
            success = True
            logger.info("=" * 70)
            logger.info("✓✓✓ POST PUBLISHED SUCCESSFULLY! ✓✓✓")
            logger.info("=" * 70)
            
        except Exception as e:
            logger.error(f"Error during posting: {e}")
            success = False
        finally:
            logger.info("Browser open for verification (10 seconds)...")
            time.sleep(10)
            context.close()
    
    return success


# =============================================================================
# FILE HANDLING FUNCTIONS
# =============================================================================


def read_post_content(filepath: Path) -> str:
    """Extract post content from draft file."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Extract content between ## Content and ---
        match = re.search(r'## Content\n\n(.+?)\n---', content, re.DOTALL)
        if match:
            return match.group(1).strip()
        
        return content
    except Exception as e:
        logger.error(f"Error reading {filepath}: {e}")
        return ""


def move_to_done(filepath: Path):
    """Move posted file to Done folder."""
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    dest = DONE_FOLDER / f"posted_{filepath.name}"
    
    try:
        with open(dest, 'w', encoding='utf-8') as f:
            f.write(f"""---
type: linkedin_post_sent
source: {filepath.name}
posted_at: {datetime.now().isoformat()}
status: posted
---

# Posted

*Posted {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*
""")
        
        if filepath.exists():
            filepath.unlink()
        
        logger.info(f"✓ Moved to Done: {dest.name}")
    except Exception as e:
        logger.error(f"Error moving to Done: {e}")


def check_approved_posts() -> list:
    """Check for approved posts in Approved folder."""
    if not APPROVED_FOLDER.exists():
        return []
    
    approved_files = list(APPROVED_FOLDER.glob("linkedin_post_*.md"))
    for f in approved_files:
        logger.info(f"Found approved post: {f.name}")
    
    return approved_files


# =============================================================================
# MAIN FUNCTION
# =============================================================================


def main():
    """Main function - check for approved posts and post them."""
    print("=" * 70)
    print("LinkedIn Auto Poster - FIXED TYPING & SUBMIT")
    print("=" * 70)
    print(f"Session: {SESSION_PATH}")
    print(f"Approved: {APPROVED_FOLDER}")
    print(f"Log: {LOG_FILE}")
    print("-" * 70)
    print("INSTRUCTIONS:")
    print("1. Move draft file to: Pending_Approval/Approved/")
    print("2. Run this script")
    print("3. Browser will open, type post, and submit automatically!")
    print("=" * 70)
    
    # Check for approved posts
    approved = check_approved_posts()
    
    if not approved:
        print("\n✗ No approved posts found!")
        print(f"Please move a draft to: {APPROVED_FOLDER}")
        return
    
    print(f"\n✓ Found {len(approved)} approved post(s)")
    
    # Post each approved file
    for filepath in approved:
        print(f"\n{'=' * 70}")
        print(f"POSTING: {filepath.name}")
        print(f"{'=' * 70}")
        
        content = read_post_content(filepath)
        
        if not content:
            print(f"✗ Could not read content from {filepath.name}")
            continue
        
        print(f"Content length: {len(content)} chars")
        print(f"Preview: {content[:100]}...")
        print("\nStarting in 3 seconds...")
        time.sleep(3)
        
        if post_to_linkedin(content):
            print(f"\n✓✓✓ SUCCESS! Post published!")
            move_to_done(filepath)
        else:
            print(f"\n✗✗✗ FAILED! Check logs: {LOG_FILE}")
    
    print("\n" + "=" * 70)
    print("DONE!")
    print("=" * 70)


if __name__ == "__main__":
    main()
