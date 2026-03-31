"""
Test Complete Workflow - AI Employee
=====================================
This script tests the entire workflow:
1. Creates test files in Needs_Action with keywords
2. Verifies Gold Orchestrator creates drafts in Pending_Approval
3. Verifies files move to Done only after draft creation

Run: python test_complete_workflow.py
"""

import os
import time
from pathlib import Path
from datetime import datetime

PROJECT_ROOT = Path(__file__).resolve().parent
NEEDS_ACTION = PROJECT_ROOT / "Needs_Action"
PENDING_APPROVAL = PROJECT_ROOT / "Pending_Approval"
DONE = PROJECT_ROOT / "Done"

# Keywords that should trigger processing
KEYWORDS = ["urgent", "sales", "payment", "invoice", "deal", "order",
            "client", "customer", "quotation", "proposal", "overdue",
            "follow up", "meeting", "booking", "asap"]

def create_test_file(platform: str, content: str):
    """Create a test file in Needs_Action."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"TEST_{platform}_{timestamp}.md"
    filepath = NEEDS_ACTION / filename
    
    md_content = f"""---
type: {platform.lower()}
from: Test User
subject: Test Message
received: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
priority: high
status: pending
---

## Content

{content}

---
*Test file created by test_complete_workflow.py*
"""
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(md_content)
    
    print(f"✓ Created test file: {filename}")
    return filename

def check_draft_created(original_filename: str, timeout: int = 30) -> bool:
    """Check if a draft was created in Pending_Approval."""
    base_name = original_filename.replace('.md', '').replace(f"TEST_{original_filename.split('_')[1]}_", "")
    
    start = time.time()
    while time.time() - start < timeout:
        # Look for DRAFT_ files
        drafts = list(PENDING_APPROVAL.glob("DRAFT_*.md"))
        for draft in drafts:
            if original_filename.replace('.md', '') in draft.name:
                print(f"✓ Draft found: {draft.name}")
                return True
        time.sleep(1)
    
    print(f"✗ No draft found for {original_filename}")
    return False

def check_file_moved_to_done(original_filename: str, timeout: int = 30) -> bool:
    """Check if file was moved to Done."""
    start = time.time()
    while time.time() - start < timeout:
        if (DONE / original_filename).exists():
            print(f"✓ File moved to Done: {original_filename}")
            return True
        time.sleep(1)
    
    print(f"✗ File not moved to Done: {original_filename}")
    return False

def main():
    print("=" * 70)
    print("AI EMPLOYEE - COMPLETE WORKFLOW TEST")
    print("=" * 70)
    
    # Ensure directories exist
    for folder in [NEEDS_ACTION, PENDING_APPROVAL, DONE]:
        folder.mkdir(parents=True, exist_ok=True)
    
    print(f"\nDirectories:")
    print(f"  Needs_Action: {NEEDS_ACTION}")
    print(f"  Pending_Approval: {PENDING_APPROVAL}")
    print(f"  Done: {DONE}")
    
    print("\n" + "=" * 70)
    print("STEP 1: Creating test files with IMPORTANT KEYWORDS")
    print("=" * 70)
    
    test_files = [
        ("WHATSAPP", "URGENT: Payment pending for client order #12345"),
        ("GMAIL", "Invoice overdue - follow up needed ASAP"),
        ("LINKEDIN", "New sales opportunity - customer interested in quotation"),
        ("TWITTER", "Meeting booking request from potential deal"),
    ]
    
    created_files = []
    for platform, content in test_files:
        # Check if content has keywords
        has_keyword = any(kw in content.lower() for kw in KEYWORDS)
        print(f"\nCreating {platform} test file...")
        print(f"  Content: {content[:60]}...")
        print(f"  Has keyword: {'✓ YES' if has_keyword else '✗ NO'}")
        
        if has_keyword:
            filename = create_test_file(platform, content)
            created_files.append(filename)
            time.sleep(2)  # Wait between files
    
    print("\n" + "=" * 70)
    print(f"Created {len(created_files)} test files in Needs_Action")
    print("=" * 70)
    
    print("\n" + "=" * 70)
    print("STEP 2: Waiting for Gold Orchestrator to process...")
    print("=" * 70)
    print("\nNOTE: Make sure Gold Orchestrator is running!")
    print("If not, run: python gold/tools/gold_orchestrator.py")
    print("\nWaiting 60 seconds for processing...\n")
    
    results = {"drafts_created": 0, "files_moved": 0, "failed": 0}
    
    for filename in created_files:
        print(f"\nChecking: {filename}")
        
        # Check if draft was created
        draft_created = check_draft_created(filename, timeout=30)
        if draft_created:
            results["drafts_created"] += 1
        
        # Check if file moved to Done
        file_moved = check_file_moved_to_done(filename, timeout=30)
        if file_moved:
            results["files_moved"] += 1
        
        if not draft_created or not file_moved:
            results["failed"] += 1
    
    print("\n" + "=" * 70)
    print("TEST RESULTS")
    print("=" * 70)
    print(f"  Files created: {len(created_files)}")
    print(f"  Drafts created in Pending_Approval: {results['drafts_created']}")
    print(f"  Files moved to Done: {results['files_moved']}")
    print(f"  Failed: {results['failed']}")
    
    if results['drafts_created'] == len(created_files) and results['files_moved'] == len(created_files):
        print("\n✓✓✓ ALL TESTS PASSED! ✓✓✓")
        print("Workflow is working correctly!")
    else:
        print("\n✗✗✗ TESTS FAILED! ✗✗✗")
        print("\nTroubleshooting:")
        print("1. Make sure Gold Orchestrator is running")
        print("2. Check Logs folder for errors")
        print("3. Verify claude.cmd is available (if using Claude)")
    
    print("\n" + "=" * 70)

if __name__ == "__main__":
    main()
