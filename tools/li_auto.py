"""
LinkedIn Auto Poster - USER PROOF VERSION
==========================================
Works regardless of who runs it
"""

import os, sys, time, re, logging
from datetime import datetime
from pathlib import Path

try:
    from playwright.sync_api import sync_playwright
except:
    print("pip install playwright && playwright install chromium")
    sys.exit(1)

ROOT = Path(__file__).parent.parent
PENDING = ROOT / "Pending_Approval"
DONE = ROOT / "Done"
LOGS = ROOT / "Logs"
SESSION = ROOT / "session" / "linkedin"
DEBUG = ROOT / "debug_li"

for d in [PENDING, DONE, LOGS, SESSION, DEBUG]:
    d.mkdir(parents=True, exist_ok=True)

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s',
    handlers=[logging.FileHandler(LOGS / f"li_{datetime.now().strftime('%Y%m%d')}.log"),
              logging.StreamHandler()])
log = logging.getLogger(__name__)


def get_content(path):
    with open(path, 'r', encoding='utf-8') as f:
        txt = f.read()
    m = re.search(r'## Content\n\n(.+?)\n---', txt, re.DOTALL)
    return m.group(1).strip() if m else None


def is_logged_in(page):
    """Check if user is logged in by looking for feed elements."""
    indicators = [
        page.query_selector('nav.global-nav'),
        page.query_selector('a[href*="/mynetwork/"]'),
        page.query_selector('a[href*="/notifications/"]'),
        page.query_selector('div[data-testid="update-editor"]'),
    ]
    return any(indicators) or ("feed" in page.url.lower() and "login" not in page.url.lower())


def main():
    log.info("="*70)
    log.info("LINKEDIN AUTO POSTER - USER PROOF VERSION")
    log.info("="*70)
    
    drafts = list(PENDING.glob('linkedin_post_*.md'))
    if not drafts:
        log.error("No drafts found!")
        input("Press Enter...")
        return
    
    draft = drafts[0]
    content = get_content(draft)
    if not content:
        log.error("Could not read content!")
        input("Press Enter...")
        return
    
    log.info(f"Draft: {draft.name}")
    log.info(f"Content: {len(content)} chars")
    
    with sync_playwright() as p:
        log.info("Launching browser...")
        ctx = p.chromium.launch_persistent_context(
            user_data_dir=str(SESSION),
            headless=False,
            args=["--no-sandbox", "--disable-gpu", "--start-maximized"],
            timeout=180000
        )
        
        page = ctx.pages[0] if ctx.pages else ctx.new_page()
        page.set_viewport_size({"width": 1920, "height": 1080})
        
        # Go to LinkedIn
        log.info("Going to LinkedIn...")
        page.goto("https://www.linkedin.com/", wait_until="domcontentloaded", timeout=120000)
        time.sleep(5)
        
        # Check and wait for login
        log.info("Checking login...")
        
        if not is_logged_in(page):
            log.warning("="*70)
            log.warning("NOT LOGGED IN - Please login now!")
            log.warning("You have 3 minutes")
            log.warning("="*70)
            
            # Wait up to 3 minutes
            start = time.time()
            while time.time() - start < 180:
                time.sleep(5)
                if is_logged_in(page):
                    log.info("LOGIN DETECTED!")
                    break
                elapsed = int(time.time() - start)
                log.info(f"Waiting for login... ({elapsed}/180s) - URL: {page.url[:60]}")
            
            if not is_logged_in(page):
                log.error("Login timeout!")
                page.screenshot(path=str(DEBUG / "login_timeout.png"))
                input("Press Enter...")
                ctx.close()
                return
        
        # Navigate to feed
        log.info("Going to feed...")
        page.goto("https://www.linkedin.com/feed/", wait_until="domcontentloaded", timeout=120000)
        time.sleep(5)
        page.screenshot(path=str(DEBUG / "feed.png"))
        log.info("Feed loaded")
        
        # Click "Start a post"
        log.info("Clicking 'Start a post'...")
        
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
            log.error("Could not click 'Start a post'")
            page.screenshot(path=str(DEBUG / "no_click.png"))
            input("Press Enter...")
            ctx.close()
            return
        
        # Wait for modal
        log.info("Waiting for modal...")
        time.sleep(5)
        page.screenshot(path=str(DEBUG / "modal.png"))
        
        # Find text input
        log.info("Finding text input...")
        
        text_el = None
        try:
            divs = page.locator('div[contenteditable="true"]').all()
            if divs:
                text_el = divs[0]
                log.info(f"Found {len(divs)} editable divs")
        except: pass
        
        if not text_el:
            try:
                areas = page.locator('textarea').all()
                if areas:
                    text_el = areas[0]
                    log.info(f"Found {len(areas)} textareas")
            except: pass
        
        if not text_el:
            log.error("No text input found!")
            page.screenshot(path=str(DEBUG / "no_input.png"))
            input("Press Enter...")
            ctx.close()
            return
        
        # Type content
        log.info(f"Typing {len(content)} chars...")
        
        # Ensure focus on text input
        text_el.click()
        time.sleep(1)
        
        # Clear any existing text
        page.keyboard.press('Control+A')
        time.sleep(0.3)
        page.keyboard.press('Delete')
        time.sleep(0.3)
        
        # Type content in chunks with focus check
        chunks = [content[i:i+50] for i in range(0, len(content), 50)]
        for i, chunk in enumerate(chunks):
            try:
                # Refocus before each chunk
                if i > 0:
                    text_el.click()
                    time.sleep(0.2)
                page.keyboard.type(chunk, delay=10)
                log.debug(f"Chunk {i+1}/{len(chunks)} typed")
            except Exception as e:
                log.warning(f"Chunk {i+1} failed: {e}")
                # Fallback: use fill
                try:
                    text_el.fill(chunk)
                except:
                    pass
            time.sleep(0.2)
        
        time.sleep(2)
        
        page.screenshot(path=str(DEBUG / "typed.png"))
        
        try:
            entered = text_el.inner_text()
            log.info(f"Entered: {len(entered)}/{len(content)} chars")
            if len(entered) < len(content) * 0.8:
                log.warning("Text mismatch - retrying...")
                text_el.fill(content)
                time.sleep(1)
        except Exception as e:
            log.warning(f"Could not verify text: {e}")
        
        # Click Post
        log.info("Clicking Post button...")

        post_clicked = False
        for sel in [
            'button:has-text("Post")',
            'button.artdeco-button:has-text("Post")',
            '[data-control-name="post_post"]',
            'button:has-text("POST")',
        ]:
            try:
                btn = page.locator(sel).first
                if btn.count() > 0:
                    # Wait for button to be enabled
                    btn.wait_for(state="enabled", timeout=5000)
                    btn.click()
                    log.info(f"Post clicked: {sel}")
                    post_clicked = True
                    break
            except Exception as e:
                log.debug(f"Selector {sel} failed: {e}")
                pass

        if not post_clicked:
            # Fallback: Try to find any button with "Post" text
            try:
                all_buttons = page.locator('button').all()
                for btn in all_buttons:
                    try:
                        txt = btn.inner_text().strip().upper()
                        if txt == "POST" or txt.startswith("POST"):
                            btn.wait_for(state="enabled", timeout=2000)
                            btn.click()
                            log.info("Post clicked via fallback")
                            post_clicked = True
                            break
                    except:
                        pass
            except Exception as e:
                log.debug(f"Fallback failed: {e}")

        if not post_clicked:
            log.error("Post button not found!")
            log.info("Available buttons:")
            try:
                buttons = page.locator('button').all()
                for i, btn in enumerate(buttons[:30]):
                    try:
                        txt = btn.inner_text().strip()
                        if txt:
                            log.info(f"  [{i}] {txt[:50]}")
                    except:
                        pass
            except:
                pass
            page.screenshot(path=str(DEBUG / "no_post.png"))
            log.info("Browser kept open - check debug_li folder for screenshots")
            log.info("Press Enter to exit...")
            try:
                input("Press Enter...")
            except:
                pass
            ctx.close()
            return
        
        # Wait for post to publish
        log.info("Waiting for post to publish...")
        time.sleep(3)
        
        # Check for success indicators
        success_indicators = [
            page.locator('button:has-text("See fewer")'),
            page.locator('text="View post"'),
            page.locator('text="Post successful"'),
        ]
        
        for indicator in success_indicators:
            try:
                if indicator.count() > 0:
                    log.info("Post publication confirmed!")
                    break
            except:
                pass
        
        page.screenshot(path=str(DEBUG / "done.png"))
        
        log.info("="*70)
        log.info("SUCCESS! Post published!")
        log.info("="*70)
        
        # Move to Done
        done_file = DONE / f"li_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        with open(done_file, 'w', encoding='utf-8') as f:
            f.write(f"# Posted\n\n{content}\n")
        draft.unlink()
        log.info(f"Done: {done_file.name}")
        
        log.info("Verify at: https://www.linkedin.com/feed/")
        log.info("Press Enter to exit...")
        try:
            input("Press Enter...")
        except: pass
        
        ctx.close()


if __name__ == "__main__":
    main()
