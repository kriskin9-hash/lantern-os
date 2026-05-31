# Small Context Window Optimization for SWE-1.6 Slow on Windsurf

Generated: 2026-05-29
Target: Lantern OS development with limited context AI models

## Current Situation

**Model**: SWE-1.6 Slow on Windsurf
**Constraint**: Small context window
**Impact**: Limited ability to maintain long conversations and remember extensive context

## Core Optimization Strategies

### 1. Chunk Large Tasks into Small Steps

**Instead of**: "Build the complete payment integration system"

**Do**: 
```
Step 1: Set up payment bridge directory structure
Step 2: Create Stripe invoice converter module
Step 3: Implement payment bridge server
Step 4: Configure environment variables
Step 5: Test payment bridge health endpoint
```

### 2. Use External Memory Systems

**Key Files to Reference**:
- `AGENTS.md` - Operating rules and repository information
- `manifests/` - Current system state and validation
- `data/wallet/` - Current wallet state and ledger
- Open specific files rather than describing them

### 3. Restart Conversations for New Topics

**When to restart**:
- Switching from payment to deployment topics
- Moving from funding to development work
- Starting a completely new feature
- After ~10-15 exchanges on same topic

**How to restart**:
- "Starting new conversation: [topic]"
- Reference key file paths for context
- State current state clearly

### 4. Use File References Instead of Descriptions

**Inefficient**: "The file in data/wallet/local-cash-wallet.json shows a pending invoice of $199..."

**Efficient**: "Check the current wallet state in data/wallet/local-cash-wallet.json and the pending invoice amount"

### 5. Create Task Lists Early

**At conversation start**:
```
Current task: Configure Stripe payment integration
Sub-tasks:
1. Create config.json with Stripe keys
2. Test payment bridge health endpoint  
3. Create first test invoice
4. Validate webhook handling
```

## Lantern OS Specific Optimizations

### Memory System for Development

**Key Reference Files**:
- `AGENTS.md` - Operating rules, source repos, promotion criteria
- `manifests/open-issues.md` - Current blockers and held issues
- `manifests/LOCAL-CONTROLS-LATEST.json` - System validation status
- `data/wallet/local-cash-wallet.json` - Current financial state

**Quick Context Recovery**:
- Always read AGENTS.md before major decisions
- Check manifests/ for current system state
- Reference specific files rather than asking me to remember

### Development Workflow Optimization

**For Complex Features**:
```
1. Design phase: Create spec in manifests/ (new conversation)
2. Implementation: Build core feature (new conversation)
3. Testing: Validate and fix (new conversation)
4. Documentation: Update AGENTS.md (new conversation)
```

**For Bug Fixes**:
```
1. Identify issue: Check open-issues.md (current conversation)
2. Locate code: Use grep to find file (current conversation)
3. Implement fix: Edit specific file (current conversation)
4. Validate: Run convergence loop (new conversation)
```

### Repository Management

**Multi-Repo Work**:
- Work on one repo at a time
- Restart conversation when switching repos
- Reference specific repo paths explicitly
- Use convergence loop for repo-state checks

## Communication Patterns for Small Context

### Effective Question Patterns

**Good**:
- "Read data/wallet/local-cash-wallet.json and tell me the pending invoice amount"
- "Check AGENTS.md line 20-25 for the promotion criteria"
- "Search for 'payment' in the wallet directory and show results"

**Inefficient**:
- "What was the pending invoice amount we discussed earlier?"
- "What are the promotion criteria for artifacts?"
- "Where did we put the payment code?"

### State Management

**Always state current state**:
- "Current task: Configuring Stripe integration"
- "Just completed: Payment bridge server created"
- "Next step: Add Stripe credentials to config"

**Use file system as memory**:
- Create state files in data/ directory
- Update manifests/ with current status
- Use ledger.jsonl for operation history

## Workflow Templates for Common Tasks

### New Feature Development
```
1. NEW CONVERSATION: Design spec
   - Create manifest: manifests/FEATURE-NAME.md
   - Define requirements and success criteria
   
2. NEW CONVERSATION: Implementation  
   - Reference FEATURE-NAME.md
   - Build core functionality
   - Save key decisions to FEATURE-NAME.md
   
3. NEW CONVERSATION: Testing
   - Reference implementation files
   - Run validation tests
   - Update FEATURE-NAME.md with results
   
4. NEW CONVERSATION: Documentation
   - Update AGENTS.md if needed
   - Move FEATURE-NAME.md to validation/ if approved
```

### Bug Fix Workflow
```
1. Check manifests/open-issues.md
2. Use grep to locate related code
3. Read specific file for context
4. Implement fix in single operation
5. Run convergence loop to validate
6. Update open-issues.md
```

### Multi-Repo Operations
```
1. Start with lantern-os repo (current conversation)
2. Switch to HFF repo (new conversation)
3. Switch to orchestrator repo (new conversation)
4. Return to lantern-os (new conversation)
```

## External Memory Aids

### File-Based Context
**Create reference files**:
- `data/context/current-task.md` - Current task and next steps
- `data/context/decisions.md` - Key decisions made
- `data/context/blockers.md` - Current blockers

### Git as Memory
**Use commits for context**:
- Make frequent, focused commits
- Use descriptive commit messages
- Reference commit hashes in new conversations
- Use git log to recall recent work

### Documentation as Memory
**Update documentation immediately**:
- Record decisions in relevant manifests
- Update AGENTS.md with rule changes
- Create new manifest files for new workstreams
- Use RAG system for knowledge retention

## Specific Commands for Context Recovery

### Quick Context Commands
```bash
# Current system state
cat manifests/open-issues.md

# Recent work
git log --oneline -10

# Find relevant files
grep -r "payment" data/wallet/

# Wallet state  
cat data/wallet/local-cash-wallet.json

# Convergence status
powershell -File scripts/Invoke-LanternConvergenceLoop.ps1
```

### Conversation Reset Template
```
NEW CONTEXT RESET
Task: [specific task]
Files to reference: [key file paths]
Current state: [where we left off]
Next action: [immediate next step]
```

## Error Handling with Small Context

### When Context is Lost
**Symptoms**:
- I don't remember previous decisions
- I ask about information we discussed
- I can't locate files we were working with

**Recovery Strategy**:
1. Check recent git commits for context
2. Read relevant manifest files
3. Check data/context/ files if created
4. State current task explicitly
5. Reference specific files for needed information

### Prevention Strategies
- Save key decisions to files immediately
- Create task lists in external files
- Use git commits frequently
- Update manifests with current status
- Restart conversations before context gets too large

## Lantern OS Specific Memory Aids

### Critical Reference Files
```
AGENTS.md                              # Operating rules and repo info
manifests/open-issues.md                # Current blockers
manifests/LOCAL-CONTROLS-LATEST.json   # System validation
data/wallet/local-cash-wallet.json     # Financial state
data/wallet/ledger.jsonl                # Operation history
manifests/CONVERGENCE-FLEET-LATEST.json # Agent fleet status
```

### Workflow Memory Aids
```
data/context/current-task.md            # What we're working on now
data/context/next-steps.md             # Planned next actions
data/context/recent-decisions.md       # Key decisions made
data/context/dependencies.md            # Dependencies and blockers
```

## Conversation Length Guidelines

### Optimal Length
- 5-10 exchanges per conversation
- Single focused topic per conversation
- Restart when topic changes significantly
- Restart after complex operations complete

### Signs It's Time to Restart
- I ask about information we discussed earlier
- Conversation feels "stuck" or repetitive
- You need to remind me of context multiple times
- We're working on a new major sub-task

### Restart Protocol
```
CONVERSATION RESTART
Previous topic: [what we were working on]
Completion status: [done/partial/not started]
Current topic: [new focused task]
Key files: [file paths for new task]
```

## Summary: Small Context Workflow

### Before Starting Work
1. Read AGENTS.md for operating context
2. Check manifests/open-issues.md for current blockers
3. Reference relevant manifest for current task
4. State current task clearly at conversation start

### During Work
1. Keep exchanges focused on single topic
2. Reference specific files rather than describing
3. Save decisions to files immediately
4. Make git commits for significant progress

### When Switching Context
1. Save current state to data/context/ files
2. Commit current work with clear message
3. Start new conversation for new topic
4. Reference key files for new context

### When Context is Lost
1. Check git log for recent work
2. Read relevant manifest files
3. Use grep to find related code
4. Restart conversation with clear context

This approach will make SWE-1.6 Slow on Windsurf much more effective for Lantern OS development despite the small context window constraint.