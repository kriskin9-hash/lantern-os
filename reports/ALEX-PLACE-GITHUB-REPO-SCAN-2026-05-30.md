# Alex-Place GitHub Organization Repository Scan

**Date:** 2026-05-30  
**Scan Scope:** alex-place GitHub organization including Human Flourishing Frameworks (HFF)  
**Status:** Comprehensive repository inventory and classification

---

## Executive Summary

Total repositories identified: **43** (from official inventory)  
Local HFF variants observed: **5** (recovery/evidence snapshots)  
Primary control plane: `alex-place/lantern-os`  
Primary framework source: `human-flourishing-frameworks/human-flourishing-frameworks`

---

## Repository Classification Overview

| Category | Count | Description |
|---|---:|---|
| Core Control | 1 | Lantern OS control plane |
| Execution Dependencies | 3 | MCP, agents, orchestrators, GameMaker tooling |
| RAG Dependencies | 2 | COMET LEAP framework, symbolic sandbox |
| Business Services | 15 | Apps, services, payment, monitoring |
| Game Projects | 10 | GameMaker, libGDX, game assets |
| Library/Vendor | 3 | API clients, large forks |
| Site Content | 3 | Public sites, content repos |
| Placeholder | 3 | Empty/control points |
| Retired References | 3 | Recovery/evidence only |

---

## Core Control Plane

### alex-place/lantern-os
- **Visibility:** Private
- **Branch:** master
- **Size:** 5,330 KB
- **Indexed:** Yes
- **Class:** `core_control`
- **Status:** Project/control plane
- **Local Path:** `C:\tmp\lantern-os`
- **Description:** Local-first AI control plane for Windows with ASI Arc Reactor MK1 integration, human trial demo readiness gates, and Windsurf hooks for safety validation.

---

## Execution Dependencies

### gm-agent-orchestrator
- **Visibility:** Private
- **Branch:** master
- **Size:** 6,126 KB
- **Indexed:** Yes
- **Class:** `execution_dependency`
- **Status:** Authoritative agent/MCP source
- **Local Path:** `C:\Users\alexp\Documents\gm-agent-orchestrator`
- **Description:** Agent orchestration and MCP connector source.

### gamemaker-room-editor
- **Visibility:** Private
- **Branch:** main
- **Size:** 377 KB
- **Indexed:** Yes
- **Class:** `execution_dependency`
- **Status:** GameMaker tooling adapter, cloud-access enabled for users
- **Description:** GameMaker room editor tooling.

### lantern-symbolic-sandbox
- **Visibility:** Private
- **Branch:** master
- **Size:** 16,243 KB
- **Indexed:** Yes
- **Class:** `rag_dependency`
- **Status:** Symbolic/RAG/quarantine dependency
- **Local Path:** `C:\Users\alexp\Documents\lantern-symbolic-sandbox`
- **Description:** Symbolic sandbox for RAG and quarantine testing.

---

## RAG Dependencies

### human-flourishing-frameworks/human-flourishing-frameworks
- **Visibility:** Private
- **Branch:** master
- **Size:** 8,721 KB
- **Indexed:** Yes
- **Class:** `rag_dependency`
- **Status:** COMET LEAP/framework source
- **Local Path:** `C:\tmp\human-flourishing-frameworks-scan`
- **Description:** COMET LEAP framework and Human Flourishing Frameworks source.

---

## Business Services

### moneybags
- **Visibility:** Public
- **Branch:** master
- **Size:** 61,228 KB
- **Indexed:** Yes
- **Class:** `business_service_dependency`
- **Status:** Wallet/store inspiration; inspect first
- **Description:** Wallet and store functionality reference.

### KeepSafe
- **Visibility:** Public
- **Branch:** master
- **Size:** 9,900 KB
- **Indexed:** No
- **Class:** `business_service_dependency`
- **Status:** Held until runtime/env known
- **Description:** Desktop utility application.

### LoL-Chat
- **Visibility:** Public
- **Branch:** master
- **Size:** 4,507 KB
- **Indexed:** No
- **Class:** `business_service_dependency`
- **Status:** API-currentness review first
- **Description:** League of Legends chat API client.

### Cloudbot
- **Visibility:** Public
- **Branch:** master
- **Size:** 2,564 KB
- **Indexed:** No
- **Class:** `business_service_dependency`
- **Status:** Bot token/env review first
- **Description:** Cloud bot application.

### clouddataissexy
- **Visibility:** Public
- **Branch:** master
- **Size:** 4,133 KB
- **Indexed:** No
- **Class:** `business_service_dependency`
- **Status:** App/env review first
- **Description:** Cloud data application.

### corporate_crawler
- **Visibility:** Public
- **Branch:** master
- **Size:** 776 KB
- **Indexed:** No
- **Class:** `business_service_dependency`
- **Status:** Held for endpoint/rights review
- **Description:** Corporate web crawler.

### OpenTray
- **Visibility:** Public
- **Branch:** master
- **Size:** 180 KB
- **Indexed:** No
- **Class:** `business_service_dependency`
- **Status:** Desktop utility reference
- **Description:** Desktop tray utility.

### badslothserver
- **Visibility:** Private
- **Branch:** master
- **Size:** 10 KB
- **Indexed:** Yes
- **Class:** `business_service_dependency`
- **Status:** Secrets/env held
- **Description:** BadSloth server application.

### server-debugclient
- **Visibility:** Public
- **Branch:** master
- **Size:** 6 KB
- **Indexed:** Yes
- **Class:** `business_service_dependency`
- **Status:** Debug-only fallback
- **Description:** Server debug client.

### slothapi
- **Visibility:** Public
- **Branch:** master
- **Size:** 17 KB
- **Indexed:** Yes
- **Class:** `business_service_dependency`
- **Status:** API/env review first
- **Description:** Sloth API server.

### intspeedcheck
- **Visibility:** Private
- **Branch:** main
- **Size:** 4 KB
- **Indexed:** Yes
- **Class:** `business_service_dependency`
- **Status:** Utility reference; inspect first
- **Description:** Internet speed check utility.

### statusmonitor
- **Visibility:** Private
- **Branch:** main
- **Size:** 11 KB
- **Indexed:** Yes
- **Class:** `business_service_dependency`
- **Status:** Monitoring fallback candidate
- **Description:** Status monitoring application.

### smartmealplanning
- **Visibility:** Private
- **Branch:** main
- **Size:** 10 KB
- **Indexed:** Yes
- **Class:** `business_service_dependency`
- **Status:** Family/productivity candidate
- **Description:** Smart meal planning application.

### SmartBid
- **Visibility:** Private
- **Branch:** master
- **Size:** 63 KB
- **Indexed:** Yes
- **Class:** `business_service_dependency`
- **Status:** SMB cleanup candidate
- **Description:** Smart bidding application.

### place_co
- **Visibility:** Private
- **Branch:** main
- **Size:** 143 KB
- **Indexed:** Yes
- **Class:** `site_content_dependency`
- **Status:** Company/public surface candidate
- **Description:** Company website.

---

## Game Projects

### Returners
- **Visibility:** Public
- **Branch:** master
- **Size:** 146,656 KB
- **Indexed:** No
- **Class:** `game_dependency`
- **Status:** Preserve/source-summary only
- **Description:** Game project.

### Quest
- **Visibility:** Public
- **Branch:** master
- **Size:** 38,944 KB
- **Indexed:** No
- **Class:** `game_dependency`
- **Status:** Preserve/source-summary only
- **Description:** Game project.

### GDXJam
- **Visibility:** Public
- **Branch:** master
- **Size:** 92,090 KB
- **Indexed:** No
- **Class:** `game_dependency`
- **Status:** Preserve/source-summary only
- **Description:** GameMaker jam game.

### GdxJam2
- **Visibility:** Public
- **Branch:** master
- **Size:** 18,156 KB
- **Indexed:** No
- **Class:** `game_dependency`
- **Status:** Preserve/source-summary only
- **Description:** GameMaker jam game sequel.

### Porkopolis
- **Visibility:** Public
- **Branch:** master
- **Size:** 30,504 KB
- **Indexed:** No
- **Class:** `game_dependency`
- **Status:** Preserve/source-summary only
- **Description:** Game project.

### MysticGarden
- **Visibility:** Public
- **Branch:** master
- **Size:** 16,672 KB
- **Indexed:** No
- **Class:** `game_dependency`
- **Status:** Preserve/source-summary only
- **Description:** Game project.

### ChildOfLevistus
- **Visibility:** Private
- **Branch:** master
- **Size:** 183,750 KB
- **Indexed:** Yes
- **Class:** `game_dependency`
- **Status:** GameMaker/game lane candidate, cloud-access enabled for users
- **Description:** GameMaker game project.

### BadSloth
- **Visibility:** Public
- **Branch:** master
- **Size:** 300 KB
- **Indexed:** Yes
- **Class:** `game_dependency`
- **Status:** Client source-summary
- **Description:** BadSloth game client.

### Mr.Nom
- **Visibility:** Public
- **Branch:** master
- **Size:** 680 KB
- **Indexed:** No
- **Class:** `game_dependency`
- **Status:** Preserve/source-summary only
- **Description:** Game project.

### GDungeon
- **Visibility:** Public
- **Branch:** master
- **Size:** 1,508 KB
- **Indexed:** No
- **Class:** `game_dependency`
- **Status:** Preserve/source-summary only
- **Description:** Game project.

### Dungeon
- **Visibility:** Public
- **Branch:** master
- **Size:** 781 KB
- **Indexed:** No
- **Class:** `game_dependency`
- **Status:** Preserve/source-summary only
- **Description:** Game project.

### Orion
- **Visibility:** Public
- **Branch:** master
- **Size:** 1,264 KB
- **Indexed:** No
- **Class:** `game_dependency`
- **Status:** Preserve/source-summary only
- **Description:** Game project.

---

## Library/Vendor Dependencies

### libgdx
- **Visibility:** Public
- **Branch:** master
- **Size:** 835,619 KB
- **Indexed:** No
- **Class:** `library_vendor_dependency`
- **Status:** Vendor-sized; do not absorb
- **Description:** libGDX game framework fork.

### riot-api-java
- **Visibility:** Public
- **Branch:** master
- **Size:** 3,894 KB
- **Indexed:** No
- **Class:** `library_vendor_dependency`
- **Status:** API-currentness review first
- **Description:** Riot Games API Java client.

### The_Josephus_Problem
- **Visibility:** Public
- **Branch:** master
- **Size:** 212 KB
- **Indexed:** No
- **Class:** `library_vendor_dependency`
- **Status:** Sample/reference only
- **Description:** Josephus problem implementation.

### jriot
- **Visibility:** Public
- **Branch:** master
- **Size:** 324 KB
- **Indexed:** No
- **Class:** `library_vendor_dependency`
- **Status:** External/API client reference
- **Description:** Riot API Java client.

---

## Site Content Dependencies

### alex-place.github.io
- **Visibility:** Public
- **Branch:** master
- **Size:** 44 KB
- **Indexed:** No
- **Class:** `site_content_dependency`
- **Status:** Public-site reference
- **Description:** Personal GitHub Pages site.

### TheGiddyLimit.github.io
- **Visibility:** Public
- **Branch:** master
- **Size:** 1,456,094 KB
- **Indexed:** No
- **Class:** `site_content_dependency`
- **Status:** Metadata-first; rights gate
- **Description:** Large GitHub Pages site.

### dnd_homebrew
- **Visibility:** Public
- **Branch:** master
- **Size:** 33 KB
- **Indexed:** No
- **Class:** `site_content_dependency`
- **Status:** Rights/content review first
- **Description:** D&D homebrew content.

---

## Placeholder Dependencies

### VisionPark
- **Visibility:** Public
- **Branch:** master
- **Size:** 0 KB
- **Indexed:** No
- **Class:** `placeholder_dependency`
- **Status:** Held
- **Description:** Empty control point.

### alex-place..github.io
- **Visibility:** Public
- **Branch:** master
- **Size:** 2 KB
- **Indexed:** No
- **Class:** `placeholder_dependency`
- **Status:** Held
- **Description:** GitHub profile config.

### tradiest
- **Visibility:** Public
- **Branch:** master
- **Size:** 2 KB
- **Indexed:** No
- **Class:** `placeholder_dependency`
- **Status:** Held
- **Description:** Empty control point.

### human-flourishing-frameworks/.github
- **Visibility:** Public
- **Branch:** main
- **Size:** 0 KB
- **Indexed:** No
- **Class:** `placeholder_dependency`
- **Status:** Org profile/config only
- **Description:** HFF organization config.

---

## Local HFF Recovery/Evidence Snapshots

### hff-lantern-recovery
- **Local Path:** `C:\tmp\hff-lantern-recovery`
- **Items:** 392
- **Status:** Recovery evidence only
- **Class:** `retired_reference`
- **Description:** Lantern OS recovery evidence snapshot.

### hff-evidence-master-clean
- **Local Path:** `C:\tmp\hff-evidence-master-clean`
- **Items:** 3
- **Status:** Evidence only
- **Class:** `retired_reference`
- **Description:** Evidence master clean snapshot.

### hff-master-clean
- **Local Path:** `C:\tmp\hff-master-clean`
- **Items:** 225
- **Status:** Evidence only
- **Class:** `retired_reference`
- **Description:** Master clean evidence snapshot.

### hff-release-candidate
- **Local Path:** `C:\tmp\hff-release-candidate`
- **Items:** 35
- **Status:** Evidence only
- **Class:** `retired_reference`
- **Description:** Release candidate evidence snapshot.

### hff-seven-validate
- **Local Path:** `C:\tmp\hff-seven-validate`
- **Items:** 256
- **Status:** Retired comparison only
- **Class:** `retired_reference`
- **Description:** Seven validation comparison snapshot.

---

## HFF Public Site

### hff-public-site
- **Local Path:** `C:\tmp\hff-public-site`
- **Items:** 4
- **Status:** Public hub
- **Description:** Human Flourishing Frameworks public site with dashboards and GitHub repository links.

---

## Dependency Promotion Path

All dependencies must follow this path:

```text
registered -> read_only_inspected -> dependency_profiled -> adapter_or_manifested -> promoted_or_held
```

No dependency can skip:
- Local status
- Remote status
- Branch verification
- Build/test validation
- Secrets/env review
- Artifact verification
- Fallback path review

---

## Promotion Boundary Requirements

A dependency may be promoted into Lantern OS only if it has:

1. Source path and remote URL
2. Clean or explicitly recorded dirty state
3. Build/test/run command or reason none exists
4. Secrets/environment variable review
5. License/rights/asset review
6. Rollback/fallback path
7. Validation receipt
8. Operator approval when required

---

## Current Promotion Status

### Promoted to Lantern OS
- None (Lantern OS is the control plane, dependencies are referenced)

### Held for Review
- Most business services (secrets/env review required)
- Site content (rights/content review required)
- Library/vendor forks (delta analysis required)

### Retired References
- All HFF recovery/evidence snapshots
- Local backup directories

---

## Next Actions

1. **Secrets/Env Review**: Complete secrets and environment variable review for business service dependencies
2. **Rights/Content Review**: Complete rights and content review for site content dependencies
3. **Delta Analysis**: Analyze library/vendor forks to determine if delta is required
4. **Validation Receipts**: Generate validation receipts for promoted dependencies
5. **Fallback Paths**: Document rollback/fallback paths for all active dependencies
6. **HFF Consolidation**: Consolidate HFF recovery/evidence snapshots into single archive

---

## Summary Statistics

| Metric | Count |
|---|---:|
| Total GitHub Repositories | 43 |
| Public Repositories | 31 |
| Private Repositories | 12 |
| Master Branch | 36 |
| Main Branch | 7 |
| Connector Indexed | 16 |
| Connector Not Indexed | 27 |
| Local HFF Snapshots | 5 |
| Core Control Plane | 1 |
| Active Dependencies | 40 |
| Retired References | 8 |

---

**Report Generated:** 2026-05-30  
**Scanner:** Cascade (Lantern OS Agent)  
**Source:** manifests/ALL-REPOS-INVENTORY.md + local workspace scan
