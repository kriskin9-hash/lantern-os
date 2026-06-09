# Git Hooks — Version & Changelog Enforcement

This repo uses git hooks to enforce consistent version bumping and changelog entries per pull request.

## Quick Start

Install hooks (one time):
```bash
bash scripts/install-hooks.sh
```

Then git will automatically validate on every commit.

---

## Hook Behaviors

### 1. Pre-commit Hook: Version/Changelog Validation

**When it runs:** Before every commit (after `git commit`, before editor)

**What it checks:**
1. ✅ If code files changed → version must be bumped
2. ✅ If version was bumped → changelog must be updated
3. ✅ Version format must be semantic (major.minor.patch)
4. ✅ Changelog entry must exist for new version
5. ✅ Changelog entry must have required sections (Added/Fixed/Changed)

**Example validation:**
```bash
$ git commit -m "feat: add new api endpoint"

[*] Validating version and changelog...
    Current version: 1.2.3
    Staged version:  1.2.3
    Code changed: true
    Version changed: false

[!] VALIDATION FAILED:
    [ERROR] Code files changed but version not bumped (still 1.2.3)

[!] To fix:
    1. Update package.json version (e.g., to 1.2.4)
    2. Add entry to CHANGELOG.md
    3. Stage both files
    4. Commit again
```

**Skip validation (if needed):**
```bash
SKIP_VERSION_CHECK=1 git commit -m "wip: temporary commit"
```

### 2. Commit-msg Hook: Message Format Validation

**When it runs:** After you write the commit message (validates before committing)

**Required format:**
```
type(scope): subject — description

Optional body...
```

**Valid types:**
- `feat` — New feature
- `fix` — Bug fix
- `docs` — Documentation changes
- `refactor` — Code refactoring (no feature/fix)
- `perf` — Performance improvement
- `test` — Test additions/changes
- `chore` — Maintenance (version bumps, deps, etc)
- `ci` — CI/CD changes
- `build` — Build system changes
- `style` — Code style (formatting, semicolons)
- `revert` — Revert a prior commit

**Valid scopes (optional):**
- `training` — ML training changes
- `versioning` — Version/release changes
- `api` — REST API changes
- `ui` — Frontend/UI changes
- `router` — Intent routing/classification
- `db` — Database/persistence
- etc. (any logical grouping)

**Examples:**
```
feat(training): add Bayesian learning rate scheduling — adapts LR based on validation plateau

fix(router): handle null intent classification when message is empty

docs: update knowledge center with internal RAG house link

chore: bump version to 1.2.4

refactor(api): extract query parsing to utility function
```

**Constraints:**
- Subject min 8 characters, max 100 per line
- Type required
- Scope optional

### 3. Prepare-commit-msg Hook: Template (Optional)

**When it runs:** When you create a new commit (shows template in editor)

**What it does:**
- Displays a commit message template with types/scopes/examples
- Can be edited or deleted if you don't want it
- Only shows for new commits (not amends, merges, etc)

---

## Changelog Format (Required for Version Bumps)

When you bump the version, **the changelog MUST be updated** with the exact format:

```markdown
## [1.2.4] - 2026-06-08

### Added
- New feature description
- Another new feature

### Fixed
- Bug fix description
- Another bug fix

### Changed
- API change or breaking change
- Behavior change

## [1.2.3] - 2026-06-07

...previous version...
```

**Rules:**
- Version header: `## [x.y.z] - YYYY-MM-DD`
- Date format: `YYYY-MM-DD` (ISO 8601)
- At least one of: Added, Fixed, Changed
- Each section must have items (bullet points with `-`)
- Empty sections will fail validation

**Example CHANGELOG.md:**
```markdown
# Changelog

All notable changes to Lantern OS are documented here.

## [1.2.4] - 2026-06-08

### Added
- Internal RAG House link in knowledge center
- Bayesian learning rate scheduling in training harness
- Pre-commit hook for version/changelog validation

### Fixed
- Knowledge center display on mobile devices

### Changed
- Training now requires changelog entry per version bump

## [1.2.3] - 2026-06-07

### Added
- Phase 1 training convergence system
- PCSF receipt logging for model training
- HFF Bayesian status cube integration

...
```

---

## Typical Workflow

### Scenario 1: Feature + Version Bump

```bash
# 1. Make code changes
echo "new code" >> src/feature.js

# 2. Bump version in package.json
# Before: "version": "1.2.3"
# After:  "version": "1.2.4"

# 3. Update CHANGELOG.md
cat >> CHANGELOG.md << 'EOF'

## [1.2.4] - 2026-06-08

### Added
- New awesome feature

### Fixed
- Bug that was annoying
EOF

# 4. Stage all changes
git add src/feature.js package.json CHANGELOG.md

# 5. Commit (hooks validate automatically)
git commit -m "feat: add new awesome feature"

# Hooks check:
#   ✓ Code changed: true
#   ✓ Version bumped: 1.2.3 → 1.2.4
#   ✓ Changelog has [1.2.4] entry
#   ✓ Changelog entry has sections
#   ✓ Commit message format valid
# → Commit succeeds!
```

### Scenario 2: Code Changes Without Version Bump (FAILS)

```bash
# 1. Make code changes
echo "fix: handle edge case" >> src/router.js

# 2. Forget to bump version (still 1.2.3)

# 3. Stage and commit
git add src/router.js
git commit -m "fix(router): handle edge case"

# Hook validation:
#   ✗ Code changed: true
#   ✗ Version changed: false
#   → ERROR: Code files changed but version not bumped
# → Commit BLOCKED!

# To fix:
# 1. Update package.json: "version": "1.2.4"
# 2. Update CHANGELOG.md with [1.2.4] entry
# 3. Stage both: git add package.json CHANGELOG.md
# 4. Commit again
```

### Scenario 3: Version Bump Without Changelog (FAILS)

```bash
# 1. Bump version in package.json only
# Before: "version": "1.2.3"
# After:  "version": "1.2.4"

# 2. Commit (forget changelog)
git add package.json
git commit -m "chore: bump version to 1.2.4"

# Hook validation:
#   ✓ Code changed: false (only package.json)
#   ✓ Version bumped: 1.2.3 → 1.2.4
#   ✗ Changelog missing [1.2.4] entry
#   → ERROR: Version not found in changelog
# → Commit BLOCKED!

# To fix:
# 1. Add CHANGELOG.md entry with [1.2.4]
# 2. Stage it: git add CHANGELOG.md
# 3. Amend the commit: git commit --amend
```

---

## Manual Validation

Run the validator outside of git hooks:

```bash
# Check version/changelog consistency
python3 scripts/validate-version-changelog.py

# Output:
#   [*] Validating version and changelog...
#       Current version: 1.2.3
#       Staged version:  1.2.4
#       Code changed: true
#       Version changed: true
#       [✓] Version format valid: 1.2.4
#       [✓] Changelog version found: 1.2.4
#       [✓] Changelog entry valid
#   
#   [OK] All validations passed
```

---

## Bypass Hooks (Emergency Only)

If you absolutely must skip validation:

```bash
# Skip version/changelog validation
SKIP_VERSION_CHECK=1 git commit -m "emergency: temp fix for prod issue"

# Skip commit message validation
git commit --no-verify -m "wip: work in progress"

# Both
SKIP_VERSION_CHECK=1 git commit --no-verify -m "quick patch"
```

⚠️ **Note:** Use bypasses sparingly. They exist for emergencies, not daily use.

---

## Troubleshooting

### "python3: command not found"
Solution: Ensure Python 3 is installed and in PATH:
```bash
python --version  # or python3 --version
```

### "File exists" error on hook installation
Solution: Hooks may already exist. Back up and remove:
```bash
mv .git/hooks/pre-commit .git/hooks/pre-commit.bak
bash scripts/install-hooks.sh
```

### "Changelog entry invalid: requires sections"
Solution: Ensure changelog has Added/Fixed/Changed:
```markdown
## [1.2.4] - 2026-06-08

### Added
- Your feature here

### Fixed
- Your bug fix here
```

### "Invalid version format"
Solution: Use semantic versioning only:
```
✓ 1.2.3
✓ 1.2.3-rc1  (pre-release)
✓ 1.2.3+build123  (build metadata)
✗ 1.2  (missing patch)
✗ v1.2.3  (don't include "v" prefix)
✗ 1.2.3.4  (too many parts)
```

---

## PR Review Checklist

When reviewing a PR, check:
- [ ] Version was bumped if code changed
- [ ] Changelog entry exists for new version
- [ ] Changelog entry has proper format (date, sections, items)
- [ ] Commit messages follow type(scope): subject format
- [ ] No commits with `--no-verify` flag (unless emergency)

---

## Files

- `scripts/validate-version-changelog.py` — Main validation logic
- `scripts/hooks/pre-commit-version-changelog` — Pre-commit hook
- `scripts/hooks/commit-msg-format` — Commit-msg hook
- `scripts/install-hooks.sh` — Hook installer
- `docs/HOOKS.md` — This documentation

---

## References

- [Git Hooks Documentation](https://git-scm.com/book/en/v2/Customizing-Git-Git-Hooks)
- [Semantic Versioning](https://semver.org/)
- [Conventional Commits](https://www.conventionalcommits.org/)

