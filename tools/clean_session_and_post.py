"""
LinkedIn Session Cleaner
========================
Cleans session folder and launches fresh browser for posting.

Run: python tools\clean_session_and_post.py
"""

import os
import sys
import shutil
import time
import subprocess

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SESSION_PATH = os.path.join(PROJECT_ROOT, "session", "linkedin")
PENDING_APPROVAL_FOLDER = os.path.join(PROJECT_ROOT, "Pending_Approval")


def kill_chrome():
    """Kill all Chrome processes."""
    print("[1/4] Closing Chrome browsers...")
    subprocess.run(['taskkill', '/F', '/IM', 'chrome.exe'], 
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    subprocess.run(['taskkill', '/F', '/IM', 'msedge.exe'], 
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time.sleep(2)
    print("  [OK] Chrome closed")


def clean_session():
    """Clean session folder."""
    print("[2/4] Cleaning session folder...")
    
    if os.path.exists(SESSION_PATH):
        try:
            # Try to delete
            shutil.rmtree(SESSION_PATH)
            print(f"  [OK] Deleted: {SESSION_PATH}")
        except PermissionError:
            print(f"  [WARNING] Could not delete - folder in use: {SESSION_PATH}")
            print("  [INFO] Will try to use existing session")
    
    # Recreate
    os.makedirs(SESSION_PATH, exist_ok=True)
    print(f"  [OK] Created: {SESSION_PATH}")


def list_drafts():
    """List available drafts."""
    print("[3/4] Finding drafts...")
    
    if not os.path.exists(PENDING_APPROVAL_FOLDER):
        print("  [ERROR] Pending_Approval folder not found!")
        return []
    
    files = [f for f in os.listdir(PENDING_APPROVAL_FOLDER)
             if f.startswith('linkedin_post_') and f.endswith('.md')]
    
    if not files:
        print("  [ERROR] No drafts found!")
        print("  [INFO] Run: python tools\\auto_linkedin_poster.py --scan")
        return []
    
    print(f"  [OK] Found {len(files)} draft(s):")
    for i, f in enumerate(sorted(files), 1):
        print(f"      {i}. {f}")
    
    return sorted(files)


def select_draft(drafts):
    """Let user select a draft."""
    print()
    print("[4/4] Select draft to post:")
    
    while True:
        try:
            choice = input(f"Enter number (1-{len(drafts)}) or 'q' to cancel: ").strip()
            
            if choice.lower() == 'q':
                return None
            
            idx = int(choice) - 1
            if 0 <= idx < len(drafts):
                return drafts[idx]
            else:
                print(f"  Enter number between 1 and {len(drafts)}")
        except ValueError:
            print("  Enter valid number or 'q'")


def main():
    print()
    print("=" * 60)
    print("LinkedIn Session Cleaner & Post Helper")
    print("=" * 60)
    print()
    
    # Kill Chrome
    kill_chrome()
    
    # Clean session
    clean_session()
    
    # List drafts
    drafts = list_drafts()
    
    if not drafts:
        print()
        print("[INFO] No drafts to post.")
        input("Press Enter to exit...")
        return
    
    # Select draft
    selected = select_draft(drafts)
    
    if not selected:
        print("Cancelled.")
        input("Press Enter to exit...")
        return
    
    print()
    print("-" * 60)
    print(f"Selected: {selected}")
    print("-" * 60)
    print()
    print("IMPORTANT INSTRUCTIONS:")
    print("  1. Browser will open with FRESH session (no login)")
    print("  2. LOGIN to LinkedIn manually")
    print("  3. Script will auto-detect login and proceed")
    print("  4. Post will be AUTO-TYPED and AUTO-POSTED")
    print("  5. Browser will STAY OPEN for verification")
    print("  6. Press Enter in console to exit")
    print()
    
    confirm = input("Continue? (y/n): ").strip().lower()
    if confirm != 'y':
        print("Cancelled.")
        input("Press Enter to exit...")
        return
    
    print()
    print("Running LinkedIn poster...")
    print()
    
    # Import and run
    sys.path.insert(0, PROJECT_ROOT)
    from tools.auto_linkedin_poster import post_to_linkedin
    
    result = post_to_linkedin(selected)
    
    print()
    if result['success']:
        print("=" * 60)
        print("[SUCCESS] Post published!")
        print("=" * 60)
    else:
        print("=" * 60)
        print(f"[FAILED] {result['error']}")
        print("=" * 60)
    
    input("Press Enter to exit...")


if __name__ == "__main__":
    main()
