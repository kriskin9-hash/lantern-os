# Dream Journal Discord Bot — Linear Backlog (Ready to Import)

**Date:** June 1, 2026  
**Status:** Ready for operator claiming  
**Total effort:** 13.5–16.5 days (3–4 weeks)

---

## PHASE 1: Patreon + Discord Setup (Week 1)

### LIN-1: Create Patreon page (Free Dreamer tier)
**Team:** Dream Journal  
**Assignee:** TBD (marketing/product)  
**Effort:** 2 hours  
**Priority:** P0  
**Acceptance Criteria:**
- [ ] Patreon account created for Dream Journal
- [ ] Page name: "Dream Journal by Lantern OS"
- [ ] Preferred URL slug: `dreamjournal`
- [ ] Bio text added: "Dream Journal by Lantern OS is a private dream-journaling community built around reflection, memory, and meaningful conversation."
- [ ] Header photo uploaded (recommend: serene landscape or night sky)
- [ ] Cover photo uploaded (recommend: dream-themed or meditation-themed)
- [ ] Free Dreamer tier created and published with description: "Follow Dream Journal, join the public Discord, and explore the Lantern OS dream-journaling community before becoming a paid member."
- [ ] Benefits added to Free tier:
  - Private community (text: "Public Discord access for Dream Journal updates, community chat, and bot command discovery.")
  - General Support (text: "Follow and support Dream Journal while exploring the public community.")
- [ ] Shipping: Off
- [ ] Member limit: Off
- [ ] Page is live and viewable

**Resources:**
- Bio text provided in requirements
- No photos yet (use placeholder or generic image)

---

### LIN-2: Create Dream Supporter tier ($20/mo)
**Team:** Dream Journal  
**Assignee:** TBD (marketing/product)  
**Effort:** 1.5 hours  
**Priority:** P0  
**Acceptance Criteria:**
- [ ] Tier created with name: "Dream Supporter"
- [ ] Price: $20/month
- [ ] Tier description: "Unlock the main Dream Journal experience: private dream notes, guided prompts, notebook recall, and access to the Dreamer Well inside Discord."
- [ ] Benefits added:
  - Private community (text: "Supporter Discord role with access to the Dreamer Well and support channels.")
  - Exclusive content (text: "Member-only dream prompts, reflections, and Dream Journal updates.")
  - Digital downloads (text: "Access digital Dream Journal materials, prompts, and reflection templates when released.")
  - Live chat (text: "Participate in Discord-based dream reflection and community chat.")
- [ ] Free trial: Off
- [ ] Shipping: Off
- [ ] Member limit: Off
- [ ] Discord access: Prepared for mapping (not yet connected)
- [ ] Tier is published and visible in checkout

**Commands unlocked:**
/help, /status, /subscribe, /note, /recall, /dream, /prompt, /music, /art, /movies

---

### LIN-3: Create Dream Pilot tier ($200/mo)
**Team:** Dream Journal  
**Assignee:** TBD (marketing/product)  
**Effort:** 1.5 hours  
**Priority:** P0  
**Acceptance Criteria:**
- [ ] Tier created with name: "Dream Pilot"
- [ ] Price: $200/month
- [ ] Tier description: "For members who want deeper support, custom workflows, and priority access. Includes the full Dream Journal experience plus Pilot workspace access, queue/intake support, and higher-touch operator help."
- [ ] Benefits added:
  - Private community (text: "Pilot Discord role with access to the Pilot Workspace and Pilot Workshop voice channel.")
  - Commissions (digital) (text: "Request custom digital workflow or skill support through the Pilot queue.")
  - Fan requests (text: "Submit priority requests for Dream Journal workflows, bot improvements, or custom use cases.")
  - Live chat (text: "Higher-touch Discord support and direct queue coordination.")
  - Live Q&As (text: "Access periodic Q&A or working sessions when scheduled.")
- [ ] Free trial: Off
- [ ] Shipping: Off
- [ ] Member limit: On, capped at 5
- [ ] Discord access: Prepared for mapping (not yet connected)
- [ ] Tier is published and visible in checkout

**Commands unlocked:**
/help, /status, /subscribe, /note, /recall, /dream, /prompt, /music, /art, /movies, /queue, /intake, /skill, /workspace, /sing, /nextsong, /stop, /leave

---

### LIN-4: Connect Discord to Patreon (OAuth role mapping)
**Team:** Dream Journal  
**Assignee:** TBD (Discord/integration ops)  
**Effort:** 0.5 hours  
**Priority:** P0  
**Dependencies:** LIN-1, LIN-2, LIN-3 (all tiers must exist first)  
**Acceptance Criteria:**
- [ ] Patreon Settings → Connected apps → Discord is authorized
- [ ] Patreon authenticates with Discord (OAuth handshake successful)
- [ ] Tier-to-role mapping configured:
  - Dream Supporter tier → Discord "Supporter" role
  - Dream Pilot tier → Discord "Pilot" role
- [ ] Do NOT map Free Dreamer or Founder as Patreon tiers (Free Dreamer is default, Founder is internal)
- [ ] Test with 1 test account: Subscriber joins Patreon Supporter tier → verify Discord automatically assigns Supporter role within 5 minutes
- [ ] Mapping is live and working

**Resources:**
- Discord server must have Supporter and Pilot roles already created
- Patreon account must have admin permission on Discord server
- Discord bot (Lantern OS#3589) must already be in server

---

### LIN-5: Verify Discord roles and channels exist
**Team:** Dream Journal  
**Assignee:** TBD (Discord admin)  
**Effort:** 0.5 hours  
**Priority:** P0  
**Dependencies:** None (can do in parallel with LIN-1 to LIN-4)  
**Acceptance Criteria:**

**Roles (verify exist + names are exact):**
- [ ] Role: "Supporter" exists
- [ ] Role: "Pilot" exists
- [ ] Role: "Founder" exists

**Text channels (verify exist + permissions are correct):**
- [ ] #welcome (public, read-only)
- [ ] #announcements (public, read-only)
- [ ] #general-chat (public, @everyone can read + write)
- [ ] #bot-commands (public, @everyone can read + write)
- [ ] #dreamer-well (Supporter+ only, @everyone else cannot see)
- [ ] #support (Supporter+ only, @everyone else cannot see)
- [ ] #pilot-workspace (Pilot+ only, Supporter users cannot see)

**Voice channels (verify exist + permissions are correct):**
- [ ] Lounge (public, @everyone can join)
- [ ] Pilot Workshop (Pilot+ only, Supporter users cannot see)
- [ ] Founder Council (Founder only, no one else can join)

**Permissions verification:**
- [ ] Bot role (Lantern OS) is ABOVE Supporter and Pilot roles in role hierarchy
- [ ] Bot has permissions: Send Messages, Use Slash Commands, Connect (voice), Speak (voice), Manage Messages
- [ ] All channels have permissions set correctly (test by switching roles and verifying visibility)

---

## PHASE 2: Bot Startup + Command Gating (Week 2)

### LIN-6: Start Discord bot process (production)
**Team:** Dream Journal  
**Assignee:** TBD (DevOps/bot ops)  
**Effort:** 1 hour  
**Priority:** P0  
**Dependencies:** LIN-5 (roles and channels must exist first)  
**Acceptance Criteria:**
- [ ] Environment variables set:
  - DISCORD_BOT_TOKEN=<valid-token>
  - DISCORD_GUILD_ID=<guild-id>
  - LANTERN_STATUS_URL=http://127.0.0.1:4177/api/status (or mock if backend down)
  - SUBSCRIBER_DATA_PATH=data/discord/subscribers.json
- [ ] .env file created in src/discord_lounge_bot/ (or env vars exported)
- [ ] Bot process started: `python src/discord_lounge_bot/bot_v2.py`
- [ ] Startup log shows:
  - [INFO] Starting Lantern OS Discord Bot v2...
  - [READY] Logged in as Lantern OS#xxxx
  - [INFO] Voice player initialized.
  - No error messages in logs
- [ ] Bot appears "Online" in Discord server member list
- [ ] Slash commands synced to server (should show 27+ commands)
- [ ] Bot watchdog configured to auto-restart on crash (within 30s)

**Resources:**
- Discord bot token (must be pre-created in Discord Developer Portal)
- Guild ID (Discord server ID)
- FFmpeg must be installed and in PATH

**Troubleshooting:**
- If bot doesn't appear online: verify token is correct, bot has permissions on server
- If commands don't sync: wait 10–15 seconds, refresh Discord client (Ctrl+R)

---

### LIN-7: Test free user commands (/help, /status, /subscribe)
**Team:** Dream Journal  
**Assignee:** TBD (QA/testing)  
**Effort:** 0.5 hours  
**Priority:** P0  
**Dependencies:** LIN-6 (bot must be running)  
**Acceptance Criteria:**
- [ ] Free user (no Supporter role) can execute: /help
- [ ] /help output shows all available commands and tier requirements
- [ ] Free user can execute: /status
- [ ] /status returns bot status + Lantern uptime info
- [ ] Free user can execute: /subscribe
- [ ] /subscribe button/link directs to Patreon checkout at patreon.com/dreamjournal
- [ ] No errors in bot logs for these commands
- [ ] All 3 commands respond within 2 seconds

**Test users:**
- Use yourself (remove Supporter/Pilot roles)
- Or create test Discord account and give it no roles

---

### LIN-8: Test Supporter command gating (/note, /recall, /dream, /prompt)
**Team:** Dream Journal  
**Assignee:** TBD (QA/testing)  
**Effort:** 0.75 hours  
**Priority:** P0  
**Dependencies:** LIN-6, LIN-4 (bot running + role mapping working)  
**Acceptance Criteria:**
- [ ] **Supporter user can execute:**
  - /note test dream → saves note to notebook
  - /recall → returns list of saved notes
  - /dream → shows dream prompt
  - /prompt → shows guided reflection prompt
- [ ] **Free user is blocked from above commands** with error: "Supporter tier required"
- [ ] No command leaks (free user cannot access Supporter commands)
- [ ] All commands respond within 2 seconds
- [ ] Bot logs show no errors for blocked attempts

**Test procedure:**
1. Create test Discord account or remove Supporter role from yourself
2. Try /note as free user → expect error
3. Add Supporter role
4. Try /note as Supporter → expect success
5. Try /recall, /dream, /prompt
6. Verify all succeed

---

### LIN-9: Test Pilot command gating (/queue, /intake, /skill, /workspace)
**Team:** Dream Journal  
**Assignee:** TBD (QA/testing)  
**Effort:** 0.75 hours  
**Priority:** P0  
**Dependencies:** LIN-6, LIN-4 (bot running + role mapping working)  
**Acceptance Criteria:**
- [ ] **Pilot user can execute:**
  - /queue → shows queue status
  - /intake → opens workflow intake form
  - /skill → shows available skills
  - /workspace → shows pilot workspace
- [ ] **Supporter user is blocked** from all above with error: "Pilot tier required"
- [ ] **Free user is blocked** from all above with error: "Pilot tier required"
- [ ] No command leaks between tiers
- [ ] All commands respond within 2 seconds
- [ ] Bot logs show no errors

**Test procedure:**
1. Test as free user: all 4 commands should error
2. Test as Supporter: all 4 commands should error
3. Test as Pilot: all 4 commands should succeed

---

### LIN-10: Verify Founder commands remain private (/dispatch, /controls, /boot-check, /release-gate)
**Team:** Dream Journal  
**Assignee:** Founder or lead engineer  
**Effort:** 0.25 hours  
**Priority:** P1  
**Dependencies:** LIN-6 (bot running)  
**Acceptance Criteria:**
- [ ] /dispatch, /controls, /boot-check, /release-gate are NOT listed in /help output
- [ ] /help shows only free + Supporter + Pilot commands (no Founder commands)
- [ ] Non-Founder users cannot execute Founder commands (error: "Founder access only")
- [ ] Founder user can execute Founder commands without error
- [ ] Bot logs show no errors for blocked Founder command attempts

---

## PHASE 3: Launch Readiness (Week 2–3)

### LIN-11: Add Patreon welcome copy to Discord
**Team:** Dream Journal  
**Assignee:** TBD (content/community)  
**Effort:** 0.5 hours  
**Priority:** P0  
**Dependencies:** LIN-5 (channels must exist)  
**Acceptance Criteria:**
- [ ] Welcome post pinned in #welcome with content:

```
Welcome to Dream Journal by Lantern OS.

Start here:
/help — see available commands
/status — check Lantern status
/subscribe — upgrade access

Supporters unlock:
/note — save dream notes
/recall — review saved notes
/dream — guided dream prompts
/prompt — reflection prompts

Pilots unlock:
/queue — submit requests
/intake — workflow setup
/skill — available skills
/workspace — pilot workspace

Join the Patreon to unlock features: patreon.com/dreamjournal
```

- [ ] Welcome message is pinned and visible at top of channel
- [ ] All links (patreon.com/dreamjournal) are correct
- [ ] Formatting is clean and readable

---

### LIN-12: Invite 10 test users for soft launch
**Team:** Dream Journal  
**Assignee:** Founder + TBD (community manager)  
**Effort:** 3 hours  
**Priority:** P0  
**Dependencies:** LIN-11 (welcome post should be pinned)  
**Acceptance Criteria:**
- [ ] 10 test users invited to Discord server
- [ ] At least 3 test users subscribe to Supporter tier ($20/mo)
- [ ] At least 1 test user subscribes to Pilot tier ($200/mo)
- [ ] Discord role sync verified (Supporters have Supporter role, Pilots have Pilot role)
- [ ] Test user feedback collected on:
  - [ ] Can they join Discord without friction?
  - [ ] Does Patreon assign the right Discord role?
  - [ ] Can Supporter use /note, /recall, /dream, /prompt?
  - [ ] Can Pilot use /queue, /intake, /skill, /workspace?
  - [ ] Does /subscribe send them to the right checkout?
- [ ] No critical bugs reported by test users
- [ ] All feedback documented for Phase 3-3

**Resources:**
- 10 trusted friends or community members to test as paying users
- Patreon checkout URL (should be patreon.com/dreamjournal)

---

### LIN-13: Fix bugs from soft launch feedback
**Team:** Dream Journal  
**Assignee:** Lead engineer + QA  
**Effort:** 3–5 hours (variable)  
**Priority:** P1  
**Dependencies:** LIN-12 (must collect feedback first)  
**Acceptance Criteria:**
- [ ] All P1 bugs reported by test users are fixed
- [ ] All P2 bugs are triaged (fix or defer decision made)
- [ ] Bot logs show no errors after fixes
- [ ] Supporter workflow tested again after fixes
- [ ] Pilot workflow tested again after fixes
- [ ] Test users confirm fixes work (1:1 confirmation not needed, spot checks OK)

**Expected bugs:**
- Command permission errors
- Role sync delays
- FFmpeg issues (if voice commands tested)
- Patreon checkout redirect issues

---

### LIN-14: Public launch — publish Patreon + Discord invite
**Team:** Dream Journal  
**Assignee:** Founder + marketing operator  
**Effort:** 1 hour  
**Priority:** P0  
**Dependencies:** LIN-13 (all bugs must be fixed)  
**Acceptance Criteria:**
- [ ] Patreon page is public (not in draft mode)
- [ ] Patreon page link is shareable and working
- [ ] Discord invite link is public (or handle-based, e.g., /dreamjournal)
- [ ] Announcement posted to social/community channels (Twitter, Reddit, Patreon feed, etc.)
- [ ] Announcement text includes:
  - [ ] What Dream Journal is (1–2 sentences)
  - [ ] Patreon link (patreon.com/dreamjournal)
  - [ ] Discord invite link
  - [ ] Tier pricing and benefits (brief)
- [ ] At least 5 soft-launch test users have already paid
- [ ] 0 critical issues in bot logs or Discord
- [ ] Bot is online and responding
- [ ] Go/no-go decision: IF all boxes checked, launch. IF blockers exist, defer to LIN-13.

---

## PHASE COMPLETION CHECKLIST

**By Jun 3 (end of Phase 1):**
- [ ] LIN-1: Patreon Free Dreamer tier live
- [ ] LIN-2: Patreon Supporter tier live
- [ ] LIN-3: Patreon Pilot tier live
- [ ] LIN-4: Discord-Patreon OAuth mapping working (test with 1 user)
- [ ] LIN-5: All Discord roles + channels verified

**By Jun 10 (end of Phase 2):**
- [ ] LIN-6: Bot running and online
- [ ] LIN-7: Free commands working
- [ ] LIN-8: Supporter commands gated + working
- [ ] LIN-9: Pilot commands gated + working
- [ ] LIN-10: Founder commands private

**By Jun 15 (end of Phase 3):**
- [ ] LIN-11: Welcome post pinned
- [ ] LIN-12: 10 test users, 3+ Supporters, 1+ Pilot, feedback collected
- [ ] LIN-13: All bugs fixed, test users happy
- [ ] LIN-14: Public launch, 5+ paid members, announcement posted

---

## Success Metrics

| Milestone | Target | Definition of Done |
|-----------|--------|---|
| Patreon live | Jun 3 | 3 tiers published, 0 errors in checkout |
| Discord sync | Jun 5 | OAuth working, 2+ test users auto-assigned roles |
| Command gating | Jun 7 | All 3 tiers tested, 0 command leaks |
| Soft launch | Jun 10 | 10 users, 3+ Supporters, 1+ Pilot, 0 P1 bugs |
| Public launch | Jun 15 | Patreon public, 5+ paid, announcement live |
| **Monthly revenue** | **Jun 30** | **$260+ MRR** (3 Supporters × $20 + 1 Pilot × $200) |

---

## Ready to Import

Copy these 14 issues into Linear:
- Team: Dream Journal
- Cycle 1: Jun 1–7 (Phase 1: LIN-1 to LIN-5)
- Cycle 2: Jun 8–14 (Phase 2: LIN-6 to LIN-10)
- Cycle 3: Jun 15–21 (Phase 3: LIN-11 to LIN-14)

All acceptance criteria, dependencies, and resources are documented above.

**Status:** 🚀 Ready for operator claiming
