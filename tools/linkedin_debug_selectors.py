"""
LinkedIn Debug - Find Post Box Selectors
=========================================
Opens LinkedIn and finds the correct selectors for post creation.

Run: python tools\linkedin_debug_selectors.py
"""

import os
import sys
import time
from pathlib import Path

try:
    from playwright.sync_api import sync_playwright
except ImportError:
    print("Install: pip install playwright && playwright install chromium")
    sys.exit(1)

PROJECT_ROOT = Path(__file__).parent.parent
SESSION_PATH = PROJECT_ROOT / "session" / "linkedin"

def main():
    print()
    print("=" * 60)
    print("LinkedIn Post Box - Selector Debugger")
    print("=" * 60)
    print()
    print("This script will:")
    print("  1. Open LinkedIn in browser")
    print("  2. Wait for you to login and click 'Start a post'")
    print("  3. Find ALL possible selectors for the text input")
    print("  4. Show you the correct selectors to use")
    print()
    print("IMPORTANT:")
    print("  - Login to LinkedIn when browser opens")
    print("  - Click 'Start a post' button manually")
    print("  - Then press Enter in this console")
    print("  - Script will find correct selectors")
    print()
    
    input("Press Enter to start...")
    print()
    
    with sync_playwright() as p:
        print("[INFO] Launching browser...")
        
        context = p.chromium.launch_persistent_context(
            user_data_dir=str(SESSION_PATH),
            headless=False,
            args=["--no-sandbox"],
            timeout=120000
        )
        
        page = context.pages[0] if context.pages else context.new_page()
        
        # Go to LinkedIn
        print("[INFO] Going to LinkedIn...")
        page.goto("https://www.linkedin.com/feed/", wait_until="domcontentloaded", timeout=60000)
        
        print()
        print("=" * 60)
        print("NOW DO THIS:")
        print("  1. Login to LinkedIn (if not already)")
        print("  2. Click 'Start a post' button")
        print("  3. When the modal opens, come back here")
        print("  4. Press Enter in this console")
        print("=" * 60)
        print()
        
        input("Press Enter when post modal is open...")
        print()
        
        # Take screenshot
        screenshot = PROJECT_ROOT / "debug_modal.png"
        page.screenshot(path=str(screenshot))
        print(f"[INFO] Screenshot saved: {screenshot}")
        
        # Save HTML
        html_file = PROJECT_ROOT / "debug_modal.html"
        with open(html_file, 'w', encoding='utf-8') as f:
            f.write(page.content())
        print(f"[INFO] HTML saved: {html_file}")
        
        # Find ALL contenteditable elements
        print()
        print("[INFO] Searching for text inputs...")
        print("-" * 60)
        
        try:
            # Get all contenteditable elements
            editable = page.query_selector_all('div[contenteditable="true"]')
            print(f"[INFO] Found {len(editable)} contenteditable divs")
            
            for i, el in enumerate(editable):
                try:
                    # Get element info
                    tag = el.tag_name()
                    classes = el.get_attribute('class') or ''
                    role = el.get_attribute('role') or ''
                    dataid = el.get_attribute('data-testid') or ''
                    text = el.inner_text()[:50] if el.inner_text() else '(empty)'
                    
                    print()
                    print(f"  [{i+1}] contenteditable div:")
                    print(f"      Tag: {tag}")
                    print(f"      Class: {classes[:80]}...")
                    print(f"      Role: {role}")
                    print(f"      Data-testid: {dataid}")
                    print(f"      Current text: {text}")
                    
                    # Generate selector
                    if dataid:
                        print(f"      SELECTOR: [data-testid=\"{dataid}\"]")
                    elif role:
                        print(f"      SELECTOR: {tag}[contenteditable=\"true\"][role=\"{role}\"]")
                    elif classes:
                        first_class = classes.split()[0]
                        print(f"      SELECTOR: {tag}.{first_class}[contenteditable=\"true\"]")
                    else:
                        print(f"      SELECTOR: {tag}[contenteditable=\"true\"] (nth: {i+1})")
                    
                except Exception as e:
                    print(f"  [{i+1}] Error: {e}")
            
            # Also check for textareas
            textareas = page.query_selector_all('textarea')
            if textareas:
                print()
                print(f"[INFO] Found {len(textareas)} textarea elements")
            
            # Check for inputs
            inputs = page.query_selector_all('input[type="text"]')
            if inputs:
                print(f"[INFO] Found {len(inputs)} text inputs")
            
        except Exception as e:
            print(f"[ERROR] Search failed: {e}")
        
        print()
        print("-" * 60)
        print()
        print("[INFO] Debug files created:")
        print(f"  - {screenshot}")
        print(f"  - {html_file}")
        print()
        print("[INFO] Open the HTML file in browser to inspect structure")
        print()
        print("NOW - Update auto_linkedin_poster.py with correct selectors!")
        print()
        
        input("Press Enter to exit...")
        
        context.close()


if __name__ == "__main__":
    main()
