import time
from playwright.sync_api import sync_playwright

def snap():
    with sync_playwright() as p:
        try:
            print("Connecting to 9223...")
            browser = p.chromium.connect_over_cdp("http://localhost:9223")
            context = browser.contexts[0] if browser.contexts else browser
            page = context.pages[0] if context.pages else context.new_page()
            page.screenshot(path="wa_debug_screen.png")
            print("Captured wa_debug_screen.png")
            browser.disconnect()
        except Exception as e:
            print(f"Failed: {e}")

if __name__ == "__main__":
    snap()
