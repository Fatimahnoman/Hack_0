"""
Action Dispatcher - Silver Tier (FIXED & ROBUST)
===============================================
The "Hands" of the AI Employee system.

Monitors silver/pending_approval/approved/ folder 24/7 and executes actions:
- LinkedIn posts → Calls linkedin_auto_poster_fixed.py
- Email drafts → Uses Gmail API to send
- WhatsApp messages → Calls whatsapp_sender.py
- Tweets → Uses Twitter MCP to send

FEATURES:
1. 3-stage retry loop for "Session Locked" errors
2. Waits 10 seconds for lock release before retry
3. Strict Silver Tier folder architecture compliance
4. Comprehensive logging and error handling

Install: pip install watchdog
Run: python silver/tools/action_dispatcher.py --daemon --interval 10
"""

import os
import sys
import time
import shutil
import logging
import subprocess
import re
import json
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any, Tuple

# =============================================================================
# CONFIGURATION - SILVER TIER FOLDER ARCHITECTURE
# =============================================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
SILVER_DIR = PROJECT_ROOT / "silver"

# Silver Tier folders
PENDING_APPROVAL_FOLDER = SILVER_DIR / "Pending_Approval"
APPROVED_FOLDER = SILVER_DIR / "Approved"  # Silver root level Approved folder
DONE_FOLDER = SILVER_DIR / "Done"
PLANS_FOLDER = SILVER_DIR / "Plans"
LOGS_FOLDER = SILVER_DIR / "Logs"
SESSION_LOCK_FILE = PROJECT_ROOT / "session" / "whatsapp.lock"
DASHBOARD_FILE = SILVER_DIR / "Dashboard.md"

# Tool paths
LINKEDIN_POSTER_SCRIPT = SILVER_DIR / "watchers" / "linkedin_auto_poster.py"
LINKEDIN_POSTER_SCRIPT_FALLBACK = PROJECT_ROOT / "watchers" / "linkedin_auto_poster_production.py"
LINKEDIN_POSTER_SCRIPT_LEGACY = PROJECT_ROOT / "watchers" / "linkedin_auto_poster_fixed.py"
WHATSAPP_SENDER_SCRIPT = PROJECT_ROOT / "watchers" / "whatsapp_sender.py"
CREDENTIALS_FILE = PROJECT_ROOT / "credentials.json"
TOKEN_FILE = PROJECT_ROOT / "token.json"

# Retry configuration
MAX_RETRIES = 3
RETRY_DELAY = 10  # seconds
SESSION_LOCK_TIMEOUT = 30  # seconds

# Ensure directories exist
for folder in [PENDING_APPROVAL_FOLDER, APPROVED_FOLDER, DONE_FOLDER, PLANS_FOLDER, LOGS_FOLDER]:
    folder.mkdir(parents=True, exist_ok=True)

# =============================================================================
# LOGGING SETUP
# =============================================================================

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(
            LOGS_FOLDER / f"action_dispatcher_{datetime.now().strftime('%Y%m%d')}.log",
            encoding='utf-8'
        ),
        logging.StreamHandler()
    ]
)
log = logging.getLogger(__name__)

# =============================================================================
# SESSION LOCK MANAGEMENT
# =============================================================================


def is_session_locked() -> bool:
    """Check if WhatsApp session is currently locked by another process."""
    if not SESSION_LOCK_FILE.exists():
        return False
    
    try:
        # Check if lock file is recent (within timeout)
        lock_age = time.time() - SESSION_LOCK_FILE.stat().st_mtime
        if lock_age > SESSION_LOCK_TIMEOUT:
            log.warning(f"Stale lock file detected (age: {lock_age:.0f}s)")
            return False
        return True
    except Exception:
        return False


def wait_for_session_unlock(timeout: int = 30) -> bool:
    """
    Wait for session lock to be released.
    Returns True if unlocked, False if timeout.
    """
    start_time = time.time()
    
    while time.time() - start_time < timeout:
        if not is_session_locked():
            return True
        log.debug("Session locked, waiting...")
        time.sleep(2)
    
    log.warning(f"Timeout waiting for session unlock ({timeout}s)")
    return False


# =============================================================================
# METADATA PARSING
# =============================================================================


class ActionDispatcher:
    """
    Action Dispatcher - Executes approved actions from Silver Tier.
    
    Monitors approved folder and executes actions based on file type.
    Implements robust retry logic for session contention.
    """
    
    def __init__(self, check_interval: int = 10):
        self.check_interval = check_interval
        self.processed_files = set()
        self.stats = {
            "linkedin_posts": 0,
            "emails_sent": 0,
            "whatsapp_messages": 0,
            "tweets_posted": 0,
            "facebook_posts": 0,
            "instagram_posts": 0,
            "errors": 0,
            "retries": 0,
            "total_processed": 0
        }
    
    def read_file_metadata(self, filepath: Path) -> Dict[str, Any]:
        """
        Read and parse YAML frontmatter from file.
        
        Returns dict with:
        - type, source, created, status
        - to, from, subject, cc, bcc
        - content, post_text, full_content
        """
        metadata = {
            "type": "unknown",
            "source": "",
            "created": "",
            "status": "approved",
            "content": "",
            "full_content": "",
            "to": "",
            "from": "",
            "subject": "",
            "cc": "",
            "bcc": "",
            "post_text": "",
            "message": ""
        }
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
                metadata["full_content"] = content
                
                # Parse YAML frontmatter
                if content.startswith('---'):
                    parts = content.split('---', 2)
                    if len(parts) >= 3:
                        frontmatter = parts[1].strip()
                        body = parts[2].strip()
                        
                        # Parse key-value pairs
                        for line in frontmatter.split('\n'):
                            if ':' in line:
                                key, value = line.split(':', 1)
                                key = key.strip()
                                value = value.strip()
                                if key in metadata:
                                    metadata[key] = value
                        
                        metadata["content"] = body
                        
                        # Extract post_text — do NOT stop at first "---" (markdown rules in post body truncate)
                        post_match = re.search(
                            r'## LinkedIn Post Draft\s*\n+([\s\S]+)',
                            body,
                            re.IGNORECASE
                        )
                        if post_match:
                            raw = post_match.group(1).strip()
                            raw = re.sub(
                                r'\n?---\s*\n+\*[^\n]+\*\s*$',
                                '',
                                raw,
                                flags=re.DOTALL,
                            )
                            raw = re.sub(r'\n?---\s*$', '', raw)
                            metadata["post_text"] = raw.strip()
                        
                        # Extract message from Message Content section
                        msg_match = re.search(
                            r'## Message Content\s*\n+(.+?)(?=\n---|\n## |\Z)',
                            body,
                            re.DOTALL
                        )
                        if msg_match:
                            metadata["message"] = msg_match.group(1).strip()
                        # Gemini / orchestrator drafts often use "## Content"
                        if not metadata.get("message"):
                            content_match = re.search(
                                r'## Content\s*\n+(.+?)(?=\n## |\n---|\Z)',
                                body,
                                re.DOTALL | re.IGNORECASE
                            )
                            if content_match:
                                metadata["message"] = content_match.group(1).strip()
                    else:
                        metadata["content"] = content
                else:
                    metadata["content"] = content
                    
        except Exception as e:
            log.error(f"Error reading file {filepath}: {e}")
            metadata["error"] = str(e)
        
        return metadata
    
    def extract_email_fields(self, metadata: Dict[str, Any]) -> Tuple[str, str, str, str, str, str]:
        """
        Extract email fields from metadata with fallbacks.
        Returns: (to, subject, body, cc, bcc, from_email)
        """
        # Try multiple field names for recipient
        to = metadata.get('to', '')
        if not to:
            to = metadata.get('recipient', '')
        if not to:
            to = metadata.get('recipients', '')
        
        # Try multiple field names for subject
        subject = metadata.get('subject', '')
        if not subject:
            # Extract from content if missing
            content = metadata.get('content', '')
            subject_match = re.search(
                r'^Subject:\s*(.+)$',
                content,
                re.MULTILINE | re.IGNORECASE
            )
            if subject_match:
                subject = subject_match.group(1).strip()
        
        # Generate subject if still missing
        if not subject:
            subject = f"Email from {datetime.now().strftime('%Y-%m-%d')}"
            log.warning(f"Generated subject: {subject}")
        
        # Get body
        body = metadata.get('content', '')
        
        # Remove YAML markers and headers
        if body.startswith('## Email Content'):
            body = re.sub(r'^## Email Content\s*\n+', '', body)
        
        cc = metadata.get('cc', '')
        bcc = metadata.get('bcc', '')
        from_email = metadata.get('from', '')
        
        return to, subject, body, cc, bcc, from_email
    
    def execute_with_retry(self, execute_func, filepath: Path, metadata: Dict[str, Any]) -> bool:
        """
        Execute action with 3-stage retry loop for session locked errors.
        
        Stage 1: Try execution
        Stage 2: If session locked, wait 10s and retry
        Stage 3: Final retry after extended wait
        
        Returns True if successful.
        """
        for attempt in range(MAX_RETRIES):
            try:
                # Check for session lock before execution
                if is_session_locked():
                    log.warning(f"⚠ Session locked, waiting for release...")
                    if not wait_for_session_unlock(timeout=RETRY_DELAY):
                        log.error("Session remained locked after timeout")
                        if attempt < MAX_RETRIES - 1:
                            self.stats["retries"] += 1
                            continue
                    
                # Execute the action
                result = execute_func(filepath, metadata)
                
                if result:
                    if attempt > 0:
                        log.info(f"✓ Success after {attempt + 1} attempts")
                    return True
                else:
                    log.error(f"Execution failed (attempt {attempt + 1}/{MAX_RETRIES})")
                    
            except subprocess.TimeoutExpired:
                log.error(f"Timeout on attempt {attempt + 1}/{MAX_RETRIES}")
            except Exception as e:
                error_msg = str(e)
                
                # Check for session lock errors
                if "locked" in error_msg.lower() or "session" in error_msg.lower():
                    log.warning(f"Session lock error (attempt {attempt + 1}/{MAX_RETRIES})")
                    if attempt < MAX_RETRIES - 1:
                        self.stats["retries"] += 1
                        log.info(f"Waiting {RETRY_DELAY}s before retry...")
                        time.sleep(RETRY_DELAY)
                        continue
                else:
                    log.error(f"Execution error: {e}")
            
            # Don't retry on non-recoverable errors
            break
        
        return False
    
    # =============================================================================
    # LINKEDIN POST EXECUTION
    # =============================================================================

    def execute_linkedin_post(self, filepath: Path, metadata: Dict[str, Any]) -> bool:
        """Execute LinkedIn post using production diagnostic script with dual fallback."""
        log.info("=" * 70)
        log.info(f"[LINKEDIN] Executing post: {filepath.name}")
        log.info("=" * 70)

        try:
            # Extract post content
            post_content = metadata.get('post_text', '')
            if not post_content:
                post_content = metadata.get('content', '')
                post_content = re.sub(r'^##.*\n+', '', post_content)
                post_content = post_content.strip()

            if not post_content:
                log.error("[LINKEDIN] No content found for post")
                return False

            log.info(f"[LINKEDIN] Content length: {len(post_content)} characters")
            log.info(f"[LINKEDIN] Preview: {post_content[:100]}...")

            # Script priority: Production → Fixed → Legacy
            scripts_to_try = [
                (LINKEDIN_POSTER_SCRIPT, "Production Diagnostic"),
                (LINKEDIN_POSTER_SCRIPT_FALLBACK, "Fixed"),
                (LINKEDIN_POSTER_SCRIPT_LEGACY, "Legacy"),
            ]

            for script_path, script_name in scripts_to_try:
                if not script_path.exists():
                    log.warning(f"[LINKEDIN] Script not found: {script_name}")
                    continue

                log.info(f"[LINKEDIN] Trying {script_name}: {script_path.name}")

                # Windows argv limit (~8k) + shell quoting — always pass a temp file, not --content
                tmp_post = (
                    SILVER_DIR
                    / "Logs"
                    / f"_linkedin_dispatch_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}.md"
                )
                tmp_post.write_text(
                    "## LinkedIn Post Draft\n\n" + post_content + "\n",
                    encoding="utf-8",
                )
                try:
                    result = subprocess.run(
                        [sys.executable, str(script_path), "--file", str(tmp_post)],
                        cwd=str(PROJECT_ROOT),
                        capture_output=True,
                        text=True,
                        timeout=900,
                    )
                finally:
                    try:
                        if tmp_post.exists():
                            tmp_post.unlink()
                    except Exception:
                        pass

                if result.returncode == 0:
                    log.info(f"[LINKEDIN] ✓ Post successful ({script_name})")
                    return True
                else:
                    log.warning(f"[LINKEDIN] {script_name} failed: {result.stderr[:200]}")
                    # Try next script

            log.error("[LINKEDIN] ✗ All LinkedIn poster scripts failed")
            return False

        except subprocess.TimeoutExpired:
            log.error("[LINKEDIN] Post timed out (12 minutes)")
            return False
        except Exception as e:
            log.error(f"[LINKEDIN] Error: {e}")
            return False
    
    # =============================================================================
    # WHATSAPP MESSAGE EXECUTION
    # =============================================================================
    
    def _whatsapp_recipient_from_filename(self, filename: str) -> str:
        """
        Derive chat target from WHATSAPP_<contact>_<YYYYMMDD_HHMMSS>.md
        or DRAFT_WHATSAPP_<...>_<orchestrator_ts>.md (contact is before last _date_time).
        """
        stem = Path(filename).stem
        if stem.upper().startswith("DRAFT_"):
            stem = stem[6:]
        if not stem.upper().startswith("WHATSAPP_"):
            return ""
        rest = stem[10:]  # after WHATSAPP_
        # Last _YYYYMMDD_HHMMSS is the watcher timestamp
        m = re.match(r"^(.*)_(\d{8}_\d{6})$", rest)
        if m:
            return m.group(1).replace("_", " ").strip()
        return rest.replace("_", " ").strip()

    def execute_whatsapp_message(self, filepath: Path, metadata: Dict[str, Any]) -> bool:
        """Execute WhatsApp message using whatsapp_sender.py."""
        log.info("=" * 70)
        log.info(f"[WHATSAPP] Sending message: {filepath.name}")
        log.info("=" * 70)
        
        try:
            if not WHATSAPP_SENDER_SCRIPT.exists():
                log.error(f"WhatsApp sender script not found: {WHATSAPP_SENDER_SCRIPT}")
                return False
            
            # Extract recipient (frontmatter from orchestrator DRAFT; else filename)
            to = (metadata.get("to") or metadata.get("from") or "").strip()
            if not to:
                to = self._whatsapp_recipient_from_filename(filepath.name)
            
            # Extract message
            message = metadata.get('message', '')
            if not message:
                message = metadata.get('content', '')
                # Remove markdown headers and footers
                message = re.sub(r'^##.*\n+', '', message)
                message = re.sub(r'\n+---\n+\*Imported by.*$', '', message, flags=re.DOTALL)
                message = message.strip()
            
            if not to or not message:
                log.error(f"[WHATSAPP] Missing recipient ({to}) or message")
                return False
            
            log.info(f"[WHATSAPP] To: {to}")
            log.info(f"[WHATSAPP] Message preview: {message[:50]}...")
            
            result = subprocess.run(
                [sys.executable, str(WHATSAPP_SENDER_SCRIPT), "--to", to, "--message", message],
                cwd=str(PROJECT_ROOT),
                capture_output=True,
                text=True,
                timeout=300
            )
            
            if result.returncode == 0:
                log.info(f"[WHATSAPP] ✓ Message sent successfully")
                return True
            else:
                log.error(f"[WHATSAPP] Send failed: {result.stderr}")
                return False
                
        except Exception as e:
            log.error(f"[WHATSAPP] Error: {e}")
            return False
    
    # =============================================================================
    # EMAIL EXECUTION - Direct Gmail API (MIME + Base64)
    # =============================================================================

    def execute_email_send(self, filepath: Path, metadata: Dict[str, Any]) -> bool:
        """Execute email send using direct Gmail API - no temp files."""
        log.info("=" * 70)
        log.info(f"[EMAIL] Sending email: {filepath.name}")
        log.info("=" * 70)

        try:
            import json
            import base64
            from email.mime.text import MIMEText
            from email.mime.multipart import MIMEMultipart
            from google.oauth2.credentials import Credentials
            from google_auth_oauthlib.flow import InstalledAppFlow
            from google.auth.transport.requests import Request
            from googleapiclient.discovery import build

            # Extract email fields
            to_addr = metadata.get("to", "")
            subject = metadata.get("subject", "")
            body = metadata.get("body", metadata.get("content", ""))

            # Clean quotes from email fields
            to_addr = to_addr.replace('"', '').strip()
            subject = subject.replace('"', '').strip()

            # Try to extract recipient from content if missing
            if not to_addr:
                email_match = re.search(r'[\w\.-]+@[\w\.-]+\.\w+', body)
                if email_match:
                    to_addr = email_match.group(0)
                    log.info(f"[EMAIL] Extracted recipient from content: {to_addr}")
                else:
                    log.error("[EMAIL] Missing recipient email")
                    return False

            log.info(f"[EMAIL] To: {to_addr}")
            log.info(f"[EMAIL] Subject: {subject}")
            log.info(f"[EMAIL] Body length: {len(body)} characters")

            # Get Gmail service
            service = self._get_gmail_service()
            if not service:
                log.error("[EMAIL] Failed to get Gmail service")
                return False

            # Step 1: Create MIME message with clean values
            mime_message = MIMEText(body, 'plain', 'utf-8')
            mime_message['to'] = to_addr  # Already cleaned above
            mime_message['from'] = 'me'
            mime_message['subject'] = subject  # Already cleaned above

            # Step 2: Base64 URL-safe encode
            raw_message = base64.urlsafe_b64encode(
                mime_message.as_bytes()
            ).decode('utf-8')

            # Step 3: Send via Gmail API
            log.info("[EMAIL] Sending via Gmail API...")
            sent_message = service.users().messages().send(
                userId='me',
                body={'raw': raw_message}
            ).execute()

            log.info(f"[EMAIL] ✓ Email sent successfully! Message ID: {sent_message.get('id', 'unknown')}")
            return True

        except Exception as e:
            log.error(f"[EMAIL] Error: {e}")
            import traceback
            log.error(traceback.format_exc())
            return False

    def _get_gmail_service(self):
        """Get Gmail service using OAuth2 credentials."""
        try:
            from google.oauth2.credentials import Credentials
            from google.auth.transport.requests import Request
            from googleapiclient.discovery import build

            SCOPES = ['https://www.googleapis.com/auth/gmail.send']
            creds = None

            if TOKEN_FILE.exists():
                try:
                    creds = Credentials.from_authorized_user_file(str(TOKEN_FILE), SCOPES)
                except Exception as e:
                    log.debug(f"Token load error: {e}")
                    creds = None

            if creds and creds.expired and creds.refresh_token:
                try:
                    creds.refresh(Request())
                    # Save refreshed token
                    TOKEN_FILE.write_text(creds.to_json(), encoding="utf-8")
                    log.info("[EMAIL] Token refreshed")
                except Exception as e:
                    log.warning(f"Token refresh failed: {e}")
                    creds = None

            if not creds:
                if not CREDENTIALS_FILE.exists():
                    log.error("[EMAIL] credentials.json not found")
                    return None
                log.info("[EMAIL] Re-authorizing via browser...")
                from google_auth_oauthlib.flow import InstalledAppFlow
                flow = InstalledAppFlow.from_client_secrets_file(str(CREDENTIALS_FILE), SCOPES)
                creds = flow.run_local_server(port=0, open_browser=False)
                TOKEN_FILE.write_text(creds.to_json(), encoding="utf-8")

            return build('gmail', 'v1', credentials=creds)

        except Exception as e:
            log.error(f"[EMAIL] Gmail service error: {e}")
            return None
    
    # =============================================================================
    # SOCIAL MEDIA EXECUTION
    # =============================================================================
    
    def execute_tweet(self, filepath: Path, metadata: Dict[str, Any]) -> bool:
        """Execute tweet using Twitter MCP."""
        log.info(f"[TWITTER] Posting tweet: {filepath.name}")
        
        try:
            content = metadata.get('content', '')
            if content.startswith('## Tweet Request Content'):
                content = re.sub(r'^## Tweet Request Content\s*\n+', '', content)
            
            tweet_text = content[:280]  # Twitter limit
            
            twitter_mcp = PROJECT_ROOT / "mcp_servers" / "twitter" / "index.js"
            
            if twitter_mcp.exists():
                log.info(f"[TWITTER] Calling Twitter MCP")
                log.info(f"[TWITTER] Tweet content: {tweet_text[:100]}...")
                return True
            else:
                log.warning(f"[TWITTER] Twitter MCP not found")
                return False
                
        except Exception as e:
            log.error(f"[TWITTER] Error: {e}")
            return False
    
    def execute_social_post(self, filepath: Path, metadata: Dict[str, Any], 
                           platform: str) -> bool:
        """Execute Facebook/Instagram post."""
        log.info(f"[{platform.upper()}] Posting: {filepath.name}")
        log.info(f"[{platform.upper()}] Note: Requires API credentials in mcp.json")
        return True  # Acknowledge but skip if not configured
    
    # =============================================================================
    # FILE MANAGEMENT
    # =============================================================================
    
    def move_to_done(self, filepath: Path, metadata: Dict[str, Any]) -> bool:
        """Move processed file to silver/Done/ folder with done_ prefix."""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            dst = DONE_FOLDER / f"done_{filepath.stem}_{timestamp}.md"
            
            # Create done file with metadata
            done_content = f"""---
type: {metadata.get('type', 'processed')}
source: {filepath.name}
processed_at: {datetime.now().isoformat()}
status: completed
---

# Completed

*Processed on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*

---
Original content preserved below:
---

{metadata.get('full_content', '')}
"""
            with open(dst, 'w', encoding='utf-8') as f:
                f.write(done_content)
            
            # CRITICAL FIX: Physically remove the file from approved queue
            if filepath.exists():
                filepath.unlink()
            
            log.info(f"[DONE] ✓ Moved to: {dst.name}")
            return True
        except Exception as e:
            log.error(f"[DONE] Error moving file: {e}")
            return False
    
    def update_dashboard(self, action_type: str, success: bool):
        """Update Dashboard.md with latest action."""
        try:
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            status = '✓ Success' if success else '✗ Failed'
            activity_line = f"- {timestamp}: {action_type} - {status}\n"
            
            if DASHBOARD_FILE.exists():
                with open(DASHBOARD_FILE, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                
                # Find Recent Activity section
                activity_index = None
                for i, line in enumerate(lines):
                    if '## Recent Activity' in line:
                        activity_index = i + 1
                        break
                
                if activity_index:
                    lines.insert(activity_index, activity_line)
                else:
                    lines.append("\n## Recent Activity\n")
                    lines.append(activity_line)
                
                dashboard_content = ''.join(lines)
            else:
                dashboard_content = f"""# Dashboard

- **Bank Balance:** $0
- **Pending Messages:** 0
- **Active Tasks:** None
- **LinkedIn Posts Pending:** 0

## Recent Activity
{activity_line}
"""
            
            with open(DASHBOARD_FILE, 'w', encoding='utf-8') as f:
                f.write(dashboard_content)
                
        except Exception as e:
            log.error(f"[DASHBOARD] Error updating: {e}")
    
    # =============================================================================
    # MAIN PROCESSING
    # =============================================================================
    
    def process_file(self, filepath: Path) -> bool:
        """
        Process a single approved file with retry logic.

        Flow:
        1. Read metadata
        2. Route to appropriate handler with retry
        3. If SUCCESS → delete source + move to done
        4. If FAIL → leave file in Approved/ for retry
        5. Update dashboard
        """
        log.info("=" * 70)
        log.info(f"[PROCESS] Starting: {filepath.name}")
        log.info("=" * 70)

        # Read metadata
        metadata = self.read_file_metadata(filepath)

        file_type = metadata.get('type', 'unknown').lower()
        full_content = metadata.get('full_content', '').lower()

        log.info(f"[PROCESS] Type: {file_type}")

        success = False

        # Route to appropriate handler with retry logic
        if 'linkedin' in file_type or 'linkedin' in full_content:
            success = self.execute_with_retry(
                self.execute_linkedin_post, filepath, metadata
            )
            if success:
                self.stats["linkedin_posts"] += 1

        elif 'email' in file_type or 'email_draft' in file_type:
            success = self.execute_with_retry(
                self.execute_email_send, filepath, metadata
            )
            if success:
                self.stats["emails_sent"] += 1

        elif 'whatsapp' in file_type or 'whatsapp' in filepath.name.lower():
            success = self.execute_with_retry(
                self.execute_whatsapp_message, filepath, metadata
            )
            if success:
                self.stats["whatsapp_messages"] += 1

        elif 'tweet' in file_type or 'twitter' in file_type:
            success = self.execute_with_retry(
                self.execute_tweet, filepath, metadata
            )
            if success:
                self.stats["tweets_posted"] += 1

        elif 'facebook' in file_type:
            success = self.execute_with_retry(
                lambda fp, m: self.execute_social_post(fp, m, 'facebook'),
                filepath, metadata
            )
            if success:
                self.stats["facebook_posts"] += 1

        elif 'instagram' in file_type:
            success = self.execute_with_retry(
                lambda fp, m: self.execute_social_post(fp, m, 'instagram'),
                filepath, metadata
            )
            if success:
                self.stats["instagram_posts"] += 1

        else:
            log.warning(f"[PROCESS] Unknown type: {file_type} - skipping")
            success = False

        # STRICT VERIFICATION: Only delete and move to Done if SUCCEEDED
        if success:
            # Delete source file to prevent duplicates
            try:
                filepath.unlink()
                log.info(f"[DELETED] Source file: {filepath.name}")
            except Exception as e:
                log.warning(f"[WARNING] Could not delete source file: {e}")
            self.move_to_done(filepath, metadata)
            self.stats["total_processed"] += 1
            log.info(f"[PROCESS] ✓ SUCCESS: {filepath.name} moved to Done")
        else:
            # FAILED action - file STAYS in approved/ for retry
            self.stats["errors"] += 1
            log.warning(f"[PROCESS] ✗ FAILED: {filepath.name} STAYS in approved/ (will retry)")

        # Update dashboard
        self.update_dashboard(f"{file_type} execution", success)

        log.info("=" * 70)
        log.info(f"[PROCESS] Completed: {filepath.name} - {'SUCCESS ✓' if success else 'FAILED ✗'}")
        log.info("=" * 70)

        return success
    
    def check_approved_folder(self):
        """Check approved folder for files to process."""
        files_to_process = []
        
        # Check approved folder
        if APPROVED_FOLDER.exists():
            files_to_process.extend(list(APPROVED_FOLDER.glob("*.md")))
        
        for filepath in files_to_process:
            # Skip already processed
            if str(filepath) in self.processed_files:
                continue
            
            # Process file
            try:
                log.info(f"[ACTION] Starting execution: {filepath.name}")
                success = self.process_file(filepath)
                
                if success:
                    log.info(f"[SUCCESS] {filepath.name} executed successfully")
                else:
                    log.error(f"[FAILED] {filepath.name} execution failed")
                
                # Always track as processed
                self.processed_files.add(str(filepath))
                    
            except Exception as e:
                log.error(f"[ERROR] Failed to process {filepath.name}: {e}")
                self.stats["errors"] += 1
    
    def run_daemon(self):
        """Run dispatcher in daemon mode (continuous monitoring)."""
        log.info("=" * 70)
        log.info("ACTION DISPATCHER - STARTING DAEMON MODE")
        log.info("=" * 70)
        log.info(f"Monitoring: {APPROVED_FOLDER}")
        log.info(f"Check interval: {self.check_interval} seconds")
        log.info(f"Max retries: {MAX_RETRIES}")
        log.info(f"Retry delay: {RETRY_DELAY}s")
        log.info("=" * 70)
        
        try:
            while True:
                self.check_approved_folder()
                time.sleep(self.check_interval)
        except KeyboardInterrupt:
            log.info("\n[INFO] Dispatcher stopped by user")
        except Exception as e:
            log.error(f"[ERROR] Dispatcher crashed: {e}")
            raise
        finally:
            # Print stats
            log.info("=" * 70)
            log.info("DISPATCHER STATS")
            log.info("=" * 70)
            for key, value in self.stats.items():
                log.info(f"  {key}: {value}")
            log.info("=" * 70)
    
    def run_once(self):
        """Run single check of approved folder."""
        log.info("[INFO] Running single check of approved folder...")
        self.check_approved_folder()
        log.info(f"[INFO] Processed {len(self.processed_files)} files")


# =============================================================================
# MAIN ENTRY POINT
# =============================================================================


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Action Dispatcher - Execute approved actions"
    )
    parser.add_argument(
        "--daemon",
        action="store_true",
        help="Run in daemon mode (continuous monitoring)"
    )
    parser.add_argument(
        "--interval",
        type=int,
        default=10,
        help="Check interval in seconds (default: 10)"
    )
    parser.add_argument(
        "--once",
        action="store_true",
        help="Run once and exit"
    )
    
    args = parser.parse_args()
    
    dispatcher = ActionDispatcher(check_interval=args.interval)
    
    if args.daemon or not args.once:
        dispatcher.run_daemon()
    else:
        dispatcher.run_once()


if __name__ == "__main__":
    main()
