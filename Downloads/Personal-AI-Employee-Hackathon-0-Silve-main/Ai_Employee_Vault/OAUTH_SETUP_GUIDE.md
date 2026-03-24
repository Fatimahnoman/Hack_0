# Gmail OAuth Setup - Complete Guide

## Problem
Your current OAuth 2.0 Client ID has restricted redirect URIs that don't match what the Python library uses.

## Solution: Create New OAuth Client

### Step 1: Go to Google Cloud Console
1. Open: https://console.cloud.google.com/apis/credentials
2. Select your project: `personal-ai-employee-488712`

### Step 2: Create New OAuth Client ID
1. Click **"+ CREATE CREDENTIALS"** (top of page)
2. Select **"OAuth client ID"**
3. Application type: **"Desktop app"**
4. Name: `Gmail Watcher Desktop`
5. Click **"CREATE"**

### Step 3: Download New Credentials
1. Click **"DOWNLOAD JSON"** button
2. Save the file as `credentials.json`
3. Replace your current `credentials.json` with this new file

### Step 4: Run Authentication
```bash
python watchers/gmail_watcher.py
```

The script will:
- Open browser automatically
- Ask you to sign in
- Save token.json after successful auth

---

## Alternative: Fix Existing OAuth Client

If you MUST use the existing client:

### Step 1: Edit OAuth Client
1. Go to: https://console.cloud.google.com/apis/credentials
2. Click on your OAuth 2.0 Client ID name
3. Under **"Authorized redirect URIs"**, add:
   - `http://localhost`
   - `http://localhost:8080`
   - `http://localhost:3000`
   - `http://localhost:5000`
   - `http://localhost:*` (wildcard for any port)

### Step 2: Save Changes
Click **"SAVE"** at the bottom

### Step 3: Run Authentication
```bash
python watchers/gmail_watcher.py
```

---

## Why This Happens

| Your Current Config | What Python Library Uses |
|---------------------|--------------------------|
| `http://localhost` | `http://localhost:RANDOM_PORT/` |

The redirect URI must **exactly match** what's registered in Google Cloud Console.

---

## Quick Fix Command

After creating new OAuth client:

```bash
# Delete old token if exists
del token.json

# Run authentication
python watchers/gmail_watcher.py
```
