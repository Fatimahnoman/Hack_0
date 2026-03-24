"""
WhatsApp Watcher - Simple File-Based Version
=============================================
This is a simple alternative to the Playwright-based WhatsApp watcher.
It monitors a folder for manually created message files.

Use this when Python 3.14 compatibility issues prevent using Playwright.

Usage: python watchers/whatsapp_watcher_simple.py
"""

import os
import time
from datetime import datetime
from pathlib import Path

# Configuration
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))).replace("Silver_Tier", "").rstrip("\\")
INBOX_FOLDER = os.path.join(PROJECT_ROOT, "Bronze_Tier", "Inbox")
NEEDS_ACTION_FOLDER = os.path.join(PROJECT_ROOT, "Bronze_Tier", "Needs_Action")
CHECK_INTERVAL = 30  # seconds

# Keywords to monitor (case-insensitive)
IMPORTANT_KEYWORDS = ["urgent", "invoice", "payment", "sales"]


def check_important_message(content: str) -> bool:
    """Check if message contains important keywords."""
    text = content.lower()
    return any(keyword in text for keyword in IMPORTANT_KEYWORDS)


def get_priority(content: str) -> str:
    """Determine priority based on keywords."""
    text = content.lower()
    if "urgent" in text:
        return "high"
    elif "invoice" in text or "payment" in text:
        return "medium"
    elif "sales" in text:
        return "normal"
    return "low"


def process_inbox_file(filepath: str) -> str:
    """Process a file from Inbox and create Needs_Action entry."""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    filename = os.path.basename(filepath)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Create new filename for Needs_Action
    new_filename = f"WHATSAPP_{filename}_{timestamp}.md"
    new_filepath = os.path.join(NEEDS_ACTION_FOLDER, new_filename)
    
    # Extract or generate metadata
    priority = get_priority(content)
    
    # Create Needs_Action file with YAML frontmatter
    na_content = f"""---
type: whatsapp_message
source: {filename}
received: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
priority: {priority}
status: pending
---

## Message Content

{content}

---
*Processed by WhatsApp Watcher (Simple) on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*
"""
    
    with open(new_filepath, 'w', encoding='utf-8') as f:
        f.write(na_content)
    
    return new_filename, priority


def ensure_directories():
    """Ensure required directories exist."""
    for folder in [INBOX_FOLDER, NEEDS_ACTION_FOLDER]:
        if not os.path.exists(folder):
            os.makedirs(folder)
            print(f"[INFO] Created directory: {folder}")


def main():
    """Main function to start simple WhatsApp watcher."""
    print("=" * 60)
    print("WhatsApp Watcher - Simple File-Based Version")
    print("=" * 60)
    print(f"Monitoring: {INBOX_FOLDER}")
    print(f"Destination: {NEEDS_ACTION_FOLDER}")
    print(f"Keywords: {', '.join(IMPORTANT_KEYWORDS)}")
    print(f"Check interval: {CHECK_INTERVAL} seconds")
    print("-" * 60)
    print("HOW TO USE:")
    print("1. Create a .txt file in /Inbox with message content")
    print("2. This watcher will process it and create entry in /Needs_Action")
    print("3. Press Ctrl+C to stop")
    print("=" * 60)

    ensure_directories()

    processed_files = set()

    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Watcher started!")

    try:
        while True:
            # Check inbox folder
            if os.path.exists(INBOX_FOLDER):
                files = [f for f in os.listdir(INBOX_FOLDER)
                        if os.path.isfile(os.path.join(INBOX_FOLDER, f))]

                for filename in files:
                    if filename in processed_files:
                        continue
                    
                    # Skip .md files (Gmail watcher handles those)
                    if filename.endswith('.md'):
                        continue

                    filepath = os.path.join(INBOX_FOLDER, filename)

                    try:
                        with open(filepath, 'r', encoding='utf-8') as f:
                            content = f.read()

                        # Check for important keywords
                        if check_important_message(content):
                            new_filename, priority = process_inbox_file(filepath)
                            processed_files.add(filename)

                            print(f"\n[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] New important message!")
                            print(f"  -> Created: {new_filename}")
                            print(f"     Priority: {priority}")
                            print(f"     Keywords found: {[kw for kw in IMPORTANT_KEYWORDS if kw in content.lower()]}")
                        else:
                            processed_files.add(filename)

                    except Exception as e:
                        print(f"[ERROR] Processing {filename}: {e}")

            time.sleep(CHECK_INTERVAL)

    except KeyboardInterrupt:
        print("\n[INFO] WhatsApp watcher stopped by user.")

    print("[INFO] WhatsApp watcher stopped.")


if __name__ == "__main__":
    main()
