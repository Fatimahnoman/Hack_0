"""
Manual Test - Process file from Approved folder
================================================
Run this to manually test Action Dispatcher
"""

import sys
import time
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from silver.tools.action_dispatcher import ActionDispatcher, APPROVED_FOLDER, PENDING_APPROVAL_FOLDER

def main():
    print("=" * 70)
    print("ACTION DISPATCHER - MANUAL TEST")
    print("=" * 70)
    
    dispatcher = ActionDispatcher(check_interval=5)
    
    # Check for files in Approved folder
    print("\nChecking Approved folder...")
    approved_files = list(APPROVED_FOLDER.glob("*.md")) if APPROVED_FOLDER.exists() else []
    print(f"Files in Approved: {len(approved_files)}")
    for f in approved_files:
        print(f"  - {f.name}")
    
    # Check for DRAFT files in Pending_Approval root
    print("\nChecking Pending_Approval root for DRAFT files...")
    draft_files = list(PENDING_APPROVAL_FOLDER.glob("DRAFT_*.md")) if PENDING_APPROVAL_FOLDER.exists() else []
    print(f"DRAFT files in Pending_Approval: {len(draft_files)}")
    for f in draft_files:
        print(f"  - {f.name}")
    
    # Process files
    print("\n" + "=" * 70)
    print("Processing files...")
    print("=" * 70)
    
    all_files = approved_files + draft_files
    
    if not all_files:
        print("\n[INFO] No files to process!")
        print("\nNOTE: To test, manually move a DRAFT file to Approved folder:")
        print(f"  {PENDING_APPROVAL_FOLDER}")
        print("  ↓")
        print(f"  {APPROVED_FOLDER}")
        return
    
    for filepath in all_files:
        print(f"\n[TEST] Processing: {filepath.name}")
        try:
            success = dispatcher.process_file(filepath)
            if success:
                print(f"[SUCCESS] {filepath.name} processed successfully")
                print(f"[MOVED] File moved to Done")
            else:
                print(f"[FAILED] {filepath.name} processing failed")
        except Exception as e:
            print(f"[ERROR] {filepath.name}: {e}")
            import traceback
            traceback.print_exc()
    
    print("\n" + "=" * 70)
    print("TEST COMPLETE")
    print("=" * 70)
    
    # Show stats
    print("\nFinal Stats:")
    for key, value in dispatcher.stats.items():
        print(f"  {key}: {value}")

if __name__ == "__main__":
    main()
