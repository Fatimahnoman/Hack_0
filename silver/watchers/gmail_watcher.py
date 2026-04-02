"""
Gmail Watcher - Gold Tier (Fixed)
==================================
Monitors Gmail inbox for unread important emails.
Creates files in gold/needs_action/ folder first.

Install: pip install google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client
Setup:
  1. Download credentials.json to project root
  2. Run once to authorize
Run: python silver/watchers/gmail_watcher.py
"""

import os
import re
import sys
import time
import base64
import logging
import webbrowser
from datetime import datetime
from pathlib import Path

try:
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from googleapiclient.discovery import build
except ImportError as e:
    print(f"[ERROR] Missing: {e}")
    print("Run: pip install google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client")
    sys.exit(1)

# =============================================================================
# CONFIGURATION - GOLD TIER FOLDERS
# =============================================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
GOLD_DIR = PROJECT_ROOT / "gold"

# CRITICAL: Gold Tier folder structure
NEEDS_ACTION_FOLDER = GOLD_DIR / "needs_action"
LOGS_FOLDER = GOLD_DIR / "logs"

# Credentials (OAuth client JSON from Google Cloud Console → project root)
CREDENTIALS_FILE = PROJECT_ROOT / "credentials.json"
TOKEN_FILE = PROJECT_ROOT / "token.json"
# Fixed loopback port so browser + redirect work reliably (add http://127.0.0.1:8090/ to OAuth client if required)
OAUTH_LOCAL_PORT = int(os.environ.get("GMAIL_OAUTH_PORT", "8090"))
SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]

# Ensure folders exist
NEEDS_ACTION_FOLDER.mkdir(parents=True, exist_ok=True)
LOGS_FOLDER.mkdir(parents=True, exist_ok=True)

# Settings
CHECK_INTERVAL = 60  # seconds
IMPORTANT_KEYWORDS = [
    "urgent", "sales", "payment", "invoice", "deal", "order",
    "client", "customer", "quotation", "proposal", "overdue",
    "follow up", "meeting", "booking", "asap", "test"
]

# Track processed
processed_emails = set()
PROCESSED_FILE = LOGS_FOLDER / "gmail_processed.txt"

# =============================================================================
# LOGGING
# =============================================================================

def setup_logging():
    log_file = LOGS_FOLDER / f"gmail_{datetime.now().strftime('%Y%m%d')}.log"
    
    logger = logging.getLogger("GmailWatcher")
    logger.setLevel(logging.INFO)
    logger.handlers = []
    
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
    logger.addHandler(file_handler)
    
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(logging.Formatter("[%(levelname)s] %(message)s"))
    logger.addHandler(console_handler)
    
    return logger

logger = setup_logging()

# =============================================================================
# MESSAGE PROCESSING
# =============================================================================

def load_processed():
    global processed_emails
    if PROCESSED_FILE.exists():
        try:
            with open(PROCESSED_FILE, 'r', encoding='utf-8') as f:
                processed_emails = set(line.strip() for line in f)
            logger.info(f"Loaded {len(processed_emails)} processed emails")
        except:
            pass

def save_processed(email_id: str):
    processed_emails.add(email_id)
    try:
        with open(PROCESSED_FILE, 'a', encoding='utf-8') as f:
            f.write(f"{email_id}\n")
    except:
        pass

def get_priority(subject: str, snippet: str) -> str:
    text = f"{subject} {snippet}".lower()
    if "urgent" in text or "asap" in text:
        return "high"
    if "invoice" in text or "payment" in text or "order" in text:
        return "medium"
    return "normal"

def _yaml_one_line(s: str) -> str:
    return (s or "").replace('"', '\\"').replace("\r", " ").replace("\n", " ").strip()


def create_needs_action_file(email_data: dict, logger) -> Path:
    """CRITICAL: Create file in gold/needs_action/ folder"""
    priority = get_priority(email_data['subject'], email_data['snippet'])
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    safe_sender = re.sub(r"[^a-zA-Z0-9]", "_", email_data['from'][:20]) or "Unknown"
    filename = f"GMAIL_{safe_sender}_{timestamp}.md"
    filepath = NEEDS_ACTION_FOLDER / filename
    
    content = f"""---
type: email
from: "{_yaml_one_line(email_data['from'])}"
to: ""
subject: "{_yaml_one_line(email_data['subject'])}"
priority: {priority}
status: pending
created_at: {datetime.now().isoformat()}
message_id: {email_data['id']}
---

## Email Content

{email_data['body']}

## Metadata

- **From:** {email_data['from']}
- **Subject:** {email_data['subject']}
- **Priority:** {priority}
- **Received:** {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

---
*Gmail Watcher - Gold Tier*
"""
    
    with open(filepath, "w", encoding='utf-8') as f:
        f.write(content)
    
    logger.info(f"✓ CREATED: {filename} in needs_action/")
    return filepath

# =============================================================================
# GMAIL API
# =============================================================================

def _save_token(creds) -> None:
    TOKEN_FILE.write_text(creds.to_json(), encoding="utf-8")


def get_gmail_service():
    """
    Gmail API using OAuth2: credentials.json (client) + token.json (saved session).
    First run opens browser for Google login; later runs use token refresh.
    """
    creds = None

    if TOKEN_FILE.exists():
        try:
            creds = Credentials.from_authorized_user_file(str(TOKEN_FILE), SCOPES)
        except Exception as e:
            logger.error(f"token.json read error: {e}")
            creds = None

    if creds and creds.expired and creds.refresh_token:
        try:
            creds.refresh(Request())
            _save_token(creds)
            logger.info("Gmail token refreshed")
        except Exception as e:
            logger.warning(f"Token refresh failed (re-auth needed): {e}")
            creds = None

    if not creds or not creds.valid:
        if not CREDENTIALS_FILE.exists():
            logger.error(
                f"Missing {CREDENTIALS_FILE.name} in project root. "
                "Download OAuth 2.0 Client ID (Desktop) JSON from Google Cloud Console."
            )
            return None

        try:
            logger.info(
                f"OAuth: local server http://localhost:{OAUTH_LOCAL_PORT}/ "
                "(browser should open for Google sign-in)"
            )
            flow = InstalledAppFlow.from_client_secrets_file(str(CREDENTIALS_FILE), SCOPES)
            creds = flow.run_local_server(
                host="localhost",
                port=OAUTH_LOCAL_PORT,
                open_browser=True,
                success_message="<p>Gmail authorized. You can close this tab.</p>",
            )
            _save_token(creds)
            logger.info(f"Saved OAuth session to {TOKEN_FILE.name}")
        except OSError as e:
            if "Address already in use" in str(e) or "Only one usage" in str(e):
                logger.error(
                    f"Port {OAUTH_LOCAL_PORT} busy. Set env GMAIL_OAUTH_PORT=8091 and retry, "
                    "or close the app using that port."
                )
            else:
                logger.error(f"OAuth server error: {e}")
            return None
        except Exception as e:
            logger.error(f"OAuth failed: {e}")
            # Help if browser did not open: show auth URL is printed by the library to console
            logger.info(
                "If the browser did not open, check this window for a Google authorization URL "
                "and open it manually."
            )
            return None

    try:
        return build("gmail", "v1", credentials=creds, cache_discovery=False)
    except Exception as e:
        logger.error(f"Gmail API build failed: {e}")
        return None


def open_gmail_in_browser():
    """Optional: open Gmail web UI (read-only convenience)."""
    try:
        webbrowser.open("https://mail.google.com/mail/u/0/#inbox")
    except Exception as e:
        logger.debug(f"Could not open browser: {e}")


def check_emails(service, logger):
    """Check Gmail for unread emails with keywords."""
    try:
        # Get unread messages
        results = service.users().messages().list(
            userId='me',
            q='is:unread',
            maxResults=10
        ).execute()
        
        messages = results.get('messages', [])
        
        if not messages:
            logger.debug("No unread emails")
            return 0
        
        new_tasks = 0
        
        for msg in messages:
            try:
                # Get message details
                message = service.users().messages().get(
                    userId='me',
                    id=msg['id'],
                    format='metadata',
                    metadataHeaders=['From', 'Subject', 'Snippet']
                ).execute()
                
                # Extract data
                headers = message['payload']['headers']
                subject = ""
                sender = ""
                snippet = message.get('snippet', '')
                
                for header in headers:
                    if header['name'] == 'Subject':
                        subject = header['value']
                    elif header['name'] == 'From':
                        sender = header['value']
                
                # Check if processed
                if msg['id'] in processed_emails:
                    continue
                
                # Check keywords
                text_to_check = f"{subject} {snippet}".lower()
                if any(kw in text_to_check for kw in IMPORTANT_KEYWORDS):
                    # Get full body
                    try:
                        full_msg = service.users().messages().get(
                            userId='me',
                            id=msg['id'],
                            format='full'
                        ).execute()
                        
                        body = ""
                        if 'parts' in full_msg['payload']:
                            for part in full_msg['payload']['parts']:
                                if part['mimeType'] == 'text/plain':
                                    if 'data' in part['body']:
                                        body = base64.urlsafe_b64decode(
                                            part['body']['data'] + "==="
                                        ).decode('utf-8', errors='ignore')
                                        break
                        elif 'body' in full_msg['payload']:
                            if 'data' in full_msg['payload']['body']:
                                body = base64.urlsafe_b64decode(
                                    full_msg['payload']['body']['data'] + "==="
                                ).decode('utf-8', errors='ignore')
                        
                        if not body:
                            body = snippet
                    
                    except Exception as e:
                        body = snippet
                    
                    # Create task file
                    email_data = {
                        'id': msg['id'],
                        'from': sender,
                        'subject': subject,
                        'snippet': snippet,
                        'body': body
                    }
                    
                    create_needs_action_file(email_data, logger)
                    save_processed(msg['id'])
                    new_tasks += 1
                    logger.info(f"📧 Found: {subject[:50]}...")
                    
            except Exception as e:
                logger.debug(f"Error processing message: {e}")
                continue
        
        return new_tasks
        
    except Exception as e:
        logger.error(f"Error checking emails: {e}")
        return 0

# =============================================================================
# MAIN
# =============================================================================

def main():
    logger.info("=" * 70)
    logger.info("GMAIL WATCHER - GOLD TIER")
    logger.info("=" * 70)
    logger.info(f"Tasks folder: {NEEDS_ACTION_FOLDER}")
    logger.info(f"Check interval: {CHECK_INTERVAL}s")
    logger.info("=" * 70)
    
    load_processed()
    
    logger.info("Connecting to Gmail API...")
    service = get_gmail_service()
    
    if not service:
        logger.error("Failed to connect to Gmail API")
        logger.info("Please ensure credentials.json exists and OAuth is completed")
        return
    
    logger.info("✓ Gmail API connected")
    if os.environ.get("GMAIL_OPEN_INBOX", "1") != "0":
        logger.info("Opening Gmail inbox in default browser (set GMAIL_OPEN_INBOX=0 to skip)")
        open_gmail_in_browser()
    logger.info("Starting monitoring loop...")
    
    consecutive_errors = 0
    
    while True:
        try:
            new_tasks = check_emails(service, logger)
            
            if new_tasks > 0:
                logger.info(f"✓ Created {new_tasks} new task(s) in needs_action/")
                consecutive_errors = 0
            else:
                consecutive_errors += 1
                if consecutive_errors > 10:
                    logger.info("Still monitoring...")
                    consecutive_errors = 0
            
            time.sleep(CHECK_INTERVAL)
            
        except KeyboardInterrupt:
            logger.info("\n👋 Stopping...")
            break
        except Exception as e:
            logger.error(f"Loop error: {e}")
            consecutive_errors += 1
            if consecutive_errors > 10:
                # Reconnect service
                logger.info("Reconnecting to Gmail API...")
                service = get_gmail_service()
                consecutive_errors = 0
            time.sleep(CHECK_INTERVAL)
    
    logger.info("Gmail Watcher stopped")

if __name__ == "__main__":
    main()
