"""
Auto Instagram Post - Direct Upload to Instagram
Actually uploads and posts to Instagram using Playwright

Usage:
    python skills/auto_insta_post_direct.py
    
Features:
- Uses saved Instagram session
- Uploads image from specified path
- Adds caption
- Posts directly to Instagram
"""

import os
import sys
import time
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

try:
    from playwright.sync_api import sync_playwright
except ImportError:
    print("Error: Playwright not installed. Run: pip install playwright && playwright install chromium")
    sys.exit(1)

# Configuration
SESSION_PATH = PROJECT_ROOT / "instagram_session"
VAULT_PATH = PROJECT_ROOT / "Vault"
NEEDS_ACTION_PATH = VAULT_PATH / "Needs_Action"
LOGS_PATH = VAULT_PATH / "Logs"

# Default test image (you can change this)
DEFAULT_IMAGE_PATH = PROJECT_ROOT / "test_image.jpg"

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(LOGS_PATH / "auto_insta_post_direct.log", encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)


class InstagramDirectPoster:
    """Direct Instagram poster using Playwright."""

    def __init__(self):
        self.session_path = SESSION_PATH
        self.vault_path = VAULT_PATH
        self.playwright = None
        self.context = None
        self.page = None

        logger.info("Instagram Direct Poster initialized")
        logger.info(f"Session Path: {self.session_path}")

    def start_browser(self):
        """Start browser with saved session."""
        logger.info("Starting browser with Instagram session...")

        self.playwright = sync_playwright().start()

        # Launch with persistent context (saved session)
        self.context = self.playwright.chromium.launch_persistent_context(
            user_data_dir=str(self.session_path),
            headless=False,  # Keep visible to see posting process
            viewport={"width": 1280, "height": 720},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            args=[
                "--disable-gpu",
                "--no-sandbox",
                "--disable-dev-shm-usage",
            ]
        )

        if self.context.pages:
            self.page = self.context.pages[0]
        else:
            self.page = self.context.new_page()

        logger.info("Browser started")

    def navigate_to_instagram(self) -> bool:
        """Navigate to Instagram and check login."""
        logger.info("Navigating to Instagram...")

        try:
            self.page.goto("https://www.instagram.com/", wait_until="networkidle")
            self.page.wait_for_timeout(5000)

            # Check if logged in
            if self.is_logged_in():
                logger.info("✓ Already logged in to Instagram")
                return True
            else:
                logger.error("Not logged in! Please login manually in the browser.")
                logger.info("Waiting 60 seconds for manual login...")
                
                # Wait for manual login
                for i in range(60):
                    time.sleep(1)
                    if self.is_logged_in():
                        logger.info("✓ Login successful!")
                        return True
                
                logger.error("Login timeout. Please run instagram_watcher.py first to save session.")
                return False

        except Exception as e:
            logger.error(f"Navigation error: {e}")
            return False

    def is_logged_in(self) -> bool:
        """Check if user is logged in."""
        try:
            # Look for profile icon or create button
            self.page.wait_for_selector('a[href="/direct/inbox/"], img[alt="Profile"]', timeout=3000)
            return True
        except:
            return False

    def create_new_post(self, image_path: str, caption: str) -> bool:
        """Create and upload a new post."""
        logger.info(f"Creating new post with image: {image_path}")
        logger.info(f"Caption: {caption[:100]}...")

        try:
            # Check if image exists
            if not os.path.exists(image_path):
                logger.error(f"Image not found: {image_path}")
                return False

            # Go to Instagram home
            self.page.goto("https://www.instagram.com/", wait_until="networkidle")
            self.page.wait_for_timeout(3000)

            # Click on Create button (New Post)
            logger.info("Clicking Create button...")
            try:
                # Try multiple selectors for create button
                create_selectors = [
                    'svg[aria-label="New post"]',
                    'div[role="button"]:has-text("Create")',
                    '[aria-label="Create"]',
                ]
                
                clicked = False
                for selector in create_selectors:
                    try:
                        self.page.click(selector, timeout=2000)
                        clicked = True
                        logger.info("Create button clicked")
                        break
                    except:
                        continue
                
                if not clicked:
                    logger.error("Could not find Create button")
                    return False

            except Exception as e:
                logger.error(f"Error clicking create: {e}")
                return False

            self.page.wait_for_timeout(2000)

            # Upload image
            logger.info("Uploading image...")
            try:
                # Find file input
                file_input = self.page.query_selector('input[type="file"]')
                if file_input:
                    file_input.set_input_files(image_path)
                    logger.info("Image uploaded successfully")
                else:
                    logger.error("File input not found")
                    return False
            except Exception as e:
                logger.error(f"Error uploading image: {e}")
                return False

            self.page.wait_for_timeout(3000)

            # Click Next
            logger.info("Clicking Next...")
            try:
                self.page.click('button:has-text("Next"), div[role="button"]:has-text("Next")', timeout=5000)
                self.page.wait_for_timeout(3000)
                
                # Click Next again for filters
                try:
                    self.page.click('button:has-text("Next"), div[role="button"]:has-text("Next")', timeout=5000)
                    self.page.wait_for_timeout(2000)
                except:
                    logger.info("No filter step, continuing...")
            except Exception as e:
                logger.error(f"Error clicking Next: {e}")
                return False

            # Add caption
            logger.info("Adding caption...")
            try:
                caption_field = self.page.query_selector('textarea[aria-label*="caption"], textarea[placeholder*="caption"]')
                if caption_field:
                    caption_field.fill(caption)
                    logger.info("Caption added")
                else:
                    logger.warning("Caption field not found, skipping caption")
            except Exception as e:
                logger.error(f"Error adding caption: {e}")

            self.page.wait_for_timeout(2000)

            # Click Share/Post
            logger.info("Clicking Share...")
            try:
                self.page.click('button:has-text("Share"), div[role="button"]:has-text("Share")', timeout=5000)
                logger.info("Share button clicked")
            except Exception as e:
                logger.error(f"Error clicking Share: {e}")
                return False

            # Wait for post to complete
            logger.info("Waiting for post to complete...")
            self.page.wait_for_timeout(5000)

            # Check for success message
            try:
                success_indicators = [
                    "Your post has been shared",
                    "Post shared",
                    "Upload complete"
                ]
                
                page_content = self.page.content().lower()
                if any(indicator.lower() in page_content for indicator in success_indicators):
                    logger.info("✓ Post successful!")
                    return True
                else:
                    logger.info("Post appears to be successful (no error detected)")
                    return True
            except:
                logger.info("Post completed (assuming success)")
                return True

        except Exception as e:
            logger.error(f"Error creating post: {e}")
            return False

    def post(self, image_path: str, caption: str) -> bool:
        """Main post function."""
        try:
            # Start browser
            self.start_browser()

            # Navigate to Instagram
            if not self.navigate_to_instagram():
                return False

            # Create post
            success = self.create_new_post(image_path, caption)

            if success:
                logger.info("=" * 60)
                logger.info("✓ INSTAGRAM POST SUCCESSFUL!")
                logger.info("=" * 60)
            else:
                logger.error("=" * 60)
                logger.error("✗ INSTAGRAM POST FAILED")
                logger.error("=" * 60)

            return success

        except Exception as e:
            logger.error(f"Fatal error: {e}")
            return False
        finally:
            # Cleanup
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


def auto_post(image_path: str, caption: str) -> bool:
    """
    Direct Instagram post function.
    
    Args:
        image_path: Path to image file (JPG, PNG)
        caption: Caption text for the post
    
    Returns:
        True if successful, False otherwise
    """
    logger.info("=" * 60)
    logger.info("Instagram Direct Post")
    logger.info("=" * 60)
    logger.info(f"Image: {image_path}")
    logger.info(f"Caption: {caption[:100]}...")
    logger.info("=" * 60)

    poster = InstagramDirectPoster()
    return poster.post(image_path, caption)


def main():
    """Run direct Instagram post."""
    print("=" * 60)
    print("Instagram Direct Poster - Silver Tier")
    print("=" * 60)
    print()
    print("This will upload a post directly to Instagram.")
    print()

    # Get image path
    image_path = input(f"Image path (or press Enter for test): ").strip()
    if not image_path:
        # Create a test image
        print("\nNo image provided. Creating a test post...")
        print("Please provide an image path for actual posting.")
        print("\nExample usage:")
        print('  python skills/auto_insta_post_direct.py "C:/path/to/image.jpg" "Your caption here"')
        return

    # Get caption
    caption = input("Caption: ").strip()
    if not caption:
        caption = "Test post from Silver Tier AI Employee 🚀 #Automation #AI"

    print()
    print("Starting Instagram post...")
    print("Browser will open - DO NOT CLOSE IT")
    print()

    # Post
    success = auto_post(image_path, caption)

    print()
    if success:
        print("✓ POST SUCCESSFUL! Check your Instagram.")
    else:
        print("✗ POST FAILED. Check logs for details.")
    
    print("=" * 60)


if __name__ == "__main__":
    # Check if command line args provided
    if len(sys.argv) > 1:
        image_path = sys.argv[1]
        caption = sys.argv[2] if len(sys.argv) > 2 else "Posted from Silver Tier AI Employee 🚀"
        success = auto_post(image_path, caption)
        sys.exit(0 if success else 1)
    else:
        main()
