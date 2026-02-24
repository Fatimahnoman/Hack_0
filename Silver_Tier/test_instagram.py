"""
Quick Instagram Test - Check if Instagram watcher is working
"""

import os
import sys
from pathlib import Path
from datetime import datetime

PROJECT_ROOT = Path(__file__).parent
VAULT_PATH = PROJECT_ROOT / "Vault"
NEEDS_ACTION_PATH = VAULT_PATH / "Needs_Action"

print("=" * 60)
print("Instagram Watcher - Quick Test")
print("=" * 60)

# Check if session exists
session_path = PROJECT_ROOT / "instagram_session"
if session_path.exists():
    print(f"[OK] Instagram session found: {session_path}")
    print(f"  Session files: {len(list(session_path.glob('**/*')))} files")
else:
    print("[ERROR] Instagram session NOT found")
    print("  Run 'python watchers/instagram_watcher.py' to login first")

print()

# Check for Instagram files in Needs_Action
instagram_files = list(NEEDS_ACTION_PATH.glob("INSTAGRAM*.md"))

if instagram_files:
    print(f"[OK] Found {len(instagram_files)} Instagram file(s) in Needs_Action/")
    print()
    for file in instagram_files[:5]:  # Show first 5
        mtime = datetime.fromtimestamp(file.stat().st_mtime)
        print(f"  - {file.name} ({mtime})")
    
    if len(instagram_files) > 5:
        print(f"  ... and {len(instagram_files) - 5} more")
else:
    print("[EMPTY] No Instagram files found yet")
    print()
    print("To test:")
    print("1. Run: python watchers/instagram_watcher.py")
    print("2. Login to Instagram in the browser")
    print("3. Create a new post on Instagram")
    print("4. Wait for watcher to check (or restart watcher)")
    print("5. Check this folder for .md files")

print()
print("=" * 60)

# Check Approved and Done folders
approved_files = list((VAULT_PATH / "Approved").glob("INSTAGRAM*.md"))
done_files = list((VAULT_PATH / "Done").glob("INSTAGRAM*.md"))

print(f"Approved folder: {len(approved_files)} Instagram file(s)")
print(f"Done folder: {len(done_files)} Instagram file(s)")
print("=" * 60)
