"""
Twitter Watcher - Simple File-Based Version
============================================
Monitors Inbox folder for Twitter-related tasks.
Creates entries in Needs_Action for the orchestrator to process.

Usage: python watchers/twitter_watcher.py
"""

import os
import time
from datetime import datetime
from pathlib import Path

# Configuration
PROJECT_ROOT = Path(__file__).resolve().parent.parent
INBOX_FOLDER = PROJECT_ROOT / "Inbox"
NEEDS_ACTION_FOLDER = PROJECT_ROOT / "gold" / "needs_action"
CHECK_INTERVAL = 30  # seconds

# Keywords to monitor (case-insensitive)
IMPORTANT_KEYWORDS = [
    "urgent", "sales", "payment", "invoice", "deal", "order", 
    "client", "customer", "quotation", "proposal", "overdue", 
    "follow up", "meeting", "booking", "asap"
]


def check_important_message(content: str) -> bool:
    """Check if message contains important keywords."""
    text = content.lower()
    return any(keyword in text for keyword in IMPORTANT_KEYWORDS)


def get_priority(content: str) -> str:
    """Determine priority based on keywords."""
    text = content.lower()
    if "urgent" in text:
        return "high"
    elif "post" in text or "tweet" in text:
        return "medium"
    return "low"


def process_inbox_file(filepath: Path) -> str:
    """Process a file from Inbox and create Needs_Action entry."""
    content = filepath.read_text(encoding='utf-8')
    
    filename = filepath.name
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Create new filename for Needs_Action
    new_filename = f"TWITTER_{filename}_{timestamp}.md"
    new_filepath = NEEDS_ACTION_FOLDER / new_filename
    
    # Extract or generate metadata
    priority = get_priority(content)
    
    # Create Needs_Action file with YAML frontmatter
    na_content = f"""---
type: tweet_request
source: {filename}
received: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
priority: {priority}
status: pending
---

## Tweet Request Content

{content}

---
*Processed by Twitter Watcher (Simple) on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*
"""
    
    new_filepath.write_text(na_content, encoding='utf-8')
    return new_filename, priority


def ensure_directories():
    """Ensure required directories exist."""
    INBOX_FOLDER.mkdir(parents=True, exist_ok=True)
    NEEDS_ACTION_FOLDER.mkdir(parents=True, exist_ok=True)


def main():
    """Main function to start simple Twitter watcher."""
    print("=" * 60)
    print("Twitter Watcher - Simple File-Based Version")
    print("=" * 60)
    print(f"Monitoring: {INBOX_FOLDER} (Filter: TWITTER_*)")
    print(f"Destination: {NEEDS_ACTION_FOLDER}")
    print(f"Check interval: {CHECK_INTERVAL} seconds")
    print("-" * 60)
    
    ensure_directories()
    
    processed_files = set()
    
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Watcher started!")
    
    try:
        while True:
            # Check inbox folder for TWITTER_ files
            if INBOX_FOLDER.exists():
                for filepath in INBOX_FOLDER.glob("TWITTER_*"):
                    if filepath.name in processed_files:
                        continue
                    
                    try:
                        new_filename, priority = process_inbox_file(filepath)
                        processed_files.add(filepath.name)
                        
                        print(f"\n[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] New Twitter task!")
                        print(f"  -> Created: {new_filename}")
                        print(f"     Priority: {priority}")
                    except Exception as e:
                        print(f"[ERROR] Processing {filepath.name}: {e}")
            
            time.sleep(CHECK_INTERVAL)
    
    except KeyboardInterrupt:
        print("\n[INFO] Twitter watcher stopped by user.")


if __name__ == "__main__":
    main()
