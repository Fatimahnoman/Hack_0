# Gmail OAuth - Complete Fix Guide

## Current Issue
Your OAuth 2.0 Client ID is returning 404 errors, which means:
- The client may be deleted/disabled
- The client ID is incorrect
- The project may have issues

## COMPLETE FIX - Step by Step

### Step 1: Go to Google Cloud Console
Open: https://console.cloud.google.com/

### Step 2: Select/Create Project
1. Click on the project dropdown at the top
2. Select: `personal-ai-employee-488712`
   - OR create a new project

### Step 3: Enable Gmail API
1. Go to: https://console.cloud.google.com/apis/library/gmail.googleapis.com
2. Click **"ENABLE"**

### Step 4: Configure OAuth Consent Screen (IMPORTANT!)
1. Go to: https://console.cloud.google.com/apis/credentials/consent
2. Click **"CREATE"** or **"EDIT"**
3. Fill in:
   - **User Type**: External
   - **App name**: Gmail Watcher
   - **User support email**: Your email
   - **Developer contact**: Your email
4. Click **"SAVE AND CONTINUE"**
5. Skip Scopes (click SAVE AND CONTINUE)
6. Skip Test users (click SAVE AND CONTINUE)

### Step 5: Create NEW OAuth Client ID
1. Go to: https://console.cloud.google.com/apis/credentials
2. Click **"+ CREATE CREDENTIALS"**
3. Select **"OAuth client ID"**
4. **Application type**: **"Desktop app"** (IMPORTANT!)
5. **Name**: `Gmail Watcher`
6. Click **"CREATE"**

### Step 6: Download Credentials
1. Click **"DOWNLOAD JSON"**
2. Save as `credentials.json`
3. Replace: `F:\heckathon\heckathon-0\credentials.json`

### Step 7: Run Authentication
```bash
python auth_step1.py
```

---

## If You Still See Errors

### Check OAuth Consent Screen Status
1. Go to: https://console.cloud.google.com/apis/credentials/consent
2. Make sure it shows **"Published"** (not "Testing")
3. If "Testing", click **"PUBLISH APP"**

### Check API is Enabled
1. Go to: https://console.cloud.google.com/apis/library/gmail.googleapis.com
2. Make sure it shows **"API enabled"**

---

## Quick Links
- Credentials: https://console.cloud.google.com/apis/credentials
- OAuth Consent: https://console.cloud.google.com/apis/credentials/consent
- Gmail API: https://console.cloud.google.com/apis/library/gmail.googleapis.com
- API Dashboard: https://console.cloud.google.com/apis/dashboard
