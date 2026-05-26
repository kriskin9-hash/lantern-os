# Lantern Core MK II - COMET LEAP Arc Reactor Housing Report

Date: 2026-05-26  
Repo: `alex-place/lantern-os`  
Mode: procurement/RFQ package, safety-gated, external wearable only

## Boundary

ChatGPT cannot order parts, pay suppliers, arrange China assembly, receive goods, assemble hardware, or ship hardware.

This report is the procurement and manufacturing handoff: BOM tiers, safety gates, RFQ language, prototype sequence, and COMET LEAP sprint.

## Product Frame

Lantern Core MK II is a safe external cyborg wearable: a low-voltage chest lantern core with tiny haptic feedback, passive identity, and future BLE/Wi-Fi/Starlink path through a phone or router.

It is not:

- an implant;
- a medical device;
- life support;
- a diagnostic system;
- a tool for high-power stimulation;
- a device to charge while worn.

## COMET LEAP Decision

Build MK0.5 first.

Do not jump straight to mass assembly or body-critical features. The first safe win is a low-voltage external chest puck with:

- diffused lantern glow;
- tiny haptic actuator like a soft DualShock pulse;
- tactile button;
- passive NFC / Java Card identity layer;
- soft skin-contact shell;
- removable protected power;
- no Wi-Fi required for the first comfort proof.

## Research Anchors

- ESP32-S3 is suitable for a later Wi-Fi/BLE version because it supports 2.4 GHz Wi-Fi, Bluetooth 5 LE, GPIOs, touch/PWM style peripherals, security features, and low-power modes.
- DRV2605L-style haptic controllers are suitable for ERM/LRA haptic prototyping.
- Lithium-ion power banks have real recall/fire/burn history, so battery placement and charging rules are a first-class safety gate.
- Any sold Wi-Fi/BLE product needs compliance planning and preferably pre-certified radio modules.
- Java Card / NFC is plausible as a passive/offline identity layer, but private secrets need encryption and careful access control.

## 12 Safe Now Lines

| # | Line | Meaning | Allowed now |
|---:|---|---|---|
| 1 | Soft skin shell | TPU/silicone/foam contact surface | yes |
| 2 | Glow ring | Diffused LED ring or COB LED | yes |
| 3 | Tiny haptic | LRA or small ERM vibration motor | yes |
| 4 | One button | Large tactile input | yes |
| 5 | Passive NFC | NFC tag or Java Card carried in housing | yes |
| 6 | Offline identity | tap-to-read profile/emergency card | yes |
| 7 | USB power | external certified USB power source | yes |
| 8 | Quick release | strap/magnet/snap breakaway | yes |
| 9 | Over-shirt test | comfort test before skin-contact | yes |
| 10 | No charging worn | remove to charge | yes |
| 11 | No medical claims | wellness/accessibility/status only | yes |
| 12 | Manual parent/operator mode | no hidden actions | yes |

## 12 Soon-To-Be Safe Lines

| # | Line | Unlock condition |
|---:|---|---|
| 1 | BLE connection | MK0.5 comfort passes; use phone/local only |
| 2 | Wi-Fi burst mode | firmware limits radio use; no high-power antenna |
| 3 | Lantern OS status feed | local dashboard endpoint exists |
| 4 | Haptic pattern language | tested with wearer comfort limits |
| 5 | Chest contact sensor | detect seating only; no diagnosis |
| 6 | IMU gesture input | no emergency automation without confirmation |
| 7 | Prosthetic strap mount | mechanical comfort tested |
| 8 | Parent/caregiver alert button | manual press only |
| 9 | Starlink via router | connect to Wi-Fi router; no satellite hardware on body |
| 10 | Encrypted NFC identity | do not store sensitive secrets in plain text |
| 11 | Local AI macro relay | no password/payment/account actions |
| 12 | Small vendor assembly | DFM, safety review, and prototype burn-in pass |

## 12 Future Held Lines

| # | Future line | Held until |
|---:|---|---|
| 1 | Medical monitoring mode | clinician/regulatory review |
| 2 | Implant-adjacent use | doctor clearance, especially if pacemaker/monitor appears |
| 3 | Always-on microphone | privacy model, explicit consent |
| 4 | Always-on camera | privacy model, explicit consent |
| 5 | Electrical stimulation | medical/professional review |
| 6 | Charging while worn | formal thermal/safety certification |
| 7 | Autonomous emergency calls | false-positive safety design |
| 8 | High-power radio | compliance and exposure review |
| 9 | Prosthetic control output | fail-safe engineering and clinician/prosthetist review |
| 10 | Public retail sale | FCC/CE/UKCA, battery transport, labeling, QA |
| 11 | Cloud health records | legal/privacy architecture |
| 12 | Mass China assembly | pilot units pass burn, skin, drop, RF, and comfort tests |

## Prototype BOM Tiers

| Module | Prototype part class | Why | Safety note |
|---|---|---|---|
| Brain | none for MK0.5; ESP32-S3 dev board for MK1 | Wi-Fi/BLE later | radio off for first comfort test |
| Haptic | LRA coin actuator + haptic driver | clean taps/pulses | limit duty cycle and intensity |
| Alt haptic | small ERM coin motor | DualShock-like buzz | use soft mount, low duty |
| Light | diffused LED ring or small RGB LED board | lantern glow | current limit; heat check |
| Identity | NFC tag or Java Card/contactless card | offline tap identity | no private secrets in plain text |
| Housing | 3D-printed shell + silicone/foam back | skin comfort | round edges; cleanable surface |
| Mount | elastic harness / chest strap / breakaway clip | wearable stability | quick release |
| Power | certified USB power bank or protected battery module | safe power | do not charge while worn |
| Protection | inline fuse/PTC, switch, strain relief | failure reduction | required before body tests |
| Firmware | simple pulse mode -> BLE/Wi-Fi later | staged complexity | no cloud dependency first |
| Packaging | labeled prototype case + warning card | safe handling | not medical / remove if uncomfortable |

## China Assembly Strategy

Do not send a vague arc reactor idea to a factory. Send a controlled RFQ package:

- CAD/STL files;
- PCB Gerbers if a custom PCB exists;
- BOM and CPL if using PCB assembly;
- firmware boundary;
- material requirements;
- safety requirements;
- test checklist;
- acceptance criteria.

First China order should be 3-10 non-sale engineering samples, not a consumer product batch.

Candidate path:

```text
local maker prototype
-> PCB design
-> 3D printed or silicone prototype
-> DFM review
-> PCB assembly house
-> enclosure vendor
-> final assembly house
-> engineering sample burn-in
```

## Vendor RFQ Message

```text
Hello - I need a small external wearable electronics prototype assembled. It is not an implant and not a medical device. It is a low-voltage chest-worn LED/haptic status puck. First batch: 3-10 engineering samples. Required: smooth rounded enclosure, soft skin-contact backing, LED diffuser, small haptic actuator, protected power input, no charging while worn, and optional ESP32-S3 BLE/Wi-Fi module in the later version. Please quote PCB assembly, enclosure printing/molding options, final assembly, and basic functional test. Provide material certifications and confirm no sharp edges, no exposed wiring, no unprotected Li-ion pouch cell, and no high-temperature surface under normal operation.
```

## Test Plan

| Gate | Test | Pass condition |
|---|---|---|
| Bench electrical | run 30 minutes on table | no heat, no reset, no odor |
| Haptic comfort | 10 patterns at low power | comfortable, not startling/painful |
| Skin/backing | 10 minute contact test | no irritation/pressure mark |
| Strap | bend, sit, breathe, remove | quick release works |
| Heat | measure shell temp after LED/haptic | warm is fail; skin-safe cool only |
| Power | disconnect/strain test | no exposed wire; fuse/protection works |
| NFC | tap with phone | reads intended public info only |
| BLE/Wi-Fi | MK1 only | connects locally; radio can be disabled |
| Starlink path | MK2 only | works through router/phone; no satellite hardware on body |
| Accessibility | wearer can trigger button | usable without fine dexterity |
| Stop rule | remove immediately if discomfort | documented and followed |

## 11-Day COMET LEAP Sprint

| Day | Action | Output |
|---:|---|---|
| 0 | Freeze MK0.5 spec | this report + BOM |
| 1 | Select body location and shell shape | round/lantern gem/flat badge decision |
| 2 | Order maker parts manually | cart + receipt, not automated by AI |
| 3 | Bench LED/haptic wiring | glow + pulse demo |
| 4 | Build soft dummy housing | comfort-only shell |
| 5 | Install electronics into shell | no exposed conductors |
| 6 | Over-shirt wear test | comfort notes |
| 7 | Skin-contact short test | comfort/skin notes |
| 8 | NFC identity card test | phone tap demo |
| 9 | Haptic language test | 12 patterns scored |
| 10 | Photos/video proof | Movie 2 public/private proof |
| 11 | Decide MK1 upgrade | ESP32-S3 + BLE/Wi-Fi plan |

## Key Missing Questions

1. Do you expect an implanted device soon: pacemaker, loop recorder, neurostimulator, insulin pump, cochlear implant, implanted monitor, or other device?
2. Will the reactor sit directly on sternum skin, over shirt, shoulder strap, prosthetic strap, or wheelchair/cane/bag mount?
3. Do you want the first shell to be round Arc Reactor, lantern gem, or flat badge?
4. Do you want buzz/rumble ERM or precise taps LRA as the main sensation?
5. What is the maximum budget for MK0.5 parts: $50, $100, $200, or more?
6. Do you want no-radio MK0.5 first, or ESP32-S3 from the beginning?
7. Should the NFC profile contain only a public message, or an emergency-contact page?
8. What disability/prosthetic need comes first: fatigue cueing, hand-pain macro button, emergency marker, low-vision haptics, mobility mount, or identity/medical info card?

## Done Definition

The next state is complete when:

- MK0.5 parts are selected by a human operator;
- battery and charging rules are written on the device card;
- a soft dummy housing is tested for comfort;
- haptic intensity is tested at low power;
- no radio or vendor assembly is added until comfort proof passes.
