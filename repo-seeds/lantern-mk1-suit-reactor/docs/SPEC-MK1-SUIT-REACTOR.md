# SPEC - MK1 Suit Reactor

Status: private repo seed inside `alex-place/lantern-os`.
Intended future repo: `alex-place/lantern-mk1-suit-reactor`.

## Converged Product

The MK1 system is a suit-compatible, PPE-aware, passive-exosuit carrier with a slim Lantern reactor core and 12-node Tough Ring optical/status array.

It is designed to fit under or inside a formal/dark suit silhouette: Tony-start aesthetic, not bulky cosplay armor.

## System Stack

1. Base compression/work shirt for comfort and routing.
2. Passive under-jacket yoke harness.
3. Slim chest Lantern Core puck.
4. Belt/back battery/control pack.
5. Green caption glasses / sight assist module.
6. Forearm low-profile bracer.
7. Tough Ring control/identity module.
8. 12-node gem/status ring around reactor.
9. PPE modules where hazards demand certified protection.
10. Lantern OS native status integration.
11. Future BLE/Wi-Fi/Starlink-through-router link.
12. RAG/spec/test matrix for every module.

## Tough Ring

Tough Ring is the durable operator loop around the system. It can mean a wearable finger ring, a chest reactor ring, or both.

### Ring Functions

- NFC/Java Card identity.
- tactile confirm/cancel action.
- haptic feedback source or trigger.
- capacitive touch input.
- emergency/manual event marker.
- Lantern OS pairing token.

### Ring Safety

- no skin-piercing contacts;
- no electrical stimulation;
- no high-current path through finger/chest;
- breakaway if snagged;
- no private secrets in plain NFC text.

## 12 Phased-Array Gems

The reactor face uses 12 low-power optical nodes. They are called gems for aesthetics, but engineering treats them as LED/light-pipe/sensor nodes.

| Node | Name | Function |
|---:|---|---|
| 1 | Proof | real validation pulse |
| 2 | Cash | wallet/invoice state |
| 3 | RAG | indexing/retrieval state |
| 4 | Orch | MCP/orchestrator state |
| 5 | 4D-GMS | game system status |
| 6 | Sight | glasses/caption/OCR state |
| 7 | Body | comfort/contact/haptic state |
| 8 | PPE | protection module state |
| 9 | Power | battery/thermal state |
| 10 | Link | BLE/Wi-Fi/router state |
| 11 | Status Cube | coordinate/dimensional UI mode |
| 12 | Hold | safety block/stop state |

## Laser / Optical Rule

MK1 does not use open high-power lasers. Use LEDs, diffusers, light pipes, low-power ToF/range modules, or Class 1 enclosed optical sensors only. Any laser-like aesthetic must be decorative or enclosed.

## Status Cube Notes

Status Cube does not mean exotic propulsion, time travel, or a physical drive.
In MK1 it means a 4D UI map:

- x: body location;
- y: module lane;
- z: risk/safety depth;
- t: timeline/proof state.

The 12 gems map to a rotating Status Cube dashboard in Lantern OS. The cube is
an interface metaphor for module status, safety depth, and proof history; it is
not a time machine or exotic-physics claim.

## Proposed Exotic Matter - Safe Interpretation

`Exotic matter` is a design metaphor and materials research lane, not a claim of real negative-mass matter or unsafe synthesis.

Safe candidate classes:

- phosphorescent pigment for afterglow;
- photochromic film for light-reactive shell panels;
- thermochromic film for heat warning;
- electroluminescent wire/panel for soft glow;
- silicone/TPU composite for skin-contact shell;
- carbon-fiber-look polymer for aesthetic without conductive hazards;
- retroreflective film for passive visibility;
- magnetic faceplate only if implant constraints allow.

Held classes:

- actual hazardous chemicals;
- radioactive material;
- high-voltage plasma;
- strong magnets near implanted devices;
- high-power lasers;
- batteries embedded directly against skin.

## Lantern OS Native Integration

Data path:

```text
MK1 module record
  -> manifests/MODULE-REGISTRY.yaml
  -> Lantern OS RAG flat file
  -> dashboard/surface state
  -> 12-gem visual + haptic language
```

Runtime path:

```text
Chest Reactor / Tough Ring
  -> BLE phone bridge or ESP32-S3
  -> local Lantern OS endpoint
  -> RAG / wallet / orch / 4D-GMS status
  -> glow and haptic pattern
```

## First Build Halt

Pause before hardware until these are answered:

1. Is Tough Ring a finger ring, chest ring, or both?
2. Which suit jacket/vest dimensions must the puck fit under?
3. Are the 12 gems purely visual LEDs or also sensors?
4. Is blind-assist priority captions, OCR, navigation support, or all three?
5. What hazards require actual PPE: eye impact, falls, work tools, weather, dust, electrical, mobility?
6. What implanted device is expected soon, if any?
7. Budget tier: $100, $250, $500, or prototype-vendor level?
