"""
LinkedIn Session Cleaner & Post Helper
=======================================
Cleans corrupted session and posts to LinkedIn.

Run:
    python tools\\linkedin_post_helper.py
"""

import os
import sys
import shutil
import time

# Configuration
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SESSION_PATH = os.path.join(PROJECT_ROOT, "session", "linkedin")
PENDING_APPROVAL_FOLDER = os.path.join(PROJECT_ROOT, "Pending_Approval")

def clean_session():
    """Clean LinkedIn session folder."""
    print("=" * 60)
    print("LinkedIn Session Cleaner")
    print("=" * 60)
    print()
    
    # Kill Chrome processes
    print("[1/3] Closing Chrome browsers...")
    os.system('taskkill /F /IM chrome.exe 2>nul')
    os.system('taskkill /F /IM msedge.exe 2>nul')
    time.sleep(2)
    
    # DON'T delete session - we want to keep login!
    print("[2/3] Checking session folder...")
    if os.path.exists(SESSION_PATH):
        print(f"  [INFO] Session exists: {SESSION_PATH}")
        print(f"  [INFO] Keeping existing login (NOT deleting)")
    else:
        print(f"  [INFO] Creating new session folder...")
        os.makedirs(SESSION_PATH, exist_ok=True)
        print(f"  [OK] Created: {SESSION_PATH}")
    
    print()
    print("[INFO] Session ready!")
    print()
    
    return True

def list_drafts():
    """List available drafts."""
    if not os.path.exists(PENDING_APPROVAL_FOLDER):
        print("[ERROR] Pending_Approval folder not found!")
        return []
    
    files = [f for f in os.listdir(PENDING_APPROVAL_FOLDER)
             if f.startswith('linkedin_post_') and f.endswith('.md')]
    
    if not files:
        print("[INFO] No drafts found!")
        return []
    
    print()
    print("Available drafts:")
    print("-" * 60)
    for i, f in enumerate(sorted(files), 1):
        print(f"  {i}. {f}")
    print()
    
    return sorted(files)

def main():
    """Main function."""
    print()
    print("=" * 60)
    print("LinkedIn Post Helper - Silver Tier")
    print("=" * 60)
    print()
    print("This script will:")
    print("  1. Close all Chrome browsers")
    print("  2. Clean LinkedIn session")
    print("  3. Launch fresh browser for posting")
    print()
    
    confirm = input("Continue? (y/n): ").strip().lower()
    if confirm != 'y':
        print("Cancelled.")
        return
    
    # Clean session
    if not clean_session():
        print()
        print("[ERROR] Session cleaning failed!")
        return
    
    # List drafts
    drafts = list_drafts()
    
    if not drafts:
        print()
        print("[INFO] No drafts to post.")
        print("Run: python tools\\auto_linkedin_poster.py --scan")
        return
    
    # Select draft
    while True:
        try:
            choice = input(f"Select draft (1-{len(drafts)}) or 'q' to cancel: ").strip()
            
            if choice.lower() == 'q':
                print("Cancelled.")
                return
            
            choice_num = int(choice)
            if 1 <= choice_num <= len(drafts):
                selected = drafts[choice_num - 1]
                break
            else:
                print(f"Enter number between 1 and {len(drafts)}")
        except ValueError:
            print("Enter valid number or 'q'")
    
    print()
    print("-" * 60)
    print(f"Selected: {selected}")
    print("-" * 60)
    print()
    print("Now running LinkedIn poster...")
    print()
    print("IMPORTANT:")
    print("  - Browser will open")
    print("  - Post will be published automatically")
    print("  - Browser will STAY OPEN after posting")
    print("  - Verify your post on LinkedIn")
    print("  - Close browser manually when done")
    print("  - Press Enter in console to exit")
    print()

    # Import and run poster
    sys.path.insert(0, PROJECT_ROOT)
    from tools.auto_linkedin_poster import post_to_linkedin

    result = post_to_linkedin(selected)

    print()
    if result['success']:
        print("=" * 60)
        print("[SUCCESS] Post published to LinkedIn!")
        print("=" * 60)
        print()
        print("Browser is still open.")
        print("Verify your post: https://www.linkedin.com/feed/")
        print("Close browser manually when done.")
        print()
    else:
        print("=" * 60)
        print(f"[FAILED] {result['error']}")
        print("=" * 60)
        print()
        print("Browser is still open for debugging.")
        print("Close it manually when done.")
        print()

if __name__ == "__main__":
    main()
