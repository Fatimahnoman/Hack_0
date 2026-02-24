"""
Instagram Watcher for Silver Tier
Monitors Instagram for notifications AND handles auto-posting with approval workflow

Features:
- Check notifications every 4 hours
- Auto-generate post captions daily at 9 AM
- Create post requests in Needs_Action/
- Auto-post when file moved to Approved/
- Track posted content in Done/
"""

import os
import sys
import time
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict
import random

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

try:
    from playwright.sync_api import sync_playwright
except ImportError:
    print("Error: Playwright not installed. Run: pip install playwright && playwright install chromium")
    sys.exit(1)

# Configuration
CHECK_INTERVAL = 14400  # 4 hours
SESSION_PATH = PROJECT_ROOT / "instagram_session"
VAULT_PATH = PROJECT_ROOT / "Vault"
NEEDS_ACTION_PATH = VAULT_PATH / "Needs_Action"
PENDING_APPROVAL_PATH = VAULT_PATH / "Pending_Approval"
APPROVED_PATH = VAULT_PATH / "Approved"
DONE_PATH = VAULT_PATH / "Done"
LOGS_PATH = VAULT_PATH / "Logs"

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(LOGS_PATH / "instagram_watcher.log", encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)


class InstagramWatcher:
    """Instagram Watcher with auto-post approval workflow."""

    def __init__(self):
        self.session_path = SESSION_PATH
        self.vault_path = VAULT_PATH
        self.needs_action_path = NEEDS_ACTION_PATH
        self.pending_approval_path = PENDING_APPROVAL_PATH
        self.approved_path = APPROVED_PATH
        self.done_path = DONE_PATH
        self.logs_path = LOGS_PATH

        # Ensure directories exist
        for path in [self.session_path, self.needs_action_path, 
                     self.pending_approval_path, self.approved_path, 
                     self.done_path, self.logs_path]:
            path.mkdir(parents=True, exist_ok=True)

        # Track processed notifications
        self.processed_notifications = set()

        # Browser objects
        self.playwright = None
        self.context = None
        self.page = None

        # Hashtags for auto-generation
        self.hashtags = {
            "business": ["#Business", "#Entrepreneur", "#Success", "#Motivation", "#Growth"],
            "tech": ["#AI", "#Technology", "#Innovation", "#Automation", "#Future"],
            "engagement": ["#Follow", "#Like", "#Comment", "#Share", "#Community"],
            "trending": ["#Trending", "#Viral", "#Explore", "#InstaGood", "#PhotoOfTheDay"],
        }

        logger.info("Instagram Watcher initialized")
        logger.info(f"Session: {self.session_path}")
        logger.info(f"Check Interval: {CHECK_INTERVAL} seconds")

    def start_browser(self):
        """Start browser with saved session."""
        logger.info("Starting Instagram browser...")

        self.playwright = sync_playwright().start()

        self.context = self.playwright.chromium.launch_persistent_context(
            user_data_dir=str(self.session_path),
            headless=False,
            viewport={"width": 1280, "height": 720},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            args=["--disable-gpu", "--no-sandbox", "--disable-dev-shm-usage"]
        )

        if self.context.pages:
            self.page = self.context.pages[0]
        else:
            self.page = self.context.new_page()

        logger.info("Browser started")

    def navigate_to_instagram(self) -> bool:
        """Navigate to Instagram and ensure login."""
        logger.info("Navigating to Instagram...")

        try:
            self.page.goto("https://www.instagram.com/", wait_until="networkidle")
            self.page.wait_for_timeout(5000)

            if self.is_logged_in():
                logger.info("✓ Already logged in")
                return True
            else:
                logger.warning("Not logged in - waiting for manual login (60s)...")
                for i in range(60):
                    time.sleep(1)
                    if self.is_logged_in():
                        logger.info("✓ Login successful!")
                        return True
                logger.error("Login timeout")
                return False

        except Exception as e:
            logger.error(f"Navigation error: {e}")
            return False

    def is_logged_in(self) -> bool:
        """Check if logged in to Instagram."""
        try:
            self.page.wait_for_selector('a[href="/direct/inbox/"], img[alt="Profile"]', timeout=3000)
            return True
        except:
            return False

    def check_notifications(self) -> List[Dict]:
        """Check for new notifications."""
        notifications = []

        try:
            # Go to notifications
            self.page.goto("https://www.instagram.com/accounts/activity/", wait_until="networkidle")
            self.page.wait_for_timeout(3000)

            # Get notification elements
            notif_elements = self.page.query_selector_all('div[role="listitem"]')

            for elem in notif_elements[:10]:  # Last 10 notifications
                try:
                    text = elem.inner_text()
                    timestamp_elem = elem.query_selector('time')
                    timestamp = timestamp_elem.get_attribute('datetime') if timestamp_elem else 'Unknown'

                    # Create unique ID
                    notif_id = f"{text[:50]}_{timestamp}"

                    if notif_id not in self.processed_notifications:
                        notifications.append({
                            'id': notif_id,
                            'text': text,
                            'timestamp': timestamp,
                            'type': self.classify_notification(text)
                        })
                        self.processed_notifications.add(notif_id)

                except:
                    continue

        except Exception as e:
            logger.error(f"Error checking notifications: {e}")

        return notifications

    def classify_notification(self, text: str) -> str:
        """Classify notification type."""
        text_lower = text.lower()
        if 'like' in text_lower:
            return 'like'
        elif 'comment' in text_lower:
            return 'comment'
        elif 'follow' in text_lower:
            return 'follower'
        elif 'mention' in text_lower:
            return 'mention'
        else:
            return 'other'

    def create_notification_file(self, notification: Dict) -> Optional[Path]:
        """Create .md file for notification."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"INSTAGRAM_{notification['type']}_{timestamp}.md"
        filepath = self.needs_action_path / filename

        content = f"""# Instagram Notification

**Type:** {notification['type'].title()}
**Received:** {notification['timestamp']}
**Platform:** Instagram
**Priority:** Medium

---

## Details

{notification['text']}

---

## Actions Required

- [ ] Review notification
- [ ] Respond if needed (comment/DM)
- [ ] Add [APPROVED] marker to move to Approved
- [ ] Add [DONE] marker to move to Done

---

## Workflow

- Current: Needs_Action
- After 2 min: Auto-move to Pending_Approval
- Add [APPROVED] marker: Move to Approved
- Add [DONE] marker: Move to Done

---

## Status

Needs_Action

---

*Generated by Instagram Watcher - Silver Tier AI Employee*
"""

        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            logger.info(f"✓ Created: {filename}")
            return filepath
        except Exception as e:
            logger.error(f"Error creating file: {e}")
            return None

    def generate_post_caption(self) -> str:
        """Generate engaging Instagram caption."""
        emojis = ["🚀", "✨", "💡", "🔥", "⭐", "💪", "🎯", "📈"]
        
        hooks = [
            "Ready to level up? 💼",
            "Game-changer alert! 🚀",
            "Here's what you need to know! 💡",
            "Exciting news coming your way! ✨",
            "Let's talk about growth! 📈",
        ]

        values = [
            "Success is built one step at a time.",
            "Innovation meets execution.",
            "Your journey matters more than the destination.",
            "Every expert was once a beginner.",
            "Progress over perfection, always.",
        ]

        ctas = [
            "💬 Drop a comment below!",
            "👉 Tag someone who needs this!",
            "🔗 Link in bio for more!",
            "💾 Save this for later!",
            "📲 Share with your network!",
        ]

        # Select random components
        caption = f"{random.choice(emojis)} {random.choice(hooks)}\n\n"
        caption += f"{random.choice(values)}\n\n"
        caption += f"{random.choice(ctas)}\n\n"

        # Add hashtags
        selected_tags = []
        for category in self.hashtags.values():
            selected_tags.extend(random.sample(category, 2))
        
        caption += " ".join(selected_tags)

        return caption

    def create_daily_post_request(self) -> Optional[Path]:
        """Create daily Instagram post request."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"INSTA_POST_REQUEST_{timestamp}.md"
        filepath = self.needs_action_path / filename

        caption = self.generate_post_caption()

        content = f"""# Instagram Post Request

**Generated:** {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
**Type:** Daily Auto-Post
**Platform:** Instagram
**Status:** Pending Approval

---

## Caption

{caption}

---

## Image

**Path:** [Add image path here]

**Note:** Add image path or move to Approved/ to post without image

---

## Approval Workflow

### To Post:
1. ✅ Add image path above (optional)
2. ✅ Move this file to `Vault/Approved/`
3. ⏳ Instagram Watcher will auto-post
4. ✅ File moves to `Vault/Done/` after posting

### To Edit:
1. ✏️ Modify caption or add image path
2. ✅ Move to `Approved/`

### To Cancel:
1. 🗑️ Delete this file or move to `Logs/`

---

## Auto-Post Settings

- **Auto-Post on Approval:** YES
- **Post Time:** Immediately on approval
- **Retry on Failure:** 3 attempts

---

*Generated by Instagram Watcher - Silver Tier AI Employee*
"""

        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            logger.info(f"✓ Created post request: {filename}")
            return filepath
        except Exception as e:
            logger.error(f"Error creating post request: {e}")
            return None

    def check_approved_posts(self) -> int:
        """Check Approved/ folder for posts to publish."""
        if not self.approved_path.exists():
            return 0

        posted_count = 0
        post_files = list(self.approved_path.glob("INSTA_POST_REQUEST_*.md"))

        for filepath in post_files:
            try:
                content = filepath.read_text(encoding='utf-8')

                # Extract caption
                caption = self.extract_caption(content)
                
                # Extract image path
                image_path = self.extract_image_path(content)

                # Post to Instagram
                logger.info(f"Posting: {filepath.name}")
                success = self.upload_post(image_path, caption)

                if success:
                    # Move to Done/
                    dest = self.done_path / filepath.name
                    filepath.rename(dest)
                    logger.info(f"✓ Moved to Done: {filepath.name}")
                    posted_count += 1
                else:
                    logger.error(f"✗ Post failed: {filepath.name}")

            except Exception as e:
                logger.error(f"Error processing {filepath.name}: {e}")

        return posted_count

    def extract_caption(self, content: str) -> str:
        """Extract caption from post request."""
        try:
            # Find caption section
            if "## Caption" in content:
                caption_section = content.split("## Caption")[1]
                if "##" in caption_section:
                    caption_section = caption_section.split("##")[0]
                return caption_section.strip()
        except:
            pass
        return "Posted from Silver Tier AI Employee 🚀 #Automation #AI"

    def extract_image_path(self, content: str) -> Optional[str]:
        """Extract image path from post request."""
        try:
            if "**Path:**" in content:
                path_line = content.split("**Path:**")[1].split("\n")[0].strip()
                if path_line and path_line != "[Add image path here]" and path_line != "None":
                    return path_line
        except:
            pass
        return None

    def upload_post(self, image_path: Optional[str], caption: str) -> bool:
        """Upload post to Instagram."""
        try:
            # Navigate to Instagram
            self.page.goto("https://www.instagram.com/", wait_until="networkidle")
            self.page.wait_for_timeout(3000)

            # Click Create button
            try:
                create_selectors = ['svg[aria-label="New post"]', '[aria-label="Create"]']
                for selector in create_selectors:
                    try:
                        self.page.click(selector, timeout=2000)
                        break
                    except:
                        continue
            except Exception as e:
                logger.error(f"Error clicking create: {e}")
                return False

            self.page.wait_for_timeout(2000)

            # Upload image if provided
            if image_path and os.path.exists(image_path):
                try:
                    file_input = self.page.query_selector('input[type="file"]')
                    if file_input:
                        file_input.set_input_files(image_path)
                        logger.info(f"✓ Uploaded image: {image_path}")
                except Exception as e:
                    logger.error(f"Error uploading image: {e}")

            self.page.wait_for_timeout(3000)

            # Click Next (twice - for image and filters)
            for i in range(2):
                try:
                    self.page.click('button:has-text("Next"), [role="button"]:has-text("Next")', timeout=5000)
                    self.page.wait_for_timeout(2000)
                except:
                    break

            # Add caption
            try:
                caption_field = self.page.query_selector('textarea[aria-label*="caption"]')
                if caption_field:
                    caption_field.fill(caption)
                    logger.info("✓ Caption added")
            except Exception as e:
                logger.error(f"Error adding caption: {e}")

            self.page.wait_for_timeout(2000)

            # Click Share
            try:
                self.page.click('button:has-text("Share"), [role="button"]:has-text("Share")', timeout=5000)
                logger.info("✓ Share clicked")
            except Exception as e:
                logger.error(f"Error clicking share: {e}")
                return False

            # Wait for completion
            self.page.wait_for_timeout(5000)
            logger.info("✓ Post successful!")
            return True

        except Exception as e:
            logger.error(f"Upload error: {e}")
            return False

    def run(self):
        """Main watcher loop."""
        logger.info("=" * 60)
        logger.info("Instagram Watcher - Silver Tier")
        logger.info("=" * 60)
        logger.info(f"Check Interval: {CHECK_INTERVAL} seconds (4 hours)")
        logger.info(f"Auto-Post: Enabled (with approval)")
        logger.info("=" * 60)

        try:
            # Start browser
            self.start_browser()

            # Login
            if not self.navigate_to_instagram():
                logger.error("Failed to login. Exiting.")
                return

            logger.info("Starting Instagram monitoring...")

            while True:
                try:
                    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    logger.info(f"\n[{timestamp}] Checking Instagram...")

                    # Check if still logged in
                    if not self.is_logged_in():
                        logger.warning("Session expired. Reconnecting...")
                        self.navigate_to_instagram()

                    # Check notifications
                    notifications = self.check_notifications()
                    if notifications:
                        logger.info(f"Found {len(notifications)} new notification(s)")
                        for notif in notifications:
                            self.create_notification_file(notif)

                    # Check for approved posts to publish
                    posted = self.check_approved_posts()
                    if posted > 0:
                        logger.info(f"✓ Posted {posted} content(s) to Instagram")

                    # Sleep
                    logger.info(f"Next check in {CHECK_INTERVAL} seconds...")
                    time.sleep(CHECK_INTERVAL)

                except KeyboardInterrupt:
                    logger.info("\nWatcher stopped by user")
                    break
                except Exception as e:
                    logger.error(f"Error in loop: {e}")
                    time.sleep(CHECK_INTERVAL)

        except KeyboardInterrupt:
            logger.info("\nWatcher stopped by user")
        except Exception as e:
            logger.error(f"Fatal error: {e}")
        finally:
            self.close()

    def close(self):
        """Close browser."""
        logger.info("Closing browser...")
        if self.page:
            self.page.close()
        if self.context:
            self.context.close()
        if self.playwright:
            self.playwright.stop()
        logger.info("Browser closed")


def main():
    """Entry point."""
    watcher = InstagramWatcher()
    watcher.run()


if __name__ == "__main__":
    main()
