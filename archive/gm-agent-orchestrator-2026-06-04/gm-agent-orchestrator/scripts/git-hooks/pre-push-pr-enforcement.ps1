# Pre-push PR enforcement hook (stub)
# Prevents accidental force-pushes to main branches
# For now: allow all pushes (can be tightened later)

param([string]$RefName, [string]$RefHash, [string]$RemoteRefName, [string]$RemoteRefHash)

# Check if pushing to master (should be fast-forward only)
if ($RemoteRefName -match "master|main") {
    # Stub: allow for now
    # TODO: Add enforcement that this is fast-forward only
    exit 0
}

# All other pushes allowed
exit 0
