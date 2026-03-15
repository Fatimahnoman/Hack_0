"""
LinkedIn Login Tester
=====================
Test if LinkedIn session is working.

Run:
    python tools\test_linkedin_login.py
"""

import os
import sys
import time
from pathlib import Path

# Add parent directory
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout
except ImportError:
    print("[ERROR] Playwright not installed!")
    print("Run: pip install playwright")
    print("     playwright install chromium")
    sys.exit(1)

# Configuration
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SESSION_PATH = os.path.join(PROJECT_ROOT, "session", "linkedin")
SCREENSHOT_PATH = os.path.join(PROJECT_ROOT, "linkedin_test.png")

def test_login():
    """Test LinkedIn login."""
    print("=" * 60)
    print("LinkedIn Login Tester")
    print("=" * 60)
    print()
    print(f"Session folder: {SESSION_PATH}")
    print()
    
    # Ensure session folder exists
    os.makedirs(SESSION_PATH, exist_ok=True)
    
    with sync_playwright() as p:
        print("[INFO] Launching browser...")
        
        context = p.chromium.launch_persistent_context(
            user_data_dir=SESSION_PATH,
            headless=False,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
                "--disable-dev-shm-usage"
            ]
        )
        
        page = context.pages[0]
        
        # Navigate to LinkedIn
        print("[INFO] Navigating to LinkedIn...")
        page.goto("https://www.linkedin.com", wait_until="domcontentloaded", timeout=60000)
        
        # Wait and check
        print("[INFO] Checking login status...")
        print("[INFO] Waiting 10 seconds for page to load...")
        time.sleep(10)
        
        # Take screenshot
        print(f"[INFO] Taking screenshot: {SCREENSHOT_PATH}")
        page.screenshot(path=SCREENSHOT_PATH)
        
        # Check URL
        current_url = page.url
        print(f"[INFO] Current URL: {current_url}")
        
        # Check selectors
        selectors_to_try = [
            'nav.global-nav',
            'div#global-nav',
            'a[href*="/mynetwork/"]',
            'a[href*="/notifications/"]',
            'img.actor-name',
            'button[data-control-name="nav_settings"]',
            '.nav-item--mynetwork',
            'header[role="banner"]',
        ]
        
        logged_in = False
        for selector in selectors_to_try:
            try:
                element = page.wait_for_selector(selector, timeout=2000)
                if element:
                    print(f"[OK] Found: {selector}")
                    logged_in = True
            except:
                print(f"[NOT FOUND] {selector}")
        
        print()
        print("-" * 60)
        if logged_in:
            print("[SUCCESS] You are logged in to LinkedIn!")
        else:
            print("[WARNING] Login not detected")
            print("[INFO] Please login manually in the browser window")
            print("[INFO] Then close the browser when done")
            
            # Wait for manual login
            try:
                input("Press Enter when you have logged in...")
            except:
                pass
        
        print("-" * 60)
        print()
        print(f"Screenshot saved to: {SCREENSHOT_PATH}")
        print()
        print("Keeping browser open for 30 seconds...")
        print("Close it manually or wait for auto-close.")
        
        time.sleep(30)
        context.close()
        
        print("[INFO] Browser closed.")

if __name__ == "__main__":
    test_login()
