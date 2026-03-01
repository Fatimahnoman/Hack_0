"""
Workflow Manager for Silver Tier
Auto-moves files between workflow stages based on time and markers
"""

import os
import time
import shutil
from datetime import datetime, timedelta
from pathlib import Path
import logging

# Configuration
CHECK_INTERVAL = 60  # seconds
PENDING_DELAY = 120  # seconds before moving to Pending_Approval

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class WorkflowManager:
    """Manages file workflow: Needs_Action → Pending_Approval → Approved/Done"""

    def __init__(self):
        self.vault_path = Path(__file__).parent / "Vault"
        self.needs_action_path = self.vault_path / "Needs_Action"
        self.pending_approval_path = self.vault_path / "Pending_Approval"
        self.approved_path = self.vault_path / "Approved"
        self.done_path = self.vault_path / "Done"

        # Ensure all directories exist
        for path in [self.needs_action_path, self.pending_approval_path, 
                     self.approved_path, self.done_path]:
            path.mkdir(parents=True, exist_ok=True)

        # Track file timestamps
        self.file_timestamps = {}

        logger.info(f"Workflow Manager initialized")
        logger.info(f"Vault: {self.vault_path}")

    def load_existing_timestamps(self):
        """Load timestamps for existing files in Pending_Approval."""
        if not self.pending_approval_path.exists():
            return
        
        for filepath in self.pending_approval_path.glob("*.md"):
            # Use file modification time
            mtime = datetime.fromtimestamp(filepath.stat().st_mtime)
            self.file_timestamps[filepath.name] = mtime
            logger.info(f"Loaded existing file: {filepath.name} ({mtime})")

    def move_to_pending(self, filepath: Path):
        """Move file from Needs_Action to Pending_Approval."""
        try:
            dest = self.pending_approval_path / filepath.name
            shutil.move(str(filepath), str(dest))
            self.file_timestamps[filepath.name] = datetime.now()
            logger.info(f"✓ Moved to Pending: {filepath.name}")
            return True
        except Exception as e:
            logger.error(f"Error moving to pending: {e}")
            return False

    def check_and_move_approved(self, filepath: Path):
        """Check if file has [APPROVED] marker and move to Approved."""
        try:
            content = filepath.read_text(encoding='utf-8')

            # Only move if [APPROVED] marker is present
            if "[APPROVED]" in content:
                dest = self.approved_path / filepath.name
                shutil.move(str(filepath), str(dest))
                if filepath.name in self.file_timestamps:
                    del self.file_timestamps[filepath.name]
                logger.info(f"✓ Approved: {filepath.name}")
                return True
        except Exception as e:
            logger.error(f"Error checking approved: {e}")
        return False

    def check_and_move_done(self, filepath: Path):
        """Check if file has [DONE] marker and move to Done."""
        try:
            content = filepath.read_text(encoding='utf-8')

            # Only move if [DONE] marker is present
            if "[DONE]" in content:
                dest = self.done_path / filepath.name
                shutil.move(str(filepath), str(dest))
                if filepath.name in self.file_timestamps:
                    del self.file_timestamps[filepath.name]
                logger.info(f"✓ Done: {filepath.name}")
                return True
        except Exception as e:
            logger.error(f"Error checking done: {e}")
        return False

    def process_needs_action(self):
        """Check Needs_Action files and move old ones to Pending_Approval."""
        if not self.needs_action_path.exists():
            return 0

        moved_count = 0
        now = datetime.now()

        for filepath in self.needs_action_path.glob("*.md"):
            # Use file modification time for tracking
            try:
                file_mtime = datetime.fromtimestamp(filepath.stat().st_mtime)
                age = (now - file_mtime).total_seconds()
                
                logger.info(f"File: {filepath.name}, Age: {age:.0f}s (need {PENDING_DELAY}s)")

                if age >= PENDING_DELAY:
                    if self.move_to_pending(filepath):
                        moved_count += 1
            except Exception as e:
                logger.error(f"Error processing {filepath.name}: {e}")

        return moved_count

    def process_approved(self):
        """Check Approved files for [DONE] marker and move to Done."""
        if not self.approved_path.exists():
            return 0

        processed = 0
        for filepath in self.approved_path.glob("*.md"):
            # Skip Instagram post requests (already in Done after posting)
            if filepath.name.startswith("INSTA_POST_REQUEST"):
                continue

            if self.check_and_move_done(filepath):
                processed += 1

        return processed

    def process_pending_approval(self):
        """Check Pending_Approval files for markers."""
        if not self.pending_approval_path.exists():
            return 0

        processed = 0
        for filepath in self.pending_approval_path.glob("*.md"):
            # Skip Instagram post requests (handled by instagram_watcher)
            if filepath.name.startswith("INSTA_POST_REQUEST"):
                continue

            if self.check_and_move_approved(filepath):
                processed += 1
            elif self.check_and_move_done(filepath):
                processed += 1

        return processed

    def process_instagram_posts(self):
        """Move Instagram posts from Pending_Approval to Approved if they have [APPROVED] marker."""
        if not self.pending_approval_path.exists():
            return 0

        moved = 0
        for filepath in self.pending_approval_path.glob("INSTA_POST_REQUEST_*.md"):
            try:
                content = filepath.read_text(encoding='utf-8')
                
                # Check if file has [APPROVED] marker
                if "[APPROVED]" in content:
                    dest = self.approved_path / filepath.name
                    shutil.move(str(filepath), str(dest))
                    logger.info(f"✓ Instagram post approved: {filepath.name}")
                    moved += 1
            except Exception as e:
                logger.error(f"Error processing Instagram post: {e}")

        return moved

    def run(self):
        """Main workflow loop."""
        logger.info("=" * 60)
        logger.info("Workflow Manager - Silver Tier")
        logger.info("=" * 60)
        logger.info(f"Check Interval: {CHECK_INTERVAL} seconds")
        logger.info(f"Pending Delay: {PENDING_DELAY} seconds")
        logger.info("=" * 60)

        # Load existing files
        self.load_existing_timestamps()

        while True:
            try:
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                logger.info(f"\n[{timestamp}] Processing workflow...")

                # Process Needs_Action → Pending_Approval
                moved = self.process_needs_action()
                if moved > 0:
                    logger.info(f"Moved {moved} file(s) to Pending_Approval")

                # Process Pending_Approval → Approved (for non-Instagram files with [APPROVED])
                processed = self.process_pending_approval()
                if processed > 0:
                    logger.info(f"Processed {processed} file(s) with markers")

                # Process Instagram posts: Pending_Approval → Approved (if [APPROVED])
                insta_moved = self.process_instagram_posts()
                if insta_moved > 0:
                    logger.info(f"Moved {insta_moved} Instagram post(s) to Approved")

                # Process Approved → Done (if [DONE] marker)
                done_count = self.process_approved()
                if done_count > 0:
                    logger.info(f"Moved {done_count} file(s) to Done")

                logger.info(f"Next check in {CHECK_INTERVAL} seconds...")
                time.sleep(CHECK_INTERVAL)

            except KeyboardInterrupt:
                logger.info("\nWorkflow Manager stopped by user")
                break
            except Exception as e:
                logger.error(f"Error in workflow: {e}")
                time.sleep(CHECK_INTERVAL)


def main():
    """Entry point."""
    manager = WorkflowManager()
    manager.run()


if __name__ == "__main__":
    main()
