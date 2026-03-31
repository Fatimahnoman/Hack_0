"""
LinkedIn Watcher - Gold Tier (Fixed)
=====================================
Monitors LinkedIn for sales leads and opportunities.
Creates files in gold/needs_action/ folder first.

Run: python watchers/linkedin_watcher_fixed.py
"""

import os
import re
import sys
import time
import logging
from datetime import datetime
from pathlib import Path

try:
    from playwright.sync_api import sync_playwright
except ImportError as e:
    print(f"[ERROR] Missing: {e}")
    print("Run: pip install playwright && playwright install chrome")
    sys.exit(1)

# =============================================================================
# CONFIGURATION - GOLD TIER FOLDERS
# =============================================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent
GOLD_DIR = PROJECT_ROOT / "gold"

# CRITICAL: Gold Tier folder structure
NEEDS_ACTION_FOLDER = GOLD_DIR / "needs_action"
LOGS_FOLDER = GOLD_DIR / "logs"
SESSION_PATH = PROJECT_ROOT / "session" / "linkedin_chrome"

# Ensure folders exist
NEEDS_ACTION_FOLDER.mkdir(parents=True, exist_ok=True)
LOGS_FOLDER.mkdir(parents=True, exist_ok=True)
SESSION_PATH.mkdir(parents=True, exist_ok=True)

# Settings
LINKEDIN_URL = "https://www.linkedin.com/feed/"
CHECK_INTERVAL = 60  # seconds - Faster checking

# Keywords for sales leads
SALES_KEYWORDS = [
    "looking for", "need", "require", "seeking", "hire",
    "developer", "service", "help", "project", "budget",
    "urgent", "asap", "recommend", "suggestion"
]

# Track processed
processed_posts = set()
PROCESSED_FILE = SESSION_PATH / "processed.txt"

# =============================================================================
# LOGGING
# =============================================================================

def setup_logging():
    log_file = LOGS_FOLDER / f"linkedin_{datetime.now().strftime('%Y%m%d')}.log"
    
    logger = logging.getLogger("LinkedInWatcher")
    logger.setLevel(logging.INFO)
    logger.handlers = []
    
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
    logger.addHandler(file_handler)
    
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(logging.Formatter("[%(levelname)s] %(message)s"))
    logger.addHandler(console_handler)
    
    return logger

logger = setup_logging()

# =============================================================================
# MESSAGE PROCESSING
# =============================================================================

def load_processed():
    global processed_posts
    if PROCESSED_FILE.exists():
        try:
            with open(PROCESSED_FILE, 'r', encoding='utf-8') as f:
                processed_posts = set(line.strip() for line in f)
            logger.info(f"Loaded {len(processed_posts)} processed posts")
        except:
            pass

def save_processed(post_id: str):
    processed_posts.add(post_id)
    try:
        with open(PROCESSED_FILE, 'a', encoding='utf-8') as f:
            f.write(f"{post_id}\n")
    except:
        pass

def get_priority(content: str) -> str:
    text = content.lower()
    if "urgent" in text or "asap" in text or "budget" in text:
        return "high"
    if "need" in text or "require" in text or "looking for" in text:
        return "medium"
    return "normal"

def create_needs_action_file(post_data: dict, logger) -> Path:
    """CRITICAL: Create file in gold/needs_action/ folder"""
    priority = get_priority(post_data['content'])
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    safe_author = re.sub(r"[^a-zA-Z0-9]", "_", post_data['author'][:20]) or "Unknown"
    filename = f"LINKEDIN_{safe_author}_{timestamp}.md"
    filepath = NEEDS_ACTION_FOLDER / filename
    
    content = f"""---
type: linkedin_lead
from: {post_data['author']}
content: {post_data['content'][:200]}
priority: {priority}
status: pending
created_at: {datetime.now().isoformat()}
source: linkedin
post_url: {post_data['url']}
---

## LinkedIn Post Content

{post_data['content']}

## Metadata

- **Author:** {post_data['author']}
- **Priority:** {priority}
- **Found:** {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
- **URL:** {post_data['url']}

## Suggested Action

Review this lead and consider:
1. Engaging with the post (like/comment)
2. Sending a connection request
3. Creating a targeted response

---
*LinkedIn Watcher - Gold Tier*
"""
    
    with open(filepath, "w", encoding='utf-8') as f:
        f.write(content)
    
    logger.info(f"✓ CREATED: {filename} in needs_action/")
    return filepath

# =============================================================================
# SCANNING
# =============================================================================

def scan_feed(page, logger):
    """Scan LinkedIn feed for sales opportunities."""
    try:
        # Wait for feed to load
        try:
            page.wait_for_selector('[data-id="urn:li:ugc:post"]', timeout=30000)
        except:
            logger.warning("Feed not loaded yet")
            return 0
        
        # Get posts
        posts = page.query_selector_all('[data-id="urn:li:ugc:post"]')
        
        if not posts:
            logger.debug("No posts found")
            return 0
        
        new_tasks = 0
        
        for post in posts[:10]:  # Check first 10 posts
            try:
                # Get post ID
                post_id = post.get_attribute('data-id')
                if not post_id or post_id in processed_posts:
                    continue
                
                # Get author
                author = "Unknown"
                author_elem = post.query_selector('a[href*="/in/"] span[dir="auto"]')
                if author_elem:
                    author = author_elem.inner_text().strip()
                
                # Get content
                content = ""
                content_elem = post.query_selector('div.update-components-text')
                if content_elem:
                    content = content_elem.inner_text().strip()
                
                if not content:
                    continue
                
                # Check keywords
                content_lower = content.lower()
                if any(kw in content_lower for kw in SALES_KEYWORDS):
                    # Get post URL
                    post_url = f"https://www.linkedin.com/feed/update/{post_id}/"
                    
                    post_data = {
                        'id': post_id,
                        'author': author,
                        'content': content,
                        'url': post_url
                    }
                    
                    create_needs_action_file(post_data, logger)
                    save_processed(post_id)
                    new_tasks += 1
                    logger.info(f"📍 Lead found: {author[:30]}...")
                    
            except Exception as e:
                continue
        
        return new_tasks
        
    except Exception as e:
        logger.error(f"Scan error: {e}")
        return 0

# =============================================================================
# MAIN
# =============================================================================

def main():
    logger.info("=" * 70)
    logger.info("LINKEDIN WATCHER - GOLD TIER")
    logger.info("=" * 70)
    logger.info(f"Session: {SESSION_PATH}")
    logger.info(f"Tasks folder: {NEEDS_ACTION_FOLDER}")
    logger.info("=" * 70)
    
    load_processed()
    
    with sync_playwright() as p:
        context = None
        
        try:
            # Launch Chrome
            logger.info("Launching Chrome...")
            context = p.chromium.launch_persistent_context(
                user_data_dir=str(SESSION_PATH),
                headless=False,
                channel="chrome",
                args=[
                    "--disable-gpu",
                    "--no-sandbox",
                    "--window-size=1280,720",
                    "--remote-debugging-port=9222"
                ],
                timeout=60000
            )
            
            logger.info("✓ Chrome launched")
            
            page = context.pages[0] if context.pages else context.new_page()
            
            logger.info(f"Navigating to LinkedIn...")
            page.goto(LINKEDIN_URL, timeout=120000)
            
            logger.info("Waiting for LinkedIn to load (login if needed)...")
            logger.info("⚠️  KEEP BROWSER OPEN - Do not close!")
            
            # Wait for feed
            try:
                page.wait_for_selector('[data-id="urn:li:ugc:post"]', timeout=120000)
                logger.info("✓ LinkedIn feed loaded!")
            except:
                logger.warning("Timeout - please login manually")
            
            logger.info("Starting monitoring loop...")
            consecutive_errors = 0
            
            while True:
                try:
                    new_tasks = scan_feed(page, logger)
                    
                    if new_tasks > 0:
                        consecutive_errors = 0
                        logger.info(f"✓ Found {new_tasks} new lead(s)")
                    else:
                        consecutive_errors += 1
                        if consecutive_errors > 5:
                            logger.info("Still monitoring...")
                            consecutive_errors = 0
                    
                    time.sleep(CHECK_INTERVAL)
                    
                except Exception as e:
                    logger.error(f"Loop error: {e}")
                    consecutive_errors += 1
                    if consecutive_errors > 5:
                        logger.info("Reloading page...")
                        page.reload()
                        consecutive_errors = 0
                    time.sleep(CHECK_INTERVAL)
                    
        except KeyboardInterrupt:
            logger.info("\n👋 Stopping...")
        except Exception as e:
            logger.error(f"Fatal: {e}")
            import traceback
            logger.error(traceback.format_exc())
        finally:
            if context:
                context.close()
                logger.info("Browser closed")

if __name__ == "__main__":
    main()
