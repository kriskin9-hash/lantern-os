#!/bin/bash
# Issue cleanup for 1.5 sprint (6/20 launch)
# Closes duplicates, irrelevant, and old issues

set -e

echo "🧹 Lantern OS Issue Cleanup — 1.5 Sprint"
echo "========================================"
echo ""

# Close duplicate convergence issues (keep lowest number, close others)
echo "Closing duplicate convergence issues..."

# Phase B duplicates (419-422 are duplicates of 409-412, keep 409-412)
for issue in 419 420 421 422; do
  gh issue close $issue -c "Duplicate of earlier phase issue. See #$((issue - 10))"
done

# Same issues again (423 duplicates 413)
gh issue close 423 -c "Duplicate of #413. Consolidating convergence phases into single tracking."

# Close old redundant phase tracking (406-418 all duplicated)
for issue in 407 408 409; do
  gh issue close $issue -c "Subsumed by convergence-roadmap tracking. See Phase A/B/C issues for current status."
done

# Close obviously broken/stale
echo "Closing clearly stale/broken issues..."

gh issue close 395 -c "Audit request without acceptance criteria. Use convergence-mathematical-foundations skill for review."
gh issue close 389 -c "Feature-runtime-host superseded by neural SDE routing. See convergence-mathematical-foundations for current architecture."

echo ""
echo "📊 Issue status after cleanup:"
gh issue list --state open --limit 1 | wc -l
echo "open issues remaining"
echo ""

# List critical P0 issues
echo "🚨 Critical issues (P0):"
gh issue list --state open --label p0 --limit 20

echo ""
echo "✅ Cleanup complete. Issues reorganized for 1.5 sprint (6/20 launch)."
