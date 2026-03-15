"""
WhatsApp Watcher - One-Time Scan
Run once to verify the watcher is detecting chats correctly
"""

import os
import sys
import time
from datetime import datetime

# Fix Windows console encoding
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SESSION_PATH = os.path.join(PROJECT_ROOT, "session", "whatsapp")
WHATSAPP_URL = "https://web.whatsapp.com"

def scan_chats(page):
    """Scan for unread messages."""
    # Wait for page to load
    try:
        page.wait_for_selector('#pane-side', timeout=30000)
    except PlaywrightTimeout:
        print("Timeout waiting for page to load")
        return 0, 0
    
    time.sleep(3)  # Extra wait
    
    # Get chats
    chats = page.query_selector_all('#pane-side [role="row"]')
    total_chats = len(chats)
    total_unread = 0
    
    print(f"\nFound {total_chats} total chats\n")
    
    for i, chat in enumerate(chats):
        try:
            gridcells = chat.query_selector_all('[role="gridcell"]')
            if len(gridcells) < 3:
                continue
            
            cell_2 = gridcells[2]
            cell_2_text = cell_2.inner_text().strip()
            
            if not cell_2_text or not cell_2_text.isdigit():
                continue
            
            unread_count = int(cell_2_text)
            if unread_count == 0:
                continue
            
            total_unread += 1
            
            # Get name
            cell_1 = gridcells[1]
            name_elem = cell_1.query_selector('span[dir="auto"]')
            contact = name_elem.inner_text() if name_elem else "Unknown"
            
            # Get message
            cell_0 = gridcells[0]
            msg_elem = cell_0.query_selector('span[data-testid="last-message-content"]')
            message = msg_elem.inner_text() if msg_elem else ""
            
            print(f"  UNREAD [{unread_count:3d}]: {contact[:30]:30s} | {message[:60]}")
            
        except Exception as e:
            print(f"  Error on chat {i}: {e}")
    
    return total_chats, total_unread

def main():
    print("=" * 60)
    print("WhatsApp One-Time Scan")
    print("=" * 60)
    
    with sync_playwright() as p:
        context = p.chromium.launch_persistent_context(
            user_data_dir=SESSION_PATH,
            headless=False,
            args=["--disable-blink-features=AutomationControlled"]
        )
        
        page = context.pages[0]
        print("Navigating to WhatsApp...")
        page.goto(WHATSAPP_URL)
        
        total_chats, total_unread = scan_chats(page)
        
        print(f"\n{'=' * 60}")
        print(f"RESULTS: {total_chats} chats, {total_unread} with unread messages")
        print(f"{'=' * 60}")
        
        context.close()

if __name__ == "__main__":
    main()
