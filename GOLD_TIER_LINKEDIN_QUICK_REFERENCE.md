# Gold Tier LinkedIn Auto-Post - Quick Reference Card

## 🚀 Quick Start Commands

### Start All Components
```bash
start_gold_tier.bat
```

### Start Individual Components
```bash
# LinkedIn Watcher (monitors for leads)
python watchers\linkedin_watcher_fixed.py

# Gold Orchestrator (AI drafts)
python gold\tools\gold_orchestrator.py

# Action Dispatcher (executes posts)
python silver\tools\action_dispatcher.py --daemon --interval 10

# LinkedIn Auto Poster
python watchers\linkedin_auto_poster_fixed.py
```

---

## 📁 Folder Architecture

```
gold/
├── needs_action/          # Raw leads from watcher
├── pending_approval/      # AI drafts
│   └── approved/          # Approved (ready to post)
├── done/                  # Completed posts
├── logs/                  # Logs
└── plans/                 # AI plans
```

---

## 🔄 Complete Workflow

```
1. Watcher detects lead → gold/needs_action/
2. Orchestrator creates draft → gold/pending_approval/
3. Human moves to → gold/pending_approval/approved/
4. Dispatcher executes → posts to LinkedIn
5. Completed → gold/done/
```

---

## 📝 Create LinkedIn Post Draft

```markdown
---
type: linkedin_post_draft
priority: normal
status: pending
created_at: 2026-03-31T10:00:00
---

## LinkedIn Post Draft

🚀 Your engaging content here!

Key points:
✅ Point 1
✅ Point 2
✅ Point 3

Call to action!

#Hashtag1 #Hashtag2 #Hashtag3

---
*Draft created by Gold Orchestrator*
```

**Approve:** Move to `gold/pending_approval/approved/`

---

## 🔧 Configuration

### Watcher Keywords
```python
SALES_KEYWORDS = [
    "looking for", "need", "require", "seeking", "hire",
    "developer", "service", "help", "project", "budget"
]
```

### Check Interval
```python
CHECK_INTERVAL = 60  # seconds
```

### Retry Settings
```python
MAX_RETRIES = 3
RETRY_DELAY = 10  # seconds
```

---

## 🧪 Testing

### Test Manual Post
```bash
python watchers\linkedin_auto_poster_fixed.py --content "Test post #LinkedIn"
```

### Test Full Workflow
```bash
# 1. Create test lead
echo ---
type: linkedin_lead
from: Test User
content: Need AI automation
priority: high
---
Test content
> gold\needs_action\TEST.md

# 2. Wait for draft
dir gold\pending_approval

# 3. Approve
move gold\pending_approval\DRAFT_*.md gold\pending_approval\approved\

# 4. Check done folder
dir gold\done
```

---

## 📊 Monitoring

### View Logs
```bash
# Recent posts
type Logs\linkedin-posts.jsonl

# Comments
type Logs\linkedin-comments.jsonl

# Action Dispatcher
type gold\logs\action_dispatcher_*.log
```

### Check Dashboard
```bash
type Dashboard.md
```

---

## ⚠️ Troubleshooting

| Issue | Solution |
|-------|----------|
| Browser won't connect | Delete `session\linkedin_chrome`, re-run watcher |
| Post not publishing | Check session active, no overlays |
| Session locked | Wait 10s, delete `session\whatsapp.lock` |
| No leads detected | Check watcher running, verify keywords |
| API errors | Regenerate token, check env vars |

---

## 🔑 Environment Variables (API Method)

```bash
setx LINKEDIN_ACCESS_TOKEN "your-token"
setx LINKEDIN_ORG_ID "your-org-id"  # Optional
setx LINKEDIN_PERSON_ID "urn:li:person:YOUR-ID"
setx LINKEDIN_AUTO_REPLY "false"
```

---

## 📈 Gold Tier Features

| Feature | File |
|---------|------|
| Lead Detection | `watchers/linkedin_watcher_fixed.py` |
| Auto Posting | `watchers/linkedin_auto_poster_fixed.py` |
| AI Drafts | `gold/tools/gold_orchestrator.py` |
| Execution | `silver/tools/action_dispatcher.py` |
| API Skill | `gold/skills/linkedin-auto-post.js` |
| Error Recovery | `gold/skills/error-recovery.js` |
| Weekly Audit | `gold/skills/weekly-business-audit.js` |
| Ralph Loop | `gold/skills/ralph-wiggum-loop.js` |

---

## ✅ Compliance Checklist

- [ ] All Silver requirements ✅
- [ ] Auto-post to LinkedIn ✅
- [ ] Lead monitoring ✅
- [ ] HITL approval ✅
- [ ] Cross-domain integration ✅
- [ ] Error recovery ✅
- [ ] Audit logging ✅
- [ ] Ralph Wiggum Loop ✅
- [ ] Agent Skills ✅
- [ ] Documentation ✅

---

## 📚 Documentation

- `GOLD_TIER_LINKEDIN_AUTO_POST_COMPLETE.md` - Full guide
- `GOLD_TIER_IMPLEMENTATION_COMPLETE.md` - Gold Tier overview
- `LINKEDIN_SETUP.md` - LinkedIn setup
- `Dashboard.md` - Real-time status

---

**Quick Reference v1.0 | 2026-03-31**
