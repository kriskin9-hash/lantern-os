# Linear Setup for Phase A — 1 Week

## Step 1: Connect Linear MCP (2 minutes)

### Via Claude Desktop/Code
1. Go to Claude Settings → Connectors
2. Search for "Linear"
3. Click "Connect"
4. Log in with your Linear account
5. Authorize access

## Step 2: Create Linear Workspace (5 minutes)

Once connected:

1. **Create workspace:** `Lantern OS`
2. **Create team:** `Repo Reset`
3. **Create cycles:**
   - Cycle 1: Jun 1-14 (Phase C cleanup)
   - Cycle 2: Jun 15-28 (Phase C validation)
   - Cycle 3: Jul 1-14 (Phase C finalization)

## Step 3: Auto-Populate Backlog (1 minute)

I'll use Linear MCP to create all 28 issues from LINEAR-BACKLOG.md

---

## Phase A Issues to Create

### A-1: Discord Bot MCP Bridge
- Status: In Progress
- Priority: P0
- Description: Wire Discord bot slash commands to MCP server endpoints

### A-2: Archive Curator Implementation
- Status: In Progress
- Priority: P0
- Description: Generic Internet Archive media curator for Discord voice channels

### A-3: Linear Workspace Setup
- Status: Pending
- Priority: P0
- Description: Create Linear workspace + team + cycles for work tracking

### A-4: Handoff Documentation
- Status: Pending
- Priority: P1
- Description: Prepare runbooks for operators to take over cleanup execution

### A-5: CI/Test Verification
- Status: Pending
- Priority: P1
- Description: Ensure all tests pass and bot is production-ready

---

## Quick Start Checklist

- [ ] Linear MCP connected
- [ ] Workspace created: "Lantern OS"
- [ ] Team created: "Repo Reset"
- [ ] 3 cycles created (Jun 1-14, Jun 15-28, Jul 1-14)
- [ ] Backlog issues created (I'll handle this)
- [ ] First issue claimed by operator

---

## Next: Discord Bot Testing

Once Linear is set up, test the bot:

1. **Create voice channel:** `archive` (not "Lounge")
2. **Test commands:**
   - `/archive-join` → bot connects + starts streaming
   - `/archive-list` → shows 6 Frank Sinatra songs
   - `/archive-play the_world_we_knew` → plays song
   - `/archive-next`, `/archive-loop`, `/archive-stop` → controls
   - `/archive-leave` → disconnects

3. **Verify bot is online:** Should show "27 commands synced globally"

---

## If Linear Connection Fails

Alternative: Manual import
1. Copy issues from LINEAR-BACKLOG.md
2. Paste into Linear UI one by one
3. Takes ~10 minutes, same result

---

## Timeline

- Connect Linear MCP: **2 min**
- Create workspace: **5 min**
- Auto-populate backlog: **1 min**
- Test Discord bot: **5 min**
- **Total: ~15 minutes**

Ready to proceed?
