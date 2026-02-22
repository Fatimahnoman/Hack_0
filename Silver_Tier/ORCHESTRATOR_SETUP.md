# Silver Tier Orchestrator - Setup Guide

## 🚀 How to Run

### Quick Start

```powershell
cd E:\Hackathon_Zero\Silver_Tier
python orchestrator.py
```

---

## 📦 Installation

### Step 1: Install Dependencies

```powershell
# Install all required packages
pip install apscheduler playwright

# Install Playwright browsers
playwright install chromium

# Install Google API packages (for Gmail)
pip install google-api-python-client google-auth-httplib2 google-auth-oauthlib

# Install FastMCP (for MCP tools)
pip install fastmcp
```

### Step 2: Verify Installation

```powershell
# Check packages installed
pip list | findstr apscheduler
pip list | findstr playwright
pip list | findstr fastmcp
```

---

## ⚙️ Windows Task Scheduler - Auto Start on Boot

### Option 1: Using PowerShell Script (Recommended)

**Step 1:** Create a batch file `start_orchestrator.bat` in `E:\Hackathon_Zero\Silver_Tier\`:

```batch
@echo off
cd /d E:\Hackathon_Zero\Silver_Tier
python orchestrator.py
pause
```

**Step 2:** Open Task Scheduler

```powershell
# Run this command
taskschd.msc
```

**Step 3:** Create Basic Task

1. Click **"Create Basic Task..."** in right panel
2. **Name:** `Silver Tier Orchestrator`
3. **Description:** `Auto-start Silver Tier AI Employee on boot`
4. Click **Next**

**Step 4:** Set Trigger

1. Select **"When the computer starts"**
2. Click **Next**

**Step 5:** Set Action

1. Select **"Start a program"**
2. Click **Next**
3. **Program/script:** `C:\Users\LENOVO\Downloads\python.exe`
   (Or wherever Python is installed - check with `where python`)
4. **Add arguments:** `E:\Hackathon_Zero\Silver_Tier\orchestrator.py`
5. **Start in:** `E:\Hackathon_Zero\Silver_Tier`
6. Click **Next**

**Step 6:** Finish

1. Check **"Open the Properties dialog..."**
2. Click **Finish**

**Step 7:** Configure Properties

1. Go to **"General"** tab
2. Check **"Run with highest privileges"**
3. Select **"Run whether user is logged on or not"**
4. Go to **"Conditions"** tab
5. Uncheck **"Start the task only if the computer is on AC power"**
6. Go to **"Settings"** tab
7. Check **"Allow task to be run on demand"**
8. Check **"If the task fails, restart every:"** → Set to **1 minute**
9. Check **"Attempt to restart up to:"** → Set to **3 times**
10. Click **OK**

---

### Option 2: Using PowerShell Command (Advanced)

Run this in **PowerShell as Administrator**:

```powershell
$taskName = "Silver Tier Orchestrator"
$taskPath = "\"
$action = New-ScheduledTaskAction -Execute "C:\Users\LENOVO\Downloads\python.exe" `
    -Argument "E:\Hackathon_Zero\Silver_Tier\orchestrator.py" `
    -WorkingDirectory "E:\Hackathon_Zero\Silver_Tier"
$trigger = New-ScheduledTaskTrigger -AtStartup
$principal = New-ScheduledTaskPrincipal -UserId "SYSTEM" -LogonType ServiceAccount -RunLevel Highest
$settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries `
    -StartWhenAvailable -RestartCount 3 -RestartInterval (New-TimeSpan -Minutes 1)

Register-ScheduledTask -TaskName $taskName -TaskPath $taskPath `
    -Action $action -Trigger $trigger -Principal $principal -Settings $settings
```

---

### Option 3: Using schtasks Command

Run in **Command Prompt as Administrator**:

```cmd
schtasks /Create /TN "Silver Tier Orchestrator" /TR "python E:\Hackathon_Zero\Silver_Tier\orchestrator.py" /SC ONSTART /RU SYSTEM /RL HIGHEST /F
```

---

## 🔍 Verify Task Scheduler

### Check Task Created

```powershell
# List all tasks
schtasks /Query | findstr "Silver Tier"

# Or use PowerShell
Get-ScheduledTask | Where-Object {$_.TaskName -like "*Silver*"}
```

### Run Task Manually (Test)

```powershell
# Run the task
schtasks /Run /TN "Silver Tier Orchestrator"

# Check status
schtasks /Query /TN "Silver Tier Orchestrator" /V
```

### View Task History

1. Open **Task Scheduler** (`taskschd.msc`)
2. Find **"Silver Tier Orchestrator"** in middle panel
3. Right-click → **"View"** → **"Enable All Tasks History"**
4. Check **"History"** tab in bottom panel

---

## 📊 What Orchestrator Does

### Background Threads (Always Running)

| Watcher | Check Interval | Purpose |
|---------|---------------|---------|
| Gmail | 5 minutes | Monitor emails |
| WhatsApp | 1 minute | Monitor messages |
| Instagram | 4 hours | Monitor posts/DMs |

### Scheduled Tasks (APScheduler)

| Task | Schedule | Action |
|------|----------|--------|
| Daily Instagram Post | 9:00 AM UTC | Generate caption + create request |
| Needs_Action Check | Every 30 min | Process new files |
| Dashboard Update | Every 5 min | Update live status |

---

## 📁 Expected Output

### Console Output

```
============================================================
Silver Tier Orchestrator - Starting
============================================================
Project Root: E:\Hackathon_Zero\Silver_Tier
Vault Path: E:\Hackathon_Zero\Silver_Tier\Vault
============================================================
============================================================
Starting all watchers...
============================================================
Starting Gmail Watcher thread...
[LOG] Gmail Watcher initialized
Starting WhatsApp Watcher thread...
[LOG] WhatsApp Watcher initialized
Starting Instagram Watcher thread...
[LOG] Instagram Watcher initialized
All watchers started
============================================================
Setting up APScheduler...
============================================================
✓ Scheduled: Daily Instagram Post at 09:00 AM UTC
✓ Scheduled: Needs_Action check every 30 minutes
✓ Scheduled: Dashboard update every 5 minutes
============================================================
Starting APScheduler...
Press Ctrl+C to stop
============================================================
```

### Dashboard.md Update

```markdown
# AI Employee Dashboard - Silver Tier

## Status
- Last checked: 2026-02-22 20:30:00
- Watchers: Gmail ✅ | WhatsApp ✅ | Instagram ✅ | Last check: 2026-02-22 20:30:00

## Task Log

### 2026-02-22 20:30:00 - Orchestrator started
### 2026-02-22 20:35:00 - Needs_Action check complete
### 2026-02-22 20:40:00 - Dashboard update complete
```

---

## 🛑 Stop Orchestrator

### Manual Run
```
Press Ctrl + C in terminal
```

### Task Scheduler
```powershell
# Stop running task
schtasks /End /TN "Silver Tier Orchestrator"

# Delete task
schtasks /Delete /TN "Silver Tier Orchestrator" /F
```

---

## 🐛 Troubleshooting

### Issue: "APScheduler not installed"

```powershell
pip install apscheduler
```

### Issue: "Module not found: watchers.gmail_watcher"

Check file exists:
```powershell
dir E:\Hackathon_Zero\Silver_Tier\watchers\gmail_watcher.py
```

### Issue: Task Scheduler doesn't start

1. Check Python path:
   ```powershell
   where python
   ```
2. Update task with correct path
3. Check **"Run with highest privileges"**

### Issue: Orchestrator crashes on start

Check logs:
```powershell
type E:\Hackathon_Zero\Silver_Tier\Vault\Logs\orchestrator.log
```

### Issue: Watchers not starting

1. Check dependencies installed
2. Run individual watcher to test:
   ```powershell
   python watchers\whatsapp_watcher.py
   ```

---

## ✅ Quick Test Checklist

- [ ] Dependencies installed (`pip install apscheduler playwright`)
- [ ] Orchestrator runs manually (`python orchestrator.py`)
- [ ] All 3 watchers start (check console output)
- [ ] Dashboard.md updates with status
- [ ] Task Scheduler task created
- [ ] Task runs manually (`schtasks /Run`)
- [ ] Logs created in `Vault/Logs/`

---

## 📋 Commands Reference

| Command | Purpose |
|---------|---------|
| `python orchestrator.py` | Run orchestrator manually |
| `taskschd.msc` | Open Task Scheduler |
| `schtasks /Create ...` | Create scheduled task |
| `schtasks /Run /TN "..."` | Run task manually |
| `schtasks /Delete /TN "..."` | Delete task |
| `Get-ScheduledTask` | List tasks (PowerShell) |

---

## 🎯 Daily Workflow

### Morning (9:00 AM)
- ✅ Auto-generate Instagram post
- ✅ Check Needs_Action folder

### Throughout Day
- ✅ WhatsApp messages monitored (every 1 min)
- ✅ Gmail monitored (every 5 min)
- ✅ Instagram monitored (every 4 hours)
- ✅ Dashboard updated (every 5 min)

### Every 30 Minutes
- ✅ Process new files in Needs_Action
- ✅ Create plans for new tasks
- ✅ Route sensitive actions to approval

---

## 🔗 Related Files

| File | Purpose |
|------|---------|
| `orchestrator.py` | Main orchestrator script |
| `watchers/gmail_watcher.py` | Gmail monitor |
| `watchers/whatsapp_watcher.py` | WhatsApp monitor |
| `watchers/instagram_watcher.py` | Instagram monitor |
| `skills/auto_insta_post.py` | Instagram post generator |
| `skills/process_needs_action.py` | Task processor |
| `Vault/Dashboard.md` | Live status |
| `Vault/Logs/orchestrator.log` | Orchestrator logs |

---

**Ready to automate!** 🚀

Run now:
```powershell
python E:\Hackathon_Zero\Silver_Tier\orchestrator.py
```
