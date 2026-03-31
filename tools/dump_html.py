
from playwright.sync_api import sync_playwright
with sync_playwright() as p:
    try:
        browser = p.chromium.connect_over_cdp("http://127.0.0.1:9222")
        page = browser.contexts[0].pages[0]
        
        # Take screenshot
        page.screenshot(path="debug_linkedin/DIAG_HTML.png")
        
        # Check for ANY div with high z-index or fixed/absolute position which modals usually are
        # Or just find all roles
        print("--- DIALOGS FOUND ---")
        dialogs = page.locator('[role="dialog"], .artdeco-modal').all()
        for i, d in enumerate(dialogs):
            print(f"Dialog {i}: {d.evaluate('node => node.className')}")
            print(f"Visible: {d.is_visible()}")
            
        print("--- BUTTONS FOUND ---")
        btns = page.locator('button').all()
        for b in btns:
            txt = b.inner_text().strip().replace('\n', ' ')
            if txt:
                print(f"Button: '{txt}' | Visible: {b.is_visible()}")

        # Save HTML snippet of body
        html = page.content()
        with open("debug_linkedin/page_dump.html", "w", encoding="utf-8") as f:
            f.write(html)
        print("HTML dumped to debug_linkedin/page_dump.html")
        
    except Exception as e:
        print(f"Error: {e}")
