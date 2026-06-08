#!/bin/bash
# Install git hooks for version/changelog validation and commit message formatting
# Usage: bash scripts/install-hooks.sh

set -e

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# Handle both regular repos and git worktrees
if [ -d "$REPO_ROOT/.git" ]; then
    GIT_HOOKS_DIR="$REPO_ROOT/.git/hooks"
else
    # Worktree: .git is a file pointing to real location
    GIT_DIR=$(git rev-parse --git-dir)
    GIT_HOOKS_DIR="$GIT_DIR/hooks"
fi

echo "[*] Installing git hooks..."
echo "    Repo: $REPO_ROOT"
echo "    Git dir: $(git rev-parse --git-dir)"
echo "    Hooks dir: $GIT_HOOKS_DIR"

# Ensure hooks directory exists
mkdir -p "$GIT_HOOKS_DIR"

# Install pre-commit hook (version/changelog validation)
echo "[*] Installing pre-commit hook (version/changelog validation)..."
cp "$REPO_ROOT/scripts/hooks/pre-commit-version-changelog" "$GIT_HOOKS_DIR/pre-commit"
chmod +x "$GIT_HOOKS_DIR/pre-commit"
echo "    [OK] pre-commit hook installed"

# Install commit-msg hook (message format validation)
echo "[*] Installing commit-msg hook (message format)..."
cp "$REPO_ROOT/scripts/hooks/commit-msg-format" "$GIT_HOOKS_DIR/commit-msg"
chmod +x "$GIT_HOOKS_DIR/commit-msg"
echo "    [OK] commit-msg hook installed"

# Install prepare-commit-msg hook (optional template)
echo "[*] Creating prepare-commit-msg hook template..."
cat > "$GIT_HOOKS_DIR/prepare-commit-msg" << 'HOOK_SCRIPT'
#!/bin/bash
# Prepare-commit-msg hook: Add template to commit editor
# (Optional - removes template if user doesn't want it)

COMMIT_MSG_FILE="$1"
COMMIT_SOURCE="$2"

# Only show template for new commits (not amends, merges, etc)
if [ "$COMMIT_SOURCE" != "message" ] && [ "$COMMIT_SOURCE" != "squash" ]; then
    # Read current message
    CURRENT_MSG=$(cat "$COMMIT_MSG_FILE")

    # Only show template if message is empty or auto-generated
    if [ -z "$CURRENT_MSG" ] || echo "$CURRENT_MSG" | grep -q "^#"; then
        cat >> "$COMMIT_MSG_FILE" << 'TEMPLATE'

# Type(scope): subject — description
#
# Types: feat, fix, docs, refactor, perf, test, chore, ci
# Scopes: (optional) training, versioning, api, ui, router, etc.
#
# Examples:
#   feat(training): add Bayesian LR scheduling — auto-adapts learning rate based on plateau
#   fix(router): handle null intent classification
#   chore: bump version to v1.2.3
#   docs: update knowledge center with RAG house link
#
# Version/Changelog rules:
# - If code changed: version MUST be bumped
# - If version bumped: changelog MUST be updated
# - Changelog format: ## [x.y.z] - YYYY-MM-DD with Added/Fixed/Changed sections
TEMPLATE
    fi
fi

exit 0
HOOK_SCRIPT
chmod +x "$GIT_HOOKS_DIR/prepare-commit-msg"
echo "    [OK] prepare-commit-msg hook installed"

echo ""
echo "[OK] All hooks installed successfully"
echo ""
echo "[*] Hook behaviors:"
echo "    1. pre-commit:"
echo "       - Validates version bump matches code changes"
echo "       - Ensures changelog updated with new version"
echo "       - Validates changelog entry structure"
echo "       - Skip with: SKIP_VERSION_CHECK=1 git commit"
echo ""
echo "    2. commit-msg:"
echo "       - Enforces structured commit messages"
echo "       - Type(scope): subject format required"
echo "       - Min 8 chars subject, max 100 chars per line"
echo ""
echo "    3. prepare-commit-msg (optional):"
echo "       - Shows commit message template in editor"
echo "       - Can be edited or deleted if unwanted"
echo ""
echo "[*] To manually run validation:"
echo "    python3 scripts/validate-version-changelog.py"
echo ""
