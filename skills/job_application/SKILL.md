---
name: job_application
status: live
version: 1.0.0
module: skills/job_application/job_application.py
depends_on:
  - web_search (tool-runner.js)
  - web_fetch (tool-runner.js)
  - create_document (tool-runner.js)
  - workspace_write (tool-runner.js)
---

# Job Application Assistant Skill

**Status: live** — all dependent tools are implemented and wired.

## What it does

A workflow Skill (ADR-0008: Skills chain Tools) that helps the operator
apply for a job end-to-end:

1. **Find + read the posting** — `web_search(job title + company)` to
   locate the URL; `web_fetch(url)` to extract the full posting text.
2. **Analyze requirements** — extract key skills, qualifications, and
   tone from the posting.
3. **Tailor documents** — `create_document("resume", fields)` and
   `create_document("cover_letter", fields)` with posting-specific
   customisation written to `~/.keystone/workspace/applications/<slug>/`.
4. **Human confirmation gate** — the skill returns a summary and the
   workspace paths; it does NOT submit anything. Submission requires
   explicit operator action.

## Acceptance criteria

- [x] End-to-end run produces a tailored resume + cover letter in workspace
- [x] No autonomous submission (human must confirm and act)
- [x] Results include workspace paths for review
- [x] Posting URL is cited as evidence per Σ₀ External Reality Rule

## Trigger phrases (dream-chat routing)

- "help me apply for [role] at [company]"
- "write a cover letter for [job]"
- "tailor my resume for [posting URL]"
- "job application assistant"

## Out of scope

- Submitting the application (intentional — human-in-the-loop)
- Storing the operator's base resume (use workspace_write directly)
- ATS scraping or form-filling (follow-up issue)
