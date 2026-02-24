"""
WhatsApp Watcher for Silver Tier
Monitors WhatsApp Web for new messages and creates task files in Vault/Needs_Action/

Features:
- Persistent session from sessions/whatsapp_session/
- Checks every 60 seconds
- Keyword detection: invoice, payment, urgent, price, quote, hello, asap, help
- Auto-priority assignment (high for keyword matches)
- Creates .md files in Vault/Needs_Action/
"""

import os
import sys
import time
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Set

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

try:
    from playwright.sync_api import sync_playwright, Page, Browser, BrowserContext
except ImportError:
    print("Error: Playwright not installed. Run: pip install playwright && playwright install chromium")
    sys.exit(1)

# Configuration
CHECK_INTERVAL = 60  # seconds
SESSION_PATH = PROJECT_ROOT / "sessions" / "whatsapp_session"
VAULT_PATH = PROJECT_ROOT / "Vault"
NEEDS_ACTION_PATH = VAULT_PATH / "Needs_Action"
LOGS_PATH = VAULT_PATH / "Logs"

# Keywords to detect (case-insensitive)
KEYWORDS = {
    "high": ["invoice", "payment", "urgent", "asap", "help"],
    "medium": ["price", "quote", "hello", "hi", "hey"],
}

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(LOGS_PATH / "whatsapp_watcher.log", encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)


class WhatsAppWatcher:
    """WhatsApp Web watcher using Playwright persistent context."""
    
    def __init__(self):
        self.project_root = PROJECT_ROOT
        self.session_path = SESSION_PATH
        self.vault_path = VAULT_PATH
        self.needs_action_path = NEEDS_ACTION_PATH
        self.logs_path = LOGS_PATH
        
        # Ensure directories exist
        self.session_path.mkdir(parents=True, exist_ok=True)
        self.needs_action_path.mkdir(parents=True, exist_ok=True)
        self.logs_path.mkdir(parents=True, exist_ok=True)
        
        # Track processed messages to avoid duplicates
        self.processed_messages: Set[str] = set()
        
        # Browser objects
        self.playwright = None
        self.browser = None
        self.context = None
        self.page = None
        
        logger.info(f"WhatsApp Watcher initialized")
        logger.info(f"Session Path: {self.session_path}")
        logger.info(f"Output Path: {self.needs_action_path}")
    
    def start_browser(self) -> None:
        """Start Playwright with persistent context."""
        logger.info("Starting Playwright browser...")

        self.playwright = sync_playwright().start()

        # Launch browser with persistent context using launch_persistent_context
        # headless=False zaroori hai QR code login ke liye
        self.context = self.playwright.chromium.launch_persistent_context(
            user_data_dir=str(self.session_path),
            headless=False,  # Keep visible for QR code login (required for first time)
            viewport={"width": 1280, "height": 720},  # Smaller window
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            args=[
                "--disable-gpu",
                "--no-sandbox",
                "--disable-dev-shm-usage",
                "--disable-features=TranslateUI",
                "--disable-features=ChromeWhatsNewUI",
            ]
        )

        # Get the browser instance from context
        self.browser = self.context.browser

        # Get the first page or create a new one
        if self.context.pages:
            self.page = self.context.pages[0]
        else:
            self.page = self.context.new_page()
        
        logger.info("Browser started successfully (minimized after login)")
    
    def navigate_to_whatsapp(self) -> bool:
        """Navigate to WhatsApp Web and ensure login."""
        logger.info("Navigating to WhatsApp Web...")

        try:
            # Navigate to WhatsApp Web
            self.page.goto("https://web.whatsapp.com/", wait_until="domcontentloaded", timeout=60000)
            
            # Wait for page to fully load
            self.page.wait_for_timeout(5000)
            
            # Take screenshot for debugging
            try:
                self.page.screenshot(path=str(self.session_path / "debug_whatsapp.png"))
                logger.info("Debug screenshot saved to session folder")
            except:
                pass

            # Check if already logged in
            if self.is_logged_in():
                logger.info("✓ Already logged in to WhatsApp")
                return True

            # Wait for QR code to appear
            logger.info("Waiting for QR code to load...")
            try:
                # Wait for QR code element
                self.page.wait_for_selector('[data-testid="qr-code"]', timeout=10000)
                logger.info("QR code loaded successfully!")
            except:
                logger.info("QR code element not found, but continuing...")

            # Wait for QR code login
            logger.info("Waiting for QR code login (120 seconds max)...")
            logger.info("Scan QR code with WhatsApp on your phone:")
            logger.info("1. Open WhatsApp on phone")
            logger.info("2. Settings > Linked Devices")
            logger.info("3. Tap 'Link a Device'")
            logger.info("4. Scan the QR code in browser")

            try:
                # Wait for main chat pane (logged in indicator)
                self.page.wait_for_selector('div[role="main"]', timeout=120000)
                logger.info("✓ WhatsApp login successful!")
                
                # Save session
                self.page.wait_for_timeout(3000)
                return True
            except Exception as e:
                logger.warning(f"QR login timeout: {e}")
                logger.warning("You can manually login in the browser window")
                return False

        except Exception as e:
            logger.error(f"Navigation error: {e}")
            return False
    
    def is_logged_in(self) -> bool:
        """Check if WhatsApp Web is logged in."""
        try:
            # Look for main chat pane or chat list
            self.page.wait_for_selector('div[role="main"], div[data-testid="chat-list"]', timeout=3000)
            return True
        except:
            return False
    
    def get_unread_chats(self) -> List[Dict]:
        """Get list of chats with unread messages."""
        unread_chats = []
        
        try:
            # Find all chat rows
            chat_rows = self.page.query_selector_all('div[role="row"]')
            
            for row in chat_rows:
                try:
                    # Check for unread indicator
                    unread_badge = row.query_selector('span[aria-label*="unread"], h4[aria-label*="unread"]')
                    
                    if unread_badge:
                        # Get contact/group name
                        contact_elem = row.query_selector('span[title], div[title]')
                        contact = contact_elem.get_attribute("title") if contact_elem else "Unknown"
                        
                        # Get unread count
                        unread_label = unread_badge.get_attribute("aria-label")
                        
                        # Get last message preview
                        message_elem = row.query_selector('span[dir="auto"]')
                        last_message = message_elem.inner_text() if message_elem else ""
                        
                        unread_chats.append({
                            "contact": contact,
                            "unread_count": unread_label,
                            "last_message": last_message,
                        })
                        
                except Exception as e:
                    continue
                    
        except Exception as e:
            logger.error(f"Error getting unread chats: {e}")
        
        return unread_chats
    
    def open_chat_and_get_messages(self, contact: str) -> List[Dict]:
        """Open a specific chat and extract recent messages."""
        messages = []
        
        try:
            # Click on the chat
            chat_selector = f'span[title="{contact}"]'
            self.page.click(chat_selector)
            self.page.wait_for_timeout(2000)
            
            # Get all message elements
            message_elements = self.page.query_selector_all('div[data-testid="chat-message"]')
            
            for msg_elem in message_elements[-10:]:  # Last 10 messages
                try:
                    # Get message text
                    text_elem = msg_elem.query_selector('span[dir="auto"]')
                    text = text_elem.inner_text() if text_elem else ""
                    
                    # Get sender (for groups)
                    sender_elem = msg_elem.query_selector('span[dir="auto"][dir="auto"]')
                    sender = sender_elem.inner_text() if sender_elem else contact
                    
                    # Get timestamp
                    time_elem = msg_elem.query_selector('span[dir="auto"] + span')
                    timestamp = time_elem.inner_text() if time_elem else datetime.now().strftime("%H:%M")
                    
                    if text:  # Only non-empty messages
                        messages.append({
                            "sender": sender,
                            "text": text,
                            "time": timestamp,
                        })
                except:
                    continue
                    
        except Exception as e:
            logger.error(f"Error getting messages from {contact}: {e}")
        
        return messages
    
    def check_keywords(self, text: str) -> tuple[str, List[str]]:
        """Check text for keywords and return priority + matched keywords."""
        text_lower = text.lower()
        matched = []
        
        # Check high priority keywords first
        for keyword in KEYWORDS["high"]:
            if keyword in text_lower:
                matched.append(keyword)
        
        if matched:
            return "high", matched
        
        # Check medium priority keywords
        for keyword in KEYWORDS["medium"]:
            if keyword in text_lower:
                matched.append(keyword)
        
        if matched:
            return "medium", matched
        
        return "low", []
    
    def create_task_file(self, sender: str, message: str, timestamp: str, 
                         priority: str, matched_keywords: List[str]) -> Optional[str]:
        """Create .md file in Vault/Needs_Action/"""
        
        # Clean sender name for filename
        sender_clean = "".join(c if c.isalnum() else "_" for c in sender)[:30]
        time_str = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        filename = f"WHATSAPP_{sender_clean}_{time_str}.md"
        filepath = self.needs_action_path / filename
        
        # Check if already processed
        file_key = f"{sender}:{message[:50]}"
        if file_key in self.processed_messages:
            return None
        
        content = f"""# WhatsApp Message Alert

**From:** {sender}
**Received:** {timestamp}
**Platform:** WhatsApp
**Priority:** {priority.upper()}
**Matched Keywords:** {', '.join(matched_keywords) if matched_keywords else 'None'}

---

## Message Content

{message}

---

## Actions Required

- [ ] Review message
- [ ] Respond if needed
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

*Generated by WhatsApp Watcher - Silver Tier AI Employee*
"""
        
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            
            self.processed_messages.add(file_key)
            logger.info(f"✓ Created task file: {filename}")
            return str(filepath)
            
        except Exception as e:
            logger.error(f"Error creating file: {e}")
            return None
    
    def check_new_messages(self) -> int:
        """Main check for new messages."""
        tasks_created = 0
        
        try:
            # Get unread chats
            unread_chats = self.get_unread_chats()
            
            if not unread_chats:
                logger.debug("No unread messages")
                return 0
            
            logger.info(f"Found {len(unread_chats)} unread chat(s)")
            
            for chat in unread_chats:
                contact = chat["contact"]
                last_message = chat["last_message"]
                
                # Check keywords
                priority, matched = self.check_keywords(last_message)
                
                # Create task file if keywords match
                if matched:
                    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    filepath = self.create_task_file(
                        sender=contact,
                        message=last_message,
                        timestamp=timestamp,
                        priority=priority,
                        matched_keywords=matched
                    )
                    
                    if filepath:
                        tasks_created += 1
                        logger.info(f"Priority: {priority.upper()} | Keywords: {', '.join(matched)}")
            
            # Click on chat list header to go back
            try:
                self.page.click('div[data-testid="chat-list"]')
                self.page.wait_for_timeout(500)
            except:
                pass
                
        except Exception as e:
            logger.error(f"Error checking messages: {e}")
        
        return tasks_created
    
    def run(self):
        """Main watcher loop."""
        logger.info("=" * 60)
        logger.info("WhatsApp Watcher - Silver Tier")
        logger.info("=" * 60)
        logger.info(f"Check Interval: {CHECK_INTERVAL} seconds")
        logger.info(f"Keywords: {', '.join([k for keywords in KEYWORDS.values() for k in keywords])}")
        logger.info("=" * 60)
        
        try:
            # Start browser
            self.start_browser()
            
            # Navigate to WhatsApp
            if not self.navigate_to_whatsapp():
                logger.error("Failed to login to WhatsApp. Exiting.")
                return
            
            logger.info("Starting message monitoring...")
            
            # Main loop
            while True:
                try:
                    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    logger.info(f"\n[{timestamp}] Checking for new messages...")
                    
                    # Check if still logged in
                    if not self.is_logged_in():
                        logger.warning("WhatsApp session expired. Reconnecting...")
                        self.navigate_to_whatsapp()
                    
                    # Check for new messages
                    tasks = self.check_new_messages()
                    
                    if tasks > 0:
                        logger.info(f"✓ Created {tasks} task(s) in Needs_Action/")
                    
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
            # Cleanup
            logger.info("Closing browser...")
            if self.browser:
                self.browser.close()
            if self.playwright:
                self.playwright.stop()
            logger.info("WhatsApp Watcher stopped")
    
    def stop(self):
        """Stop the watcher gracefully."""
        logger.info("Stopping WhatsApp Watcher...")
        if self.browser:
            self.browser.close()
        if self.playwright:
            self.playwright.stop()


def main():
    """Entry point."""
    watcher = WhatsAppWatcher()
    watcher.run()


if __name__ == "__main__":
    main()
