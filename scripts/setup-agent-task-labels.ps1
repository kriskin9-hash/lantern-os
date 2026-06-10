# One-shot setup for the issue-queue task system (docs/AGENT-SWARM-OPERATIONS.md)
# Requires: gh CLI authenticated against alex-place/lantern-os
# Usage: powershell -ExecutionPolicy Bypass -File scripts/setup-agent-task-labels.ps1

$repo = "alex-place/lantern-os"

# Stream + system labels
gh label create "convergence-io" --repo $repo --color "1D76DB" --description "Convergence IO stream task queue" --force
gh label create "dream-journal"  --repo $repo --color "8250DF" --description "Dream Journal stream task queue (incl. Three Doors / Kingdome of Hearts)" --force
gh label create "agent-task"     --repo $repo --color "0E8A16" --description "Workable by an agent lane; pulled top-of-queue by priority" --force
gh label create "needs-founder"  --repo $repo --color "D93F0B" --description "Human gate: security, providers, lore canon, data/, pricing" --force
gh label create "p0" --repo $repo --color "B60205" --description "Pull first" --force
gh label create "p1" --repo $repo --color "FBCA04" --description "Pull second" --force
gh label create "p2" --repo $repo --color "C2E0C6" --description "Backlog" --force

# Route the existing Three Doors / Kingdome implementation queue into the Dream Journal stream
$dreamJournalIssues = 292, 296, 298, 299, 300, 301
foreach ($n in $dreamJournalIssues) {
  gh issue edit $n --repo $repo --add-label "dream-journal","agent-task","p1"
}

# Kingdome of Hearts garden hub + poem are the active lore push: promote to p0
gh issue edit 298 --repo $repo --remove-label "p1" --add-label "p0"
gh issue edit 299 --repo $repo --remove-label "p1" --add-label "p0"

Write-Host "Done. Agents now pull labeled issues top-of-queue. Unlabeled issues are invisible to agents."
