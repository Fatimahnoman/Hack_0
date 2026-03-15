"""
LinkedIn Manual Poster - Silver Tier
=====================================
Simple approach: Browser opens, you click Start a Post, 
then script types and posts automatically.

Run: python tools\linkedin_manual_post.py
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

PROJECT_ROOT = Path(__file__).parent.parent
PENDING_FOLDER = PROJECT_ROOT / "Pending_Approval"
DONE_FOLDER = PROJECT_ROOT / "Done"
LOGS_FOLDER = PROJECT_ROOT / "Logs"
SESSION_PATH = PROJECT_ROOT / "session" / "linkedin"

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(message)s',
    handlers=[
        logging.FileHandler(LOGS_FOLDER / f"linkedin_{datetime.now().strftime('%Y-%m-%d')}.log", encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


def list_drafts():
    """List available drafts."""
    if not PENDING_FOLDER.exists():
        return []
    return sorted([f for f in PENDING_FOLDER.iterdir() 
                   if f.name.startswith('linkedin_post_') and f.name.endswith('.md')])


def read_post_content(filepath):
    """Extract post content from draft file."""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    match = re.search(r'## Content\n\n(.+?)\n---', content, re.DOTALL)
    if match:
        return match.group(1).strip()
    return None


def main():
    print()
    print("=" * 60)
    print("LinkedIn Manual Poster")
    print("=" * 60)
    print()
    
    # List drafts
    drafts = list_drafts()
    if not drafts:
        print("[ERROR] No drafts found in Pending_Approval!")
        input("Press Enter to exit...")
        return
    
    print(f"[INFO] Found {len(drafts)} draft(s)")
    for i, d in enumerate(drafts[:10], 1):
        print(f"  {i}. {d.name}")
    if len(drafts) > 10:
        print(f"  ... and {len(drafts) - 10} more")
    
    # Select first draft for now
    print()
    print("[INFO] Using first draft (you can modify code to select)")
    selected = drafts[0]
    print(f"  Selected: {selected.name}")
    
    post_content = read_post_content(selected)
    if not post_content:
        print("[ERROR] Could not read post content!")
        input("Press Enter to exit...")
        return
    
    print(f"[INFO] Post length: {len(post_content)} chars")
    print()
    
    print("=" * 60)
    print("INSTRUCTIONS:")
    print("  1. Browser will open - LOGIN to LinkedIn (2 min)")
    print("  2. Click 'Start a post' button YOURSELF")
    print("  3. Script will auto-type and post")
    print("=" * 60)
    print()
    print("Starting in 3 seconds...")
    for i in range(3, 0, -1):
        print(f"  {i}...")
        time.sleep(1)
    print()
    
    logger.info("Starting browser...")
    
    with sync_playwright() as p:
        context = p.chromium.launch_persistent_context(
            user_data_dir=str(SESSION_PATH),
            headless=False,
            args=["--no-sandbox", "--disable-gpu"],
            timeout=120000
        )
        
        page = context.pages[0] if context.pages else context.new_page()
        
        # Go to LinkedIn
        logger.info("Going to LinkedIn...")
        page.goto("https://www.linkedin.com/feed/", wait_until="domcontentloaded", timeout=60000)
        time.sleep(3)
        
        # Wait for user to login and click Start a Post
        print()
        print("-" * 60)
        print("STEP 1: Login to LinkedIn (if not already)")
        print("STEP 2: Click 'Start a post' button")
        print("STEP 3: Script will auto-detect and type the post")
        print("-" * 60)
        print()
        
        # Wait and check for modal
        modal_detected = False
        max_wait = 120  # 2 minutes
        
        logger.info(f"Waiting for post modal (max {max_wait}s)...")
        start_time = time.time()
        
        while time.time() - start_time < max_wait:
            try:
                # Check for modal backdrop or text input
                modal_indicators = [
                    page.query_selector('div[role="dialog"]'),
                    page.query_selector('div[aria-label*="post"]'),
                    page.query_selector('div[contenteditable="true"]'),
                ]
                
                if any(modal_indicators):
                    modal_detected = True
                    logger.info("[OK] Modal detected!")
                    break
                
            except:
                pass
            
            time.sleep(2)
        
        if not modal_detected:
            print()
            logger.warning("[WARNING] Modal not detected after 2 minutes")
            logger.info("[INFO] Trying to proceed anyway...")
        
        # Small delay for modal to fully render
        time.sleep(2)
        
        # Find text input
        logger.info("Looking for text input...")
        
        text_input = None
        selectors_tried = []
        
        # Try multiple selectors
        selectors = [
            'div[contenteditable="true"][role="textbox"]',
            'div[contenteditable="true"]',
            '[data-testid="update-editor-text-input"]',
            'div.editor-content-area',
        ]
        
        for selector in selectors:
            selectors_tried.append(selector)
            try:
                el = page.query_selector(selector)
                if el:
                    text_input = el
                    logger.info(f"[OK] Found via: {selector}")
                    break
            except Exception as e:
                logger.debug(f"Failed {selector}: {e}")
        
        if not text_input:
            # Fallback: find ANY contenteditable
            try:
                all_editable = page.query_selector_all('div[contenteditable="true"]')
                if all_editable:
                    text_input = all_editable[0]
                    logger.info(f"[OK] Using first of {len(all_editable)} editable divs")
            except:
                pass
        
        if not text_input:
            logger.error("[ERROR] Text input not found!")
            logger.info(f"[INFO] Selectors tried: {selectors_tried}")
            print()
            print("MANUAL MODE: Browser will stay open.")
            print("You can manually paste the post content.")
            print()
            print(f"Post content ({len(post_content)} chars):")
            print("-" * 40)
            print(post_content[:500] + "..." if len(post_content) > 500 else post_content)
            print("-" * 40)
            print()
            input("Press Enter to exit...")
            context.close()
            return
        
        # Click to focus
        logger.info("Clicking text input...")
        text_input.click()
        time.sleep(1)
        
        # Clear existing
        logger.info("Clearing existing content...")
        page.keyboard.press('Control+A')
        time.sleep(0.5)
        page.keyboard.press('Delete')
        time.sleep(0.5)
        
        # TYPE the content
        logger.info(f"Typing {len(post_content)} characters...")
        
        # Type in chunks
        chunk_size = 100
        chunks = [post_content[i:i+chunk_size] for i in range(0, len(post_content), chunk_size)]
        
        for i, chunk in enumerate(chunks):
            try:
                page.keyboard.type(chunk, delay=15)
                logger.info(f"  Chunk {i+1}/{len(chunks)} typed")
            except Exception as e:
                logger.warning(f"  Chunk {i+1} failed: {e}")
                # Try fill as fallback
                try:
                    text_input.fill(chunk)
                    logger.info(f"  Chunk {i+1} filled (fallback)")
                except:
                    logger.error(f"  Chunk {i+1} completely failed")
            time.sleep(0.3)
        
        time.sleep(2)
        
        # Verify
        try:
            entered = text_input.inner_text()
            logger.info(f"Entered text: {len(entered)} chars")
        except:
            logger.warning("Could not verify entered text")
        
        # Click Post button
        logger.info("Looking for Post button...")
        
        post_clicked = False
        post_selectors = [
            'button:has-text("Post")',
            'button.artdeco-button:has-text("Post")',
        ]
        
        for selector in post_selectors:
            try:
                btn = page.query_selector(selector)
                if btn:
                    btn.click()
                    post_clicked = True
                    logger.info("[OK] Post button clicked!")
                    break
            except:
                pass
        
        if post_clicked:
            time.sleep(5)
            
            logger.info("=" * 60)
            logger.info("[SUCCESS] Post should be published!")
            logger.info("=" * 60)
            logger.info("Verify at: https://www.linkedin.com/feed/")
            logger.info("Browser staying open for verification...")
            logger.info("Press Enter to exit...")
            
            # Move to Done
            done_file = DONE_FOLDER / f"linkedin_post_{datetime.now().strftime('%Y%m%d_%H%M%S')}_DONE.md"
            with open(done_file, 'w', encoding='utf-8') as f:
                f.write(f"""---
type: linkedin_post_sent
source: {selected.name}
posted_at: {datetime.now().isoformat()}
status: posted
---

# Posted

{post_content}
""")
            
            selected.unlink()
            logger.info(f"[DONE] Moved to: {done_file.name}")
            
            input("Press Enter to exit...")
        else:
            logger.error("[ERROR] Post button not found!")
            logger.info("Browser open for debugging...")
            logger.info("You can manually click Post if visible")
            input("Press Enter to exit...")
        
        context.close()
    
    print()
    print("Done!")


if __name__ == "__main__":
    main()
