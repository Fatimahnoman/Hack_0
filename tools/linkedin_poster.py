"""
LinkedIn Auto Poster - Ultimate Fix
====================================
Uses human-like interaction: Click modal, wait, then type via keyboard.

Run: python tools\linkedin_poster.py --post FILENAME
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

# Config
PROJECT_ROOT = Path(__file__).parent.parent
PENDING = PROJECT_ROOT / "Pending_Approval"
DONE = PROJECT_ROOT / "Done"
LOGS = PROJECT_ROOT / "Logs"
SESSION = PROJECT_ROOT / "session" / "linkedin"
DEBUG = PROJECT_ROOT / "debug_li"

for d in [PENDING, DONE, LOGS, SESSION, DEBUG]:
    d.mkdir(parents=True, exist_ok=True)

# Logging
log_file = LOGS / f"li_{datetime.now().strftime('%Y%m%d')}.log"
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s',
    handlers=[logging.FileHandler(log_file, encoding='utf-8'), logging.StreamHandler()])
log = logging.getLogger(__name__)


def read_draft(path):
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()
    m = re.search(r'## Content\n\n(.+?)\n---', content, re.DOTALL)
    return m.group(1).strip() if m else None


def save_debug(page, name):
    try:
        page.screenshot(path=str(DEBUG / f"{name}.png"))
        with open(DEBUG / f"{name}.html", 'w', encoding='utf-8') as f:
            f.write(page.content())
        log.info(f"Debug: {name}")
    except: pass


def post(content):
    log.info("="*60)
    log.info(f"Posting {len(content)} chars to LinkedIn")
    log.info("="*60)
    
    with sync_playwright() as p:
        ctx = p.chromium.launch_persistent_context(
            user_data_dir=str(SESSION),
            headless=False,
            args=["--no-sandbox", "--disable-gpu", "--disable-blink-features=AutomationControlled"],
            timeout=120000
        )
        
        page = ctx.pages[0] if ctx.pages else ctx.new_page()
        page.set_viewport_size({"width": 1920, "height": 1080})
        
        try:
            # Go to feed
            log.info("Going to LinkedIn feed...")
            page.goto("https://www.linkedin.com/feed/", wait_until="networkidle", timeout=60000)
            time.sleep(5)
            save_debug(page, "01_feed")
            
            # Wait for login if needed
            if "login" in page.url.lower():
                log.warning("Not logged in! Waiting 120s for manual login...")
                for i in range(24):
                    time.sleep(5)
                    if "feed" in page.url.lower():
                        log.info("Logged in!")
                        break
                page.goto("https://www.linkedin.com/feed/", wait_until="networkidle", timeout=30000)
                time.sleep(3)
            
            # Click "Start a post"
            log.info("Clicking 'Start a post'...")
            
            # Try multiple ways to find and click
            clicked = False
            for sel in ['button:has-text("Start a post")', '[aria-label="Start a post"]', '.share-box-feed-entry']:
                try:
                    btn = page.locator(sel).first
                    if btn.count() > 0:
                        btn.click()
                        log.info(f"Clicked via: {sel}")
                        clicked = True
                        break
                except: pass
            
            if not clicked:
                log.error("Could not click 'Start a post'")
                save_debug(page, "01_no_click")
                input("Press Enter...")
                ctx.close()
                return False
            
            time.sleep(3)
            save_debug(page, "02_modal")
            
            # CRITICAL: Wait longer for modal animation
            log.info("Waiting for modal...")
            time.sleep(5)
            
            # Take screenshot to see what we have
            save_debug(page, "03_modal_ready")
            
            # Find ANY editable element
            log.info("Looking for text input...")
            
            text_el = None
            
            # Method 1: contenteditable divs
            try:
                divs = page.locator('div[contenteditable="true"]').all()
                if divs:
                    text_el = divs[0]
                    log.info(f"Found {len(divs)} contenteditable divs")
            except: pass
            
            # Method 2: textarea
            if not text_el:
                try:
                    areas = page.locator('textarea').all()
                    if areas:
                        text_el = areas[0]
                        log.info(f"Found {len(areas)} textareas")
                except: pass
            
            # Method 3: role=textbox
            if not text_el:
                try:
                    text_el = page.locator('[role="textbox"]').first
                    if text_el.count() > 0:
                        log.info("Found via role=textbox")
                except: pass
            
            if not text_el:
                log.error("NO TEXT INPUT FOUND!")
                log.info("Opening HTML for inspection...")
                save_debug(page, "04_no_input")
                
                # Show what elements ARE available
                try:
                    all_divs = page.locator('div').all()
                    log.info(f"Total divs on page: {len(all_divs)}")
                    
                    # Check for any with specific classes
                    for cls in ['editor', 'compose', 'share', 'update']:
                        try:
                            els = page.locator(f'div[class*="{cls}"]').all()
                            if els:
                                log.info(f"Found {len(els)} divs with class containing '{cls}'")
                        except: pass
                except: pass
                
                input("Press Enter to exit...")
                ctx.close()
                return False
            
            # CLICK to focus
            log.info("Clicking text input...")
            text_el.click()
            time.sleep(2)
            
            # Clear any existing
            page.keyboard.press('Control+A')
            time.sleep(0.5)
            page.keyboard.press('Delete')
            time.sleep(0.5)
            
            # TYPE content slowly
            log.info(f"Typing {len(content)} chars...")
            
            # Use page.keyboard directly for more reliable typing
            for i, char in enumerate(content):
                try:
                    page.keyboard.type(char, delay=5)
                except:
                    log.warning(f"Char {i} failed")
                if (i+1) % 50 == 0:
                    time.sleep(0.2)
                    log.debug(f"Typed {i+1}/{len(content)}")
            
            time.sleep(3)
            
            # Verify
            try:
                entered = text_el.inner_text()
                log.info(f"Entered {len(entered)} chars")
            except:
                log.warning("Could not verify")
            
            save_debug(page, "05_typed")
            
            # Click Post
            log.info("Clicking Post button...")
            
            post_clicked = False
            for sel in ['button:has-text("Post")', 'button.artdeco-button:has-text("Post")']:
                try:
                    btn = page.locator(sel).first
                    if btn.count() > 0:
                        btn.click()
                        log.info(f"Post clicked via: {sel}")
                        post_clicked = True
                        break
                except: pass
            
            if not post_clicked:
                log.error("Post button not found!")
                save_debug(page, "06_no_post_btn")
                input("Press Enter...")
                ctx.close()
                return False
            
            # Wait
            time.sleep(5)
            save_debug(page, "06_after_post")
            
            log.info("="*60)
            log.info("[SUCCESS] Post should be published!")
            log.info("="*60)
            
        except Exception as e:
            log.error(f"Error: {e}")
            save_debug(page, "error")
        
        log.info("Browser open for verification...")
        log.info("Press Enter to exit...")
        try:
            input("Press Enter...")
        except: pass
        
        ctx.close()
    
    return True


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--post', type=str)
    parser.add_argument('--test', action='store_true')
    args = parser.parse_args()
    
    if args.test:
        with sync_playwright() as p:
            ctx = p.chromium.launch_persistent_context(
                user_data_dir=str(SESSION),
                headless=False,
                args=["--no-sandbox"],
                timeout=120000
            )
            page = ctx.pages[0]
            page.goto("https://linkedin.com/feed/", wait_until="networkidle", timeout=60000)
            input("Press Enter...")
            ctx.close()
        return
    
    if not args.post:
        drafts = list(PENDING.glob('linkedin_post_*.md'))
        if drafts:
            log.info(f"Found {len(drafts)} draft(s):")
            for d in drafts[:5]:
                log.info(f"  - {d.name}")
            log.info(f"\nRun: python tools\\linkedin_poster.py --post {drafts[0].name}")
        else:
            log.info("No drafts found")
        return
    
    path = PENDING / args.post
    if not path.exists():
        log.error(f"Not found: {args.post}")
        return
    
    content = read_draft(path)
    if not content:
        log.error("Could not read content")
        return
    
    if post(content):
        # Move to Done
        done_file = DONE / f"li_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        with open(done_file, 'w', encoding='utf-8') as f:
            f.write(f"# Posted\n\n{content}\n")
        path.unlink()
        log.info(f"Done: {done_file.name}")
    else:
        log.error("Failed!")


if __name__ == "__main__":
    main()
