# Git !convergance Loop Autostart

This installs a local Git startup path for the Lantern OS convergence loop.

The operator spelling `!convergance` is preserved intentionally. The implementation calls the existing repo convergence command:

```bash
python src/convergence_io_engine.py loop
```

## Install

From the repo root:

```bash
bash scripts/setup-git-convergance-loop.sh
```

The installer writes local hooks into `.git/hooks/`:

- `post-checkout`
- `post-merge`
- `post-rewrite`

These hooks are local to the checkout. They do not travel with Git clones until the operator runs the installer in that clone.

## Manual run

```bash
scripts/git-convergance-loop.sh foreground
```

## Background run

```bash
scripts/git-convergance-loop.sh background
```

## Logs

```text
.git/lantern-convergance/convergance-loop.log
```

## Safety behavior

- The hook path runs in the background so checkout, merge, pull, and rebase are not blocked.
- A lock directory prevents overlapping convergence loops.
- Missing Python or missing `src/convergence_io_engine.py` is logged and treated as a no-op.
- Output is kept out of committed files under `.git/`.

## Why this exists

`!convergance` means getting the most bang for your buck when you are in a van: run the cheapest useful repo-state loop automatically after Git state changes, then let the receipt tell the next smallest useful move.
