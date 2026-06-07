#!/usr/bin/env bash
set -u

# Lantern OS git !convergance loop runner.
# The misspelling is intentional: Alex's operator command is !convergance.
# This script is safe for git hooks and startup jobs: it uses a lock, logs output,
# and defaults to background execution.

ROOT_DIR="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
cd "$ROOT_DIR" || exit 1

LOG_DIR="${LANTERN_CONVERGANCE_LOG_DIR:-$ROOT_DIR/.git/lantern-convergance}"
LOG_FILE="$LOG_DIR/convergance-loop.log"
LOCK_DIR="$LOG_DIR/.lock"
MODE="${1:-background}"

mkdir -p "$LOG_DIR"

timestamp() {
  date -u '+%Y-%m-%dT%H:%M:%SZ'
}

run_loop() {
  if ! mkdir "$LOCK_DIR" 2>/dev/null; then
    printf '[%s] convergance loop already running; skip\n' "$(timestamp)" >> "$LOG_FILE"
    return 0
  fi

  trap 'rmdir "$LOCK_DIR" 2>/dev/null || true' EXIT

  printf '\n[%s] starting git !convergance loop in %s\n' "$(timestamp)" "$ROOT_DIR" >> "$LOG_FILE"

  if [ ! -f "src/convergence_io_engine.py" ]; then
    printf '[%s] missing src/convergence_io_engine.py; nothing to run\n' "$(timestamp)" >> "$LOG_FILE"
    return 0
  fi

  if command -v python3 >/dev/null 2>&1; then
    PYTHON_BIN="python3"
  elif command -v python >/dev/null 2>&1; then
    PYTHON_BIN="python"
  else
    printf '[%s] python not found; cannot run convergence loop\n' "$(timestamp)" >> "$LOG_FILE"
    return 0
  fi

  "$PYTHON_BIN" src/convergence_io_engine.py loop >> "$LOG_FILE" 2>&1
  status=$?
  printf '[%s] finished git !convergance loop with status %s\n' "$(timestamp)" "$status" >> "$LOG_FILE"
  return "$status"
}

case "$MODE" in
  foreground|--foreground)
    run_loop
    ;;
  background|--background|'')
    (run_loop) >/dev/null 2>&1 &
    ;;
  hook)
    # Git hooks should never block normal git usage.
    (run_loop) >/dev/null 2>&1 &
    ;;
  *)
    echo "Usage: $0 [background|foreground|hook]" >&2
    exit 2
    ;;
esac
