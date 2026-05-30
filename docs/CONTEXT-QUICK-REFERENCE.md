# Quick Context Reference for Small Context Windows

## 🎯 Immediate Commands for Context Recovery

### Check Current System State
```bash
cat manifests/open-issues.md                    # Current blockers
cat data/wallet/local-cash-wallet.json          # Financial state  
git log --oneline -5                            # Recent work
```

### Find Relevant Files  
```bash
grep -r "search term" relevant/directory/       # Find code
find . -name "*.js" -path "*/payment-bridge/*"  # Find specific files
```

### Get Context Before New Conversation
```bash
cat AGENTS.md                                    # Operating rules
cat manifests/LOCAL-CONTROLS-LATEST.json        # System status
cat data/context/current-task.md                # Current task (if exists)
```

## 🔄 Conversation Reset Template

Copy and paste this when starting a new conversation:

```
NEW CONVERSATION CONTEXT
Task: [specific task]
Repo: [lantern-os / HFF / orchestrator]
Files to reference: [key file paths]
Current state: [where we left off]
Previous context: [brief summary of previous work]
Next action: [immediate next step]
```

## 📋 Task Chunking Examples

### Instead of: "Build payment integration"
```
Step 1: Create payment bridge directory structure
Step 2: Implement Stripe invoice converter
Step 3: Build payment bridge server
Step 4: Configure environment variables
Step 5: Test health endpoint
```

### Instead of: "Set up funding"
```
Step 1: Create Stripe account
Step 2: Configure payment bridge with API keys
Step 3: Apply for AWS Activate credits
Step 4: Set up Kickstarter campaign
Step 5: Launch GitHub Sponsors
```

## 🎯 When to Restart Conversation

**Restart when:**
- Switching repos (lantern-os → HFF → orchestrator)
- Switching topics (payment → deployment → funding)
- After 10-15 exchanges on same topic
- Starting completely new feature
- Context feels lost or repetitive

**Don't restart when:**
- Continuing same sub-task
- Fixing related files in same feature
- Quick validation checks
- Reading reference files

## 📁 Critical Memory Files

### Always Reference These First
- `AGENTS.md` - Operating rules and repo info
- `manifests/open-issues.md` - Current blockers  
- `data/wallet/local-cash-wallet.json` - Financial state
- `manifests/LOCAL-CONTROLS-LATEST.json` - System status

### Create These for Context
- `data/context/current-task.md` - What we're doing now
- `data/context/decisions.md` - Key decisions made
- `data/context/blockers.md` - Current blockers

## ⚡ Efficient Communication Patterns

### Good: Reference Files
❌ "What was the pending invoice amount?"
✅ "Check data/wallet/local-cash-wallet.json for the pending invoice amount"

### Good: State Context  
❌ "Continue with the funding setup"
✅ "Continue funding setup: Stripe is configured, next is AWS Activate application"

### Good: Small Tasks
❌ "Build the complete payment system"
✅ "Create the Stripe invoice converter module"

### Good: Use External Memory
❌ "Remember we decided to use port 3001"
✅ "I saved the port decision to config.json - check the server port setting"

## 🔧 Common Recovery Commands

### If I Don't Remember Something
1. Check git log: `git log --oneline -10`
2. Read relevant manifest files
3. Search for related code: `grep -r "search term"`
4. Check data/context/ files
5. Restart conversation with clear context

### If I Can't Find Files
1. Use find: `find . -name "*.extension"`
2. Use grep with pattern: `grep -r "function name"`
3. Check manifests/ for file inventories
4. Reference specific directory paths
5. Ask me to search specific directories

## 🎯 Lantern OS Specific Workflows

### Payment Integration (Example)
```
CONV 1: Create payment bridge infrastructure
CONV 2: Configure Stripe credentials  
CONV 3: Test payment bridge
CONV 4: Create first invoice
CONV 5: Validate payment flow
```

### Multi-Repo Operations (Example)
```
CONV 1: Work on lantern-os payment setup
CONV 2: Switch to HFF repo for RAG updates
CONV 3: Switch to orchestrator for queue management
CONV 4: Return to lantern-os for integration
```

## 💡 Pro Tips for Small Context

1. **Save immediately**: Record decisions to files as we make them
2. **Commit often**: Use git to preserve progress
3. **Reference files**: Point to files rather than describing contents
4. **Restart early**: Don't let conversations get too long
5. **State clearly**: Always state current task at conversation start
6. **Use templates**: Use consistent conversation reset format
7. **Check git**: Use git log as conversation memory
8. **Read manifests**: Check manifest files for system state
9. **Create context files**: Use data/context/ for task memory
10. **Single focus**: One topic per conversation maximum

## 🚨 Troubleshooting Context Loss

**Symptoms it's time to restart:**
- I ask about information we just discussed
- I can't locate files we were editing  
- I repeat myself or seem confused
- You're explaining the same thing multiple times

**Recovery steps:**
1. Check git log: `git log --oneline -5`
2. Read relevant manifests
3. Check data/context/ files
4. State: "RESTARTING CONVERSATION FOR CLARITY"
5. Provide clear new context with file references

---

**Key principle**: Use the file system and git as external memory. Don't rely on the AI conversation to remember context across exchanges.