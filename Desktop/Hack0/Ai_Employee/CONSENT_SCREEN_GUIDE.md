# OAuth Consent Screen - Visual Step-by-Step Guide

## Step 1: Open Consent Screen Page
```
https://console.cloud.google.com/apis/credentials/consent
```

## Step 2: What You'll See

### Scenario A: No Consent Screen Yet
You'll see a page with:
- Title: "OAuth consent screen"
- A big blue button: **"CREATE"** or **"GET STARTED"**

**Click that button!**

### Scenario B: Consent Screen Already Exists
You'll see:
- A table showing your app info
- Top of page: **"EDIT APP"** button

**Click "EDIT APP"!**

---

## Step 3: Fill the Form

### Screen 1: App Information
```
┌─────────────────────────────────────────┐
│ App name:          Gmail Watcher        │
│ User support email: your@email.com     │
│ App logo:          (optional)          │
│ App domain:        (leave empty)       │
│ Developer contact: your@email.com      │
└─────────────────────────────────────────┘
```
**Click: SAVE AND CONTINUE**

### Screen 2: Scopes
- No need to add anything
**Click: SAVE AND CONTINUE**

### Screen 3: Test Users (IMPORTANT!)
```
┌─────────────────────────────────────────┐
│ Test users:                            │
│  + ADD USERS                           │
│                                        │
│  Add your email: vickiee9090@gmail.com │
└─────────────────────────────────────────┘
```
**Click: + ADD USERS** and add your Gmail address

**Click: SAVE AND CONTINUE**

### Screen 4: Summary
**Click: BACK TO DASHBOARD**

---

## Step 4: Publish the App (IMPORTANT!)

After creating, go back to:
```
https://console.cloud.google.com/apis/credentials/consent
```

You'll see:
- **Publishing status: Testing** (with orange/yellow icon)

**Click: "PUBLISH APP"** button

This changes status to **Published** (green)

---

## Step 5: Create OAuth Client

Now go to:
```
https://console.cloud.google.com/apis/credentials
```

**Click: + CREATE CREDENTIALS**

Select: **OAuth client ID**

Fill:
```
Application type: Desktop app
Name: Gmail Watcher
```

**Click: CREATE**

Then: **DOWNLOAD JSON**

---

## Common Issues

### "CREATE" button not showing?
- Make sure you're logged in with correct Google account
- Make sure you have owner/editor access to the project

### Page shows error?
- Clear browser cache
- Try incognito/private mode
- Make sure billing is enabled on the project

### "Publish App" not showing?
- Complete all 4 steps first (App info, Scopes, Test users, Summary)
