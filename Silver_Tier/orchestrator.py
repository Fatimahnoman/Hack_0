"""
Orchestrator for Silver Tier AI Employee
Main runner script that manages all watchers, skills, and scheduled tasks

Features:
- Start Gmail, WhatsApp, Instagram watchers in background threads
- APScheduler for automated tasks:
  - Daily 9:00 AM: Generate Instagram Post
  - Every 30 min: Check Needs_Action + reasoning loop
- Live Dashboard.md updates with watcher status
- Windows Task Scheduler compatible
- Workflow Manager integration for auto-moving files
"""

import os
import sys
import time
import threading
import logging
from datetime import datetime
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

# Try to import APScheduler
try:
    from apscheduler.schedulers.blocking import BlockingScheduler
    from apscheduler.triggers.cron import CronTrigger
    from apscheduler.triggers.interval import IntervalTrigger
    APSCHEDULER_AVAILABLE = True
except ImportError:
    print("Warning: APScheduler not installed. Run: pip install apscheduler")
    APSCHEDULER_AVAILABLE = False

# Configuration
VAULT_PATH = PROJECT_ROOT / "Vault"
NEEDS_ACTION_PATH = VAULT_PATH / "Needs_Action"
LOGS_PATH = VAULT_PATH / "Logs"
DASHBOARD_PATH = VAULT_PATH / "Dashboard.md"
WATCHERS_DIR = PROJECT_ROOT / "watchers"
SKILLS_DIR = PROJECT_ROOT / "skills"

# Watcher check intervals (seconds)
GMAIL_CHECK_INTERVAL = 300      # 5 minutes
WHATSAPP_CHECK_INTERVAL = 60    # 1 minute
INSTAGRAM_CHECK_INTERVAL = 14400  # 4 hours
WORKFLOW_CHECK_INTERVAL = 60    # 1 minute

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(LOGS_PATH / "orchestrator.log", encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)


class WatcherStatus:
    """Track watcher status."""
    def __init__(self):
        self.gmail_active = False
        self.whatsapp_active = False
        self.instagram_active = False
        self.last_check = None
        self.last_instagram_post = None
    
    def get_status_string(self):
        """Get formatted status string for Dashboard."""
        gmail_icon = "✅" if self.gmail_active else "❌"
        whatsapp_icon = "✅" if self.whatsapp_active else "❌"
        instagram_icon = "✅" if self.instagram_active else "❌"
        
        last_check = self.last_check.strftime("%Y-%m-%d %H:%M:%S") if self.last_check else "Never"
        
        return f"Watchers: Gmail {gmail_icon} | WhatsApp {whatsapp_icon} | Instagram {instagram_icon} | Last check: {last_check}"


class SilverTierOrchestrator:
    """Main orchestrator for Silver Tier AI Employee."""

    def __init__(self):
        self.project_root = PROJECT_ROOT
        self.vault_path = VAULT_PATH
        self.needs_action_path = NEEDS_ACTION_PATH
        self.logs_path = LOGS_PATH
        self.dashboard_path = DASHBOARD_PATH
        self.watchers_dir = WATCHERS_DIR
        self.skills_dir = SKILLS_DIR
        
        # Workflow paths
        self.pending_approval_path = VAULT_PATH / "Pending_Approval"
        self.approved_path = VAULT_PATH / "Approved"
        self.done_path = VAULT_PATH / "Done"

        # Ensure directories exist
        for path in [self.vault_path, self.needs_action_path, self.logs_path,
                     self.pending_approval_path, self.approved_path, self.done_path]:
            path.mkdir(parents=True, exist_ok=True)

        # Watcher status
        self.status = WatcherStatus()
        
        # Watcher threads
        self.watcher_threads = {}
        
        # Scheduler
        self.scheduler = None
        if APSCHEDULER_AVAILABLE:
            self.scheduler = BlockingScheduler(timezone='UTC')
        
        # Running flag
        self.running = False
        
        logger.info("Silver Tier Orchestrator initialized")
        logger.info(f"Project Root: {self.project_root}")
    
    def update_dashboard(self, custom_message: str = None):
        """Update Dashboard.md with current status."""
        try:
            if not self.dashboard_path.exists():
                # Create default dashboard
                content = """# AI Employee Dashboard - Silver Tier

## Status
- Last checked: Never
- Watchers: Starting...

## Quick Links
- [Inbox](./Inbox)
- [Needs_Action](./Needs_Action)
- [Pending_Approval](./Pending_Approval)
- [Approved](./Approved)
- [Done](./Done)
- [Logs](./Logs)
- [Plans](./Plans)

## Task Log

"""
                with open(self.dashboard_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                return
            
            with open(self.dashboard_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Update timestamp
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            # Update status line
            status_line = self.status.get_status_string()
            
            if "Watchers:" in content:
                # Replace existing status line
                lines = content.split('\n')
                new_lines = []
                for line in lines:
                    if line.startswith("Watchers:"):
                        new_lines.append(status_line)
                    elif "- Last checked:" in line:
                        new_lines.append(f"- Last checked: {current_time}")
                    else:
                        new_lines.append(line)
                content = '\n'.join(new_lines)
            else:
                # Add status section
                status_section = f"""## Status
- Last checked: {current_time}
- {status_line}

"""
                if "# AI Employee Dashboard" in content:
                    content = content.replace("# AI Employee Dashboard", f"# AI Employee Dashboard\n{status_section}", 1)
            
            # Add custom message if provided
            if custom_message:
                log_entry = f"\n### {current_time} - {custom_message}\n"
                if "## Task Log" in content:
                    content = content.replace("## Task Log", f"## Task Log\n{log_entry}", 1)
                else:
                    content += f"\n## Task Log\n{log_entry}\n"
            
            with open(self.dashboard_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            logger.info(f"✓ Dashboard updated: {status_line}")
            
        except Exception as e:
            logger.error(f"Error updating dashboard: {e}")
    
    def run_gmail_watcher(self):
        """Run Gmail watcher in background thread."""
        logger.info("Starting Gmail Watcher thread...")
        
        try:
            from watchers.gmail_watcher import main as gmail_main
            self.status.gmail_active = True
            self.update_dashboard()
            gmail_main()
        except ImportError:
            logger.warning("Gmail watcher not available")
            self.status.gmail_active = False
        except Exception as e:
            logger.error(f"Gmail watcher error: {e}")
            self.status.gmail_active = False
    
    def run_whatsapp_watcher(self):
        """Run WhatsApp watcher in background thread."""
        logger.info("Starting WhatsApp Watcher thread...")
        
        try:
            from watchers.whatsapp_watcher import main as whatsapp_main
            self.status.whatsapp_active = True
            self.update_dashboard()
            whatsapp_main()
        except ImportError:
            logger.warning("WhatsApp watcher not available")
            self.status.whatsapp_active = False
        except Exception as e:
            logger.error(f"WhatsApp watcher error: {e}")
            self.status.whatsapp_active = False
    
    def run_instagram_watcher(self):
        """Run Instagram watcher in background thread."""
        logger.info("Starting Instagram Watcher thread...")
        
        try:
            from watchers.instagram_watcher import main as instagram_main
            self.status.instagram_active = True
            self.update_dashboard()
            instagram_main()
        except ImportError:
            logger.warning("Instagram watcher not available")
            self.status.instagram_active = False
        except Exception as e:
            logger.error(f"Instagram watcher error: {e}")
            self.status.instagram_active = False
    
    def start_all_watchers(self):
        """Start all watchers in background threads."""
        logger.info("=" * 60)
        logger.info("Starting all watchers...")
        logger.info("=" * 60)
        
        # Gmail Watcher
        gmail_thread = threading.Thread(
            target=self.run_gmail_watcher,
            name="GmailWatcher",
            daemon=True
        )
        gmail_thread.start()
        self.watcher_threads['gmail'] = gmail_thread
        time.sleep(2)  # Stagger startup
        
        # WhatsApp Watcher
        whatsapp_thread = threading.Thread(
            target=self.run_whatsapp_watcher,
            name="WhatsAppWatcher",
            daemon=True
        )
        whatsapp_thread.start()
        self.watcher_threads['whatsapp'] = whatsapp_thread
        time.sleep(2)  # Stagger startup
        
        # Instagram Watcher
        instagram_thread = threading.Thread(
            target=self.run_instagram_watcher,
            name="InstagramWatcher",
            daemon=True
        )
        instagram_thread.start()
        self.watcher_threads['instagram'] = instagram_thread
        
        logger.info("All watchers started")
        self.update_dashboard("All watchers started")
    
    def generate_daily_instagram_post(self):
        """Scheduled task: Generate Instagram post request every day at 9:00 AM."""
        logger.info("=" * 50)
        logger.info("Running scheduled task: Generate Instagram Post Request")
        logger.info("=" * 50)

        try:
            from watchers.instagram_watcher import InstagramWatcher

            watcher = InstagramWatcher()
            result = watcher.create_daily_post_request()

            if result:
                logger.info(f"✓ Instagram post request generated: {result}")
                self.status.last_instagram_post = datetime.now()
                self.update_dashboard("Daily Instagram post request generated")
            else:
                logger.warning("Failed to generate Instagram post request")

        except Exception as e:
            logger.error(f"Error generating Instagram post: {e}")
    
    def check_needs_action_loop(self):
        """Scheduled task: Check Needs_Action every 30 minutes."""
        logger.info("Running scheduled task: Check Needs_Action")

        try:
            from skills.process_needs_action import ProcessNeedsAction

            skill = ProcessNeedsAction()

            # Check for new files
            if self.needs_action_path.exists():
                files = list(self.needs_action_path.glob("*.md"))

                for filepath in files:
                    # Skip INSTA_POST_REQUEST files (handled by Instagram watcher)
                    if filepath.name.startswith("INSTA_POST_REQUEST"):
                        continue

                    logger.info(f"Processing: {filepath.name}")
                    skill.process_file(filepath)
            
            self.status.last_check = datetime.now()
            self.update_dashboard("Needs_Action check complete")
            
        except Exception as e:
            logger.error(f"Error in Needs_Action check: {e}")

    def setup_scheduler(self):
        """Setup APScheduler with all scheduled tasks."""
        if not APSCHEDULER_AVAILABLE:
            logger.warning("APScheduler not available, skipping scheduler setup")
            return

        logger.info("=" * 60)
        logger.info("Setting up APScheduler...")
        logger.info("=" * 60)

        # Daily Instagram Post at 9:00 AM
        self.scheduler.add_job(
            self.generate_daily_instagram_post,
            CronTrigger(hour=9, minute=0),  # 9:00 AM UTC
            id='daily_instagram_post',
            name='Generate Daily Instagram Post Request',
            replace_existing=True
        )
        logger.info("✓ Scheduled: Daily Instagram Post Request at 09:00 AM UTC")

        # Check Needs_Action every 30 minutes
        self.scheduler.add_job(
            self.check_needs_action_loop,
            IntervalTrigger(minutes=30),
            id='check_needs_action',
            name='Check Needs_Action Every 30 Minutes',
            replace_existing=True
        )
        logger.info("✓ Scheduled: Needs_Action check every 30 minutes")

        # Workflow Manager - Check every 1 minute
        self.scheduler.add_job(
            self.process_workflow,
            IntervalTrigger(seconds=WORKFLOW_CHECK_INTERVAL),
            id='workflow_manager',
            name='Workflow Manager - Auto Move Files',
            replace_existing=True
        )
        logger.info("✓ Scheduled: Workflow Manager every 60 seconds")

        # Update Dashboard every 5 minutes
        self.scheduler.add_job(
            lambda: self.update_dashboard(),
            IntervalTrigger(minutes=5),
            id='update_dashboard',
            name='Update Dashboard Status',
            replace_existing=True
        )
        logger.info("✓ Scheduled: Dashboard update every 5 minutes")

    def process_workflow(self):
        """Process workflow: move files between stages."""
        try:
            from workflow_manager import WorkflowManager

            manager = WorkflowManager()

            # Process Needs_Action → Pending_Approval
            moved = manager.process_needs_action()
            if moved > 0:
                logger.info(f"✓ Moved {moved} file(s) to Pending_Approval")
                self.update_dashboard(f"Moved {moved} file(s) to Pending_Approval")

            # Process Pending_Approval → Approved/Done
            processed = manager.process_pending_approval()
            if processed > 0:
                logger.info(f"✓ Processed {processed} file(s) with markers")
                self.update_dashboard(f"Processed {processed} file(s)")

            # Check Instagram approved posts and auto-post
            self.process_instagram_approved_posts()

        except ImportError:
            logger.error("Workflow Manager not found")
        except Exception as e:
            logger.error(f"Error in Workflow Manager: {e}")

    def process_instagram_approved_posts(self):
        """Check Approved/ folder for Instagram posts to publish."""
        try:
            from watchers.instagram_watcher import InstagramWatcher

            approved_path = self.approved_path
            if not approved_path.exists():
                return

            post_files = list(approved_path.glob("INSTA_POST_REQUEST_*.md"))
            if not post_files:
                return

            # Start Instagram watcher to post
            watcher = InstagramWatcher()
            watcher.start_browser()

            if watcher.navigate_to_instagram():
                for filepath in post_files:
                    try:
                        content = filepath.read_text(encoding='utf-8')
                        caption = watcher.extract_caption(content)
                        image_path = watcher.extract_image_path(content)

                        logger.info(f"Posting to Instagram: {filepath.name}")
                        success = watcher.upload_post(image_path, caption)

                        if success:
                            # Move to Done/
                            dest = self.done_path / filepath.name
                            filepath.rename(dest)
                            logger.info(f"✓ Posted and moved to Done: {filepath.name}")
                            self.update_dashboard(f"Posted: {filepath.name}")
                        else:
                            logger.error(f"✗ Post failed: {filepath.name}")

                    except Exception as e:
                        logger.error(f"Error processing {filepath.name}: {e}")

            watcher.close()

        except Exception as e:
            logger.error(f"Error processing Instagram posts: {e}")
    
    def run(self):
        """Main orchestrator run method."""
        logger.info("=" * 60)
        logger.info("Silver Tier Orchestrator - Starting")
        logger.info("=" * 60)
        logger.info(f"Project Root: {self.project_root}")
        logger.info(f"Vault Path: {self.vault_path}")
        logger.info("=" * 60)
        
        self.running = True
        
        # Start all watchers
        self.start_all_watchers()
        
        # Setup scheduler
        if APSCHEDULER_AVAILABLE:
            self.setup_scheduler()
            
            # Run initial checks
            logger.info("Running initial checks...")
            self.check_needs_action_loop()
            self.update_dashboard("Orchestrator started")
            
            # Start scheduler
            logger.info("=" * 60)
            logger.info("Starting APScheduler...")
            logger.info("Press Ctrl+C to stop")
            logger.info("=" * 60)
            
            try:
                self.scheduler.start()
            except KeyboardInterrupt:
                logger.info("\nOrchestrator stopped by user")
                self.running = False
        else:
            # Fallback: Simple loop without scheduler
            logger.info("=" * 60)
            logger.info("Running in fallback mode (no APScheduler)")
            logger.info("Press Ctrl+C to stop")
            logger.info("=" * 60)
            
            last_check_time = time.time()
            CHECK_INTERVAL = 1800  # 30 minutes
            
            while self.running:
                try:
                    time.sleep(60)
                    
                    # Check Needs_Action every 30 minutes
                    if time.time() - last_check_time > CHECK_INTERVAL:
                        self.check_needs_action_loop()
                        last_check_time = time.time()
                    
                except KeyboardInterrupt:
                    logger.info("\nOrchestrator stopped by user")
                    self.running = False
    
    def stop(self):
        """Stop the orchestrator gracefully."""
        logger.info("Stopping orchestrator...")
        self.running = False
        
        if self.scheduler:
            self.scheduler.shutdown()
        
        logger.info("Orchestrator stopped")


def main():
    """Entry point for orchestrator."""
    orchestrator = SilverTierOrchestrator()
    orchestrator.run()


if __name__ == "__main__":
    main()
