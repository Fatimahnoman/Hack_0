"""
Instagram Watcher for Silver Tier
Checks for Instagram post requests and posts via MCP server

Features:
- Checks every 4 hours (14400 seconds)
- Reads Vault/Needs_Action/INSTA_POST_REQUEST.md
- Calls MCP tool post_to_instagram()
- On success → moves file to Vault/Done/
- Updates Vault/Dashboard.md
"""

import os
import sys
import time
import logging
import shutil
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Configuration
CHECK_INTERVAL = 14400  # 4 hours in seconds
VAULT_PATH = PROJECT_ROOT / "Vault"
NEEDS_ACTION_PATH = VAULT_PATH / "Needs_Action"
DONE_PATH = VAULT_PATH / "Done"
LOGS_PATH = VAULT_PATH / "Logs"
DASHBOARD_PATH = VAULT_PATH / "Dashboard.md"
MCP_SERVER_SCRIPT = PROJECT_ROOT / "mcp_servers" / "actions_mcp" / "server.py"

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
    """Instagram watcher that processes post requests."""
    
    def __init__(self):
        self.vault_path = VAULT_PATH
        self.needs_action_path = NEEDS_ACTION_PATH
        self.done_path = DONE_PATH
        self.logs_path = LOGS_PATH
        self.dashboard_path = DASHBOARD_PATH
        
        # Ensure directories exist
        self.needs_action_path.mkdir(parents=True, exist_ok=True)
        self.done_path.mkdir(parents=True, exist_ok=True)
        self.logs_path.mkdir(parents=True, exist_ok=True)
        
        logger.info("Instagram Watcher initialized")
        logger.info(f"Check Interval: {CHECK_INTERVAL} seconds ({CHECK_INTERVAL/3600} hours)")
        logger.info(f"Needs Action Path: {self.needs_action_path}")
    
    def check_post_request(self) -> Optional[Path]:
        """Check if INSTA_POST_REQUEST.md exists."""
        request_file = self.needs_action_path / "INSTA_POST_REQUEST.md"
        
        if request_file.exists():
            logger.info(f"Found post request: {request_file}")
            return request_file
        
        return None
    
    def parse_request_file(self, filepath: Path) -> Dict:
        """Parse the request file and extract caption, image_path, etc."""
        data = {
            "caption": "",
            "image_path": None,
            "status": "pending",
            "raw_content": ""
        }
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
                data["raw_content"] = content
            
            # Parse caption
            if "caption:" in content:
                for line in content.split('\n'):
                    if line.startswith('caption:'):
                        # Extract caption value
                        caption = line.split('caption:', 1)[1].strip().strip('"\'')
                        data["caption"] = caption
                        break
            
            # Parse image_path
            if "image_path:" in content:
                for line in content.split('\n'):
                    if line.startswith('image_path:'):
                        value = line.split('image_path:', 1)[1].strip().strip('"\'')
                        if value and value.lower() not in ['none', 'null', '']:
                            data["image_path"] = value
                        break
            
            # Parse status
            if "status:" in content:
                for line in content.split('\n'):
                    if line.startswith('status:'):
                        data["status"] = line.split('status:', 1)[1].strip()
                        break
            
            logger.info(f"Parsed request - Caption: {data['caption'][:50]}...")
            logger.info(f"Image Path: {data['image_path']}")
            logger.info(f"Status: {data['status']}")
            
        except Exception as e:
            logger.error(f"Error parsing request file: {e}")
        
        return data
    
    def call_mcp_post_tool(self, caption: str, image_path: Optional[str] = None) -> bool:
        """Call MCP server's post_to_instagram tool."""
        logger.info("Calling MCP tool: post_to_instagram")
        
        try:
            # Import MCP server module
            from mcp_servers.actions_mcp.server import post_to_instagram
            import asyncio
            
            # Run async function
            async def post():
                result = await post_to_instagram(caption=caption, image_path=image_path)
                return result
            
            result = asyncio.run(post())
            
            logger.info(f"MCP tool result: {result}")
            
            # Check for success indicators
            if "✓" in result or "success" in result.lower():
                logger.info("✓ Instagram post successful!")
                return True
            else:
                logger.warning(f"Post may have failed: {result}")
                return False
                
        except ImportError as e:
            logger.error(f"MCP server not available: {e}")
            logger.info("Attempting alternative: direct Playwright post")
            return self.post_via_playwright(caption, image_path)
        except Exception as e:
            logger.error(f"Error calling MCP tool: {e}")
            return False
    
    def post_via_playwright(self, caption: str, image_path: Optional[str] = None) -> bool:
        """Fallback: Post directly using Playwright."""
        logger.info("Using direct Playwright method")
        
        try:
            from playwright.sync_api import sync_playwright
            
            # Load Instagram credentials from .env
            env_path = PROJECT_ROOT / ".env"
            username = ""
            password = ""
            
            if env_path.exists():
                with open(env_path, 'r', encoding='utf-8') as f:
                    for line in f:
                        if line.startswith('INSTAGRAM_USERNAME='):
                            username = line.split('=', 1)[1].strip()
                        elif line.startswith('INSTAGRAM_PASSWORD='):
                            password = line.split('=', 1)[1].strip()
            
            if not username or not password:
                logger.error("Instagram credentials not found in .env")
                return False
            
            session_path = PROJECT_ROOT / "sessions" / "instagram_session"
            session_path.mkdir(parents=True, exist_ok=True)
            
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                context = browser.new_context(
                    viewport={"width": 1920, "height": 1080},
                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
                )
                page = context.new_page()
                
                # Navigate to Instagram
                page.goto("https://www.instagram.com/", wait_until="networkidle")
                page.wait_for_timeout(3000)
                
                # Login if needed
                try:
                    page.wait_for_selector('svg[aria-label="Home"]', timeout=5000)
                    logger.info("Already logged in")
                except:
                    logger.info("Logging in...")
                    page.fill('input[name="username"]', username)
                    page.fill('input[name="password"]', password)
                    page.click('button[type="submit"]')
                    page.wait_for_selector('svg[aria-label="Home"]', timeout=15000)
                
                # Handle popups
                try:
                    page.click('button:has-text("Not Now")', timeout=3000)
                except:
                    pass
                
                # Create post
                logger.info("Creating post...")
                
                try:
                    page.click('svg[aria-label="New post"]')
                except:
                    page.keyboard.press('Control+N')
                
                page.wait_for_timeout(3000)
                
                # Upload image if provided
                if image_path and os.path.exists(image_path):
                    file_input = page.query_selector('input[type="file"]')
                    if file_input:
                        file_input.set_input_files(image_path)
                        page.wait_for_timeout(4000)
                        
                        # Click Next
                        try:
                            page.click('button:has-text("Next")')
                            page.wait_for_timeout(2000)
                            page.click('button:has-text("Next")')
                            page.wait_for_timeout(2000)
                        except:
                            pass
                
                # Add caption
                caption_field = page.query_selector('textarea[aria-label*="caption"]')
                if caption_field:
                    caption_field.fill(caption)
                    page.wait_for_timeout(1000)
                
                # Share
                try:
                    page.click('button:has-text("Share")')
                    page.wait_for_timeout(4000)
                    logger.info("✓ Post published!")
                    success = True
                except Exception as e:
                    logger.error(f"Error sharing: {e}")
                    success = False
                
                browser.close()
                return success
                
        except Exception as e:
            logger.error(f"Playwright post error: {e}")
            return False
    
    def move_to_done(self, filepath: Path) -> bool:
        """Move processed file to Vault/Done/"""
        try:
            dest = self.done_path / filepath.name
            shutil.move(str(filepath), str(dest))
            logger.info(f"✓ Moved to Done: {filepath.name}")
            return True
        except Exception as e:
            logger.error(f"Error moving file: {e}")
            return False
    
    def update_dashboard(self, success: bool, caption: str) -> None:
        """Update Dashboard.md with latest post status."""
        try:
            if not self.dashboard_path.exists():
                logger.warning("Dashboard.md not found")
                return
            
            with open(self.dashboard_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Add Instagram post log
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            status = "✓ Posted" if success else "✗ Failed"
            
            log_entry = f"""
## Instagram Post - {timestamp}
- Status: {status}
- Caption: {caption[:100]}...
"""
            
            # Find or create Instagram section
            if "## Instagram Posts" not in content:
                content += f"\n## Instagram Posts\n{log_entry}\n"
            else:
                # Add after Instagram Posts header
                content = content.replace("## Instagram Posts", f"## Instagram Posts\n{log_entry}", 1)
            
            with open(self.dashboard_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            logger.info("✓ Dashboard updated")
            
        except Exception as e:
            logger.error(f"Error updating dashboard: {e}")
    
    def process_post_request(self, filepath: Path) -> bool:
        """Process a single post request."""
        logger.info("=" * 50)
        logger.info("Processing Instagram post request")
        logger.info("=" * 50)
        
        # Parse request
        data = self.parse_request_file(filepath)
        
        if not data["caption"]:
            logger.error("No caption found in request")
            return False
        
        # Post to Instagram
        success = self.call_mcp_post_tool(
            caption=data["caption"],
            image_path=data["image_path"]
        )
        
        # Update dashboard
        self.update_dashboard(success, data["caption"])
        
        # Move file
        if success:
            self.move_to_done(filepath)
        else:
            logger.warning("Post failed, file remains in Needs_Action")
        
        return success
    
    def run(self):
        """Main watcher loop."""
        logger.info("=" * 60)
        logger.info("Instagram Watcher - Silver Tier")
        logger.info("=" * 60)
        logger.info(f"Check Interval: {CHECK_INTERVAL} seconds ({CHECK_INTERVAL/3600} hours)")
        logger.info(f"Vault Path: {self.vault_path}")
        logger.info("=" * 60)
        
        while True:
            try:
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                logger.info(f"\n[{timestamp}] Checking for post requests...")
                
                # Check for request file
                request_file = self.check_post_request()
                
                if request_file:
                    # Process the request
                    success = self.process_post_request(request_file)
                    
                    if success:
                        logger.info("✓ Post request completed successfully!")
                    else:
                        logger.warning("Post request failed, will retry next cycle")
                else:
                    logger.info("No post requests found")
                
                logger.info(f"Next check in {CHECK_INTERVAL} seconds ({CHECK_INTERVAL/3600} hours)")
                time.sleep(CHECK_INTERVAL)
                
            except KeyboardInterrupt:
                logger.info("\nWatcher stopped by user")
                break
            except Exception as e:
                logger.error(f"Error in loop: {e}")
                time.sleep(CHECK_INTERVAL)


def main():
    """Entry point."""
    watcher = InstagramWatcher()
    watcher.run()


if __name__ == "__main__":
    main()
