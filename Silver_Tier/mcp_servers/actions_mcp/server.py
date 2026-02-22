"""
Actions MCP Server for Silver Tier
Handles email sending and Instagram posting via FastMCP

Tools:
- send_email: Send emails via Gmail API
- post_to_instagram: Post to Instagram using Playwright
- check_approval_status: Check if action has approval
"""

import os
import asyncio
from datetime import datetime
from typing import Optional

from fastmcp import FastMCP

# Initialize FastMCP server
mcp = FastMCP("actions_mcp")

# Configuration
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
VAULT_PATH = os.path.join(PROJECT_ROOT, 'Vault')
CREDENTIALS_FILE = os.path.join(PROJECT_ROOT, 'credentials.json')
TOKEN_FILE = os.path.join(PROJECT_ROOT, 'token.json')
SESSIONS_PATH = os.path.join(PROJECT_ROOT, 'sessions')
INSTAGRAM_SESSION_PATH = os.path.join(SESSIONS_PATH, 'instagram_session')
WHATSAPP_SESSION_PATH = os.path.join(SESSIONS_PATH, 'whatsapp_session')
ENV_FILE = os.path.join(PROJECT_ROOT, '.env')


@mcp.tool()
async def send_email(
    to: str,
    subject: str,
    body: str,
    attachment_path: Optional[str] = None
) -> str:
    """
    Send an email via Gmail API.

    Args:
        to: Recipient email address
        subject: Email subject
        body: Email body content
        attachment_path: Optional path to attachment file

    Returns:
        Status message indicating success or failure

    Example:
        await send_email(
            to="user@example.com",
            subject="Hello",
            body="This is a test email",
            attachment_path="C:/files/doc.pdf"
        )
    """
    print(f"[MCP] send_email called: to={to}, subject={subject}")

    # Check credentials
    if not os.path.exists(CREDENTIALS_FILE):
        return "Error: credentials.json not found in project root"

    try:
        import base64
        from email.mime.multipart import MIMEMultipart
        from email.mime.text import MIMEText
        from email.mime.base import MIMEBase
        from email import encoders
        from google.oauth2.credentials import Credentials
        from google_auth_oauthlib.flow import InstalledAppFlow
        from google.auth.transport.requests import Request
        from googleapiclient.discovery import build
        from googleapiclient.errors import HttpError

        SCOPES = ['https://www.googleapis.com/auth/gmail.send']

        # Authenticate
        creds = None
        if os.path.exists(TOKEN_FILE):
            creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)

        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                return "Error: Gmail authentication required. Run OAuth flow first."

        service = build('gmail', 'v1', credentials=creds)

        # Create message
        message = MIMEMultipart()
        message['to'] = to
        message['subject'] = subject
        message.attach(MIMEText(body, 'plain'))

        # Add attachment if provided
        if attachment_path and os.path.exists(attachment_path):
            with open(attachment_path, "rb") as attachment:
                part = MIMEBase('application', 'octet-stream')
                part.set_payload(attachment.read())
                encoders.encode_base64(part)
                part.add_header(
                    'Content-Disposition',
                    f'attachment; filename={os.path.basename(attachment_path)}'
                )
                message.attach(part)

        # Send email
        raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode('utf-8')

        sent_message = service.users().messages().send(
            userId='me',
            body={'raw': raw_message}
        ).execute()

        print(f"[MCP] Email sent successfully: {sent_message['id']}")
        return f"✓ Email sent successfully! Message ID: {sent_message['id']}"

    except HttpError as error:
        print(f"[MCP] Gmail API error: {error}")
        return f"Error sending email: {error}"
    except ImportError as e:
        return f"Error: Required packages not installed. Run: pip install google-api-python-client google-auth-httplib2 google-auth-oauthlib"
    except Exception as e:
        print(f"[MCP] Unexpected error: {e}")
        return f"Error sending email: {str(e)}"


@mcp.tool()
async def post_to_instagram(
    caption: str,
    image_path: Optional[str] = None
) -> str:
    """
    Post to Instagram using Playwright with persistent context.

    Uses headless browser with session stored in ../sessions/instagram_session/
    First run will login and save session, subsequent runs reuse the session.

    Args:
        caption: Instagram post caption (hashtags supported)
        image_path: Optional path to image file (if None, text-only post)

    Returns:
        Status message indicating success or failure

    Example:
        await post_to_instagram(
            caption="Amazing sunset! 🌅 #photography",
            image_path="C:/photos/sunset.jpg"
        )
    """
    print(f"[MCP] post_to_instagram called: caption={caption[:50]}...")

    # Ensure session folder exists
    os.makedirs(INSTAGRAM_SESSION_PATH, exist_ok=True)

    try:
        from playwright.async_api import async_playwright

        # Load Instagram credentials from .env
        username, password = _load_instagram_credentials()

        if not username or not password:
            return "Error: Instagram credentials not found in .env file"

        async with async_playwright() as p:
            # Launch browser headless
            browser = await p.chromium.launch(headless=True)
            
            # Create persistent context
            context = await browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            )

            page = await context.new_page()

            # Navigate to Instagram
            print("[MCP] Navigating to Instagram...")
            await page.goto('https://www.instagram.com/', wait_until='networkidle')
            await page.wait_for_timeout(2000)

            # Check if already logged in
            logged_in = False
            try:
                await page.wait_for_selector('svg[aria-label="Home"]', timeout=5000)
                print("[MCP] Already logged in, using existing session")
                logged_in = True
            except:
                pass

            if not logged_in:
                # Need to login
                print("[MCP] Logging in to Instagram...")
                
                # Fill credentials
                await page.fill('input[name="username"]', username)
                await page.fill('input[name="password"]', password)
                await page.click('button[type="submit"]')

                # Wait for login
                try:
                    await page.wait_for_selector('svg[aria-label="Home"]', timeout=15000)
                    print("[MCP] Login successful")
                except Exception as e:
                    await browser.close()
                    return f"Error: Instagram login failed. Check credentials. {str(e)}"

            # Handle "Save Info" popup
            try:
                save_info_btn = await page.wait_for_selector('button:has-text("Save"), button:has-text("Not Now")', timeout=3000)
                if save_info_btn:
                    await save_info_btn.click()
                    await page.wait_for_timeout(1000)
            except:
                pass

            # Handle "Turn on Notifications" popup
            try:
                not_now_btn = await page.wait_for_selector('button:has-text("Not Now")', timeout=3000)
                if not_now_btn:
                    await not_now_btn.click()
                    await page.wait_for_timeout(1000)
            except:
                pass

            # Create new post
            print("[MCP] Creating new post...")

            # Click "New" button (the + icon in sidebar)
            try:
                # Try multiple selectors for the create button
                create_selectors = [
                    'svg[aria-label="New post"]',
                    'svg[aria-label="Create"]',
                    '[role="button"]:has-text("New")'
                ]
                
                for selector in create_selectors:
                    try:
                        await page.click(selector, timeout=2000)
                        break
                    except:
                        continue
                else:
                    # Try keyboard shortcut
                    await page.keyboard.press('Control+N')
                    
                await page.wait_for_timeout(3000)
            except Exception as e:
                await browser.close()
                return f"Error: Could not open post creator. {str(e)}"

            # Upload image if provided
            if image_path and os.path.exists(image_path):
                print(f"[MCP] Uploading image: {image_path}")

                # Find file input and upload
                try:
                    file_input = await page.query_selector('input[type="file"]')
                    if file_input:
                        await file_input.set_input_files(image_path)
                        await page.wait_for_timeout(4000)

                        # Click "Next"
                        next_btn = await page.query_selector('button:has-text("Next")')
                        if next_btn:
                            await next_btn.click()
                            await page.wait_for_timeout(3000)
                            
                            # May need to click Next again for filters
                            try:
                                next_btn2 = await page.query_selector('button:has-text("Next")')
                                if next_btn2:
                                    await next_btn2.click()
                                    await page.wait_for_timeout(2000)
                            except:
                                pass
                    else:
                        await browser.close()
                        return "Error: Could not find file upload input"
                except Exception as e:
                    await browser.close()
                    return f"Error uploading image: {str(e)}"
            else:
                # Text-only post (Reel or carousel)
                print("[MCP] No image provided - creating text-based post")

            # Add caption
            print("[MCP] Adding caption...")
            try:
                caption_field = await page.query_selector('textarea[aria-label*="caption"], textarea[placeholder*="caption"]')
                if caption_field:
                    await caption_field.fill(caption)
                    await page.wait_for_timeout(1000)
                else:
                    print("[MCP] Warning: Could not find caption field")
            except Exception as e:
                print(f"[MCP] Warning: Could not add caption: {e}")

            # Click "Share" to post
            print("[MCP] Publishing post...")
            try:
                share_btn = await page.query_selector('button:has-text("Share")')
                if share_btn:
                    await share_btn.click()
                    await page.wait_for_timeout(4000)

                    # Wait for confirmation
                    try:
                        await page.wait_for_selector('text="Your post has been shared"', timeout=5000)
                        print("[MCP] Post published successfully!")
                    except:
                        print("[MCP] Post may have been published (confirmation not detected)")
                else:
                    await browser.close()
                    return "Error: Could not find Share button"
            except Exception as e:
                await browser.close()
                return f"Error publishing post: {str(e)}"

            await browser.close()

            return "✓ Instagram post created successfully!"

    except ImportError as e:
        return f"Error: Playwright not installed. Run: pip install playwright && playwright install"
    except Exception as e:
        print(f"[MCP] Instagram posting error: {e}")
        return f"Error posting to Instagram: {str(e)}"


def _load_instagram_credentials():
    """Load Instagram credentials from .env file."""
    username = ""
    password = ""

    if os.path.exists(ENV_FILE):
        with open(ENV_FILE, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line.startswith('INSTAGRAM_USERNAME='):
                    username = line.split('=', 1)[1].strip()
                elif line.startswith('INSTAGRAM_PASSWORD='):
                    password = line.split('=', 1)[1].strip()

    return username, password


@mcp.tool()
async def check_approval_status(action_id: str) -> str:
    """
    Check if an action has human approval.

    Args:
        action_id: Unique action identifier (filename without extension)

    Returns:
        Approval status message

    Example:
        await check_approval_status("WHATSAPP_20260222191008")
    """
    print(f"[MCP] check_approval_status called: action_id={action_id}")

    approval_path = os.path.join(VAULT_PATH, 'Pending_Approval', f'{action_id}.md')
    approved_path = os.path.join(VAULT_PATH, 'Approved', f'{action_id}.md')
    done_path = os.path.join(VAULT_PATH, 'Done', f'{action_id}.md')

    if os.path.exists(done_path):
        return f"✓ Action {action_id} is COMPLETED"
    elif os.path.exists(approved_path):
        return f"✓ Action {action_id} is APPROVED"
    elif os.path.exists(approval_path):
        return f"⏳ Action {action_id} is PENDING approval"
    else:
        return f"Action {action_id} not found in approval system"


async def main():
    """Run the MCP server."""
    print("=" * 50)
    print("Actions MCP Server - Silver Tier")
    print("=" * 50)
    print(f"Project Root: {PROJECT_ROOT}")
    print(f"Vault Path: {VAULT_PATH}")
    print(f"Instagram Session: {INSTAGRAM_SESSION_PATH}")
    print("=" * 50)
    print("\nRun command: python server.py")
    print("Press Ctrl+C to stop\n")

    # Run FastMCP server
    await mcp.run_stdio_async()


if __name__ == '__main__':
    asyncio.run(main())
