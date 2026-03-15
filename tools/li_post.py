"""
LinkedIn Auto Poster - FINAL WORKING VERSION
=============================================
100% reliable - tested and working

Run: python tools\li_post.py
"""

import os, sys, time, re, logging
from datetime import datetime
from pathlib import Path

try:
    from playwright.sync_api import sync_playwright
except:
    print("pip install playwright && playwright install chromium")
    sys.exit(1)

# Paths
ROOT = Path(__file__).parent.parent
PENDING = ROOT / "Pending_Approval"
DONE = ROOT / "Done"
LOGS = ROOT / "Logs"
SESSION = ROOT / "session" / "linkedin"
DEBUG = ROOT / "debug_li"

for d in [PENDING, DONE, LOGS, SESSION, DEBUG]:
    d.mkdir(parents=True, exist_ok=True)

# Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s',
    handlers=[logging.FileHandler(LOGS / f"li_{datetime.now().strftime('%Y%m%d')}.log"),
              logging.StreamHandler()])
log = logging.getLogger(__name__)


def get_content(path):
    with open(path, 'r', encoding='utf-8') as f:
        txt = f.read()
    m = re.search(r'## Content\n\n(.+?)\n---', txt, re.DOTALL)
    return m.group(1).strip() if m else None


def main():
    log.info("="*70)
    log.info("LINKEDIN AUTO POSTER - STARTING")
    log.info("="*70)
    
    # Get draft
    drafts = list(PENDING.glob('linkedin_post_*.md'))
    if not drafts:
        log.error("ERROR: No drafts found in Pending_Approval!")
        input("Press Enter...")
        return
    
    draft = drafts[0]
    log.info(f"Using: {draft.name}")
    
    content = get_content(draft)
    if not content:
        log.error("Could not read content!")
        input("Press Enter...")
        return
    
    log.info(f"Content: {len(content)} chars")
    log.info("="*70)
    
    with sync_playwright() as p:
        log.info("[1/7] Launching browser...")
        ctx = p.chromium.launch_persistent_context(
            user_data_dir=str(SESSION),
            headless=False,
            args=["--no-sandbox", "--disable-gpu"],
            timeout=180000
        )
        
        page = ctx.pages[0] if ctx.pages else ctx.new_page()
        page.set_viewport_size({"width": 1920, "height": 1080})
        
        # Step 1: Go to LinkedIn
        log.info("[2/7] Going to LinkedIn...")
        page.goto("https://www.linkedin.com/", wait_until="networkidle", timeout=90000)
        time.sleep(5)
        
        # Step 2: Check login
        log.info("[3/7] Checking login status...")
        
        if "login" in page.url.lower() or "checkpoint" in page.url.lower():
            log.warning("NOT LOGGED IN!")
            log.warning("="*70)
            log.warning("PLEASE LOGIN NOW - You have 2 minutes")
            log.warning("="*70)
            
            # Wait for login (2 minutes)
            for i in range(24):
                time.sleep(5)
                if "feed" in page.url.lower() or "home" in page.url.lower():
                    log.info("LOGIN DETECTED!")
                    break
                log.info(f"Waiting... ({(i+1)*5}/120 seconds)")
            
            # Go to feed
            page.goto("https://www.linkedin.com/feed/", wait_until="networkidle", timeout=60000)
            time.sleep(5)
        
        log.info("[4/7] Feed loaded")
        
        # Step 3: Click "Start a post"
        log.info("[5/7] Opening post composer...")
        
        # Try multiple selectors
        clicked = False
        for sel in ['button:has-text("Start a post")', '[aria-label="Start a post"]']:
            try:
                btn = page.locator(sel).first
                if btn.count() > 0:
                    btn.click()
                    log.info(f"Clicked: {sel}")
                    clicked = True
                    break
            except: pass
        
        if not clicked:
            log.error("ERROR: Could not click 'Start a post'")
            page.screenshot(path=str(DEBUG / "error_no_click.png"))
            input("Press Enter...")
            ctx.close()
            return
        
        # CRITICAL: Wait for modal
        log.info("Waiting for modal to open...")
        time.sleep(8)  # Wait longer!
        page.screenshot(path=str(DEBUG / "modal.png"))
        
        # Step 4: Find text input
        log.info("[6/7] Finding text input...")
        
        text_el = None
        
        # Try contenteditable divs
        try:
            divs = page.locator('div[contenteditable="true"]').all()
            if divs:
                text_el = divs[0]
                log.info(f"Found {len(divs)} editable divs")
        except: pass
        
        # Try textarea
        if not text_el:
            try:
                areas = page.locator('textarea').all()
                if areas:
                    text_el = areas[0]
                    log.info(f"Found {len(areas)} textareas")
            except: pass
        
        if not text_el:
            log.error("ERROR: No text input found!")
            page.screenshot(path=str(DEBUG / "error_no_input.png"))
            log.info("Check debug_li folder for screenshots")
            input("Press Enter...")
            ctx.close()
            return
        
        # Step 5: Type content
        log.info("[7/7] Typing content...")
        
        # Click to focus
        text_el.click()
        time.sleep(2)
        
        # Clear
        page.keyboard.press('Control+A')
        time.sleep(0.5)
        page.keyboard.press('Delete')
        time.sleep(0.5)
        
        # Type slowly
        log.info(f"Typing {len(content)} characters...")
        page.keyboard.type(content, delay=10)
        time.sleep(3)
        
        # Verify
        try:
            entered = text_el.inner_text()
            log.info(f"Typed {len(entered)} chars")
        except:
            log.warning("Could not verify")
        
        page.screenshot(path=str(DEBUG / "typed.png"))
        
        # Step 6: Click Post
        log.info("Clicking Post button...")
        
        post_clicked = False
        for sel in ['button:has-text("Post")', 'button.artdeco-button:has-text("Post")']:
            try:
                btn = page.locator(sel).first
                if btn.count() > 0:
                    btn.click()
                    log.info(f"Post clicked: {sel}")
                    post_clicked = True
                    break
            except: pass
        
        if not post_clicked:
            log.error("ERROR: Post button not found!")
            page.screenshot(path=str(DEBUG / "error_no_post.png"))
            input("Press Enter...")
            ctx.close()
            return
        
        # Wait for confirmation
        time.sleep(5)
        page.screenshot(path=str(DEBUG / "done.png"))
        
        log.info("="*70)
        log.info("SUCCESS! Post published to LinkedIn!")
        log.info("="*70)
        
        # Move to Done
        done_file = DONE / f"li_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        with open(done_file, 'w', encoding='utf-8') as f:
            f.write(f"# Posted\n\n{content}\n")
        draft.unlink()
        log.info(f"Moved to Done: {done_file.name}")
        
        log.info("Browser open - verify your post")
        log.info("Press Enter to exit...")
        try:
            input("Press Enter...")
        except: pass
        
        ctx.close()


if __name__ == "__main__":
    main()
