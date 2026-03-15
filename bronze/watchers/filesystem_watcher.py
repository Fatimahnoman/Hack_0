"""
File System Watcher - Bronze Tier
==================================
Monitors the /Inbox folder and moves new files to /Needs_Action with metadata.

Install: pip install watchdog
Run: python watchers/filesystem_watcher.py
Test: Drop any file in /Inbox folder and see what happens in /Needs_Action
"""

import os
import time
import shutil
from datetime import datetime
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# Configuration
INBOX_FOLDER = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "Inbox")
NEEDS_ACTION_FOLDER = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "Needs_Action")
CHECK_INTERVAL = 5  # seconds
FILE_PREFIX = "FILE_"


class InboxEventHandler(FileSystemEventHandler):
    """Handles file system events in the Inbox folder."""

    def __init__(self):
        super().__init__()
        self.processed_files = set()

    def on_created(self, event):
        """Called when a file or directory is created."""
        if event.is_directory:
            return

        file_path = event.src_path

        # Skip if already processed
        if file_path in self.processed_files:
            return

        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] New file detected: {os.path.basename(file_path)}")

        try:
            self.process_file(file_path)
            self.processed_files.add(file_path)
        except Exception as e:
            print(f"[ERROR] Failed to process {os.path.basename(file_path)}: {e}")

    def process_file(self, file_path):
        """Process a new file: copy to Needs_Action and create metadata."""
        # Wait briefly to ensure file is fully written
        time.sleep(0.5)

        # Get file info
        original_name = os.path.basename(file_path)
        file_size = os.path.getsize(file_path)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

        # Generate new filename with prefix
        name_without_ext = os.path.splitext(original_name)[0]
        extension = os.path.splitext(original_name)[1]
        new_filename = f"{FILE_PREFIX}{name_without_ext}{extension}"
        new_filepath = os.path.join(NEEDS_ACTION_FOLDER, new_filename)

        # Copy file to Needs_Action
        shutil.copy2(file_path, new_filepath)
        print(f"  -> Copied to Needs_Action as: {new_filename}")

        # Create metadata file
        metadata_filename = f"{FILE_PREFIX}{name_without_ext}.md"
        metadata_filepath = os.path.join(NEEDS_ACTION_FOLDER, metadata_filename)

        metadata_content = f"""---
type: file_drop
original_name: {original_name}
size: {file_size}
status: pending
---

File imported from Inbox on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}.
"""

        with open(metadata_filepath, 'w', encoding='utf-8') as f:
            f.write(metadata_content)

        print(f"  -> Created metadata: {metadata_filename}")
        print(f"  -> File size: {file_size} bytes")
        print(f"  -> Status: pending")


def ensure_directories():
    """Ensure required directories exist."""
    for folder in [INBOX_FOLDER, NEEDS_ACTION_FOLDER]:
        if not os.path.exists(folder):
            os.makedirs(folder)
            print(f"[INFO] Created directory: {folder}")


def main():
    """Main function to start the file system watcher."""
    print("=" * 60)
    print("File System Watcher - Bronze Tier")
    print("=" * 60)
    print(f"Monitoring: {INBOX_FOLDER}")
    print(f"Destination: {NEEDS_ACTION_FOLDER}")
    print(f"Check interval: {CHECK_INTERVAL} seconds")
    print("-" * 60)
    print("Press Ctrl+C to stop the watcher...")
    print("=" * 60)

    # Ensure directories exist
    ensure_directories()

    # Set up the observer
    event_handler = InboxEventHandler()
    observer = Observer()
    observer.schedule(event_handler, INBOX_FOLDER, recursive=False)

    # Start watching
    observer.start()
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Watcher started successfully!")

    try:
        while True:
            time.sleep(CHECK_INTERVAL)
    except KeyboardInterrupt:
        print("\n[INFO] Stopping watcher...")
        observer.stop()

    observer.join()
    print("[INFO] Watcher stopped.")


if __name__ == "__main__":
    main()
