"""
WhatsApp Web Inspector - Quick diagnostic script
Run: python watchers/whatsapp_inspector.py
"""

import os
import sys
import time

try:
    from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout
except ImportError as e:
    print(f"[ERROR] Playwright not installed: {e}")
    print("Run: pip install playwright && playwright install chromium")
    sys.exit(1)

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SESSION_PATH = os.path.join(PROJECT_ROOT, "session", "whatsapp")
WHATSAPP_URL = "https://web.whatsapp.com"

def inspect_whatsapp():
    """Inspect WhatsApp Web structure."""
    
    print("[INFO] Launching browser...")
    
    with sync_playwright() as p:
        context = p.chromium.launch_persistent_context(
            user_data_dir=SESSION_PATH,
            headless=False,
            args=["--no-sandbox", "--disable-dev-shm-usage"]
        )
        
        page = context.pages[0]
        
        print("[INFO] Going to WhatsApp Web...")
        page.goto(WHATSAPP_URL)
        
        print("[INFO] Waiting 30 seconds for login (if needed)...")
        print("[INFO] Check the browser window!")
        
        # Wait for user to be logged in
        time.sleep(10)
        
        # Get page info
        print(f"\n[INFO] Current URL: {page.url}")
        print(f"[INFO] Page title: {page.title()}")
        
        # Try to find chat list
        chat_list = page.query_selector('div[data-testid="chat-list"]')
        print(f"\n[INFO] Chat list found: {chat_list is not None}")
        
        if chat_list:
            print("[INFO] Chat list exists!")
            
            # Count chat items
            chat_items = page.query_selector_all('div[role="listitem"]')
            print(f"[INFO] Total chat items: {len(chat_items)}")
            
            # Inspect first few chats
            for idx, chat in enumerate(chat_items[:5]):
                print(f"\n--- Chat {idx + 1} ---")
                
                # Get contact name
                contact = "Unknown"
                name_elem = chat.query_selector('span[dir="auto"][title]')
                if name_elem:
                    contact = name_elem.get_attribute('title')
                else:
                    name_elem = chat.query_selector('div[title]')
                    if name_elem:
                        contact = name_elem.get_attribute('title')
                
                print(f"Contact: {contact}")
                
                # Check for unread badge
                unread_badge = chat.query_selector('span[data-testid="unread-count-badge"]')
                if unread_badge:
                    try:
                        unread_text = unread_badge.inner_text()
                        print(f"Unread badge: {unread_text}")
                    except:
                        print("Unread badge: present (no text)")
                else:
                    # Try other selectors
                    for selector in ['span[class*="unread"]', 'div[class*="badge"]']:
                        unread_badge = chat.query_selector(selector)
                        if unread_badge:
                            print(f"Unread badge found with: {selector}")
                            break
                    else:
                        print("Unread badge: None")
                
                # Get last message
                msg_elem = chat.query_selector('span[data-testid="last-message-content"]')
                if msg_elem:
                    try:
                        message = msg_elem.inner_text()
                        print(f"Last message: {message[:80]}")
                    except:
                        print("Last message: [could not read]")
                else:
                    print("Last message: [not found]")
                
                # Get all span elements for debugging
                spans = chat.query_selector_all('span')
                print(f"Total spans: {len(spans)}")
                for i, span in enumerate(spans[:10]):
                    try:
                        text = span.inner_text().strip()
                        if text and len(text) < 100:
                            print(f"  Span {i}: '{text}'")
                    except:
                        pass
        else:
            print("[WARNING] Chat list not found!")
            print("[INFO] You may not be logged in yet.")
            print("[INFO] Please scan QR code if prompted.")
            print("[INFO] Waiting additional 20 seconds...")
            time.sleep(20)
            
            # Try again
            chat_list = page.query_selector('div[data-testid="chat-list"]')
            print(f"[INFO] Chat list found (retry): {chat_list is not None}")
        
        print("\n[INFO] Keeping browser open for 30 more seconds for manual inspection...")
        print("[INFO] Check the console output above for details.")
        time.sleep(30)
        
        context.close()
        print("[INFO] Done!")

if __name__ == "__main__":
    inspect_whatsapp()
