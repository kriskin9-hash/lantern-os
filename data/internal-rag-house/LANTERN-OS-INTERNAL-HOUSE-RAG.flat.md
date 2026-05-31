# Lantern OS Internal House RAG

Generated: 2026-05-31T03:42:15.8761381-04:00

This flat file is an internal, source-linked RAG house index for Lantern OS. It records file paths, hashes, evidence classes, and optional file bodies. It does not delete or move source files.

## Boundaries

- Internal storage only.
- No secrets, .env files, private folders, or raw PIID should be imported.
- Source repositories remain authoritative until a promotion commit is reviewed.
- Moving code means copy/promote with hashes first, then retire old source paths only after validation.

## Included files

### AGENTS.md

- evidenceClass: local_verified
- bytes: 2683
- sha256: 56473795c093cdc66459ff8ae6509c64abbed3cb949544ec6fde86faea76ae38
- modifiedUtc: 2026-05-29T14:33:41.3922913Z

``md
# AGENTS

Status: active agent instruction file  
Repo: Lantern OS v1.0.0 staging  
Style spine: `docs/ORION-MOOKMANREPORT4-STYLE.md`

---

## Simple Answer

Agents working in this repo should make Lantern OS clearer, safer, and easier to validate.

Every change should move raw material toward an Orion-style technical sheet: clear purpose, real evidence, held boundaries, next action, and validation path.

---

## Operating Rules

- Inspect before editing.
- Keep changes small and reviewable.
- Do not import dirty worktree state blindly from source repos.
- Do not mutate boot configuration, partitions, firmware boot order, or disks.
- Do not claim v1.0.0 readiness without operator approval.
- Use the Innovator evidence method for promotion decisions.
- Do not stop at skeletons. If a loop finds actionable local issues, fix the first 2-4 before starting new expansion work.
- Retire deprecated surfaces as an explicit convergence step.
- Apply the Orion / Mookman Report 4 style to public-facing Markdown, flat text, and CSS.

---

## Source Repos

```text
C:\tmp\human-flourishing-frameworks-scan
C:\Users\alexp\Documents\gm-agent-orchestrator
```

Both may be dirty. Treat their working tree state as evidence, not as something to overwrite or reset.

---

## Promotion Criteria

An artifact can move into this repo when it has:

- source path;
- purpose;
- claim IDs or clear claim summary;
- validation status;
- blockers and rollback notes;
- operator approval status;
- human-readable first screen;
- no raw filepath spam above the first explanation.

---

## Flat Document Shape

Use this order for public-safe `.md` and `.txt` files unless the file has a stronger operational structure:

1. title;
2. short metadata block;
3. simple answer;
4. what it actually does;
5. evidence / source discipline;
6. proven / held / local-only;
7. next safe action;
8. validation path;
9. appendices, raw commands, paths, and receipts.

---

## CSS Surface Shape

For static surfaces, use the Orion style:

- limestone / warm white paper;
- thin blue grid lines;
- teal/cyan status accents;
- amber held-state accents;
- rounded technical panels;
- visible focus outlines;
- no fake active buttons;
- disabled controls clearly marked as local-only or held.

---

## Required Loop

Before meaningful work, run:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\Invoke-LanternConvergenceLoop.ps1
```

Then handle the first 2-4 reported issues in priority order. If an issue cannot be fixed safely, mark it held in `manifests/open-issues.md` with the reason.

---

## Branching

Use `codex/` branch names for agent work unless the operator asks otherwise.
``

### QUICK-START.md

- evidenceClass: local_verified
- bytes: 8464
- sha256: 5025bc1318a66acf856f096e3ce9f2cba72086e0f4e5bb3ef7c9335d95841b8c
- modifiedUtc: 2026-05-29T14:28:19.4737116Z

``md
# Windsurf Developer Quick Start Guide

Generated: 2026-05-28
Get started with the Windsurf-inspired AI-powered developer interface for Lantern OS.

## What is Windsurf Developer?

Windsurf Developer is an AI-powered development environment designed specifically for Lantern OS. It brings Windsurf-style functionality to Lantern OS with:

- **Real-time AI code assistance** with full RAG context
- **Integrated developer tools** for Lantern OS workflows
- **Seamless Git integration** for version control
- **Command palette** for quick access to Lantern OS commands
- **Developer productivity features** enhanced by AI

## Quick Start (5 Minutes)

### 1. Open the Interface

Navigate to the Windsurf Developer interface:

```bash
cd surfaces/windsurf-dev
# Open index.html in your browser
# Or use the local server if configured
```

### 2. Navigate Files

Use the file explorer (left panel) to navigate the Lantern OS repository:
- Click folders to expand them
- Click files to open them
- Use file tabs to switch between open files

### 3. Get AI Assistance

**Option 1: Quick Actions**
- Click one of the quick action buttons in the AI panel:
  - "Explain" - Explain selected code
  - "Debug" - Debug current code
  - "Optimize" - Optimize code performance
  - "Test" - Generate tests

**Option 2: AI Chat**
- Press Ctrl+K to open AI chat focus
- Type your question or request
- Press Enter to send
- Get context-aware AI responses

**Option 3: Command Palette**
- Press Ctrl+P to open command palette
- Search for commands or files
- Execute with Enter

### 4. Run Code

- Press Ctrl+Enter to run the current code
- View results in the output panel
- Get AI assistance with debugging if needed

## Essential Keyboard Shortcuts

| Shortcut | Action |
|---|---|
| Ctrl+K | Open AI chat |
| Ctrl+P | Open command palette |
| Ctrl+Enter | Run code |
| Ctrl+S | Save file |
| Escape | Close modals |
| Tab | Insert indentation |

## Common Workflows

### Debugging Lantern OS Code

1. Open the file you want to debug (e.g., `scripts/Invoke-LanternConvergenceLoop.ps1`)
2. Select the code section you're working on
3. Press Ctrl+K to open AI chat
4. Ask: "Debug this code for potential issues"
5. Review AI suggestions and explanations
6. Apply fixes with AI assistance

### Writing New Lantern OS Scripts

1. Create or navigate to the scripts directory
2. Start writing your script with AI assistance
3. Use "Explain" to understand Lantern OS patterns
4. Use "Optimize" for performance improvements
5. Use "Test" to generate test cases
6. Run the script and debug with AI help

### Updating Manifests

1. Navigate to the manifests directory
2. Open the manifest you want to update
3. Use AI to understand the manifest structure
4. Make changes with AI assistance
5. Get AI explanations of manifest conventions
6. Validate changes with AI review

## AI Commands

Use these commands in the AI chat:

- `/explain` - Explain selected code
- `/debug` - Debug current code
- `/optimize` - Optimize current code
- `/test` - Generate tests
- `/rag` - Update RAG context
- `/commit` - Create Git commit
- `/format` - Format code

## Tips for Maximum Productivity

### Leverage RAG Context

The AI has full awareness of:
- Lantern OS documentation and manifests
- Repository structure and conventions
- Deployment scripts and workflows
- Safety boundaries and access controls

**Ask context-specific questions:**
- "How does this fit into the Lantern OS architecture?"
- "What are the safety considerations for this code?"
- "How does this integrate with the convergence loop?"

### Use Quick Actions

Quick actions are faster than typing full questions:
- Click "Explain" instead of typing "Please explain this code"
- Click "Debug" instead of typing "Please debug this code"
- Get instant results without waiting for AI response

### Keyboard Mastery

Master the essential shortcuts:
- Ctrl+K for AI assistance (most used)
- Ctrl+P for commands (fastest way to execute actions)
- Ctrl+Enter to run code (instant feedback)
- Escape to close modals (quick exit)

### Multi-File Workflow

- Use file tabs to switch between related files
- AI maintains context across open files
- Use command palette to quickly access files
- Leverage AI for understanding file relationships

## AI Assistance Best Practices

### Good Questions

- "Explain how the convergence loop works"
- "Debug this PowerShell script for potential issues"
- "Optimize this JavaScript code for better performance"
- "Generate tests for this function"

### Context-Rich Questions

- "How does this script integrate with the Lantern OS deployment?"
- "What are the safety considerations for this RAG integration?"
- "How can I improve the error handling in this file?"

### Actionable Requests

- "Show me how to add error handling to this function"
- "Suggest optimizations for this database query"
- "Help me write tests for the convergence loop"

## Common Use Cases

### Convergence Loop Development

1. Open `scripts/Invoke-LanternConvergenceLoop.ps1`
2. Use AI to understand the loop logic
3. Ask: "Explain how this convergence loop works"
4. Make changes with AI assistance
5. Use "Debug" to check for issues
6. Run the script with Ctrl+Enter

### RAG System Updates

1. Navigate to the RAG system files
2. Use AI to understand RAG architecture
3. Ask: "What are the key components of the RAG system?"
4. Make updates with AI guidance
5. Validate changes with AI review
6. Update documentation with AI help

### Deployment Script Development

1. Navigate to deployment scripts
2. Use AI to understand deployment patterns
3. Ask: "Explain the deployment workflow"
4. Write or modify scripts with AI assistance
5. Use "Test" to generate deployment tests
6. Validate deployment with AI help

## Troubleshooting

### AI Not Responding

- Check AI connection status in header
- Verify RAG context is loaded
- Refresh the page if needed
- Check your internet connection

### Code Not Running

- Verify file is saved (Ctrl+S)
- Check for syntax errors
- Look for AI error suggestions
- Check console for error messages

### File Access Issues

- Verify developer role permissions
- Check repository access level
- Ensure file is not locked
- Check file permissions

## Getting Help

### Built-in Help

- Press Ctrl+P for command palette
- Type "help" to see available commands
- Use AI chat to ask for assistance
- Check documentation in AI context

### Documentation

- Full documentation: `WINDSURF-DEVELOPER-EXPERIENCE.md`
- Skill documentation: `skills/windsurf-dev/SKILL.md`
- Lantern OS docs: `docs/` directory

### AI Assistance

The AI assistant can help with:
- Using the interface
- Understanding Lantern OS patterns
- Debugging code issues
- Optimizing performance
- Generating tests

## Advanced Features

### Custom Quick Actions

You can add custom quick actions by modifying the JavaScript:
- Edit `windsurf-dev.js`
- Add custom action handlers
- Extend command palette
- Add keyboard shortcuts

### Extended Context

The AI can be configured with additional context:
- Project-specific documentation
- Development patterns
- Team conventions
- Custom RAG sources

### Workflow Automation

Create automated workflows:
- Multi-step development processes
- Automated testing sequences
- Documentation generation
- Code review automation

## Safety and Access

### Developer Requirements

- Developer role required
- Read access to Lantern OS repository
- RAG system access
- AI service availability

### Safety Boundaries

- Respects Lantern OS safety rules
- No destructive operations without confirmation
- Secure credential handling
- Audit logging for AI interactions

## Next Steps

1. **Explore the Interface**: Spend 5-10 minutes exploring the interface
2. **Try AI Features**: Use quick actions and AI chat
3. **Work on Real Code**: Edit actual Lantern OS files
4. **Learn Shortcuts**: Master the essential keyboard shortcuts
5. **Customize**: Add custom actions for your workflow

## Success Criteria

You're successfully using Windsurf Developer when:
- You can navigate and edit files efficiently
- AI assistance improves your development speed
- You understand Lantern OS patterns better
- You can debug and optimize code effectively
- Keyboard shortcuts become second nature

---

**Ready to code smarter with AI assistance! ðŸš€**

**Interface**: `surfaces/windsurf-dev/index.html`  
**Documentation**: `WINDSURF-DEVELOPER-EXPERIENCE.md`  
**Skill**: `skills/windsurf-dev/SKILL.md`
``

### README.md

- evidenceClass: local_verified
- bytes: 9323
- sha256: abaad2c58f86c597ce589e85bc41f7ae7811702d065abe396fb572400bdc11a9
- modifiedUtc: 2026-05-30T19:15:51.4458112Z

``md
# Lantern OS

Status: pre-v1.0.0 staging  
Scope: local-first operating repo, surfaces, reports, manifests, and release gates  
Style spine: `docs/ORION-MOOKMANREPORT4-STYLE.md`  
Operator boundary: local MCP status, dirty worktrees, private folders, boot mutation, and live worker counts require operator-machine evidence

---

## Open Lantern

Primary local dashboard:

```text
http://127.0.0.1:4177
```

This is the front door for interaction: first-class chat, RAG memory, wallet
truth, local controls, outreach, reports, devices, diagnostics, cloud mirrors,
and Arc Reactor Mining Lab converge here. No setup screen or secondary launcher
is required when the dashboard is already running. No separate mining dashboard,
no shortcut sprawl, no fake surfaces.

Windows tester download path:

```text
https://github.com/alex-place/lantern-os/releases/latest
```

Use `lantern-desktop-tester-latest.zip` for the current tester lane. The install
wiki is `docs/wiki/WINDOWS-TESTER-INSTALL.md`. Do not claim an `.exe` is ready
unless that release asset exists on GitHub. `Lantern-OS-Free-Setup.exe` and
`Lantern-OS-Founder-20-Setup.exe` are future installer asset names only until
they are attached to a release.

---

## Simple Answer

Lantern OS is the clean control plane for the Windows/local-first Lantern line.

The repo is not a dump of every prior artifact. It is the place where promoted work becomes readable, validated, public-safe, and ready for the next operator step.

Repo = evidence store. Surface = fast access. Together they reduce confusion.

---

## What It Actually Does

| Lane | Purpose | Current state |
|---|---|---|
| Local cockpit | Open operator surfaces for app, garage, RAG, wallet, boot gates, and reports | present |
| RAG Dollhouse | Keep source-labeled flat memory and receipts | present |
| Release gates | Prevent v1 claims before proof and operator approval | active |
| MCP split | Separate remote docs from local-only health and worker proof | active |
| Agent contact | Tell agents what to inspect first and what to hold | active |
| Orion style | Convert flat docs and CSS into human-readable technical sheets | active style pass |

---

## Evidence / Source Discipline

Source repos remain authoritative until promoted:

```text
C:\tmp\human-flourishing-frameworks-scan
C:\Users\alexp\Documents\gm-agent-orchestrator
```

Remote control plane:

```text
https://github.com/alex-place/lantern-os
```

Core maps:

```text
manifests/foundry-shareholder-repos.md
docs/wiki/ALEX-PLACE.md
docs/ORION-MOOKMANREPORT4-STYLE.md
```

---

## Proven / Held / Local-Only

| State | Meaning |
|---|---|
| Proven in repo | File exists here and can be reviewed through GitHub or local checkout |
| Held local-only | Requires the operator machine: MCP health, dirty worktrees, private folders, local queue/active/failed state, live worker counts |
| Design contract | Describes intended system shape, not live proof |
| Public-safe | Avoids private identity, raw dumps, unsafe fabrication details, and fake live-state claims |

Nothing becomes v1.0.0 merely because it exists elsewhere. Promotion requires the convergence loop in `docs/CONVERGENCE-LOOP.md`.

---

## Initial Surfaces

| Surface | Path |
|---|---|
| Canonical Lantern dashboard | `http://127.0.0.1:4177` |
| Lantern Garage app | `apps/lantern-garage/` |
| Cloud mirror manifest | `manifests/cloud-mirrors.json` |
| Redirected legacy surfaces | `surfaces/shareholder-index/index.html`, `surfaces/tony-garage/index.html`, `surfaces/lantern-desktop/index.html` |
| Agent initial-contact surface | `manifests/LANTERN-OS-AGENT-INITIAL-CONTACT-SURFACES.md` |
| Arc Reactor status | `data/arc-reactor/status.json` |
| Arc Reactor Mining Lab | `docs/ARC-REACTOR-MINING-LAB.md` |
| Flat Lantern RAG Dollhouse | `skills/lantern-rag-dollhouse/references/LANTERN-OS-RAG-DOLLHOUSE.flat.md` |
| Orion / Mookman Report 4 style | `docs/ORION-MOOKMANREPORT4-STYLE.md` |

---

## One Dashboard

Lantern OS uses one dashboard with internal cards and formatted document views.
Do not add a new public dashboard for every product lane. Internal cards/routes
should be backed by real files, validation receipts, or live APIs.

The dashboard should always make chat first-class, keep cloud tunnel/mirror
status visible, and route Markdown through the formatted Lantern reader instead
of dropping operators into raw text docs.

---

## Cloud Mirrors

`master` is the canonical worktree and deploy branch until v1.0.0. Cloud URLs
are mirrors of the same Lantern OS dashboard, not separate products or extra
dashboards.

Mirror policy:

- Local primary: `http://127.0.0.1:4177`
- AWS/service mirrors live in `manifests/cloud-mirrors.json`
- AWS uses `apps/lantern-garage/cloud-server.js` and
  `apps/lantern-garage/Dockerfile`
- Local Windows uses `apps/lantern-garage/server.js`
- A mirror can be listed as `candidate`, `configured`, or `verified`; the UI
  must show that status plainly

Execution boundary: until v1.0.0, executable work must stay in the AWS-safe
deploy/check lane or the Kalshi public-data research lane. See
`docs/EXECUTION-BOUNDARIES.md`.

---

## Brand Guidelines

Lantern OS should feel like a local operator cockpit: calm, evidence-backed,
warm, and usable under pressure.

Brand rules:

- One front door: use `http://127.0.0.1:4177` as the local interaction URL.
- Local first: default to localhost, repo-backed files, and explicit operator
  control before cloud or tunnels.
- Truth first: cards appear only when backed by files, validation receipts, or
  live APIs.
- No fake dashboards: use one dashboard with internal cards/routes.
- No secret collection: never ask for seed phrases, private keys, Apple ID
  credentials, exchange passwords, or hidden signing permissions.
- Plain language: say what is ready, held, blocked, or experimental.
- Visual style: light cockpit surface, deep ink text, Lantern teal `#08756f`,
  steel blue `#1e5f89`, amber warnings `#9f5a07`, and rose risk `#9a3d55`.

---

## Arc Reactor Mining Lab

Mining Lab is a safe, legal, local-first package for inventorying owned
hardware, routing hardware into viable lanes, validating wallets in read-only
mode, and producing receipts.

Mining boundaries:

- CPU routes to Monero learning/P2Pool checks.
- GPU routes stay experimental for RVN or ETC.
- BTC/LTC/DOGE/KAS require owned or separately justified dedicated hardware.
- ETH is wallet/claim/read-only only, not a mining lane.
- No wallet cracking, brute force, hidden signing, or fake one-shot ROI claims.

---

## Release Rule

Before adding new surfaces, run the loop and fix the first 2-4 open issues it finds. Expansion is allowed only after the leading blockers are handled or explicitly marked held by the operator.

Fleet execution uses the 12x3 convergence-ring contract in `manifests/CONVERGENCE-LOOP-AGENT-FLEET.md`: 12 loop steps, 3 agent roles per step, 36 designed ring slots, and a 64-worker elastic pool target. This is a design and receipt contract, not live-worker proof.

MCP work is split by `manifests/MCP-WORK-SPLIT.md`. Remote docs can validate contracts and receipts, but local-only MCP health, dirty worktrees, private folders, and live worker counts still require operator-machine evidence.

---

## Receptionist Routing

Use `docs/LANTERN-OS-RECEPTIONIST-CALL-LIST.md` for public-safe call routing. It uses organization switchboards and public program contacts only. Do not add personal phone numbers, scraped direct dials, or unverified private numbers.

---

## Printable Reports

Quick front page:

```text
artifacts/SUPER-JARVIS-LANTERN-OS-FRONT-PAGE.pdf
```

Master convergence PDF:

```text
artifacts/COMET-LEAP-TOKEN-BURN-REVENUE-CONVERGENCE-v1.pdf
```

Public bounty radar:

```text
artifacts/PUBLIC-PUZZLE-MATH-BOUNTY-RADAR-2026-05-30.pdf
```

---

## Non-Goals For This Repo

- No unattended bootloader edits.
- No partition or disk mutation scripts.
- No unreviewed generated artifact dump.
- No claim that v1.0.0 is ready before the operator says so.
- No skeleton-only milestones.
- No treating offline/local/server-farm Foundry tokens as cloud-metered, "Lite", or per-token rated.
- No raw filepath spam above the first human-relevant explanation.

---

## First Command

Run the convergence loop:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\Invoke-LanternConvergenceLoop.ps1
```

Validate the convergence fleet count contract:

```powershell
python .\scripts\Test-ConvergenceAgentFleet.py --write-json .\manifests\validation\CONVERGENCE-FLEET-LATEST.json
```

---

## Garage Command

Open the Movie 1 operator cockpit:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\Open-TonyGarage.ps1
```

If the browser shows stale styling, reopen through the launcher or refresh with cache bypass. The garage surface cache-busts its CSS, image, and document links.

---

## Local Controls Command

Open the local control bridge and validate dashboard/MCP/Lantern health:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\Start-LanternLocalControls.ps1
```

---

## Full-Stack App Command

Start the in-house Lantern Garage app:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\Start-LanternGarageApp.ps1
```

Then open:

```text
http://127.0.0.1:4177
```
``

