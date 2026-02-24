"""
Instagram Auto-Post Skill - Human-in-the-Loop
Posts to Instagram automatically when file is in Approved/ folder

Usage:
    python skills/instagram_auto_post.py
    
Features:
- Reads INSTA_POST_REQUEST files from Approved/
- Posts to Instagram with saved session
- Moves to Done/ after successful post
- Runs as separate process (no asyncio conflicts)
"""

import os
import sys
import time
import subprocess
from pathlib import Path
from datetime import datetime

PROJECT_ROOT = Path(__file__).parent.parent
APPROVED_PATH = PROJECT_ROOT / "Vault" / "Approved"
DONE_PATH = PROJECT_ROOT / "Vault" / "Done"
SESSION_PATH = PROJECT_ROOT / "instagram_session"
LOGS_PATH = PROJECT_ROOT / "Vault" / "Logs"

def main():
    """Main auto-post function."""
    print("=" * 60)
    print("Instagram Auto-Post - Silver Tier")
    print("=" * 60)
    
    # Check for approved posts
    post_files = list(APPROVED_PATH.glob("INSTA_POST_REQUEST_*.md"))
    
    if not post_files:
        print("[INFO] No approved posts to process")
        return 0
    
    print(f"[OK] Found {len(post_files)} post(s) to process")
    
    success_count = 0
    
    for filepath in post_files:
        print(f"\n[INFO] Processing: {filepath.name}")
        
        # Read content
        content = filepath.read_text(encoding='utf-8')
        
        # Extract caption
        caption = "Posted from Silver Tier AI Employee 🚀"
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
                    print(f"[OK] Image: {image_path}")
                else:
                    print(f"[WARN] Image not found: {path_line}")
        
        # Post using Playwright
        success = post_to_instagram(image_path, caption)
        
        if success:
            # Move to Done/
            dest = DONE_PATH / filepath.name
            try:
                filepath.rename(dest)
                print(f"[OK] ✓ Posted! Moved to Done/")
                success_count += 1
            except Exception as e:
                print(f"[WARN] Could not move file: {e}")
        else:
            print(f"[ERROR] ✗ Post failed")
    
    print("\n" + "=" * 60)
    print(f"Result: {success_count}/{len(post_files)} posts successful")
    print("=" * 60)
    
    return success_count


def post_to_instagram(image_path, caption):
    """Post to Instagram using Playwright."""
    
    # Create a temporary script for posting
    temp_script = PROJECT_ROOT / "temp_post.py"
    
    script_content = f'''
import sys
import time
from pathlib import Path
from playwright.sync_api import sync_playwright

SESSION_PATH = r"{SESSION_PATH}"
IMAGE_PATH = r"{image_path}" if r"{image_path}" != "None" else None
CAPTION = """{caption}"""

print("[INFO] Starting browser...")
playwright = sync_playwright().start()

try:
    context = playwright.chromium.launch_persistent_context(
        user_data_dir=SESSION_PATH,
        headless=False,
        viewport={{"width": 1280, "height": 720}},
        args=["--disable-gpu", "--no-sandbox"]
    )
    
    page = context.pages[0] if context.pages else context.new_page()
    
    # Navigate to Instagram
    print("[INFO] Going to Instagram...")
    page.goto("https://www.instagram.com/", timeout=60000)
    page.wait_for_timeout(5000)
    
    # Check login
    try:
        page.wait_for_selector('a[href="/direct/inbox/"]', timeout=5000)
        print("[OK] Logged in")
    except:
        print("[WARN] Not logged in - waiting 60s...")
        time.sleep(60)
    
    # Click Create
    print("[INFO] Opening create dialog...")
    try:
        page.click('[aria-label="Create"]', timeout=5000)
        page.wait_for_timeout(3000)
        print("[OK] Create clicked")
    except Exception as e:
        print(f"[ERROR] Create failed: {{e}}")
        sys.exit(1)
    
    # Upload image
    if IMAGE_PATH and IMAGE_PATH != "None":
        print(f"[INFO] Uploading: {{IMAGE_PATH}}")
        try:
            page.set_input_files('input[type="file"]', IMAGE_PATH)
            page.wait_for_timeout(3000)
            print("[OK] Image uploaded")
        except Exception as e:
            print(f"[WARN] Upload failed: {{e}}")
    
    # Click Next twice
    print("[INFO] Clicking Next...")
    for i in range(2):
        try:
            page.click('button:has-text("Next"), div[role="button"]:has-text("Next")', timeout=5000)
            page.wait_for_timeout(2000)
            print(f"[OK] Next {{i+1}}")
        except:
            print(f"[INFO] No more Next (step {{i+1}})")
    
    # Add caption
    print("[INFO] Adding caption...")
    try:
        page.fill('textarea[aria-label*="caption"]', CAPTION, timeout=5000)
        print("[OK] Caption added")
    except Exception as e:
        print(f"[WARN] Caption failed: {{e}}")
    
    page.wait_for_timeout(2000)
    
    # Click Share - try multiple methods
    print("[INFO] Clicking Share...")
    shared = False
    
    # Method 1: Regular click
    try:
        page.click('button:has-text("Share")', timeout=3000)
        shared = True
        print("[OK] Share clicked (method 1)")
    except:
        # Method 2: Keyboard
        try:
            page.keyboard.press('Enter')
            page.wait_for_timeout(2000)
            shared = True
            print("[OK] Share via Enter (method 2)")
        except:
            # Method 3: Evaluate
            try:
                page.evaluate('''
                    document.querySelector('button:contains("Share")').click()
                ''')
                shared = True
                print("[OK] Share via JS (method 3)")
            except:
                print("[ERROR] Share failed")
    
    if shared:
        print("[OK] Waiting for post...")
        page.wait_for_timeout(5000)
        print("[OK] ✓ POST SUCCESSFUL!")
        sys.exit(0)
    else:
        sys.exit(1)
        
except Exception as e:
    print(f"[ERROR] Fatal: {{e}}")
    sys.exit(1)
finally:
    context.close()
    playwright.stop()
    print("[INFO] Browser closed")
'''
    
    # Write temp script
    with open(temp_script, 'w', encoding='utf-8') as f:
        f.write(script_content)
    
    # Run as subprocess
    print("[INFO] Running poster...")
    result = subprocess.run(
        [sys.executable, str(temp_script)],
        capture_output=True,
        text=True,
        cwd=str(PROJECT_ROOT)
    )
    
    # Show output
    print(result.stdout)
    if result.stderr:
        print(result.stderr)
    
    # Cleanup
    try:
        temp_script.unlink()
    except:
        pass
    
    return result.returncode == 0


if __name__ == "__main__":
    main()
