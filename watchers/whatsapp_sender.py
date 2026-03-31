"""
WhatsApp Message Sender - Gold Tier (Chrome Fixed)
===================================================
Sends messages via WhatsApp Web using Playwright with Chrome.
Uses SAME session path as whatsapp_watcher_fixed.py

Usage: python watchers/whatsapp_sender.py --to "Contact Name" --message "Hello"
"""

import os
import sys
import time
import argparse
import logging
from pathlib import Path
from playwright.sync_api import sync_playwright

# Configuration
PROJECT_ROOT = Path(__file__).resolve().parent.parent
GOLD_DIR = PROJECT_ROOT / "gold"

# CRITICAL: Same session path as watcher
SESSION_PATH = PROJECT_ROOT / "session" / "whatsapp_chrome"
LOGS_FOLDER = GOLD_DIR / "logs"

# Ensure folders exist
SESSION_PATH.mkdir(parents=True, exist_ok=True)
LOGS_FOLDER.mkdir(parents=True, exist_ok=True)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOGS_FOLDER / f"whatsapp_sender_{time.strftime('%Y%m%d')}.log"),
        logging.StreamHandler()
    ]
)
log = logging.getLogger(__name__)

def send_whatsapp_message(target_contact, message_text):
    """Launch WhatsApp Web with Chrome and send message."""
    log.info(f"Connecting to WhatsApp to send to '{target_contact}'...")
    
    with sync_playwright() as p:
        context = None
        
        try:
            # Connect over CDP
            log.info("Connecting to WhatsApp Watcher Chrome instance (Port 9223)...")
            browser = p.chromium.connect_over_cdp("http://localhost:9223")
            
            log.info("[OK] Connected to browser")
            
            context = browser.contexts[0] if browser.contexts else browser
            page = context.pages[0] if context.pages else context.new_page()
            
            try:
                # Navigate to WhatsApp
                log.info("Navigating to WhatsApp Web...")
                page.goto("https://web.whatsapp.com/", wait_until="networkidle", timeout=60000)
                
                # Wait for WhatsApp to load
                log.info("Waiting for WhatsApp to load...")
                try:
                    page.wait_for_selector('#pane-side', timeout=60000)
                    log.info("[SUCCESS] WhatsApp loaded")
                except:
                    log.warning("Timeout waiting for WhatsApp - please ensure logged in")
                    time.sleep(5)
                
                # Search for contact
                log.info(f"Searching for contact: {target_contact}")
                try:
                    # Infallible fallback that waits for the DOM
                    search_box = page.locator('div[contenteditable="true"]').first
                    search_box.wait_for(state='visible', timeout=10000)
                    search_box.click()
                    time.sleep(1)
                    
                    # Type contact name
                    search_box.fill(target_contact)
                    time.sleep(2)
                    
                    # Press Enter to open chat
                    page.keyboard.press("Enter")
                    time.sleep(2)
                except Exception as e:
                    log.error(f"Search box not found - WhatsApp may not be loaded: {e}")
                    return False
                
                try:
                    message_box = page.locator('footer div[contenteditable="true"]').first
                    message_box.wait_for(state='visible', timeout=10000)
                    message_box.click()
                    time.sleep(0.5)
                    
                    # Type the message
                    page.keyboard.type(message_text, delay=50)
                    time.sleep(0.5)
                    
                    # Click the Send button icon instead of relying on Enter keystrokes
                    try:
                        send_btn = page.locator('span[data-icon="send"]').locator("..")
                        if send_btn.count() == 0:
                            send_btn = page.locator('button[aria-label="Send"]')
                        send_btn.first.click(timeout=5000)
                    except Exception as btn_err:
                        log.warning(f"Send button click failed, falling back to Enter key: {btn_err}")
                        page.keyboard.press("Enter")
                    
                    log.info("[SUCCESS] Message sent successfully!")
                    time.sleep(2)
                    
                    return True
                except Exception as e:
                    log.error(f"Message box not found - chat may not be open: {e}")
                    return False
                    
            except Exception as e:
                log.error(f"Error during message send: {e}")
                import traceback
                log.error(traceback.format_exc())
                return False
                
        except Exception as e:
            log.error(f"Failed to launch WhatsApp: {e}")
            import traceback
            log.error(traceback.format_exc())
            return False
        finally:
            if 'browser' in locals() and browser:
                try:
                    log.info("Disconnecting from browser (keeping it alive)...")
                    browser.disconnect()
                except Exception as e:
                    log.debug(f"Disconnect error: {e}")
    
    return False

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--to", required=True, help="Contact name or phone number")
    parser.add_argument("--message", required=True, help="Message content")
    
    args = parser.parse_args()
    
    success = send_whatsapp_message(args.to, args.message)
    
    sys.exit(0 if success else 1)
