# Contributing to Lantern OS

## Backlog system

Linear is the canonical backlog. GitHub Issues are intake only — they may be triaged into Linear or closed as duplicates. Do not treat a GitHub issue as confirmed work unless it has a corresponding Linear ticket.

## Dev setup

Requirements: Node.js v20 or higher.

```bash
git clone <repo-url> lantern-os
cd lantern-os
node apps/lantern-garage/server.js
# server runs at http://127.0.0.1:4177
```

No global npm installs are required for the server. If you need Playwright for end-to-end tests:

```bash
npm install --prefix apps/lantern-garage
```

## Testing

Run the Node.js validation suite from the `apps/lantern-garage` directory:

```bash
npm run validate --prefix apps/lantern-garage
```

Run Python tests from the repo root:

```bash
python -m pytest tests/ -v --ignore=tests/node_modules
```

Both suites must pass before opening a PR.

## Branch convention

- Branch off `dev` for all work.
- Open PRs targeting `dev`.
- `dev` is merged into `master` for releases only.
- Branch naming: `dev/<short-description>` (e.g., `dev/docs-readme-contributing`).

## Repo contract

The following belong in this repository:

- `apps/` — application code
- `skills/` — operator skills
- `tests/` — automated tests
- `scripts/` — active utility scripts
- `src/` — source modules
- `data/` — local runtime data (gitignored where it contains personal entries)
- `manifests/` — system manifests
- `docs/` — documentation
- `.github/` — CI/CD workflows and config
- Root config files: `package.json`, `railway.json`, `pytest.ini`, `requirements.txt`, `Makefile`
- `README.md`, `CONTRIBUTING.md`, `ARCHITECTURE.md`, `PRIVACY_AND_OFFLINE.md`

Everything else (stale deployment guides, one-off migration docs, duplicate orchestration scripts, generated PDFs that are not canonical artifacts) should be removed via a dedicated deletion PR. When in doubt, open a Linear ticket before deleting.

## Secrets and privacy

- Never commit secrets, tokens, API keys, seed phrases, or personal identifiable information.
- `data/dream_journal/` entries are private; the directory is gitignored by default.
- Payment and wallet data (`data/wallet/`) must not contain real card numbers or Stripe secrets.

## Code style

- Node.js: vanilla JS, no framework required for the server layer.
- Python: standard library preferred; add dependencies to `requirements.txt` with a comment explaining why.
- No generated or minified files in source commits.
