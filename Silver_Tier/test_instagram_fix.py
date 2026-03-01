"""
Quick Test Script for Instagram Auto-Post Fix

Run this to verify:
1. Playwright is installed
2. Credentials exist in .env
3. Test image exists
4. Debug directories exist
"""

import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent

def check_setup():
    print("=" * 60)
    print("Instagram Auto-Post Fix - Setup Check")
    print("=" * 60)
    
    checks_passed = 0
    checks_total = 0
    
    # Check 1: Playwright installed
    checks_total += 1
    try:
        from playwright.sync_api import sync_playwright
        print("[OK] Playwright is installed")
        checks_passed += 1
    except ImportError:
        print("[FAIL] Playwright NOT installed")
        print("    Run: pip install playwright && playwright install chromium")
    
    # Check 2: .env file exists
    checks_total += 1
    env_file = PROJECT_ROOT / ".env"
    if env_file.exists():
        print(f"[OK] .env file exists: {env_file}")
        
        # Check for Instagram credentials
        with open(env_file, 'r', encoding='utf-8') as f:
            content = f.read()
            has_username = 'INSTAGRAM_USERNAME=' in content
            has_password = 'INSTAGRAM_PASSWORD=' in content
            
        if has_username and has_password:
            print("[OK] Instagram credentials found in .env")
            checks_passed += 1
        else:
            print("[FAIL] Instagram credentials missing in .env")
            print("    Add: INSTAGRAM_USERNAME=your_username")
            print("         INSTAGRAM_PASSWORD=your_password")
    else:
        print(f"[FAIL] .env file NOT found: {env_file}")
        print("    Create .env file with Instagram credentials")
    
    # Check 3: Test image exists
    checks_total += 1
    test_image = PROJECT_ROOT / "test_image.jpg"
    if test_image.exists():
        print(f"[OK] Test image exists: {test_image}")
        checks_passed += 1
    else:
        print(f"[FAIL] Test image NOT found: {test_image}")
        print("    Place a test JPG at: E:\\Hackathon_Zero\\Silver_Tier\\test_image.jpg")
    
    # Check 4: Debug directories exist
    checks_total += 1
    debug_path = PROJECT_ROOT / "debug_screenshots"
    debug_path.mkdir(parents=True, exist_ok=True)
    print(f"[OK] Debug directory exists: {debug_path}")
    checks_passed += 1
    
    # Check 5: Vault directories exist
    checks_total += 1
    approved_path = PROJECT_ROOT / "Vault" / "Approved"
    done_path = PROJECT_ROOT / "Vault" / "Done"
    
    if approved_path.exists() and done_path.exists():
        print(f"[OK] Vault directories exist")
        checks_passed += 1
    else:
        print(f"[FAIL] Vault directories missing")
        print("    Ensure Vault/Approved and Vault/Done exist")
    
    # Check 6: Session directory exists
    checks_total += 1
    session_path = PROJECT_ROOT / "sessions" / "instagram_session"
    session_path.mkdir(parents=True, exist_ok=True)
    print(f"[OK] Session directory: {session_path}")
    checks_passed += 1
    
    # Check 7: Fixed server file exists
    checks_total += 1
    server_final = PROJECT_ROOT / "mcp_servers" / "actions_mcp" / "server_final.py"
    if server_final.exists():
        print(f"[OK] Fixed server file exists: {server_final}")
        checks_passed += 1
    else:
        print(f"[FAIL] Fixed server file NOT found: {server_final}")
    
    # Summary
    print("=" * 60)
    print(f"Checks Passed: {checks_passed}/{checks_total}")
    
    if checks_passed == checks_total:
        print("\n[OK] All checks passed! Ready to test.")
        print("\nNext steps:")
        print("1. Copy INSTA_POST_REQUEST_TEST.md to Vault/Approved/")
        print("2. Run: python watchers\\instagram_watcher.py")
        print("3. Watch the browser automate the post")
        print("4. Check debug_screenshots/ for screenshots")
    else:
        print("\n[WARN] Some checks failed. Fix issues above before testing.")
    
    print("=" * 60)
    
    return checks_passed == checks_total


if __name__ == "__main__":
    success = check_setup()
    sys.exit(0 if success else 1)
