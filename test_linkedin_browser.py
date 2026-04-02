"""
Test LinkedIn Browser Launch - Simple
======================================
Just opens LinkedIn in browser to test if it works.
"""

import sys
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

PROJECT_ROOT = Path(__file__).resolve().parent
SESSION_LINKEDIN = PROJECT_ROOT / "session" / "linkedin"

print("=" * 60)
print("LINKEDIN BROWSER LAUNCH TEST")
print("=" * 60)

try:
    with sync_playwright() as p:
        print("[1] Launching browser...")
        
        context = p.chromium.launch_persistent_context(
            user_data_dir=str(SESSION_LINKEDIN),
            headless=False,
            channel="chrome",
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
            ],
            timeout=90000
        )
        
        print("[OK] Browser launched!")
        print("[2] Opening LinkedIn...")
        
        page = context.pages[0]
        page.goto("https://www.linkedin.com", timeout=60000)
        
        print("[OK] LinkedIn opened!")
        print("[3] Waiting for page to load...")
        
        # Wait for LinkedIn to load
        time.sleep(5)
        
        # Check if logged in
        if "feed" in page.url:
            print("[OK] Already logged in!")
        elif "login" in page.url:
            print("[WARN] Login required - please login manually")
        else:
            print(f"[INFO] Current URL: {page.url}")
        
        print("=" * 60)
        print("SUCCESS! LinkedIn is working!")
        print("=" * 60)
        print()
        print("Browser window should be open now.")
        print("Keep it open for 10 seconds...")
        
        time.sleep(10)
        context.close()
        
except Exception as e:
    print(f"[ERROR] {e}")
    print()
    print("TROUBLESHOOTING:")
    print("  1. Close all Chrome windows")
    print("  2. Run: playwright install chrome")
    print("  3. Try again")
    import traceback
    traceback.print_exc()
    sys.exit(1)
