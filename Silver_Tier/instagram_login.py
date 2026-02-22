from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    context = p.chromium.launch_persistent_context(
        'instagram_session',
        headless=False,
        slow_mo=500
    )
    page = context.pages[0] if context.pages else context.new_page()
    page.goto('https://www.instagram.com')
    input("Instagram pe login kar lo (username/password ya QR), phir Enter dabaao...")
    context.close()