
from playwright.sync_api import sync_playwright
with sync_playwright() as p:
    browser = p.chromium.connect_over_cdp("http://127.0.0.1:9222")
    page = browser.contexts[0].pages[0]
    page.screenshot(path="debug_linkedin/LIVE_VIEW.png")
    print("Screenshot saved to debug_linkedin/LIVE_VIEW.png")
    # Also print page title to confirm
    print(f"Page Title: {page.title()}")
    browser.disconnect()
