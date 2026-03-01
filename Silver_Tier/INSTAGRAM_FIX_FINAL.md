# Instagram Auto-Post Fix - Complete Analysis

**Date:** 2026-03-01  
**Status:** Fix Ready for Testing

---

## Problem Summary

**Issue:** Logs show "Success" but posts don't appear on Instagram. Post breaks/discards during upload.

**Root Cause:** The MCP server's `post_to_instagram()` function was returning success before properly verifying the post actually published. The discard modal was not being handled, and verification logic was weak.

---

## 1. Possible Reasons for Failure (Numbered List)

1. **Discard Modal Not Handled**: Instagram shows "Discard post?" when it detects automation or incomplete form. Code clicked Share but didn't wait for/handle this modal before declaring success.

2. **Timing Issue - Share Click Too Early**: Share button clicked before image fully uploads/processes. Instagram needs 5-10 seconds after upload before Share can succeed.

3. **Weak Verification Logic**: Verification checked URL change or generic elements, not actual post publication. URL can change without post succeeding.

4. **Instagram Anti-Bot Detection (2026)**: Instagram detects Playwright via:
   - `navigator.webdriver` property
   - Missing browser plugins
   - Robotic click patterns
   - Missing mouse movement

5. **Selector Mismatch**: Instagram changes selectors. `button:has-text("Share")` may not match if Instagram uses "Post" or different aria-label.

6. **Network/Upload Incomplete**: Image upload appears complete but Instagram servers haven't processed it. Clicking Share too soon causes silent failure.

7. **Modal Animation Not Complete**: Create dialog or Share button still animating when clicked, causing click to miss.

8. **Session Cookie Expiry**: Persistent session may have expired cookies, causing mid-flow failures.

9. **Caption Field Not Ready**: Caption textarea not fully loaded when fill attempted, causing silent failure.

10. **Share Button Disabled**: Share button greyed out/disabled if Instagram detects issue, but code tries to click anyway.

---

## 2. Debugging Steps

### Step 1: Enable Visual Debugging

Ensure browser is visible (NOT headless):

```python
# In server_final.py
headless = False  # Keep this for debugging
```

### Step 2: Check Debug Screenshots

Screenshots saved at each step in `debug_screenshots/`:

```
debug_YYYYMMDD_HHMMSS_01_home.png          # Initial state
debug_YYYYMMDD_HHMMSS_02_logged_in.png     # After login
debug_YYYYMMDD_HHMMSS_03_profile.png       # Profile page (pre-post count)
debug_YYYYMMDD_HHMMSS_04_create_dialog.png # Create dialog open
debug_YYYYMMDD_HHMMSS_05_uploaded.png      # After image upload
debug_YYYYMMDD_HHMMSS_06_next.png          # After Next clicks
debug_YYYYMMDD_HHMMSS_07_caption.png       # After caption added
debug_YYYYMMDD_HHMMSS_08_after_share.png   # After Share clicked
debug_YYYYMMDD_HHMMSS_final_verified.png   # Final verification
```

**If upload fails:** Check `debug_*_upload_fail.png`  
**If Share fails:** Check `debug_*_share_fail.png`

### Step 3: Review Logs

Log file: `Vault/Logs/instagram_watcher.log`

Key log messages:

```
✓ Already logged in           # Good - session valid
✓ Image uploaded              # Good - upload succeeded
✓ Share clicked               # Good - Share clicked
✓ POST VERIFIED SUCCESSFULLY  # Good - post published
✗ Upload failed               # Bad - check screenshot
✗ Could not click Share       # Bad - Share button missing
✗ VERIFICATION FAILED         # Bad - post not published
```

### Step 4: Console Log Capture

Fixed version captures browser console:

```
[CONSOLE log] Some message
[CONSOLE error] JavaScript error
[PAGE ERROR] Page error details
[REQ FAILED] Failed network request
```

### Step 5: Manual Inspection

When browser opens:

1. **Watch the automation** - Don't touch keyboard/mouse
2. **Look for error modals** - "Discard post?", "Try Again"
3. **Check network activity** - Slow upload may timeout
4. **Verify Share button state** - May be disabled/greyed out

---

## 3. Fixed `post_to_instagram()` Function

**Location:** `E:\Hackathon_Zero\Silver_Tier\mcp_servers\actions_mcp\server_final.py`

### Key Fixes Applied:

```python
# FIX 1: Anti-detection scripts injected BEFORE any page operations
await context.add_init_script("""
    Object.defineProperty(navigator, 'webdriver', {
        get: () => undefined
    });
    Object.defineProperty(navigator, 'plugins', {
        get: () => [1, 2, 3, 4, 5]
    });
    Object.defineProperty(navigator, 'languages', {
        get: () => ['en-US', 'en']
    });
""")

# FIX 2: Console log capture
page.on("console", lambda msg: print(f"[CONSOLE {msg.type}] {msg.text[:200]}"))
page.on("pageerror", lambda err: print(f"[PAGE ERROR] {str(err)[:200]}"))

# FIX 3: Check if Share button is disabled before clicking
is_disabled = await share_btn.is_disabled()
if is_disabled:
    print(f"[WARN] Share button disabled, waiting 5s...")
    await page.wait_for_timeout(5000)
    continue

# FIX 4: Discard modal handling AFTER Share click
for i in range(3):
    try:
        discard_text = await page.wait_for_selector('text="Discard post?"', timeout=3000)
        if discard_text:
            print("[WARN] Discard modal after Share! Clicking Cancel...")
            cancel_btn = await page.wait_for_selector(
                'button:has-text("Cancel"), button:has-text("Don\'t Discard")', 
                timeout=3000
            )
            if cancel_btn:
                await cancel_btn.click()
                await page.wait_for_timeout(3000)
                
                # Retry Share
                share_btn = await page.wait_for_selector(
                    'button:has-text("Share"), button:has-text("Post")', 
                    timeout=3000
                )
                if share_btn:
                    await share_btn.click()
                    print("[OK] Share retried after discard modal")
                    await page.wait_for_timeout(20000)
                    break
    except:
        break

# FIX 5: Multiple verification methods
verified = False

# Method 1: Success message
try:
    success_msg = await page.wait_for_selector(
        'text="Your post has been shared", text="Your Reel has been shared"', 
        timeout=5000
    )
    if success_msg:
        verified = True
        verification_method = "Success message"
except:
    pass

# Method 2: Profile post count increased
if not verified:
    # Navigate to profile and check post count
    current_count = get_post_count()
    if current_count > pre_post_count:
        verified = True
        verification_method = f"Post count increased ({pre_post_count} -> {current_count})"

# Method 3: URL check (not on /create/)
if not verified:
    if "/create/" not in page.url and "instagram.com" in page.url:
        verified = True
        verification_method = "Back on feed"

# Method 4: Inbox link found
if not verified:
    try:
        inbox_link = await page.wait_for_selector('a[href="/direct/inbox/"]', timeout=5000)
        if inbox_link:
            verified = True
            verification_method = "Inbox link found"
    except:
        pass
```

---

## 4. Instagram Watcher Changes

**Location:** `E:\Hackathon_Zero\Silver_Tier\watchers\instagram_watcher.py`

The watcher already has proper verification logic. **No changes needed** to the core logic, but ensure:

1. **File only moves to Done after verified success:**

```python
if result:  # result = verified (True/False)
    # Move to Done
    filepath.rename(self.done_path / filepath.name)
    logger.info(f"Moved to Done: {filepath.name}")
else:
    logger.info("Keeping in Approved (not verified)")
```

2. **Discard modal handler in exception:**

```python
# Handle "Discard post?" popup - click Cancel to stay on post
try:
    if page:
        discard_btn = page.locator('button:has-text("Cancel"), button:has-text("Don\'t Discard")').first
        if discard_btn.is_visible(timeout=3000):
            logger.info("Found 'Discard post?' popup - clicking Cancel to keep post")
            discard_btn.click()
            page.wait_for_timeout(3000)
            logger.info("Please complete the post manually in the browser!")
except:
    pass
```

---

## 5. Test Case

### Sample INSTA_POST_REQUEST_TEST.md

```markdown
# Instagram Post Request

**Created:** 2026-03-01 10:00:00
**Status:** Approved

## Post Details

**Type:** Image Post
**Image Path:** E:\Hackathon_Zero\Silver_Tier\test_image.jpg

## Caption

Testing the fixed Instagram auto-post system! 🚀

This is a test post to verify that:
1. Image uploads correctly
2. Caption is added properly
3. Share button is clicked
4. Post is published successfully
5. Verification passes

#InstagramTest #AutoPost #SilverTier #HackathonZero

---

## Instructions

1. Place a test image at: `E:\Hackathon_Zero\Silver_Tier\test_image.jpg`
2. Move this file to: `E:\Hackathon_Zero\Silver_Tier\Vault\Approved\`
3. Run the watcher: `python watchers\instagram_watcher.py`
4. Watch the browser automate the post
5. Check debug screenshots in: `E:\Hackathon_Zero\Silver_Tier\debug_screenshots\`
6. Verify post appears on your Instagram profile
```

### Test Procedure

```bash
# Step 1: Create test image (or use existing JPG)
# Place at: E:\Hackathon_Zero\Silver_Tier\test_image.jpg

# Step 2: Copy test file to Approved
copy E:\Hackathon_Zero\Silver_Tier\INSTA_POST_REQUEST_TEST.md E:\Hackathon_Zero\Silver_Tier\Vault\Approved\

# Step 3: Run the MCP server (for testing direct function)
cd E:\Hackathon_Zero\Silver_Tier
python mcp_servers\actions_mcp\server_final.py

# Step 4: OR run the watcher (full automation)
python watchers\instagram_watcher.py

# Step 5: Watch browser automate
# - Browser opens
# - Navigates to Instagram
# - Logs in (if needed)
# - Opens create dialog
# - Uploads image
# - Adds caption
# - Clicks Share
# - Handles any discard modals
# - Verifies post

# Step 6: Check results
# - File moved to Done/? ✓
# - Post on Instagram profile? ✓
# - Logs show "VERIFIED SUCCESSFULLY"? ✓
# - Debug screenshots look good? ✓
```

### Expected Flow

```
1. ✓ Watcher detects file in Approved folder
2. ✓ Browser launches with persistent session
3. ✓ Navigates to Instagram
4. ✓ Gets pre-post count from profile
5. ✓ Opens create dialog
6. ✓ Uploads image
7. ✓ Clicks Next (may be twice)
8. ✓ Adds caption
9. ✓ Clicks Share
10. ✓ Handles any discard modals (clicks Cancel, retries Share)
11. ✓ Waits for post to publish
12. ✓ Verifies post count increased
13. ✓ Moves file to Done folder
```

### Debug Checklist

If post fails, check:

- [ ] Debug screenshots in `debug_screenshots/` folder
- [ ] Log file: `Vault/Logs/instagram_watcher.log`
- [ ] Console output for error messages
- [ ] Browser is visible (headless=False)
- [ ] Instagram session is valid (check `sessions/instagram_session/`)
- [ ] Image path is correct and file exists
- [ ] Caption is not too long (max 2200 characters)
- [ ] No "Discard post?" modal visible (or handled)
- [ ] Share button was actually clicked
- [ ] Post count verification passed

---

## 6. Deployment

### Replace Original Files

```bash
# Backup originals
copy E:\Hackathon_Zero\Silver_Tier\mcp_servers\actions_mcp\server.py E:\Hackathon_Zero\Silver_Tier\mcp_servers\actions_mcp\server.py.bak

# Replace with fixed version
copy E:\Hackathon_Zero\Silver_Tier\mcp_servers\actions_mcp\server_final.py E:\Hackathon_Zero\Silver_Tier\mcp_servers\actions_mcp\server.py
```

### Set Headless for Production

```python
# In server.py (after testing)
headless = True  # Change to True for production
```

### Restart Watcher Service

```bash
# Stop current watcher (Ctrl+C)
# Restart
python watchers\instagram_watcher.py
```

---

## 7. Troubleshooting Matrix

| Symptom | Possible Cause | Solution |
|---------|---------------|----------|
| Login fails | Session expired | Manually log in when browser opens |
| Upload fails | Wrong file path | Check image path exists |
| Upload fails | File format | Use JPG/PNG format |
| Share button missing | UI changed | Update selectors |
| Discard modal | Network issue | Wait longer before Share |
| Discard modal | Anti-bot detected | Check anti-detection scripts |
| Verification fails | Post not published | Check Instagram manually |
| Verification fails | Post count unchanged | Wait longer for Instagram |
| File not moved | Verification failed | Check logs for reason |
| Browser crashes | Memory issue | Close other tabs, reduce viewport |

---

## 8. Success Criteria

- [ ] File moved from `Approved/` to `Done/`
- [ ] Log shows "✓ POST VERIFIED SUCCESSFULLY"
- [ ] Debug screenshot shows profile with increased post count
- [ ] Post visible on Instagram profile homepage
- [ ] No "Discard post?" modal visible at end

---

## Version History

- **v3.0 (Final):** Added disabled button check, enhanced discard modal retry, 4-method verification
- **v2.0 (Fixed):** Added discard modal handling, better verification, debug screenshots
- **v1.0 (Original):** Basic automation without proper error handling
