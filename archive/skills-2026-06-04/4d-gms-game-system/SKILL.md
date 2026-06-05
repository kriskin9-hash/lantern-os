---
name: 4d-gms-game-system
description: 4D-GMS skill for building a Lantern-native game system and kid-safe launcher/library that can compete with the feel of Steam/GOG without copying stores, bypassing DRM, or distributing copyrighted games. Use when the operator asks for Gage's game system, Second Internet games, RetroArch integration, game capsules, local-first game library, family-safe store/launcher, GameMaker publishing, or legal public-domain/homebrew game catalogs.
---

# 4D-GMS Game System

Use this skill from `C:\tmp\lantern-os` when building Gage's Lantern-native game system.

## North Star

Build the family-first game system that feels better than a normal store because it combines:

1. a safe launcher;
2. a legal game library;
3. a creator studio;
4. a memory/RAG guide;
5. local saves and capsules;
6. parent controls;
7. RetroArch support for legal games;
8. GameMaker/homebrew publishing;
9. public-domain/open-source discovery;
10. Second Internet social/play surfaces.

This is a replacement experience for Steam/GOG in the Lantern world, not a tool for piracy, DRM bypass, account theft, or unauthorized redistribution.

## 4D Meaning

4D-GMS = Four-Dimensional Game Media System.

| Dimension | Meaning | Product Feature |
|---|---|---|
| 1. Library | what games exist | legal catalog, capsules, tags |
| 2. Launcher | how games run | RetroArch, GameMaker, web/PWA, local EXE entries |
| 3. Timeline | how play evolves | saves, versions, achievements, journals |
| 4. World | how games connect | quests, art, music, maps, family co-op, RAG guide |

## Hard Boundaries

- No copyrighted ROM sourcing instructions.
- No DRM bypass.
- No Steam/GOG account scraping.
- No credential storage in child-facing surfaces.
- No purchases or downloads from kid mode without parent approval.
- No malware-like launchers, injectors, trainers, or cheats.
- No system changes from the child page.
- RetroArch is a launcher target only for homebrew, public-domain, open-source, or personally-owned legal files.

## Core Artifacts

```text
surfaces/4d-gms/index.html
manifests/4D-GMS-ROADMAP.md
reports/4D-GMS-GAME-SYSTEM-MASTER-PLAN-2026-05-26.md
skills/4d-gms-game-system/SKILL.md
```

Future runtime artifacts:

```text
data/4d-gms/catalog.json
data/4d-gms/library.local.json
assets/4d-gms/capsules/
scripts/Start-4DGms.ps1
scripts/Import-4DGmsGame.ps1
scripts/Test-4DGmsCatalog.ps1
```

## Launcher Lanes

1. **RetroArch lane** - parent-approved legal ROM/homebrew path, core mapping, controller checks.
2. **GameMaker lane** - local `.exe` or project export, game capsules, child-created games.
3. **Web/PWA lane** - safe browser games, local HTML games, offline learning games.
4. **Open-source lane** - verified licenses, source URLs, build/install notes.
5. **Public-domain/Creative Commons lane** - Archive/Commons metadata-first intake.
6. **Steam/GOG bridge lane** - optional external launch links only; no scraping or bypass.

## Capsule Record

Every game becomes a capsule before it appears in Gage Mode:

```yaml
id: game-short-slug
title: Game Title
lane: retroarch|gamemaker|web|opensource|public-domain|external-link
source: local|family-created|official-site|archive-metadata|steam-link|gog-link
license_state: owned|homebrew|open-source|public-domain|creative-commons|external-account-required|unknown
kid_mode: yes|no|parent-only
launch_command: held until verified
asset_path: held until verified
save_path: held until verified
controller: keyboard|xinput|retro-controller|touch|unknown
rating_notes: none|needs-parent-review
validation_state: not_started|metadata_only|launch_tested|play_tested|held
```

## Build Loop

Use Clean Storm discipline:

```text
Status -> Fetch -> Scan -> Sort -> Strike -> Trim -> Tighten -> Validate -> Record -> Ship
```

For 4D-GMS, the first 2-4 concrete issues are always:

1. create a safe visible surface;
2. create the roadmap and capsule schema;
3. create one legal test capsule;
4. validate no auto-launch, no downloads, no DRM bypass.

## First 11 Days

| Day | Objective | Output |
|---:|---|---|
| 0 | Create skill, report, and hub | docs/surface pushed |
| 1 | Create catalog schema | `data/4d-gms/catalog.json` draft |
| 2 | Add parent import script | `Import-4DGmsGame.ps1` dry-run |
| 3 | Add launcher script | `Start-4DGms.ps1` with allowlist |
| 4 | Add RetroArch lane notes | core/controller/preflight checklist |
| 5 | Add GameMaker lane notes | first family-created capsule |
| 6 | Add legal discovery lane | public-domain/OSS metadata only |
| 7 | Build Gage Mode polish | kid view + parent view split |
| 8 | Add save/journal timeline | play log and achievement journal |
| 9 | Test three games | one RetroArch legal, one GameMaker, one web |
| 10 | Package first release zip | local-only alpha |
| 11 | Review with Gage | record delight/friction and next sprint |

## Done Definition For Alpha

Alpha is ready when:

- the hub opens locally;
- catalog validation passes;
- at least three legal capsules exist;
- every launcher path is allowlisted;
- parent mode can edit catalog;
- kid mode cannot add downloads or purchases;
- RetroArch path is documented but not bundled with copyrighted content;
- Gage can pick and launch an approved game with help nearby.
