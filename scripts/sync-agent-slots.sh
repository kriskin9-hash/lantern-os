#!/bin/bash
# Sync-Agent-Slots.sh
# Bash version of agent slot sync job
# Purpose: Keep all agent slots in sync with master
# Schedule: Run every 5 minutes via cron

REPO_PATH="/d/tmp/lantern-os"
LOG_DIR="$REPO_PATH/logs"
LOG_FILE="$LOG_DIR/agent-sync-$(date +%Y-%m-%d).log"
DRY_RUN="${DRY_RUN:-false}"

# Ensure log directory exists
mkdir -p "$LOG_DIR"

log() {
    local timestamp=$(date "+%H:%M:%S")
    local level=$1
    shift
    local message="$@"
    echo "[$timestamp] [$level] $message" | tee -a "$LOG_FILE"
}

log "INFO" "=========================================="
log "INFO" "Agent Slot Sync Started"
log "INFO" "Repo: $REPO_PATH"
log "INFO" "Dry Run: $DRY_RUN"
log "INFO" "=========================================="

cd "$REPO_PATH" || exit 1

# Step 1: Fetch from origin
log "INFO" ""
log "INFO" "STEP 1: Fetching from origin..."
git fetch origin 2>&1 | grep -E "From|master|branch" | head -5
log "OK" "✓ Fetch complete"

# Step 2: Sync each agent slot
log "INFO" ""
log "INFO" "STEP 2: Syncing agent slots..."

for slot_config in "claude:Claude" "codex:Codex" "gemini:Gemini" "devin:Devin"; do
    IFS=: read provider name <<< "$slot_config"
    branch="${provider}/orchestrator/slot-1"

    log "INFO" ""
    log "INFO" "Syncing: $name [$branch]"

    # Checkout branch
    if [ "$DRY_RUN" = "false" ]; then
        git checkout "$branch" 2>&1 | grep -E "Switched|Already" || true
    else
        log "INFO" "(DRY RUN) Would checkout $branch"
    fi

    # Rebase with master
    if [ "$DRY_RUN" = "false" ]; then
        git rebase origin/master 2>&1 | tail -3

        if [ $? -ne 0 ]; then
            log "WARN" "⚠ Rebase conflict detected"
            git rebase --abort 2>&1 | grep -E "Aborted|failed" || true
            log "ERROR" "CONFLICT: Manual intervention required for $branch"
            continue
        fi

        log "OK" "✓ Rebased successfully"

        # Push to origin
        git push origin "$branch" --force-with-lease 2>&1 | grep -E "To https|rejected" || log "OK" "✓ Pushed $branch"
    else
        log "INFO" "(DRY RUN) Would rebase $branch with origin/master"
    fi
done

# Step 3: Update worktrees
log "INFO" ""
log "INFO" "STEP 3: Updating worktrees..."

for slot_config in "claude:Claude:claude-slot-1" "codex:Codex:codex-slot-1" "gemini:Gemini:gemini-slot-1" "devin:Devin:devin-slot-1"; do
    IFS=: read provider name slot_dir <<< "$slot_config"
    worktree_path="$HOME/.windsurf/worktrees/$slot_dir"

    if [ -d "$worktree_path/.git" ]; then
        log "INFO" "Updating worktree: $name"
        if [ "$DRY_RUN" = "false" ]; then
            cd "$worktree_path"
            git pull origin 2>&1 | grep -E "Already|Fast-forward|Merge" || log "OK" "✓ Pulled"
            cd "$REPO_PATH"
        else
            log "INFO" "(DRY RUN) Would update worktree: $worktree_path"
        fi
    else
        log "WARN" "Worktree not found: $worktree_path"
    fi
done

# Step 4: Return to master
log "INFO" ""
log "INFO" "STEP 4: Returning to master..."
if [ "$DRY_RUN" = "false" ]; then
    git checkout master 2>&1 | grep -E "Switched|Already" || true
    log "OK" "✓ Checked out master"
else
    log "INFO" "(DRY RUN) Would checkout master"
fi

# Summary
log "INFO" ""
log "OK" "✓ All agent slots synced successfully"
log "INFO" "=========================================="
log "INFO" "Agent Slot Sync Completed"
log "INFO" "=========================================="
log "INFO" ""
