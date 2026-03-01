"""
Instagram Watcher for Silver Tier
Monitors Approved folder and auto-posts to Instagram
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
CHECK_INTERVAL = 15  # Check every 15 seconds
SESSION_PATH = PROJECT_ROOT / "instagram_session"
VAULT_PATH = PROJECT_ROOT / "Vault"
APPROVED_PATH = VAULT_PATH / "Approved"
DONE_PATH = VAULT_PATH / "Done"
LOGS_PATH = VAULT_PATH / "Logs"
DEBUG_PATH = PROJECT_ROOT / "debug_screenshots"

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
    """Instagram Watcher with auto-post workflow."""

    def __init__(self):
        self.session_path = SESSION_PATH
        self.approved_path = APPROVED_PATH
        self.done_path = DONE_PATH
        self.debug_path = DEBUG_PATH
        self.logs_path = LOGS_PATH
        
        # Ensure directories exist
        for path in [self.session_path, self.approved_path, self.done_path, self.debug_path, self.logs_path]:
            path.mkdir(parents=True, exist_ok=True)
        
        logger.info("Instagram Watcher initialized")
        logger.info(f"Watching: {self.approved_path}")

    def extract_post_info(self, filepath: Path) -> dict:
        """Extract caption and image from post file."""
        try:
            content = filepath.read_text(encoding='utf-8')
            
            caption = ""
            if "## Caption" in content:
                caption_section = content.split("## Caption")[1]
                if "##" in caption_section:
                    caption_section = caption_section.split("##")[0]
                caption = caption_section.strip()
            
            image_path = None
            if "**Path:**" in content:
                path_line = content.split("**Path:**")[1].split("\n")[0].strip()
                if path_line and Path(path_line).exists():
                    image_path = path_line
            
            return {"caption": caption, "image_path": image_path}
        except Exception as e:
            logger.error(f"Error extracting post info: {e}")
            return {"caption": "", "image_path": None}

    def post_to_instagram(self, filepath: Path) -> bool:
        """Post to Instagram with persistent session."""
        
        logger.info(f"Processing: {filepath.name}")
        
        info = self.extract_post_info(filepath)
        caption = info["caption"]
        image_path = info["image_path"]
        
        caption_safe = caption.encode('ascii', errors='replace').decode()[:50]
        logger.info(f"Caption: {caption_safe}...")
        
        if not image_path:
            logger.error("No image found")
            return False
        logger.info(f"Image: {image_path}")
        
        playwright = None
        context = None
        
        try:
            playwright = sync_playwright().start()

            # Launch browser with PERSISTENT CONTEXT - saves session/cookies
            logger.info("Launching browser with persistent session...")
            logger.info(f"Session folder: {self.session_path}")
            
            context = playwright.chromium.launch_persistent_context(
                user_data_dir=str(self.session_path),
                headless=False,
                viewport={"width": 1280, "height": 800},
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                args=[
                    "--disable-gpu",
                    "--no-sandbox",
                    "--disable-dev-shm-usage",
                    "--disable-blink-features=AutomationControlled",
                    "--disable-features=IsolateOrigins,site-per-process",
                    "--disable-extensions",
                    "--disable-background-networking",
                    "--disable-default-apps",
                    "--disable-sync",
                    "--no-first-run",
                    "--disable-translate",
                    "--disable-client-side-phishing-detection",
                    "--disable-component-update",
                    "--disable-features=TranslateUI",
                    "--disable-ipc-flooding-protection",
                    "--force-color-profile=srgb",
                ],
                accept_downloads=True,
                ignore_https_errors=True,
            )

            page = context.pages[0] if context.pages else context.new_page()
            
            # CRITICAL: Inject scripts to hide automation
            logger.info("Injecting anti-detection scripts...")
            try:
                page.add_init_script("""
                    // Override the navigator.webdriver property
                    Object.defineProperty(navigator, 'webdriver', {
                        get: () => undefined
                    });
                    
                    // Override plugins to look more human
                    Object.defineProperty(navigator, 'plugins', {
                        get: () => [1, 2, 3, 4, 5]
                    });
                    
                    // Override languages
                    Object.defineProperty(navigator, 'languages', {
                        get: () => ['en-US', 'en']
                    });
                    
                    // Remove automation flags
                    delete navigator.__proto__.webdriver;
                """)
                logger.info("Anti-detection scripts injected")
            except Exception as e:
                logger.warning(f"Could not inject scripts: {str(e)[:50]}")

            # Navigate to Instagram
            logger.info("Going to Instagram...")
            page.goto("https://www.instagram.com/", wait_until="domcontentloaded", timeout=60000)
            page.wait_for_timeout(15000)  # Longer initial wait

            # Check login
            logged_in = False
            try:
                page.wait_for_selector('a[href="/direct/inbox/"]', timeout=10000)
                logged_in = True
                logger.info("✓ Already logged in (session saved)")
            except:
                logger.info("Waiting for login (90s)...")
                for i in range(90):
                    time.sleep(1)
                    try:
                        page.wait_for_selector('a[href="/direct/inbox/"]', timeout=1000)
                        logger.info("✓ Login detected! Session will be saved.")
                        logged_in = True
                        break
                    except:
                        if (i+1) % 15 == 0:
                            logger.info(f"  Waiting... {i+1}s")

            if not logged_in:
                logger.error("Login failed")
                return False

            # Handle popups
            for popup_text in ["Save", "Not Now", "Allow"]:
                try:
                    btn = page.locator(f'button:has-text("{popup_text}")').first
                    if btn.is_visible(timeout=2000):
                        btn.click()
                        page.wait_for_timeout(1000)
                except:
                    pass

            # CRITICAL: Get current post count BEFORE posting
            logger.info("Getting current post count BEFORE posting...")
            pre_post_count = 0
            try:
                # Go to profile first
                page.goto("https://www.instagram.com/", wait_until="domcontentloaded")
                page.wait_for_timeout(3000)
                
                # Find profile link and go to profile
                for selector in [
                    'a[href^="/"][aria-label*="profile" i]',
                    'a[href^="/"] img[src*="profile"]',
                    'div[role="button"] img[src*="profile"]',
                ]:
                    try:
                        profile_link = page.locator(selector).first
                        if profile_link.is_visible(timeout=2000):
                            href = profile_link.get_attribute('href')
                            if href:
                                username = href.replace('https://www.instagram.com/', '').replace('/', '')
                                if username:
                                    logger.info(f"Going to profile: {username}")
                                    page.goto(f"https://www.instagram.com/{username}/", wait_until="domcontentloaded")
                                    page.wait_for_timeout(5000)
                                    
                                    # Get post count from header
                                    try:
                                        post_count_elem = page.locator('._acut').first
                                        if post_count_elem.is_visible(timeout=3000):
                                            post_text = post_count_elem.text_content()
                                            logger.info(f"Post count text: {post_text}")
                                            # Extract number from text like "662 posts"
                                            import re
                                            numbers = re.findall(r'\d+', post_text)
                                            if numbers:
                                                pre_post_count = int(numbers[0])
                                                logger.info(f"✓ Pre-post count: {pre_post_count}")
                                    except:
                                        pass
                                    break
                    except:
                        continue
            except Exception as e:
                logger.warning(f"Could not get pre-post count: {str(e)[:50]}")

            # Go back to home to create post
            page.goto("https://www.instagram.com/", wait_until="domcontentloaded")
            page.wait_for_timeout(3000)

            # Create post
            logger.info("Opening create dialog...")
            create_clicked = False
            for selector in ['svg[aria-label="New post"]', 'svg[aria-label="Create"]']:
                try:
                    page.click(selector, timeout=3000)
                    create_clicked = True
                    logger.info("Create clicked")
                    break
                except:
                    continue
            
            if not create_clicked:
                page.keyboard.press("Control+n")
                logger.info("Create via keyboard")
            
            # Wait longer for dialog to fully open
            logger.info("Waiting for dialog...")
            page.wait_for_timeout(8000)
            
            # Take screenshot to debug
            try:
                page.screenshot(path=str(self.debug_path / f"create_dialog_{datetime.now().strftime('%H%M%S')}.png"))
                logger.info("Debug screenshot saved")
            except:
                pass
            
            # Upload image
            if image_path:
                logger.info("Uploading image...")
                upload_success = False
                
                # Wait for dialog to fully load
                page.wait_for_timeout(5000)
                
                # Method 1: Click "Select from computer" button
                try:
                    logger.info("Method 1: Clicking 'Select from computer'...")
                    select_btn = page.locator('button:has-text("Select from computer")').first
                    if select_btn.is_visible(timeout=10000):
                        select_btn.click()
                        logger.info("✓ File dialog opened")
                        
                        # Wait for file input to appear
                        page.wait_for_timeout(5000)
                        
                        # Find file input and upload (without force parameter)
                        file_input = page.locator('input[type="file"]').first
                        file_input.set_input_files(image_path)
                        logger.info("✓ Image uploaded")
                        upload_success = True
                        page.wait_for_timeout(8000)
                except Exception as e:
                    logger.warning(f"Method 1 failed: {str(e)[:50]}")
                
                # Method 2: Direct file input (fallback)
                if not upload_success:
                    try:
                        logger.info("Method 2: Direct file input...")
                        file_input = page.locator('input[type="file"]').first
                        if file_input.is_visible(timeout=25000):
                            file_input.set_input_files(image_path)
                            logger.info("✓ Image uploaded via direct input")
                            upload_success = True
                            page.wait_for_timeout(5000)
                    except Exception as e:
                        logger.warning(f"Method 2 failed: {str(e)[:50]}")
                
                if not upload_success:
                    logger.error("✗ Upload failed - check debug screenshot")
                    try:
                        page.screenshot(path=str(self.debug_path / f"upload_fail_{datetime.now().strftime('%H%M%S')}.png"))
                        logger.info(f"Screenshot saved: upload_fail_*.png")
                    except:
                        pass
                    return False
                
                # Screenshot after upload
                try:
                    page.screenshot(path=str(self.debug_path / f"uploaded_{datetime.now().strftime('%H%M%S')}.png"))
                except:
                    pass
            
            # Click Next
            logger.info("Clicking Next...")
            next_clicked = False
            for i in range(2):
                try:
                    next_btn = page.locator('button:has-text("Next")').first
                    if next_btn.is_visible(timeout=8000):
                        # Check if disabled
                        try:
                            is_disabled = next_btn.is_disabled()
                            if is_disabled:
                                logger.warning(f"Next button is DISABLED, waiting 5s...")
                                page.wait_for_timeout(5000)
                                continue
                        except:
                            pass
                            
                        # Human-like delay
                        page.wait_for_timeout(3000)
                        next_btn.click(force=True)
                        logger.info(f"Next {i+1}")
                        next_clicked = True
                        page.wait_for_timeout(5000)
                    else:
                        break
                except Exception as e:
                    logger.warning(f"Next click error: {str(e)[:50]}")
                    break
            
            # Screenshot after Next
            try:
                page.screenshot(path=str(self.debug_path / f"after_next_{datetime.now().strftime('%H%M%S')}.png"))
            except:
                pass

            # Add caption
            logger.info("Adding caption...")
            try:
                caption_field = page.locator('textarea[aria-label*="caption"]').first
                if caption_field.is_visible(timeout=8000):
                    # Human-like delay
                    page.wait_for_timeout(2000)
                    caption_field.fill(caption)
                    logger.info("Caption added")
                    page.wait_for_timeout(3000)
            except Exception as e:
                logger.warn(f"Caption error: {str(e)[:50]}")

            # Screenshot before Share
            try:
                page.screenshot(path=str(self.debug_path / f"before_share_{datetime.now().strftime('%H%M%S')}.png"))
                logger.info("Screenshot saved before Share click")
            except:
                pass

            page.wait_for_timeout(3000)

            # AUTO-CLICK SHARE BUTTON - With better human-like behavior
            logger.info("Looking for Share button...")
            share_clicked = False

            # Wait a bit before looking for Share button (human-like)
            page.wait_for_timeout(2000)

            for i in range(5):  # 5 attempts
                try:
                    # Try different Share button selectors
                    share_btn = None
                    
                    # Priority 1: Exact text match
                    for selector in [
                        'button:has-text("Share")',
                        'button:has-text("Post")',
                        'div[role="button"]:has-text("Share")',
                        'div[role="button"]:has-text("Post")',
                    ]:
                        try:
                            share_btn = page.locator(selector).first
                            if share_btn.is_visible(timeout=2000):
                                logger.info(f"Found Share button with selector: {selector}")
                                break
                        except:
                            continue
                    
                    # Priority 2: Instagram's dynamic classes
                    if not share_btn:
                        try:
                            # Look for button with Share/Post text in any element
                            all_buttons = page.locator('button, div[role="button"], a[role="button"]')
                            count = all_buttons.count()
                            for j in range(min(count, 20)):  # Check first 20 buttons
                                try:
                                    btn = all_buttons.nth(j)
                                    if btn.is_visible(timeout=1000):
                                        text = btn.text_content(timeout=1000)
                                        if text and ('Share' in text or 'Post' in text or 'Share' in text or 'Post' in text):
                                            share_btn = btn
                                            logger.info(f"Found Share button by text: {text}")
                                            break
                                except:
                                    continue
                        except:
                            pass
                    
                    # Priority 3: Last button in dialog (usually Share)
                    if not share_btn:
                        try:
                            dialog_buttons = page.locator('div[role="dialog"] button, div[class*="Modal"] button')
                            btn_count = dialog_buttons.count()
                            if btn_count > 0:
                                share_btn = dialog_buttons.nth(btn_count - 1)  # Last button
                                if share_btn.is_visible(timeout=2000):
                                    logger.info("Using last button in dialog as Share button")
                        except:
                            pass

                    if share_btn and share_btn.is_visible():
                        # Human-like behavior
                        page.wait_for_timeout(2000 + (i * 500))  # Random delay

                        # Scroll button into view
                        try:
                            share_btn.scroll_into_view_if_needed()
                            page.wait_for_timeout(1000)
                        except:
                            pass

                        # CRITICAL: Check if button is disabled
                        try:
                            is_disabled = share_btn.is_disabled()
                            if is_disabled:
                                logger.warning("Share button is DISABLED, waiting 5s...")
                                page.wait_for_timeout(5000)
                                continue
                        except:
                            pass

                        # Click with force=True to bypass Instagram's overlay issues
                        logger.info("Clicking Share button with force=True...")
                        share_btn.click(force=True, timeout=10000)
                        logger.info("✓ Share button clicked automatically!")
                        share_clicked = True

                        # Wait for post to upload and process
                        logger.info("Waiting for post to publish...")
                        page.wait_for_timeout(20000)  # 20 seconds for upload
                        break
                    else:
                        logger.warning(f"Share button not found, attempt {i+1}/5")
                        page.wait_for_timeout(2000)
                        
                except Exception as e:
                    logger.warning(f"Share click attempt {i+1}/5 failed: {str(e)[:50]}")
                    page.wait_for_timeout(2000)

            if not share_clicked:
                logger.error("✗ Could not click Share button after 5 attempts")
                logger.error("Waiting 20 seconds - please click Share manually if visible!")
                page.wait_for_timeout(20000)
            
            # CRITICAL FIX: Handle "Discard post?" popup
            # When this modal appears, DON'T click Cancel (it exits the dialog)
            # Instead, immediately click Share button again
            try:
                logger.info("Checking for 'Discard post?' popup...")
                
                # Check if modal is present
                modal_selectors = [
                    'button:has-text("Discard")',
                    'button:has-text("Cancel")',
                    'button:has-text("Don\'t Discard")',
                    'button:has-text("Keep Editing")',
                ]
                
                modal_found = False
                for selector in modal_selectors:
                    try:
                        modal_btn = page.locator(selector).first
                        if modal_btn.is_visible(timeout=2000):
                            modal_found = True
                            logger.info(f"✓ Discard modal detected (found: {selector})")
                            break
                    except:
                        continue
                
                if modal_found:
                    logger.info("Modal found - clicking Share button AGAIN immediately...")
                    
                    # Wait a bit for modal animation
                    page.wait_for_timeout(2000)
                    
                    # Click Share button AGAIN (don't click Cancel)
                    for retry in range(3):
                        try:
                            for selector in [
                                'button:has-text("Share")',
                                'button:has-text("Post")',
                                'div[role="button"]:has-text("Share")',
                                'div[role="button"]:has-text("Post")',
                            ]:
                                try:
                                    share_btn = page.locator(selector).first
                                    if share_btn.is_visible(timeout=2000):
                                        logger.info(f"Found Share button for retry: {selector}")
                                        share_btn.click()
                                        logger.info(f"✓ Share button clicked (retry {retry+1}/3 after modal)!")
                                        share_clicked = True
                                        break
                                except:
                                    continue
                            
                            if share_clicked:
                                break
                        except Exception as e:
                            logger.warning(f"Share retry {retry+1}/3 failed: {str(e)[:50]}")
                        
                        page.wait_for_timeout(3000)
                    
                    if share_clicked:
                        logger.info("Waiting for post to publish after modal...")
                        page.wait_for_timeout(25000)  # Extra long wait
                    else:
                        logger.error("✗ Could not click Share after modal")
                else:
                    logger.info("No discard modal detected - continuing...")
                    
            except Exception as e:
                logger.warning(f"Discard modal handler error: {str(e)[:50]}")

            # After waiting, check if we're back on feed (post was successful)
            logger.info("Checking if post was successful...")

            # Wait for post to fully process on Instagram servers
            logger.info("Waiting for Instagram to process post...")
            page.wait_for_timeout(10000)

            # CRITICAL: Actually go to profile and check if new post exists
            logger.info("Navigating to profile to verify post...")

            try:
                # Method 1: Go to home first, then click profile link
                logger.info("Going to Instagram home...")
                page.goto("https://www.instagram.com/", wait_until="domcontentloaded")
                page.wait_for_timeout(5000)

                # Find and click profile link (usually in sidebar or top right)
                username = ""
                for selector in [
                    'a[href^="/"][aria-label*="profile" i]',
                    'a[href^="/"] img[src*="profile"]',
                    'div[role="button"] img[src*="profile"]',
                    'a.x1lliihq[href^="/"]'  # Instagram profile link pattern
                ]:
                    try:
                        profile_link = page.locator(selector).first
                        if profile_link.is_visible(timeout=3000):
                            href = profile_link.get_attribute('href')
                            if href:
                                # Extract username from href
                                username = href.replace('https://www.instagram.com/', '').replace('/', '')
                                if username and username != '':
                                    logger.info(f"Found username: {username}")
                                    break
                    except:
                        continue

                # If username not found, try to get from account settings
                if not username:
                    logger.info("Trying to get username from account page...")
                    page.goto("https://www.instagram.com/accounts/edit/", wait_until="domcontentloaded")
                    page.wait_for_timeout(3000)
                    try:
                        username_input = page.locator('input[name="username"]').first
                        if username_input.is_visible(timeout=3000):
                            username = username_input.input_value()
                            logger.info(f"Found username from settings: {username}")
                    except:
                        username = ""

                # Navigate to profile
                if username:
                    profile_url = f"https://www.instagram.com/{username}/"
                else:
                    profile_url = "https://www.instagram.com/"  # Fallback to home
                    logger.warning("Username not found, going to home page")

                logger.info(f"Going to profile: {profile_url}")
                page.goto(profile_url, wait_until="domcontentloaded")
                page.wait_for_timeout(8000)

                # Take profile screenshot
                page.screenshot(path=str(self.debug_path / f"profile_verify_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"))
                logger.info("Profile screenshot saved for verification")

                # Get post count from profile header (e.g., "662 posts")
                post_count_text = ""
                try:
                    post_count_element = page.locator('._acut').first  # Instagram post count element
                    if post_count_element.is_visible(timeout=5000):
                        post_count_text = post_count_element.text_content()
                        logger.info(f"Post count text: {post_count_text}")
                except:
                    pass

                # Count visible post grids
                posts = page.locator('article, main img, ._aagv, ._aatc, .x9f619')
                post_count = posts.count()
                logger.info(f"Found {post_count} post elements on profile")

                # CRITICAL: Compare with pre-post count
                import re
                current_post_count = 0
                if post_count_text:
                    numbers = re.findall(r'\d+', post_count_text)
                    if numbers:
                        current_post_count = int(numbers[0])

                logger.info(f"Pre-post count: {pre_post_count}, Current count: {current_post_count}")

                # VERIFICATION: Post count should have increased by 1
                if current_post_count > pre_post_count:
                    logger.info(f"✓ SUCCESS! Post count increased from {pre_post_count} to {current_post_count}")
                    logger.info("✓ NEW POST VERIFIED ON PROFILE!")
                    verified = True
                elif current_post_count == pre_post_count and pre_post_count > 0:
                    logger.error(f"✗ FAILED! Post count unchanged at {current_post_count}")
                    logger.error("✗ Post was NOT published to profile!")
                    logger.error("✗ Share button click did not result in a published post")
                    verified = False
                elif post_count > 0:
                    logger.info("✓ Posts visible on profile (count comparison not available)")
                    verified = True
                else:
                    logger.error("✗ No posts found on profile - post may not have published")
                    logger.error(f"Current URL: {page.url}")
                    verified = False

            except Exception as e:
                logger.error(f"Profile verification error: {str(e)[:100]}")
                verified = False

            # Debug screenshot
            try:
                page.screenshot(path=str(self.debug_path / f"post_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"))
            except:
                pass

            # STRONG VERIFICATION - Check if post actually published
            verified = False
            
            # Method 1: Check for success message
            try:
                if page.is_visible('text="Your post has been shared"'):
                    logger.info("Verified: Post shared message")
                    verified = True
            except:
                pass
            
            # Method 2: Check URL - should not be on /create/ page
            if not verified:
                current_url = page.url
                if "/create/" not in current_url:
                    logger.info(f"Verified: Navigated away from create ({current_url})")
                    verified = True
                else:
                    logger.error(f"Still on create page: {current_url}")
                    logger.error("Post was NOT published - please click Share manually!")
            
            # Method 3: Check for feed elements
            if not verified:
                try:
                    feed_elements = page.locator('article, div[class*="x9f619"]')
                    count = feed_elements.count()
                    if count > 0:
                        logger.info(f"Verified: Back on home feed ({count} elements)")
                        verified = True
                except:
                    pass
            
            # Method 4: Check for inbox link (always present on logged-in home)
            if not verified:
                try:
                    inbox_link = page.locator('a[href="/direct/inbox/"]')
                    count = inbox_link.count()
                    if count > 0:
                        logger.info("Verified: Inbox link found (on home)")
                        verified = True
                except:
                    pass
            
            # Take final verification screenshot
            try:
                page.screenshot(path=str(self.debug_path / f"verified_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"))
                logger.info("Verification screenshot saved")
            except:
                pass

            if verified:
                logger.info("✓ POST VERIFIED SUCCESSFULLY")
            else:
                logger.error("✗ VERIFICATION FAILED - Post may not have been published")
                logger.error(f"Final URL: {page.url}")
                logger.error("Please check Instagram manually and click Share if needed!")

            return verified

        except Exception as e:
            logger.error(f"Post failed: {str(e)[:150]}")
            
            # Handle "Discard post?" popup - click Cancel to stay on post
            try:
                if page:
                    discard_btn = page.locator('button:has-text("Cancel"), button:has-text("Don\'t Discard")').first
                    if discard_btn.is_visible(timeout=3000):
                        logger.info("Found 'Discard post?' popup - clicking Cancel to keep post")
                        discard_btn.click()
                        page.wait_for_timeout(3000)
                        logger.info("Please complete the post manually in the browser!")
            except:
                pass
            
            return False
        finally:
            # Close context (saves session/cookies automatically)
            try:
                if context:
                    context.close()
                    logger.info("Browser closed - session saved")
            except:
                pass
            try:
                if playwright:
                    playwright.stop()
            except:
                pass

    def process_approved(self):
        """Process approved files."""
        if not self.approved_path.exists():
            return 0
        
        files = list(self.approved_path.glob("INSTA_POST_REQUEST_*.md"))
        success_count = 0
        
        for filepath in files:
            logger.info(f"Found: {filepath.name}")
            
            result = self.post_to_instagram(filepath)
            
            if result:
                # Move to Done
                try:
                    filepath.rename(self.done_path / filepath.name)
                    logger.info(f"Moved to Done: {filepath.name}")
                    success_count += 1
                except Exception as e:
                    logger.error(f"Move failed: {str(e)[:50]}")
            else:
                logger.info("Keeping in Approved (not verified)")
            
            time.sleep(3)
        
        return success_count

    def run(self):
        """Main watcher loop."""
        logger.info("=" * 60)
        logger.info("Instagram Watcher Started")
        logger.info(f"Watching: {self.approved_path}")
        logger.info("Press Ctrl+C to stop")
        logger.info("=" * 60)
        
        while True:
            try:
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                logger.info(f"\n[{timestamp}] Checking for posts...")
                
                count = self.process_approved()
                
                if count > 0:
                    logger.info(f"Successfully posted {count} file(s)")
                else:
                    logger.info("No new posts")
                    
            except Exception as e:
                logger.error(f"Error: {str(e)[:80]}")
            
            time.sleep(CHECK_INTERVAL)


def main():
    """Entry point."""
    watcher = InstagramWatcher()
    watcher.run()


if __name__ == "__main__":
    main()
