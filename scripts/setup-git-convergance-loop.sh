#!/usr/bin/env bash
set -eu

# Install local git hooks that start the Lantern OS git !convergance loop.
# This writes into .git/hooks and is intentionally local-only; hooks are not
# distributed by Git unless each operator opts in by running this setup script.

ROOT_DIR="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
cd "$ROOT_DIR"

RUNNER="scripts/git-convergance-loop.sh"

if [ ! -f "$RUNNER" ]; then
  echo "Missing $RUNNER" >&2
  exit 1
fi

chmod +x "$RUNNER"
mkdir -p .git/hooks

write_hook() {
  hook_name="$1"
  hook_path=".git/hooks/$hook_name"
  marker="Lantern OS git !convergance loop"

  if [ -f "$hook_path" ] && grep -q "$marker" "$hook_path"; then
    echo "Already installed: $hook_path"
    return 0
  fi

  if [ -f "$hook_path" ]; then
    cp "$hook_path" "$hook_path.before-lantern-convergance"
  fi

  cat > "$hook_path" <<'HOOK'
#!/usr/bin/env bash
# Lantern OS git !convergance loop
ROOT_DIR="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
cd "$ROOT_DIR" || exit 0
if [ -x "scripts/git-convergance-loop.sh" ]; then
  "scripts/git-convergance-loop.sh" hook
fi
exit 0
HOOK

  chmod +x "$hook_path"
  echo "Installed: $hook_path"
}

write_hook post-checkout
write_hook post-merge
write_hook post-rewrite

cat <<'EOF'

Installed git !convergance startup hooks.

Triggers:
- post-checkout: after branch/file checkout
- post-merge: after pull/merge
- post-rewrite: after rebase/amend

Logs:
.git/lantern-convergance/convergance-loop.log

Manual run:
scripts/git-convergance-loop.sh foreground
EOF
