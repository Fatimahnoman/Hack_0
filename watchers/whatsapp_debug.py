"""
WhatsApp Debug Script - Find correct selectors
"""

import os
import time
from playwright.sync_api import sync_playwright

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SESSION_PATH = os.path.join(PROJECT_ROOT, "session", "whatsapp")

def debug_whatsapp():
    with sync_playwright() as p:
        context = p.chromium.launch_persistent_context(
            user_data_dir=SESSION_PATH,
            headless=False,
            args=["--disable-blink-features=AutomationControlled"]
        )
        
        page = context.pages[0]
        page.goto("https://web.whatsapp.com")
        
        print("=" * 60)
        print("WHATSAPP DEBUG - Wait for page to load fully")
        print("Then check console for element info")
        print("=" * 60)
        
        # Wait for user to confirm page is loaded
        input("\nPress Enter after WhatsApp has loaded...")
        
        # Get page info
        print(f"\nURL: {page.url}")
        print(f"Title: {page.title()}")
        
        # Find all potential chat list containers
        selectors_to_try = [
            '[data-testid="chat-list"]',
            '[data-testid="chatlist"]',
            '#pane-side',
            '.app-wrapper-web',
            '[role="list"]',
            '[role="listbox"]',
            '[role="grid"]',
            '[role="row"]',
            '[role="option"]',
            '[data-testid="chat-item"]',
            '[data-list-item-id]',
            'div._33r1-',  # Old WhatsApp class
            'div[role="listitem"]',
            'div[tabindex="0"]',
        ]
        
        print("\n--- Testing Selectors ---")
        for selector in selectors_to_try:
            try:
                elements = page.query_selector_all(selector)
                if elements:
                    print(f"✅ FOUND: {selector} -> {len(elements)} elements")
                    # Show first element's HTML
                    if elements:
                        html = elements[0].evaluate('el => el.outerHTML')[:200]
                        print(f"   Sample: {html[:150]}...")
                else:
                    print(f"❌ EMPTY: {selector}")
            except Exception as e:
                print(f"❌ ERROR: {selector} -> {e}")
        
        # Find unread indicators
        print("\n--- Testing Unread Selectors ---")
        unread_selectors = [
            '[data-testid="icon-unread-count"]',
            '[data-testid="unread-count"]',
            '[data-testid="unread-badge"]',
            'span[class*="unread"]',
            'div[class*="unread"]',
            'span[class*="badge"]',
            'div[class*="badge"]',
            '[data-icon="unread"]',
            'span._1rjx-',  # Old class
            'div._1rjx-',
        ]
        
        for selector in unread_selectors:
            try:
                elements = page.query_selector_all(selector)
                if elements:
                    print(f"✅ FOUND: {selector} -> {len(elements)} elements")
                else:
                    print(f"❌ EMPTY: {selector}")
            except Exception as e:
                print(f"❌ ERROR: {selector} -> {e}")
        
        # Find message content selectors
        print("\n--- Testing Message Selectors ---")
        msg_selectors = [
            '[data-testid="last-message-content"]',
            '[data-testid="message-preview"]',
            'span[dir="auto"]',
            'div[title]',
            'span[title]',
        ]
        
        for selector in msg_selectors:
            try:
                elements = page.query_selector_all(selector)
                if elements:
                    print(f"✅ FOUND: {selector} -> {len(elements)} elements")
                else:
                    print(f"❌ EMPTY: {selector}")
            except Exception as e:
                print(f"❌ ERROR: {selector} -> {e}")
        
        # Dump all data-testid attributes on page
        print("\n--- All data-testid on page ---")
        try:
            testids = page.evaluate('''() => {
                const elements = document.querySelectorAll('[data-testid]');
                const ids = new Set();
                elements.forEach(el => ids.add(el.getAttribute('data-testid')));
                return Array.from(ids);
            }''')
            for tid in testids[:50]:  # First 50
                print(f"  - {tid}")
            if len(testids) > 50:
                print(f"  ... and {len(testids) - 50} more")
        except Exception as e:
            print(f"Error: {e}")
        
        # Dump all role attributes
        print("\n--- All role attributes on page ---")
        try:
            roles = page.evaluate('''() => {
                const elements = document.querySelectorAll('[role]');
                const roleSet = new Set();
                elements.forEach(el => roleSet.add(el.getAttribute('role')));
                return Array.from(roleSet);
            }''')
            for role in roles:
                print(f"  - {role}")
        except Exception as e:
            print(f"Error: {e}")
        
        print("\n" + "=" * 60)
        print("Debug complete. Keep browser open to inspect manually.")
        print("Press Ctrl+C to exit.")
        print("=" * 60)
        
        # Keep running
        while True:
            time.sleep(10)

if __name__ == "__main__":
    debug_whatsapp()
