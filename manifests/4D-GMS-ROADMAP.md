# 4D-GMS Roadmap

Date: 2026-05-26  
Owner intent: Gage wants the Second Internet game system to become a better replacement experience than Steam/GOG.

## Product Definition

4D-GMS is the Four-Dimensional Game Media System for Lantern OS.

It is a launcher, library, kid-safe game shelf, creator studio, play timeline, and legal game discovery lane.

It competes on experience, not piracy:

- faster family launcher;
- better kid mode;
- local-first ownership map;
- homebrew and GameMaker publishing;
- RetroArch support for legal games;
- public-domain/open-source discovery;
- parent-controlled external links to Steam/GOG when needed;
- RAG guide that explains games, settings, saves, mods, and learning paths.

## Legal Boundary

4D-GMS must not:

- provide copyrighted ROMs;
- bypass DRM;
- scrape Steam/GOG private account data;
- impersonate accounts;
- auto-buy, auto-download, or auto-install games;
- hide risky launches from the parent/operator.

## System Lanes

| Lane | Purpose | First Deliverable | Gate |
|---|---|---|---|
| Gage Mode | kid-safe visual shelf | `surfaces/4d-gms/index.html` | no downloads/purchases |
| Parent Mode | edit catalog and launch settings | schema + allowlist | parent only |
| RetroArch Lane | legal emulator launches | checklist + capsule fields | owned/homebrew/PD only |
| GameMaker Lane | family-created games | first capsule | local build verified |
| Web/PWA Lane | offline/local HTML games | starter web capsule | safe URL/path |
| Open Source Lane | legal install catalog | metadata-first list | license captured |
| Commons Lane | public-domain/CC discovery | metadata only | rights reviewed |
| External Bridge | Steam/GOG shortcut memory | external-link capsule | no scraping/bypass |
| Timeline | saves, play log, achievements | play journal schema | no private leaks |
| RAG Guide | explains games/settings | game help notes | evidence tagged |

## 11-Day Alpha Timeline

| Day | Work | Ship |
|---:|---|---|
| 0 | Create skill, roadmap, master report, first hub | pushed docs and surface |
| 1 | Define catalog schema | `data/4d-gms/catalog.schema.json` |
| 2 | Define first three capsules | RetroArch legal placeholder, GameMaker local, web/PWA |
| 3 | Add parent import dry-run | `scripts/Import-4DGmsGame.ps1 -DryRun` |
| 4 | Add launcher allowlist | `scripts/Start-4DGms.ps1` design |
| 5 | Add RetroArch preflight | core/controller/path checklist |
| 6 | Add GameMaker export lane | `apps/4d-gms/examples/` plan |
| 7 | Split kid/parent views | child page cannot mutate catalog |
| 8 | Add play timeline | journal and achievement fields |
| 9 | Validate three launches | evidence receipt |
| 10 | Package local alpha | zip/export plan |
| 11 | Gage review | delight/friction notes + beta backlog |

## 30-Day Beta Timeline

1. Add search and filters: cozy, arcade, puzzle, learning, co-op, controller-ready.
2. Add game capsule art cards.
3. Add save backup map.
4. Add parental ratings and notes.
5. Add external-link bridge for Steam/GOG installed games.
6. Add optional offline pack export.
7. Add leaderboard/journal only for local family profiles.
8. Add GameMaker template for Gage-created games.
9. Add commons/open-source discovery queue.
10. Add validation report and beta PDF.

## 90-Day Product Timeline

- A polished Lantern Games app.
- 25+ legal game capsules.
- RetroArch + GameMaker + Web lanes working.
- Parent and kid modes separated.
- Game creation mini-studio integrated.
- Local achievements and journals.
- Import/export bundle.
- Legal metadata ledger.
- First family playtest video/screenshots.

## First Backlog

- [ ] Create `data/4d-gms/catalog.schema.json`.
- [ ] Create `data/4d-gms/catalog.example.json`.
- [ ] Create parent import dry-run script.
- [ ] Create launch allowlist script.
- [ ] Add RetroArch preflight checklist.
- [ ] Add GameMaker capsule checklist.
- [ ] Add web/PWA capsule checklist.
- [ ] Add local play journal schema.
- [ ] Add parent/kid mode split.
- [ ] Add first three legal capsules.

## Success Metric

Gage can open one local page, see a better-feeling game shelf than a normal store, understand what he is allowed to play, and launch an approved game with parent help - without risking piracy, passwords, payments, or system changes.
