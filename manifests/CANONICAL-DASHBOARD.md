# Canonical Dashboard

Status: active convergence decision  
Date: 2026-05-31  
Surface: https://lantern-os-cloud.netlify.app/

## Simple Answer

The Netlify Lantern OS cloud dashboard is the canonical operator surface.

Use `dashboard/index.html` as the implementation target and deploy it through Netlify. Do not create or advance competing dashboard implementations unless the operator explicitly reopens them.

## What It Actually Does

- Provides the single operator front door for Dream Journal, convergence, batch jobs, health, repositories, RAG/PDF sync, agent fleet, Arc Reactor, run receipts, and held items.
- Keeps human gate language visible: no auto-execute and held items require operator approval.
- Presents held/blocked items from `manifests/open-issues.md` in one public-safe surface.
- Replaces scattered local/static surfaces as the implementation target.

## Evidence / Source Discipline

- Canonical URL: `https://lantern-os-cloud.netlify.app/`
- Deploy config: `netlify.toml`
- Published directory: `dashboard/`
- Implementation file: `dashboard/index.html`
- Mirror registry: `manifests/cloud-mirrors.json`
- Retired surface registry: `manifests/retired-surfaces.md`

## Proven / Held / Local-Only

| State | Boundary |
|---|---|
| Proven | Netlify dashboard is reachable and operator-approved as the front door. |
| Held | v1.0.0 readiness still requires operator approval. |
| Local-only | `http://127.0.0.1:4177` remains a development fallback, not the primary surface. |
| Retired | `surfaces/`, older dashboard drafts, and app runtime dashboards are archive/evidence unless reopened. |

## Next Safe Action

Consolidate future UI work into `dashboard/index.html` and update `manifests/cloud-mirrors.json` after each verified deploy.

## Validation Path

1. Run `powershell -NoProfile -ExecutionPolicy Bypass -File ./scripts/Invoke-LanternConvergenceLoop.ps1`.
2. Open `https://lantern-os-cloud.netlify.app/`.
3. Confirm the top bar, held-state panel, and no-auto-execute gate are visible.
4. Confirm no other surface is described as the active implementation target.
