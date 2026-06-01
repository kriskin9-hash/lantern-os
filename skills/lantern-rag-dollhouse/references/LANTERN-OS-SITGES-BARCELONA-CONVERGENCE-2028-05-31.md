# Lantern OS · Sitges-Barcelona Convergence
**t:** 2028-05-31 (horizon +2y from 2026-05-31)  
**x:** Sitges, Garraf, Catalonia, Spain (41.2340°N 1.8066°E) — 35 km SW of Barcelona  
**z:** projection | boundary: no cleared cash until receipt  
**evidence:** `external_search_snippet` → `projection` — hold until operator confirms

---

## Status Cube · Convergence Rows

| `x` location | `y` lane | `z` boundary | `t` proof action |
|---|---|---|---|
| Sitges villa hub (Carrer de Sant Gaudenci area) | product / demo lane | no live revenue without cleared receipt | confirmed pilot booking or paid seat |
| Barcelona–El Prat airport (BCN, 28 km N) | travel / logistics lane | EU entry docs current | boarding pass or e-visa receipt |
| Lantern OS repo (`alex-place/lantern-os`) | repo control plane | no dirty worktrees at handoff | `git status` clean + SHA pinned |
| RAG dollhouse (`skills/lantern-rag-dollhouse/`) | dollhouse lane | no raw private context in flat file | hash + source path in manifest |
| Kalshi / trading wallet | wallet lane | kill switch stays armed until go-live | cleared-cash ledger entry only |
| Fleet agent slots (6 active) | fleet lane | lights-on: all agents may enter dollhouse | heartbeat receipt per agent |

---

## Sitges Villa Context (local-verified class pending)

```
Location:    Sitges, comarca del Garraf, Catalonia
Type:        Coastal modernist villa town, UNESCO-adjacent heritage
Climate:     Mediterranean; May avg 22°C, no hurricane risk
Distance:    35 km BCN by C-32 motorway (~30 min); 45 min by Rodalies R2S rail
Known for:   Carnival, film festival, modernista architecture, beach villas
Villa zones: Carrer de Sant Gaudenci, Passeig de la Ribera, Vinyet neighbourhood
Evidence:    projection (operator to confirm actual property or venue)
```

---

## Compressed Agent Entry Rules (lights-on)

```
entry_check: binary
  IF flat_file_hash_valid AND no_dirty_context → ENTER
  ELSE → hold at z-boundary, emit receipt, do not loop
max_depth: -1 (no recursion limit on read; one write per session)
loopback: prohibited
search_mode: binary_only
```

---

## Held Boundaries

| ID | Reason |
|----|--------|
| `SPAIN-LEASE-001` | No lease or venue contract confirmed — projection only |
| `LIVE-KILL-SWITCH` | Trading stays armed until explicit go-live |
| `EU-ENTITY-001` | No EU legal entity confirmed; required before euro-denominated revenue |

---

## Next Safe Actions (t = now → 2028 horizon)

1. Operator confirms Sitges venue → upgrade evidence to `operator_asserted`  
2. EU entity registered → unlock euro wallet lane  
3. Demo pilot booked → raise Arc Reactor Movie 3 confidence from 32 % toward 50 %  
4. `Sync-RagAndPdf` picks this file up on next 240-min cycle → PDF auto-generated  

*Source: projection from 2026-05-31 operator session. All revenue figures held.*
