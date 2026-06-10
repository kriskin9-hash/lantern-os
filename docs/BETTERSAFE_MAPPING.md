# BetterSafe / World Cube — Architecture Mapping

**Status**: Design contract. Not all components exist yet.

**Date**: 2026-06-10

---

## Honest inventory

| Component | Exists? | Where | Notes |
|-----------|---------|-------|-------|
| HFF `Measurement` | **Yes** | `integrations/human-flourishing-frameworks/sensors.py` | Dataclass with uncertainty, provenance, scope, temporal bounds, confounders, missing coverage |
| HFF `Intervention` | **Yes** | `integrations/human-flourishing-frameworks/world_model.py:183` | Action + predicted_effect + uncertainty + side_effects |
| HFF `Prediction` | **Yes** | `integrations/human-flourishing-frameworks/world_model.py:242` | Always includes caveats |
| HFF Bayesian world model | **Yes** | `world_model.py` | Beliefs, corrections, flourishing scores |
| HFF mesh sync | **Yes** | `mesh_network.py` | HTTP POST between peers; opt-in via `ENABLE_MESH_SYNC` |
| HFF Ed25519 signing | **Yes** | `cryptographic_proof.py` | Key generation, signing, verification |
| HFF PBFT consensus | **Teaching** | `byzantine_consensus.py` | Happy path only |
| HFF node classes | **Partial** | `adoption_tracker.py` | `verified` flag exists; no `claim_node` or `security_node` formal class |
| Lantern StatusCube | **Yes** | `src/convergence_io/status_cube.py` | 4D axes, artifacts, beliefs, futures, tesseract report |
| Lantern convergence loop | **Yes** | `src/convergence_io_engine.py` | 20 phases |
| Lantern provider chain | **Yes** | `apps/lantern-garage/lib/stream-chat.js` | Gemini → Claude → OpenAI → Grok → Ollama |
| Lantern Three Doors game | **Yes** | `skills/three-doors-game/SKILL.md` | Symbolic door UI, continuity, CSF export |
| Lantern dream journal | **Yes** | `apps/lantern-garage/routes/dream.js` | CRUD, stats, export |
| **BetterSafe Engine** | **No** | Design only | Would wrap HFF + StatusCube + Consent Gate |
| **Claim Packet** | **No** | `docs/CLAIM_PACKET_SCHEMA.v1.json` | This schema defines it; no code yet |
| **Consent Gate** | **No** | Design only | Middleware concept; no implementation |
| **World Cube** | **No** | Design only | Community aggregation layer; no implementation |
| **Claim lifecycle state machine** | **No** | Design only | `draft → approved → submitted → ...` |
| **Recommendation lifecycle** | **No** | Design only | `candidate → local_test → helpful_signal → ...` |
| **BetterSafe "fun" layer** | **No** | Design only | Quests, badges, door choices as interventions |

---

## Mapping: existing pieces → BetterSafe / World Cube

### BetterSafe = HFF world model + StatusCube + Consent Gate wrapper

```
BetterSafe.observe()
  -> HFF Sensor.observe() + StatusCube.place(artifact)

BetterSafe.updateBeliefs()
  -> HFF WorldModel.update() + StatusCube.update_beliefs()

BetterSafe.rankNudges()
  -> HFF WorldModel.counterfactual() + StatusCube.project()

BetterSafe.runAllowed()
  -> HFF CapabilityControl check + local automation permissions

BetterSafe.verifyAndCorrect()
  -> HFF correction_log + StatusCube boundary transitions
```

### World Cube = mesh sync + signed claim packets + community pattern discovery

```
World Cube ingest
  -> mesh_network.py sync + cryptographic_proof.py verify
  -> but filtered: only objects matching claim-packet.v1 schema
  -> and only where review.consent_gate_status === "approved"

World Cube aggregate
  -> HFF WorldModel belief aggregation across multiple nodes
  -> but scoped to anonymized claim packets, not raw private data

World Cube recommend
  -> HFF Prediction + Intervention generation
  -> sent back to nodes as advisory only
  -> nodes decide locally whether to act
```

---

## Claim packet: the shared contract

The claim packet is the **only** object that crosses from private node → shared World Cube.

Rules:

1. Raw private data never leaves the node.
2. Only claim packets with `review.consent_gate_status === "approved"` may exit.
3. Every exported claim must be signed (`signature.signature` must be non-null).
4. `privacy.raw_private_data_included` must be `false`.
5. `measurement.uncertainty` must be in `[0, 1]`.
6. `claim.safe_wording` must use conservative phrasing (association, not causation).
7. `risk.risk_class === "blocked"` prevents all downstream use.

See `docs/CLAIM_PACKET_SCHEMA.v1.json` for the full schema.

---

## Consent Gate: validation rules

```javascript
function canExportClaim(packet) {
  return (
    packet.schema === "lantern.claim_packet.v1" &&
    packet.privacy.raw_private_data_included === false &&
    packet.privacy.allowed_use !== "unrestricted" &&
    packet.measurement.uncertainty >= 0 &&
    packet.measurement.uncertainty <= 1 &&
    packet.claim.safe_wording &&
    packet.claim.safe_wording.length >= 10 &&
    packet.evidence.evidence_class &&
    packet.evidence.certainty &&
    packet.review.consent_gate_status === "approved" &&
    packet.review.reviewer !== "auto" &&
    packet.origin.operator_approved === true &&
    packet.signature.signature &&
    packet.signature.signature.length > 0 &&
    packet.risk.risk_class !== "blocked" &&
    packet.risk.sensitive === false
  );
}
```

**Note**: `sensitive === true` does not block export if operator explicitly approves, but it triggers additional review and restricts `allowed_use` to `research_review` only.

---

## Roadmap layers

These are **real design contracts**, not vaporware. They map cleanly to existing code. But they need to be built.

### Phase 1: Claim packet (this PR)

- Schema file (done)
- Example packets in `data/claim-packets/examples/`
- Validation tests in `tests/test_claim_packet_schema.js`

### Phase 2: Consent Gate middleware

- `apps/lantern-garage/lib/consent-gate.js`
- POST `/api/claims/draft` — create packet, status = draft
- POST `/api/claims/approve-export` — operator review, status = approved, sign
- GET `/api/claims/pending` — list drafts awaiting review
- Mesh write blocked unless packet passes `canExportClaim()`

### Phase 3: World Cube endpoint

- `POST /api/world/claims` — ingest approved claim packets
- `GET /api/world/patterns` — aggregate patterns
- `GET /api/world/recommendations` — advisory recommendations

### Phase 4: BetterSafe runtime

- Wrap HFF + StatusCube + Consent Gate into branded runtime
- Add fun layer (quests, badges, door-linked interventions)

---

## Product sentences

**Current (real):**

> Lantern OS proxies a Human Flourishing Framework integration with Bayesian world models, sensor measurements, Ed25519 signing, mesh sync, and a 4D StatusCube for convergence state.

**Future (roadmap):**

> BetterSafe is the product wrapper for HFF + StatusCube + Consent Gate. World Cube is the shared aggregation layer for signed, consented claim packets.

**Corrected magic sentence:**

> The magic is that many local observer slices can safely combine into a shared map of what helps life flourish — without ever exposing raw private lives.

---

## One-line definition

**Lantern OS 1.0 is a distributed operating system for flourishing: private local cubes improve each node's world, while optional consented claim packets build a shared World Cube that helps the community learn what works — without ever commanding a node or ranking a person.**
