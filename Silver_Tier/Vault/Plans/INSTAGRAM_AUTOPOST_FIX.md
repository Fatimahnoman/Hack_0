# Instagram Auto-Post Workflow - Complete Setup

## ✅ Current Status

| Component | Status | Notes |
|-----------|--------|-------|
| Gmail Watcher | ✅ Working | Auto-check every 5 min |
| WhatsApp Watcher | ✅ Working | Auto-check every 1 min |
| Instagram Notifications | ✅ Working | Auto-check every 4 hours |
| Workflow Manager | ✅ Working | Auto-move files (2 min delay) |
| **Instagram Auto-Post** | ⚠️ **Needs Fix** | UI selector issues |

---

## 🎯 Solution: Simplified Instagram Poster

### **Problem:**
- Instagram UI elements have dynamic classes
- Share button gets intercepted by dialogs
- Playwright click fails due to overlays

### **Fix Approach:**

Create a **dedicated, robust Instagram poster** that:
1. Uses keyboard shortcuts instead of clicks
2. Waits properly for each step
3. Has better error handling
4. Runs outside orchestrator (standalone)

---

## 📋 Step-by-Step Implementation

### **Step 1: Create Robust Poster Script**

File: `skills/instagram_auto_post.py`

```python
"""
Instagram Auto-Post with Human-in-the-Loop Approval
- Reads approved post requests
- Posts automatically to Instagram
- Moves to Done/ after successful post
"""
```

### **Step 2: Update Orchestrator Integration**

- Call poster script every 60 seconds
- Run in separate process (not thread)
- Avoid asyncio conflicts

### **Step 3: Test Flow**

1. ✅ Generate post request
2. ✅ Move to Approved/
3. ✅ Auto-post triggers (within 60 sec)
4. ✅ Browser opens
5. ✅ Login (saved session)
6. ✅ Upload image (if provided)
7. ✅ Add caption
8. ✅ **Click Share** (FIX THIS)
9. ✅ Move to Done/

---

## 🔧 Technical Fixes Needed

### **Fix 1: Use Keyboard Instead of Mouse Clicks**

```python
# Instead of:
page.click('button:has-text("Share")')  # Fails

# Use:
page.keyboard.press('Enter')  # More reliable
# Or:
page.evaluate('document.querySelector("button").click()')
```

### **Fix 2: Better Element Detection**

```python
# Wait for dialog to fully load
page.wait_for_selector('div[role="dialog"]', timeout=10000)
page.wait_for_timeout(2000)  # Extra wait

# Find Share button by multiple methods
share_button = (
    page.query_selector('button:has-text("Share")') or
    page.query_selector('[aria-label="Share"]') or
    page.query_selector('div[tabindex="0"]:has-text("Share")')
)
```

### **Fix 3: Close Interfering Dialogs**

```python
# Close any open overlays
try:
    page.click('button[aria-label="Close"]', timeout=2000)
    page.wait_for_timeout(1000)
except:
    pass  # No overlay
```

### **Fix 4: Use subprocess Instead of Thread**

```python
# In orchestrator.py
import subprocess

def process_instagram_posts():
    # Run as separate process
    subprocess.run(
        ['python', 'skills/instagram_auto_post.py'],
        cwd=str(PROJECT_ROOT),
        capture_output=True
    )
```

---

## 🚀 Next Steps

1. **Create robust poster script** (30 min)
2. **Test with real Instagram account** (15 min)
3. **Integrate with orchestrator** (15 min)
4. **Full workflow test** (15 min)

**Total Time: ~1 hour**

---

## 📝 Current Workaround

Until auto-post is fixed:

```bash
# 1. Generate post request
python test_insta_post.py

# 2. Wait 2 min → Move to Pending_Approval/

# 3. Move to Approved/
move "Vault\Pending_Approval\INSTA_POST_REQUEST_*.md" "Vault\Approved\"

# 4. Run manual poster
python post_insta_approved.py

# 5. If fails, post manually in browser
#    - Open instagram.com
#    - Click Create (+)
#    - Upload image
#    - Add caption
#    - Share

# 6. Move file to Done/
move "Vault\Approved\INSTA_POST_REQUEST_*.md" "Vault\Done\"
```

---

## ✅ Success Criteria

- [ ] Post request generates automatically (9 AM daily)
- [ ] File moves through workflow (Needs_Action → Pending → Approved)
- [ ] **Browser opens and posts automatically** (within 60 sec of approval)
- [ ] File moves to Done/ after posting
- [ ] No manual intervention except approval
- [ ] Works reliably (95%+ success rate)

---

*Silver Tier AI Employee - Instagram Auto-Post Implementation Plan*
