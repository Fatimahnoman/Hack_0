# Company Handbook for AI Employee

## Core Rules
- Hamesha polite aur professional raho
- Payment ya sensitive action > $50 pe approval lo
- Sab kuch local Vault folder mein rakho
- No auto-send without approval

## Workflow Stages

### File Flow
```
Inbox → Needs_Action → Pending_Approval → Approved → Done
```

### Auto-Move Rules

| Stage | Trigger | Action |
|-------|---------|--------|
| Needs_Action | New file created | Wait 2 minutes |
| Needs_Action → Pending_Approval | File age > 120 seconds | Auto-move |
| Pending_Approval → Approved | Content contains `[APPROVED]` | Auto-move |
| Approved → Done | Content contains `[DONE]` | Auto-move |

### Manual Override
- Add `[APPROVED]` marker to skip Pending_Approval stage
- Add `[DONE]` marker to complete task immediately

## Watchers

| Watcher | Purpose | Session Path |
|---------|---------|--------------|
| Gmail | Monitor emails | N/A (OAuth) |
| WhatsApp | Monitor messages | `sessions/whatsapp_session/` |
| Instagram | Monitor DMs/posts | `sessions/instagram_session/` |

## Skills

| Skill | Trigger | Output |
|-------|---------|--------|
| Auto Instagram Post | `INSTA_*.md` in Needs_Action | Posts to Instagram |
