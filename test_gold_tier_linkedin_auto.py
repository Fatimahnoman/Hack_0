"""
Test Script for Gold Tier LinkedIn Auto Poster
==============================================
Tests the integration between Action Dispatcher and LinkedIn Auto Poster.

Run: python test_gold_tier_linkedin_auto.py
"""

import os
import sys
import time
from pathlib import Path
from datetime import datetime

# Configuration
PROJECT_ROOT = Path(__file__).resolve().parent
GOLD_DIR = PROJECT_ROOT / "gold"
APPROVED_FOLDER = GOLD_DIR / "pending_approval" / "approved"
DONE_FOLDER = GOLD_DIR / "done"
FAILED_FOLDER = GOLD_DIR / "failed"
SESSION_PATH = PROJECT_ROOT / "session" / "linkedin"
LINKEDIN_POSTER = GOLD_DIR / "watchers" / "linkedin_auto_poster.py"
ACTION_DISPATCHER = PROJECT_ROOT / "silver" / "tools" / "action_dispatcher.py"


def test_directories():
    """Test that all required directories exist."""
    print("\n" + "=" * 60)
    print("TEST 1: Directory Structure")
    print("=" * 60)
    
    required_dirs = [
        APPROVED_FOLDER,
        DONE_FOLDER,
        FAILED_FOLDER,
        SESSION_PATH,
        GOLD_DIR / "logs",
        PROJECT_ROOT / "debug_linkedin"
    ]
    
    all_exist = True
    for dir_path in required_dirs:
        exists = dir_path.exists()
        status = "✓" if exists else "✗"
        print(f"  {status} {dir_path.relative_to(PROJECT_ROOT)}")
        if not exists:
            dir_path.mkdir(parents=True, exist_ok=True)
            print(f"    -> Created directory")
        all_exist = all_exist and exists
    
    return all_exist


def test_linkedin_poster_script():
    """Test that LinkedIn poster script exists and is valid."""
    print("\n" + "=" * 60)
    print("TEST 2: LinkedIn Poster Script")
    print("=" * 60)
    
    if not LINKEDIN_POSTER.exists():
        print(f"  ✗ Script not found: {LINKEDIN_POSTER}")
        return False
    
    print(f"  ✓ Script exists: {LINKEDIN_POSTER.name}")
    
    # Check script is valid Python
    try:
        with open(LINKEDIN_POSTER, 'r', encoding='utf-8') as f:
            content = f.read()
            if 'def post_to_linkedin' in content:
                print("  ✓ Contains post_to_linkedin function")
            else:
                print("  ✗ Missing post_to_linkedin function")
                return False
            
            if 'SESSION_PATH' in content:
                print("  ✓ Uses persistent session")
            else:
                print("  ✗ Missing persistent session")
                return False
            
            if 'TYPE_DELAY' in content:
                print("  ✓ Has slow typing (anti-bot)")
            else:
                print("  ✗ Missing slow typing")
                return False
            
            if 'action_dispatcher' in content.lower() or '--file' in content:
                print("  ✓ Action Dispatcher compatible")
            else:
                print("  ⚠ May not be fully Action Dispatcher compatible")
    
    except Exception as e:
        print(f"  ✗ Error reading script: {e}")
        return False
    
    return True


def test_action_dispatcher_integration():
    """Test Action Dispatcher integration."""
    print("\n" + "=" * 60)
    print("TEST 3: Action Dispatcher Integration")
    print("=" * 60)
    
    if not ACTION_DISPATCHER.exists():
        print(f"  ✗ Action Dispatcher not found: {ACTION_DISPATCHER}")
        return False
    
    print(f"  ✓ Action Dispatcher exists")
    
    # Check it references the correct LinkedIn poster
    try:
        with open(ACTION_DISPATCHER, 'r', encoding='utf-8') as f:
            content = f.read()
            
            if 'gold/watchers/linkedin_auto_poster.py' in content or 'gold\\watchers\\linkedin_auto_poster.py' in content:
                print("  ✓ References Gold Tier LinkedIn poster")
            else:
                print("  ⚠ May not reference Gold Tier LinkedIn poster")
            
            if 'execute_linkedin_post' in content:
                print("  ✓ Has LinkedIn post execution logic")
            else:
                print("  ✗ Missing LinkedIn post execution")
                return False
            
            if 'APPROVED_FOLDER' in content:
                print("  ✓ Monitors Approved folder")
            else:
                print("  ⚠ May not monitor Approved folder")
    
    except Exception as e:
        print(f"  ✗ Error reading Action Dispatcher: {e}")
        return False
    
    return True


def test_create_test_file():
    """Create a test file in Approved folder."""
    print("\n" + "=" * 60)
    print("TEST 4: Create Test File")
    print("=" * 60)
    
    test_content = f"""---
type: linkedin_post
status: approved
created: {datetime.now().isoformat()}
---

## LinkedIn Post Draft

🧪 **TEST POST** - Gold Tier LinkedIn Auto Poster

This is a test post to verify the integration is working correctly.

**Test Details:**
- Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
- Source: test_gold_tier_linkedin_auto.py
- Action: Automated test

#Testing #GoldTier #LinkedIn #Automation

---
*This is an automated test post. Please ignore.*
"""
    
    test_file = APPROVED_FOLDER / f"test_linkedin_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
    
    try:
        test_file.write_text(test_content, encoding='utf-8')
        print(f"  ✓ Test file created: {test_file.name}")
        print(f"  Location: {test_file}")
        return test_file
    except Exception as e:
        print(f"  ✗ Error creating test file: {e}")
        return None


def test_manual_post():
    """Test manual post using LinkedIn poster."""
    print("\n" + "=" * 60)
    print("TEST 5: Manual Post Test")
    print("=" * 60)
    
    test_content = "🧪 Test post from Gold Tier LinkedIn Auto Poster - Automated test"
    
    print(f"  Running: python {LINKEDIN_POSTER} --content \"{test_content[:50]}...\"")
    print("  NOTE: This will launch a browser window")
    print("  Press Ctrl+C to skip this test")
    print()
    
    try:
        import subprocess
        result = subprocess.run(
            [sys.executable, str(LINKEDIN_POSTER), "--content", test_content],
            cwd=str(PROJECT_ROOT),
            capture_output=True,
            text=True,
            timeout=300  # 5 minute timeout
        )
        
        if result.returncode == 0:
            print("  ✓ Manual post test PASSED")
            return True
        else:
            print(f"  ✗ Manual post test FAILED")
            print(f"  Error: {result.stderr[:200]}")
            return False
            
    except subprocess.TimeoutExpired:
        print("  ✗ Test timed out (5 minutes)")
        return False
    except KeyboardInterrupt:
        print("  ⚠ Test skipped by user")
        return None
    except Exception as e:
        print(f"  ✗ Error: {e}")
        return False


def cleanup_test_files():
    """Clean up test files from Approved folder."""
    print("\n" + "=" * 60)
    print("CLEANUP: Test Files")
    print("=" * 60)
    
    test_files = list(APPROVED_FOLDER.glob("test_linkedin_*.md"))
    
    for test_file in test_files:
        try:
            test_file.unlink()
            print(f"  ✓ Deleted: {test_file.name}")
        except Exception as e:
            print(f"  ✗ Error deleting {test_file.name}: {e}")


def main():
    """Run all tests."""
    print("\n" + "=" * 70)
    print("GOLD TIER LINKEDIN AUTO POSTER - INTEGRATION TEST")
    print("=" * 70)
    print(f"Project Root: {PROJECT_ROOT}")
    print(f"Gold Tier: {GOLD_DIR}")
    print(f"Session: {SESSION_PATH}")
    print("=" * 70)
    
    results = {
        "directories": False,
        "linkedin_poster": False,
        "action_dispatcher": False,
        "test_file": None,
        "manual_post": None
    }
    
    # Run tests
    results["directories"] = test_directories()
    results["linkedin_poster"] = test_linkedin_poster_script()
    results["action_dispatcher"] = test_action_dispatcher_integration()
    results["test_file"] = test_create_test_file()
    
    # Ask user before running manual post test
    print("\n" + "=" * 60)
    print("READY FOR MANUAL POST TEST")
    print("=" * 60)
    print("This test will:")
    print("  1. Launch a browser window")
    print("  2. Navigate to LinkedIn")
    print("  3. Post a test message")
    print("  4. Take screenshots")
    print()
    
    response = input("Run manual post test? (y/n): ").strip().lower()
    
    if response == 'y':
        results["manual_post"] = test_manual_post()
    else:
        print("  ⚠ Manual post test skipped")
        results["manual_post"] = "skipped"
    
    # Summary
    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)
    
    passed = 0
    failed = 0
    skipped = 0
    
    for test_name, result in results.items():
        if result is True:
            status = "✓ PASS"
            passed += 1
        elif result is False:
            status = "✗ FAIL"
            failed += 1
        elif result is None or result == "skipped":
            status = "⚠ SKIP"
            skipped += 1
        
        print(f"  {status}: {test_name.replace('_', ' ').title()}")
    
    print()
    print(f"  Total: {passed} passed, {failed} failed, {skipped} skipped")
    print("=" * 70)
    
    # Cleanup
    if results["test_file"]:
        cleanup = input("\nCleanup test file? (y/n): ").strip().lower()
        if cleanup == 'y':
            cleanup_test_files()
    
    # Final status
    if failed == 0 and passed > 0:
        print("\n✓ ALL TESTS PASSED!")
        print("\nNext steps:")
        print("  1. Ensure LinkedIn session is logged in")
        print("  2. Run: python silver/tools/action_dispatcher.py --daemon --interval 10")
        print("  3. Move a file to gold/pending_approval/approved/")
        print("  4. Watch it auto-post to LinkedIn!")
        return 0
    else:
        print("\n⚠ SOME TESTS FAILED")
        print("\nTroubleshooting:")
        print("  1. Check logs in gold/logs/")
        print("  2. Check screenshots in debug_linkedin/")
        print("  3. Ensure Playwright is installed: pip install playwright")
        print("  4. Install Chromium: playwright install chromium")
        return 1


if __name__ == "__main__":
    sys.exit(main())
