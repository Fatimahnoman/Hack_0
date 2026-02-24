"""
Quick Instagram Post - Direct Post from Approved Folder
Run this manually to post approved Instagram requests
"""

import sys
import os
import time
from pathlib import Path
from datetime import datetime

# Set UTF-8 encoding for Windows console
if sys.platform == 'win32':
    os.system('chcp 65001 >nul 2>&1')

PROJECT_ROOT = Path(__file__).parent
APPROVED_PATH = PROJECT_ROOT / "Vault" / "Approved"
DONE_PATH = PROJECT_ROOT / "Vault" / "Done"
SESSION_PATH = PROJECT_ROOT / "instagram_session"

print("=" * 60)
print("Quick Instagram Poster")
print("=" * 60)

# Check for approved post requests
post_files = list(APPROVED_PATH.glob("INSTA_POST_REQUEST_*.md"))

if not post_files:
    print("\n[INFO] No approved post requests found in Vault/Approved/")
    print("\nSteps:")
    print("1. Create post: python test_insta_post.py")
    print("2. Wait 2 minutes (auto-move to Pending_Approval/)")
    print("3. Move to Approved/ folder")
    print("4. Run this script again")
    sys.exit(0)

print(f"\n[OK] Found {len(post_files)} post request(s):")
for pf in post_files:
    print(f"  - {pf.name}")

print()
print("Starting Instagram browser...")
print("DO NOT CLOSE THE BROWSER WINDOW")
print()

# Import and run poster
from playwright.sync_api import sync_playwright

def post_to_instagram(filepath: Path) -> bool:
    """Post to Instagram."""
    print(f"[INFO] Processing: {filepath.name}")
    
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
        if path_line and path_line != "[Add image path here]" and path_line != "None":
            if Path(path_line).exists():
                image_path = path_line
                print(f"[OK] Image found: {image_path}")
            else:
                print(f"[WARN] Image not found: {path_line}")
    
    # Print caption info (avoid emoji issues)
    caption_ascii = caption[:50].encode('ascii', errors='replace').decode()
    print(f"[INFO] Caption: {caption_ascii}...")
    print()
    
    # Start browser
    playwright = sync_playwright().start()
    
    try:
        context = playwright.chromium.launch_persistent_context(
            user_data_dir=str(SESSION_PATH),
            headless=False,
            viewport={"width": 1280, "height": 720},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            args=["--disable-gpu", "--no-sandbox", "--disable-dev-shm-usage"]
        )
        
        page = context.pages[0] if context.pages else context.new_page()
        
        # Navigate to Instagram
        print("[INFO] Navigating to Instagram...")
        page.goto("https://www.instagram.com/", wait_until="domcontentloaded", timeout=60000)
        page.wait_for_timeout(5000)
        
        # Check if logged in
        logged_in = False
        try:
            page.wait_for_selector('a[href="/direct/inbox/"], img[alt="Profile"]', timeout=5000)
            logged_in = True
            print("[OK] Already logged in to Instagram")
        except:
            print("[WARN] Not logged in!")
            print("[INFO] Waiting 60 seconds for manual login...")
            for i in range(60):
                time.sleep(1)
                try:
                    page.wait_for_selector('a[href="/direct/inbox/"]', timeout=1000)
                    print("[OK] Login successful!")
                    logged_in = True
                    break
                except:
                    continue
        
        if not logged_in:
            print("[ERROR] Login timeout. Please login manually and try again.")
            return False
        
        # Click Create button
        print("[INFO] Opening create post dialog...")
        create_clicked = False
        for selector in ['svg[aria-label="New post"]', '[aria-label="Create"]']:
            try:
                page.click(selector, timeout=3000)
                create_clicked = True
                print("[OK] Create button clicked")
                break
            except:
                continue
        
        if not create_clicked:
            print("[ERROR] Could not find Create button")
            return False
        
        page.wait_for_timeout(2000)
        
        # Upload image if provided
        if image_path:
            print(f"[INFO] Uploading image: {image_path}")
            try:
                file_input = page.query_selector('input[type="file"]')
                if file_input:
                    file_input.set_input_files(image_path)
                    print("[OK] Image uploaded")
            except Exception as e:
                print(f"[WARN] Error uploading image: {e}")
        
        page.wait_for_timeout(3000)
        
        # Click Next (twice)
        print("[INFO] Clicking Next...")
        for i in range(2):
            try:
                page.click('button:has-text("Next"), [role="button"]:has-text("Next")', timeout=5000)
                page.wait_for_timeout(2000)
                print(f"[OK] Next {i+1} clicked")
            except:
                print(f"[INFO] No more Next buttons (step {i+1})")
                break
        
        # Add caption
        print("[INFO] Adding caption...")
        try:
            caption_field = page.query_selector('textarea[aria-label*="caption"]')
            if caption_field:
                caption_field.fill(caption)
                print("[OK] Caption added")
            else:
                print("[WARN] Caption field not found")
        except Exception as e:
            print(f"[WARN] Error adding caption: {e}")
        
        page.wait_for_timeout(2000)
        
        # Click Share
        print("[INFO] Clicking Share...")
        try:
            page.click('button:has-text("Share"), [role="button"]:has-text("Share")', timeout=5000)
            print("[OK] Share clicked")
        except Exception as e:
            print(f"[ERROR] Error clicking Share: {e}")
            return False
        
        # Wait for completion
        print("[INFO] Waiting for post to complete...")
        page.wait_for_timeout(5000)
        
        print("[OK] ✓ POST SUCCESSFUL!")
        
        # Move to Done/
        dest = DONE_PATH / filepath.name
        filepath.rename(dest)
        print(f"[OK] Moved to Done: {filepath.name}")
        
        return True
        
    except Exception as e:
        print(f"[ERROR] Post failed: {e}")
        return False
    finally:
        context.close()
        playwright.stop()
        print("[INFO] Browser closed")

# Process all approved posts
success_count = 0
for filepath in post_files:
    if post_to_instagram(filepath):
        success_count += 1
    print()
    time.sleep(2)

print("=" * 60)
print(f"Result: {success_count}/{len(post_files)} posts successful")
print("=" * 60)

if success_count > 0:
    print("\n✓ Check your Instagram profile - posts should be live!")
else:
    print("\n✗ Posts failed. Check logs for details.")
