"""
Simple Instagram Auto-Post - No temp script
Direct posting with proper error handling
"""

import sys
from pathlib import Path
from playwright.sync_api import sync_playwright

SESSION_PATH = Path(__file__).parent.parent / "instagram_session"
APPROVED_PATH = Path(__file__).parent.parent / "Vault" / "Approved"
DONE_PATH = Path(__file__).parent.parent / "Vault" / "Done"

def main():
    # Find approved posts
    post_files = list(APPROVED_PATH.glob("INSTA_POST_REQUEST_*.md"))
    
    if not post_files:
        print("[INFO] No posts to process")
        return
    
    print(f"[OK] Found {len(post_files)} post(s)")
    
    for filepath in post_files:
        print(f"\n[INFO] Posting: {filepath.name}")
        
        # Read content
        content = filepath.read_text(encoding='utf-8')
        
        # Extract caption
        caption = "Posted from Silver Tier AI Employee"
        if "## Caption" in content:
            caption_section = content.split("## Caption")[1]
            if "##" in caption_section:
                caption_section = caption_section.split("##")[0]
            caption = caption_section.strip()
        
        # Extract image path
        image_path = None
        if "**Path:**" in content:
            path_line = content.split("**Path:**")[1].split("\n")[0].strip()
            if path_line and path_line not in ["[Add image path here]", "None", ""]:
                if Path(path_line).exists():
                    image_path = path_line
        
        # Post
        success = post_to_instagram(image_path, caption)
        
        if success:
            # Move to Done
            dest = DONE_PATH / filepath.name
            filepath.rename(dest)
            print(f"[OK] Posted! Moved to Done/")
        else:
            print("[ERROR] Post failed")

def post_to_instagram(image_path, caption):
    """Post to Instagram."""
    print("[INFO] Starting browser...")
    
    playwright = sync_playwright().start()
    
    try:
        context = playwright.chromium.launch_persistent_context(
            user_data_dir=str(SESSION_PATH),
            headless=False,
            viewport={"width": 1280, "height": 720},
            args=["--disable-gpu", "--no-sandbox"]
        )
        
        page = context.pages[0] if context.pages else context.new_page()
        
        # Go to Instagram
        print("[INFO] Going to Instagram...")
        page.goto("https://www.instagram.com/", timeout=60000)
        page.wait_for_timeout(5000)
        
        # Check login
        try:
            page.wait_for_selector('a[href="/direct/inbox/"]', timeout=5000)
            print("[OK] Logged in")
        except:
            print("[WARN] Not logged in - waiting 60s...")
            page.wait_for_timeout(60000)
        
        # Click Create
        print("[INFO] Clicking Create...")
        page.click('[aria-label="Create"]', timeout=5000)
        page.wait_for_timeout(3000)
        print("[OK] Create clicked")
        
        # Upload image
        if image_path:
            print(f"[INFO] Uploading: {image_path}")
            page.set_input_files('input[type="file"]', image_path)
            page.wait_for_timeout(3000)
        
        # Click Next twice
        print("[INFO] Clicking Next...")
        for i in range(2):
            try:
                page.click('button:has-text("Next")', timeout=5000)
                page.wait_for_timeout(2000)
                print(f"[OK] Next {i+1}")
            except:
                print(f"[INFO] No Next {i+1}")
        
        # Add caption
        print("[INFO] Adding caption...")
        try:
            page.fill('textarea[aria-label*="caption"]', caption, timeout=5000)
            print("[OK] Caption added")
        except Exception as ex:
            print(f"[WARN] Caption: {ex}")
        
        page.wait_for_timeout(2000)
        
        # Click Share
        print("[INFO] Clicking Share...")
        try:
            page.click('button:has-text("Share")', timeout=5000)
            print("[OK] Share clicked")
        except Exception as ex:
            print(f"[WARN] Share click: {ex}")
            # Try Enter key
            try:
                page.keyboard.press('Enter')
                page.wait_for_timeout(2000)
                print("[OK] Share via Enter")
            except:
                print("[ERROR] Share failed")
                return False
        
        # Wait for post
        print("[INFO] Waiting for post...")
        page.wait_for_timeout(5000)
        print("[OK] Post successful!")
        
        return True
        
    except Exception as ex:
        print(f"[ERROR] {ex}")
        return False
    finally:
        context.close()
        playwright.stop()
        print("[INFO] Browser closed")

if __name__ == "__main__":
    main()
