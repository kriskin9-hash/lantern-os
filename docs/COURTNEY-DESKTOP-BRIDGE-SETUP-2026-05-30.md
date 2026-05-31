# Courtney Desktop Bridge Setup Guide

**Date:** 2026-05-30  
**Purpose:** Bridge Courtney's local Windows desktop to Codex Cloud mirror setup  
**Status:** Ready for execution

---

## Simple Answer

Courtney has Codex Cloud access configured. This guide bridges her local Windows desktop to the cloud mirror for seamless local-cloud hybrid operation.

---

## Current State

**Cloud Side (Already Configured):**
- Codex Cloud environment: Active
- User: courtney (collaborator role)
- GitHub repos: lantern-os, gamemaker-room-editor, ChildOfLevistus
- RAG context: family_projects, collaboration_workflows, shared_decisions
- Content filter: family_safe

**Local Side (Needs Setup):**
- Windows desktop with Windsurf
- Lantern OS local installation (zip method)
- Local-first architecture ready

**Bridge Goal:**
Connect local desktop to Codex Cloud for:
- Repository sync
- Cloud chat access
- RAG context retrieval
- Collaborative workflows

---

## Bridge Setup Steps

### Step 1: Verify Local Prerequisites

**On Courtney's Windows desktop:**

1. **Check Windsurf Installation**
   - Open Windsurf
   - Verify it's working and can open repositories

2. **Check Node.js**
   - Open PowerShell
   - Run: `node --version`
   - Should show 20.x or higher

3. **Check Git** (if using clone method)
   - Run: `git --version`
   - Install from git-scm.com if missing

### Step 2: Clone Repository Locally

**Option A: Direct Clone (Recommended for Bridge)**

```powershell
# Open PowerShell in desired folder (e.g., C:\LanternOS)
cd C:\LanternOS
git clone https://github.com/alex-place/lantern-os.git
cd lantern-os
```

**Option B: Zip Extract + Git Init** (If offline)

```powershell
# Extract lantern-desktop-tester-latest.zip to C:\LanternOS
cd C:\LanternOS
git init
git remote add origin https://github.com/alex-place/lantern-os.git
git fetch origin
git checkout master
```

### Step 3: Configure Git for Cloud Sync

```powershell
# Set up git credentials (one-time)
git config --global user.name "Courtney Blasioli"
git config --global user.email "courtney@example.com"  # Replace with actual email

# Verify remote
git remote -v
# Should show: origin https://github.com/alex-place/lantern-os.git
```

### Step 4: Test Cloud Bridge Connection

```powershell
# Pull latest from cloud
git pull origin master

# Verify local matches cloud
git status
# Should show: "Your branch is up to date with 'origin/master'"
```

### Step 5: Start Local Lantern OS

```powershell
# Run local start script
.\scripts\Start-LanternDesktopTester.ps1

# Or if execution policy blocks:
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
.\scripts\Start-LanternDesktopTester.ps1
```

**Browser should open to:** `http://127.0.0.1:4177`

### Step 6: Configure Local-Cloud Sync

**In Windsurf, open the cloned repository:**

1. **Open Windsurf**
2. **File → Open Folder**
3. **Navigate to:** `C:\LanternOS\lantern-os`
4. **Repository now synced with cloud**

**Sync Workflow:**
```powershell
# Before starting work, pull latest changes
git pull origin master

# After making changes, commit and push
git add .
git commit -m "Your commit message"
git push origin master
```

---

## Codex Cloud Integration

### Access Cloud Chat

**Via Codex Cloud:**
1. Go to: `https://chatgpt.com/codex/cloud`
2. Select your Lantern OS environment
3. Chat with cloud-connected Lantern OS

**Via Local Web App:**
1. Local app at: `http://127.0.0.1:4177`
2. Uses local RAG context
3. Can sync with cloud via git

### RAG Context Bridge

**Your RAG context is configured for:**
- Family projects
- Collaboration workflows
- Shared decisions
- GameMaker family access

**To verify RAG context:**
1. In Codex Cloud chat, ask: "Show me my user context"
2. Should display your collaborator profile
3. Should show family-safe content filter active

---

## Discord Bot Bridge

### Join Discord Server

1. **Get Discord invite from operator**
2. **Join Lantern Discord server**
3. **Verify you're in collaboration channel**

### Bot Commands

**Status check:**
```
!lantern-status
```

**Voice check:**
```
!lantern-voice-check
```

**Note:** Voice features are held pending operator approval and safety gates.

---

## Daily Workflow

### Morning Sync

```powershell
# Open PowerShell in lantern-os directory
cd C:\LanternOS\lantern-os

# Pull latest changes from cloud
git pull origin master

# Start local Lantern OS
.\scripts\Start-LanternDesktopTester.ps1
```

### During Work

**Local work:**
- Use Windsurf for code editing
- Use local web app at `http://127.0.0.1:4177`
- Make changes locally

**Cloud sync:**
```powershell
# Commit changes
git add .
git commit -m "Describe your changes"

# Push to cloud
git push origin master
```

### Evening Sync

```powershell
# Pull any changes from others
git pull origin master

# Stop local Lantern OS (Ctrl+C in PowerShell)
```

---

## Troubleshooting

### Git Sync Issues

**Error: "Permission denied"**
```powershell
# Check git remote
git remote -v

# Re-add remote if needed
git remote set-url origin https://github.com/alex-place/lantern-os.git
```

**Error: "Authentication failed"**
- Verify GitHub credentials
- Check repository access permissions
- Contact operator to grant access if needed

### Local App Won't Start

**Port already in use:**
```powershell
# Find process using port 4177
netstat -ano | findstr :4177

# Kill the process (replace PID)
taskkill /PID <PID> /F
```

**Node.js not found:**
- Install Node.js from nodejs.org
- Restart PowerShell
- Verify with `node --version`

### Cloud Chat Not Working

**Environment not accessible:**
- Verify Codex Cloud account is active
- Check GitHub connector is configured
- Contact operator for environment setup verification

**RAG context not loading:**
- Verify environment variables are set:
  ```json
  {
    "LANCERN_USER": "courtney",
    "LANCERN_USER_ROLE": "collaborator",
    "LANCERN_CONTENT_FILTER": "family_safe"
  }
  ```
- Ask in chat: "Show me my user context"

---

## Validation Checklist

**After setup, verify:**

- [ ] Windsurf can open lantern-os repository
- [ ] Git can pull from origin/master
- [ ] Git can push to origin/master
- [ ] Local Lantern OS starts at `http://127.0.0.1:4177`
- [ ] Codex Cloud chat responds with user context
- [ ] RAG context shows family_projects, collaboration_workflows
- [ ] Content filter shows family_safe
- [ ] Discord bot responds in collaboration channel

---

## Next Actions

**Immediate (Today):**
1. Complete Steps 1-6 above
2. Run validation checklist
3. Test basic chat in Codex Cloud
4. Test local web app

**This Week:**
1. Use daily sync workflow
2. Test collaboration features
3. Provide feedback on bridge performance
4. Coordinate with operator on any issues

**Ongoing:**
1. Maintain daily sync routine
2. Use for family project collaboration
3. Help test and improve bridge
4. Coordinate with other users (Gage, Waruichinchilla)

---

## Support

**If issues arise:**
1. Check troubleshooting section above
2. Contact operator for help
3. Review docs/CODEX-CLOUD-USER-SETUP-GUIDE.md
4. Review docs/COURTNEY-WINDOWS-SETUP-GUIDE-2026-05-30.md

---

**Prepared for:** Courtney Blasioli  
**Date:** 2026-05-30  
**Bridge Type:** Local Windows Desktop ↔ Codex Cloud  
**Status:** Ready for execution
