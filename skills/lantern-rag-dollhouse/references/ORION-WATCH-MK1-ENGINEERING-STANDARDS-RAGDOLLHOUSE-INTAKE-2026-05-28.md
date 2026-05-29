# Lantern OS RAG Dollhouse Intake
## Orion Watch MK1 — Engineering Standards and Codes Boundary

**Date:** 2026-05-28  
**Scope:** watch-only, Orion Watch MK1  
**Status:** public-safe engineering standards intake  
**Decision:** hold as requirements knowledge; do not treat as a buildable blueprint

## MK1 convergence

Lantern OS Orion Watch MK1 should stay an existing-watch-platform prototype:

- existing round smartwatch donor platform
- Orion / Lantern OS watchface
- phone-side or local companion layer
- push-to-talk as the default audio gate
- haptic confirmation
- wellness-only sensor language
- custom strap / box / presentation
- no custom PCB for MK1
- no custom RF design for MK1
- no medical claims
- no payment NFC claim
- no water-resistance claim beyond supplier-proven certification

## Standards and codes map

| Area | Standard / code family | MK1 rule |
|---|---|---|
| Electrical product safety | IEC / UL 62368-1 style AV/ICT equipment safety | Use certified donor hardware; do not custom-design electronics for MK1. |
| Radio / Bluetooth / NFC | FCC Part 15 / equipment authorization, Bluetooth SIG qualification | Use donor watch with existing FCC/CE/Bluetooth documentation. Do not alter antenna/RF layout. |
| Battery safety | IEC 62133-style portable lithium safety, UN 38.3 transport expectations | Use factory-certified battery/charger only. No custom Li-ion pack in MK1. |
| Shipping batteries | UN 38.3 / carrier lithium battery rules | Ask supplier for battery shipping paperwork before samples ship. |
| Water/dust resistance | IEC 60529 IP Code, ISO 22810 watch water resistance | Claim only what the supplier can document. Prefer “not water-certified prototype” for MK1. |
| Skin contact | ISO 10993-style biocompatibility thinking; consumer material declarations | Require nickel-safe, skin-contact-safe strap/case materials. Avoid unknown coatings. |
| General wellness | FDA general wellness / low-risk wearable boundary | Steps, heart rate, sleep, reminders are wellness only. No diagnosis, treatment, emergency, blood pressure, ECG, or medical-grade language. |
| Cyber/privacy | baseline IoT privacy/security practice | PTT default, clear mute state, no always-listening claim, no hidden recording. |
| Functional safety | IEC 61508-style fail-safe thinking, used as design discipline not certification target | If uncertain, fail closed: no audio route, no upload, no health conclusion, no false “protected” state. |
| Quality process | design controls, supplier documentation, incoming inspection | Keep versioned requirements, supplier docs, test receipts, and sample validation logs. |

## MK1 engineering requirements

### Must have

- donor platform already supports mic, speaker, BLE, haptic motor, battery charging, and sensors
- supplier can provide compliance documents or at least model identifiers for certification lookup
- watchface or dial customization path exists
- battery and charger are factory-integrated
- no antenna modification
- no custom PCB
- no custom battery
- no waterproof claim unless documented

### Should have

- custom boot logo
- custom watchface package
- black round case near 46 mm
- magnetic charger
- replacement strap path
- supplier MOQ quote at 2 / 10 / 50 / 100 units

### Must not claim in MK1

- medical device
- diagnosis or treatment
- emergency rescue device
- certified payment NFC
- 10 ATM / 100 m unless documented
- custom Lantern OS kernel
- certified custom RF design
- child-safety or life-safety use

## Supplier evidence checklist

Before paying for samples, request:

1. exact model number
2. SoC / chipset family if available
3. display type and resolution
4. battery capacity and battery safety documentation
5. charger specs
6. FCC / CE / RoHS / UN38.3 documents if available
7. Bluetooth qualification / declaration info if available
8. water resistance documentation if they claim IP / ATM
9. watchface customization method
10. app / firmware customization limits
11. sample lead time and shipping method
12. unit quote at 2 / 10 / 50 / 100 / 500

## Electrical engineer review questions

1. Is the donor platform safer than custom electronics for MK1?
2. Can the watchface and PTT behavior be implemented without firmware risk?
3. What hardware claims must be removed from the concept sheet?
4. Are battery, charger, and RF already validated by supplier documentation?
5. Does any health feature cross into medical-device territory?
6. What tests should be run on the two samples before showing/preorder use?
7. What files are required before any factory talks about custom hardware?

## MK1 sample validation plan

- power-on test
- charge/discharge sanity test
- heat check during charging
- Bluetooth pairing test
- mic/speaker call test
- haptic vibration test
- watchface install test
- notification test
- battery duration observation
- strap comfort / skin irritation check
- no-water test unless supplier documentation supports water exposure
- teardown only on one sacrificial sample if needed

## RAG Dollhouse placement

**Lane:** hardware/orion-watch/mk1/standards  
**Decision:** keep watch-only  
**Private boundary:** Rose / Kevin C. Rose mechanical concept remains private-IP; do not merge into supplier RFQ except as “future private mounting/docking accessory.”  
**Public-safe summary:** Orion Watch MK1 is a donor-platform wearable prototype, not a custom electronics build.

## Sources captured

The uploaded intake captured these source families as standards context. Before supplier spend or public release, replace any secondary summaries with direct official or supplier documents where available.

- FCC Part 15 / RF marketing boundary
- FCC mark / Supplier Declaration context
- IEC 62368 family reference
- IEC 62133 lithium portable battery context
- UN 38.3 lithium transport reference context
- IEC 60529 IP Code
- ISO 22810 watch water resistance context
- ISO 10993 biocompatibility context
- FDA general wellness / low-risk wearable context
- IEC 61508 fail-safe engineering discipline context
