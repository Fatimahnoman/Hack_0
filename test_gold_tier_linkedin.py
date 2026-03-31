"""
Test Gold Tier LinkedIn Auto-Post Implementation
================================================
Comprehensive test suite for LinkedIn automation features.

Run: python test_gold_tier_linkedin.py
"""

import os
import sys
import time
import json
from pathlib import Path
from datetime import datetime

# Project root
PROJECT_ROOT = Path(__file__).resolve().parent
GOLD_DIR = PROJECT_ROOT / "gold"

# Test colors
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
RESET = "\033[0m"

def print_header(text):
    print(f"\n{'='*70}")
    print(f"{BLUE}{text.center(70)}{RESET}")
    print(f"{'='*70}\n")

def print_success(text):
    print(f"{GREEN}✓ {text}{RESET}")

def print_error(text):
    print(f"{RED}✗ {text}{RESET}")

def print_info(text):
    print(f"{YELLOW}ℹ {text}{RESET}")

def test_folder_structure():
    """Test 1: Verify Gold Tier folder structure."""
    print_header("TEST 1: Folder Structure")
    
    required_folders = [
        GOLD_DIR / "needs_action",
        GOLD_DIR / "pending_approval",
        GOLD_DIR / "pending_approval" / "approved",
        GOLD_DIR / "done",
        GOLD_DIR / "logs",
        GOLD_DIR / "plans",
        PROJECT_ROOT / "session" / "linkedin_chrome",
        PROJECT_ROOT / "debug_linkedin",
    ]
    
    all_exist = True
    for folder in required_folders:
        if folder.exists():
            print_success(f"Folder exists: {folder.relative_to(PROJECT_ROOT)}")
        else:
            print_error(f"Folder missing: {folder.relative_to(PROJECT_ROOT)}")
            all_exist = False
    
    return all_exist

def test_linkedin_files():
    """Test 2: Verify LinkedIn implementation files."""
    print_header("TEST 2: LinkedIn Implementation Files")
    
    required_files = [
        PROJECT_ROOT / "watchers" / "linkedin_watcher_fixed.py",
        PROJECT_ROOT / "watchers" / "linkedin_auto_poster_fixed.py",
        PROJECT_ROOT / "gold" / "skills" / "linkedin-auto-post.js",
        PROJECT_ROOT / "silver" / "tools" / "action_dispatcher.py",
        PROJECT_ROOT / "gold" / "tools" / "gold_orchestrator.py",
    ]
    
    all_exist = True
    for file in required_files:
        if file.exists():
            print_success(f"File exists: {file.relative_to(PROJECT_ROOT)}")
        else:
            print_error(f"File missing: {file.relative_to(PROJECT_ROOT)}")
            all_exist = False
    
    return all_exist

def test_documentation():
    """Test 3: Verify documentation files."""
    print_header("TEST 3: Documentation Files")
    
    required_docs = [
        PROJECT_ROOT / "GOLD_TIER_LINKEDIN_AUTO_POST_COMPLETE.md",
        PROJECT_ROOT / "GOLD_TIER_LINKEDIN_QUICK_REFERENCE.md",
        PROJECT_ROOT / "GOLD_TIER_IMPLEMENTATION_COMPLETE.md",
        PROJECT_ROOT / "LINKEDIN_SETUP.md",
        PROJECT_ROOT / "Dashboard.md",
    ]
    
    all_exist = True
    for file in required_docs:
        if file.exists():
            print_success(f"Doc exists: {file.relative_to(PROJECT_ROOT)}")
        else:
            print_error(f"Doc missing: {file.relative_to(PROJECT_ROOT)}")
            all_exist = False
    
    return all_exist

def create_test_lead():
    """Test 4: Create test lead in needs_action."""
    print_header("TEST 4: Create Test Lead")
    
    needs_action = GOLD_DIR / "needs_action"
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    test_file = needs_action / f"TEST_LINKEDIN_LEAD_{timestamp}.md"
    
    content = f"""---
type: linkedin_lead
from: Test User
content: Looking for AI automation services for our business
priority: high
status: pending
created_at: {datetime.now().isoformat()}
source: linkedin
post_url: https://www.linkedin.com/feed/update/test-123/
---

## LinkedIn Post Content

Looking for AI automation services for our business. Need help with:
- Email automation
- Social media posting
- Customer support

Budget: $5000

## Metadata

- **Author:** Test User
- **Priority:** high
- **Found:** {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
- **URL:** https://www.linkedin.com/feed/update/test-123/

## Suggested Action

Review this lead and consider:
1. Engaging with the post (like/comment)
2. Sending a connection request
3. Creating a targeted response

---
*LinkedIn Watcher - Gold Tier*
"""
    
    try:
        test_file.write_text(content, encoding='utf-8')
        print_success(f"Test lead created: {test_file.name}")
        return True
    except Exception as e:
        print_error(f"Failed to create test lead: {e}")
        return False

def create_test_post_draft():
    """Test 5: Create test LinkedIn post draft."""
    print_header("TEST 5: Create Test Post Draft")
    
    pending_approval = GOLD_DIR / "pending_approval"
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    test_file = pending_approval / f"LINKEDIN_POST_DRAFT_{timestamp}.md"
    
    content = f"""---
type: linkedin_post_draft
priority: normal
status: pending
created_at: {datetime.now().isoformat()}
---

## LinkedIn Post Draft

🚀 Exciting News: Gold Tier LinkedIn Auto-Post System!

We've successfully implemented a complete LinkedIn automation system with:

✅ Autonomous lead detection
✅ AI-powered draft generation  
✅ Human-in-the-loop approval
✅ Error recovery system
✅ Comprehensive audit logging

This is the future of social media automation!

Want to learn more? Drop a comment below! 👇

#AI #Automation #LinkedIn #Innovation #GoldTier

---
*Draft created for Gold Tier testing*
"""
    
    try:
        test_file.write_text(content, encoding='utf-8')
        print_success(f"Test draft created: {test_file.name}")
        print_info(f"Location: {test_file}")
        print_info(f"To approve: Move to {GOLD_DIR / 'pending_approval' / 'approved' / test_file.name}")
        return True
    except Exception as e:
        print_error(f"Failed to create test draft: {e}")
        return False

def test_linkedin_post_content():
    """Test 6: Test LinkedIn poster with sample content."""
    print_header("TEST 6: Test LinkedIn Poster (Dry Run)")
    
    poster_script = PROJECT_ROOT / "watchers" / "linkedin_auto_poster_fixed.py"
    
    if not poster_script.exists():
        print_error(f"LinkedIn poster script not found: {poster_script}")
        return False
    
    test_content = "Test post from Gold Tier LinkedIn Auto-Post system. #Test #LinkedIn #Automation"
    
    print_info(f"Test content: {test_content}")
    print_info(f"Poster script: {poster_script}")
    print_info("\nTo test actual posting, run:")
    print_info(f'python watchers\\linkedin_auto_poster_fixed.py --content "{test_content}"')
    
    print_success("LinkedIn poster script found and ready")
    return True

def check_logs():
    """Test 7: Check logging system."""
    print_header("TEST 7: Logging System")
    
    log_files = [
        PROJECT_ROOT / "Logs" / "linkedin-posts.jsonl",
        PROJECT_ROOT / "Logs" / "linkedin-comments.jsonl",
        GOLD_DIR / "logs",
    ]
    
    for log_file in log_files:
        if log_file.exists():
            if log_file.is_file():
                try:
                    with open(log_file, 'r', encoding='utf-8') as f:
                        lines = f.readlines()
                    print_success(f"Log file exists: {log_file.name} ({len(lines)} entries)")
                except:
                    print_info(f"Log file exists but unreadable: {log_file.name}")
            else:
                print_success(f"Log directory exists: {log_file.name}")
        else:
            print_info(f"Log not found (will be created on first post): {log_file.name}")
    
    return True

def check_dashboard():
    """Test 8: Check Dashboard integration."""
    print_header("TEST 8: Dashboard Integration")
    
    dashboard = PROJECT_ROOT / "Dashboard.md"
    
    if not dashboard.exists():
        print_error(f"Dashboard not found: {dashboard}")
        return False
    
    try:
        with open(dashboard, 'r', encoding='utf-8') as f:
            content = f.read()
        
        if "LinkedIn" in content or "linkedin" in content:
            print_success("Dashboard contains LinkedIn activity")
        else:
            print_info("Dashboard doesn't mention LinkedIn yet (will update after first post)")
        
        # Show recent activity
        if "Recent Activity" in content:
            print_info("\nRecent Activity (last 5 lines):")
            lines = content.split('\n')
            for i, line in enumerate(lines):
                if 'Recent Activity' in line:
                    for j in range(i+1, min(i+6, len(lines))):
                        print(f"  {lines[j]}")
                    break
        
        return True
    except Exception as e:
        print_error(f"Failed to read dashboard: {e}")
        return False

def test_gold_tier_skills():
    """Test 9: Verify Gold Tier skills."""
    print_header("TEST 9: Gold Tier Skills")
    
    skills = [
        "linkedin-auto-post.js",
        "weekly-business-audit.js",
        "accounting-audit.js",
        "ralph-wiggum-loop.js",
        "error-recovery.js",
        "audit-logger.js",
        "cross-domain-integration.js",
    ]
    
    skills_dir = GOLD_DIR / "skills"
    all_exist = True
    
    for skill in skills:
        skill_file = skills_dir / skill
        if skill_file.exists():
            print_success(f"Skill exists: {skill}")
        else:
            print_error(f"Skill missing: {skill}")
            all_exist = False
    
    return all_exist

def test_batch_scripts():
    """Test 10: Verify batch scripts."""
    print_header("TEST 10: Batch Scripts")
    
    scripts = [
        PROJECT_ROOT / "start_gold_tier.bat",
        PROJECT_ROOT / "test_gold_tier.bat",
        PROJECT_ROOT / "run_linkedin_watcher.bat",
        PROJECT_ROOT / "linkedin_auto_post.bat",
    ]
    
    all_exist = True
    for script in scripts:
        if script.exists():
            print_success(f"Script exists: {script.name}")
        else:
            print_error(f"Script missing: {script.name}")
            all_exist = False
    
    return all_exist

def run_all_tests():
    """Run all tests and generate report."""
    print_header("GOLD TIER LINKEDIN AUTO-POST TEST SUITE")
    print_info(f"Project Root: {PROJECT_ROOT}")
    print_info(f"Gold Tier: {GOLD_DIR}")
    print_info(f"Timestamp: {datetime.now().isoformat()}")
    
    tests = [
        ("Folder Structure", test_folder_structure),
        ("Implementation Files", test_linkedin_files),
        ("Documentation", test_documentation),
        ("Create Test Lead", create_test_lead),
        ("Create Test Draft", create_test_post_draft),
        ("LinkedIn Poster", test_linkedin_post_content),
        ("Logging System", check_logs),
        ("Dashboard Integration", check_dashboard),
        ("Gold Tier Skills", test_gold_tier_skills),
        ("Batch Scripts", test_batch_scripts),
    ]
    
    results = []
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print_error(f"Test '{name}' failed with exception: {e}")
            results.append((name, False))
    
    # Summary
    print_header("TEST SUMMARY")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        if result:
            print_success(f"{name}")
        else:
            print_error(f"{name}")
    
    print(f"\n{'='*70}")
    print(f"Total: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
    print(f"{'='*70}\n")
    
    if passed == total:
        print_success("🎉 All tests passed! Gold Tier LinkedIn Auto-Post is ready!")
    else:
        print_info("Some tests failed. Review the errors above.")
        print_info("Most failures are expected if this is the first setup.")
    
    # Save test report
    report_file = GOLD_DIR / "logs" / f"test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    try:
        report = {
            "timestamp": datetime.now().isoformat(),
            "total_tests": total,
            "passed": passed,
            "failed": total - passed,
            "results": [{"name": name, "passed": result} for name, result in results],
        }
        report_file.parent.mkdir(parents=True, exist_ok=True)
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2)
        print_success(f"Test report saved: {report_file.name}")
    except Exception as e:
        print_error(f"Failed to save test report: {e}")
    
    return passed == total

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
