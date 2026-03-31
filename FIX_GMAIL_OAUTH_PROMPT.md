# URGENT: Fix Gmail OAuth "This Site Can't Be Reached" Error

## Problem Summary

When running `gmail_auth.py` for Gmail API authorization:

1. Script generates authorization URL ✓
2. User clicks and logs into Google ✓
3. User grants permissions ✓
4. **ERROR:** After redirect to `http://localhost/?code=...`, browser shows:
   - "This site can't be reached"
   - "localhost refused to connect"
   - Error 400 or connection error

## Root Cause

The OAuth flow expects a local web server to catch the redirect at `http://localhost`, but:
- No server is listening on port 80
- Or the redirect URI in credentials.json doesn't match
- Or Windows is blocking localhost redirect

## Current Setup

**File:** `gmail_auth.py`
```python
flow.redirect_uri = "http://localhost"
authorization_url, state = flow.authorization_url(
    access_type="offline",
    include_granted_scopes="true",
    prompt="consent"
)
```

**credentials.json redirect_uris:** `["http://localhost"]`

## Required Solution

Please provide a **complete working fix** for one of these approaches:

### Option 1: Use `http://localhost:8080` with actual server
- Change redirect URI to `http://localhost:8080`
- Start a simple HTTP server to catch the redirect
- Extract the `code` parameter from the URL
- Complete the OAuth flow

### Option 2: Use `urn:ietf:wg:oauth:2.0:oob` (out-of-band)
- Change redirect URI to `urn:ietf:wg:oauth:2.0:oob`
- Google shows the code on the page
- User copies and pastes the code
- Script exchanges code for token

### Option 3: Use `InstalledAppFlow.run_local_server()`
- Let the library handle the server automatically
- Opens browser and starts server on available port
- Most reliable method

## What I Need

Please provide:

1. **Fixed `gmail_auth.py`** - Complete working code with proper OAuth flow
2. **Updated `credentials.json`** - Correct redirect URI configuration
3. **Step-by-step instructions** - Exact commands to run
4. **Troubleshooting** - What to do if it still fails

## Constraints

- Windows 10/11
- Python 3.12
- google-auth-oauthlib 1.3.0
- Must work with `http://localhost` or `http://localhost:8080`
- Should NOT require ngrok or external services

## Expected Flow

```
1. Run: python gmail_auth.py
2. Browser opens automatically (or user copies URL)
3. User logs into Google
4. User grants permissions
5. Browser redirects to localhost
6. Script catches the redirect
7. Token saved to token.json
8. SUCCESS message shown
```

## Files to Fix

### Current gmail_auth.py (BROKEN)
```python
"""
Gmail OAuth - Manual Authorization Flow
"""
import os
import json
from google_auth_oauthlib.flow import Flow

SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]
CREDENTIALS_FILE = os.path.join(os.path.dirname(__file__), "credentials.json")
TOKEN_FILE = os.path.join(os.path.dirname(__file__), "token.json")

def main():
    flow = Flow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
    flow.redirect_uri = "http://localhost"
    
    authorization_url, state = flow.authorization_url(
        access_type="offline",
        include_granted_scopes="true",
        prompt="consent"
    )
    
    print("Open this URL:")
    print(authorization_url)
    
    redirect_url = input("Enter the full redirect URL: ").strip()
    flow.fetch_token(authorization_response=redirect_url)
    
    # Save token...

if __name__ == "__main__":
    main()
```

### Current credentials.json
```json
{
  "installed": {
    "client_id": "...",
    "project_id": "...",
    "redirect_uris": ["http://localhost"]
  }
}
```

## Please Fix This!

The OAuth flow MUST complete successfully and save `token.json`.

Provide the complete fixed code and exact steps to run.
