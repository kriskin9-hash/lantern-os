# Patient A MK1 Armour PPE Exosuit Manual

Date: 2026-05-26  
Repo: `alex-place/lantern-os`  
User label: Patient A, de-identified  
Mode: review manual for a real protective PPE carrier + modular external exosuit  
Status: concept/manual only until certified PPE modules, fit checks, and safety tests are selected

## 0. Core Decision

Patient A's MK1 is no longer only a costume shell. It becomes a modular external armour/PPE/exosuit platform.

The suit can look like a classic Tony-start / garage-built hero system, but every protective claim must be grounded in one of three categories:

1. certified PPE module;
2. tested prototype protection with a limited claim;
3. cosmetic shell / carrier with no protection claim.

If a part has not been tested or certified, call it cosmetic, comfort, carrier, mockup, or prototype - not protective PPE.

## 1. MK1 Doctrine

> Looks heroic. Fails safe. Protects only where tested. Uses certified PPE where real hazards exist.

Hard boundaries:

- no weapons;
- no flight hardware;
- no powered strength assist in MK1;
- no electrical stimulation;
- no charging while worn;
- no uncertified ballistic, fire, chemical, electrical, or fall-protection claim;
- no sealed helmet without ventilation and escape review;
- no medical-device claim;
- no prosthetic actuator control without professional fail-safe review.

## 2. PPE Reality Rule

PPE is the last protective layer, not the first. The MK1 can carry real PPE, but it does not make the wearer invincible.

Use this protection labeling system:

| Label | Meaning |
|---|---|
| Certified PPE | bought from a known PPE vendor and used according to its instructions |
| PPE Carrier | the suit holds or exposes PPE, but does not itself certify protection |
| Tested Prototype | tested for comfort/impact/scratch/heat in a limited non-certified way |
| Cosmetic Shell | visual armour only, no protection claim |
| Held | too risky or untested for use |

## 3. MK1 Layers

### Layer A - Soft base layer

Purpose:

- comfort;
- sweat barrier;
- cable routing;
- pressure distribution;
- skin protection.

Material direction:

- breathable compression shirt or workwear base;
- removable washable liner;
- foam/silicone pads where hardware contacts body;
- no adhesive directly on fragile skin unless skin-safe and patch-tested.

### Layer B - Certified PPE modules

Use real PPE where hazards matter:

- safety glasses / face shield where eye impact exists;
- work gloves where hand abrasion exists;
- knee/elbow pads where kneeling/crawling exists;
- safety footwear where foot hazards exist;
- hearing protection where noise exists;
- respirator only if selected/fitted/used according to its own instructions.

The MK1 shell may wrap around these modules, but it must not block their function.

### Layer C - Armour-look carrier shell

Purpose:

- classic hero silhouette;
- light abrasion/scratch reduction if tested;
- mounting points;
- cable protection;
- visual identity.

Use:

- rounded 3D-printed shell;
- EVA foam mockups;
- TPU flexible guards;
- modular shoulder, chest, forearm, thigh, and shin covers.

No ballistic/fire/electrical/chemical claim unless using certified components rated for that hazard.

### Layer D - Passive exosuit frame

Purpose:

- distribute load;
- stabilize modules;
- support posture;
- mount batteries/control boxes off the chest;
- hold prosthetic/brace/wheelchair/cane interfaces.

Allowed MK1 version:

- passive harness;
- back/belt load distribution;
- shoulder yoke;
- forearm bracer mounts;
- leg strap mounts;
- quick-release buckles.

Held:

- powered joints;
- lift assistance;
- motorized knees/hips/shoulders;
- powered prosthetic outputs;
- fall arrest or rescue lifting claims.

## 4. Chest Reactor Module

Name: Lantern Core MK1-A.

Features:

- diffused lantern glow;
- LRA tap motor for precise haptics;
- optional ERM rumble motor for DualShock-style pulse;
- passive NFC / Java Card identity layer;
- large tactile button;
- soft skin-contact or over-shirt backing;
- quick-release chest mount.

Power rule:

```text
battery on back / side / belt
protected low-voltage cable
reactor on chest
no charging while worn
```

## 5. Green Caption Glasses Module

Name: **MK1 Green Caption Glasses / Tony-Start Sight Module**.

Purpose:

- give Patient A a green HUD-style look;
- provide captions and readout support;
- support blind/low-vision workflows through audio, captions, OCR, and scene description;
- avoid pretending the glasses are certified navigation, medical, or eye-protection hardware unless they actually use certified PPE lenses/frames.

### Modes

| Mode | Function | Safety note |
|---|---|---|
| Green Style Mode | green-tinted Tony-start / cyberpunk glasses | avoid too-dark tint indoors or at night |
| Caption Mode | phone/computer captions mirrored or shown nearby | not a hearing/vision cure |
| OCR Mode | read text through phone/glasses camera | verify critical text manually when possible |
| Scene Describe Mode | AI describes visible scene | advisory only; not obstacle-proof navigation |
| Bone-Conduction Companion | sends audio to existing bone-conduction setup | keep volume safe |
| Safety Glasses Mode | use certified impact-rated glasses if work hazards exist | do not modify lenses/frame in a way that voids rating |
| Blind Assist Mode | camera-to-audio/caption support | must not replace cane, guide, orientation training, or human help in dangerous spaces |

### MK1 glasses physical spec

- green translucent or green-accent frame;
- optional clip-on side display or phone-based caption window;
- optional camera module only after privacy review;
- open-ear or bone-conduction compatible audio;
- tactile temple button;
- no always-on recording by default;
- visible recording indicator if camera is active;
- no face recognition database in kid/family mode;
- no driving/traffic reliance.

### Caption line

Use this on diagrams:

> **Green Caption Glasses: Tony-start look, blind-assist captions, OCR, and scene readout - advisory only, not a substitute for certified eye PPE or mobility safety.**

## 6. Modular Suit Map

| Module | MK1 status | Protection class | Notes |
|---|---|---|---|
| Chest reactor | build now | status/accessibility, not PPE | glow + haptic + NFC |
| Green caption glasses | design now | PPE only if certified glasses are used | caption/OCR/AI assist optional |
| Shoulder plates | build mockup | cosmetic/prototype | rounded edges, breakaway |
| Forearm bracers | build now | carrier/prototype | macro buttons, LEDs, NFC tap |
| Gloves | select PPE | certified PPE if needed | do not block dexterity |
| Back/belt pack | build now | carrier | battery off sternum |
| Knee pads | buy PPE | certified/workwear PPE | integrate straps only |
| Boots | buy PPE | certified/work footwear if hazard exists | no trip shell first |
| Helmet/cowl | cosmetic first | held for PPE unless certified | no sealed breathing trap |
| Respirator | held | certified only | fit/medical/user instructions required |
| Exosuit frame | passive now | carrier/support | no powered assist |
| Prosthetic rail | passive now | carrier | clinician/prosthetist review before load-bearing use |

## 7. Exosuit Modularity Standard

Every module uses a common record:

```yaml
module_id:
body_location:
purpose:
protection_label: certified_ppe|ppe_carrier|tested_prototype|cosmetic_shell|held
hazard_addressed:
certification_or_vendor:
attachment_method:
quick_release:
weight_g:
heat_risk:
skin_contact:
electronics:
power_source:
failure_mode:
validation_state:
notes:
```

No module is allowed onto Patient A until its record exists.

## 8. Fit And Comfort Checklist

Before electronics:

- can Patient A put it on and remove it safely?
- can either hand reach quick release?
- can Patient A breathe, sit, bend, and turn?
- any pressure on ribs, sternum, neck, spine, or joints?
- any pinching or skin irritation?
- can Patient A use bathroom, drink water, and cool down?
- does any shell create a fall/trip hazard?

## 9. Heat / Battery / Electrical Checklist

- no charging while worn;
- no exposed LiPo pouch;
- no hard battery on sternum;
- no high-current line across chest;
- no exposed conductor against skin;
- strain relief on all cables;
- inline switch/disconnect;
- fuse/PTC/protection where practical;
- bench-run LEDs/haptics before wear;
- check shell temperature after 10, 20, and 30 minutes.

## 10. PPE Review Checklist

For each hazard, answer:

1. What hazard are we actually protecting against?
2. Is there a certified PPE item for that hazard?
3. Does the MK1 shell block, weaken, or modify that PPE?
4. Can Patient A don/doff it correctly?
5. Does it add heat, fatigue, or fall risk?
6. Is the claim written correctly?

Examples:

- Eye impact: use certified safety glasses or face shield. Green caption glasses are not impact PPE unless built on certified frames/lenses.
- Hand abrasion: use real work gloves, then add cosmetic bracer over/around them.
- Knee impact: use actual knee pads.
- Noise: use hearing protection or existing bone-conduction/audio at safe levels; do not crank volume.
- Dust/respiratory: do not improvise; use proper respirator guidance.

## 11. Build Order

### MK1-A: Chest + Harness

- foam dummy chest plate;
- soft harness;
- LED reactor;
- low-power haptic;
- NFC identity;
- back/belt battery pack.

### MK1-B: Green Caption Glasses

- green style glasses mockup;
- caption/OCR workflow through phone first;
- no always-on camera by default;
- safety-glasses version if work PPE is needed.

### MK1-C: Forearm Bracers

- big macro buttons;
- status LEDs;
- optional NFC tap point;
- no power tools or motors.

### MK1-D: PPE Integration

- certified gloves;
- certified eye protection;
- knee/elbow pads;
- safety footwear if needed;
- high-vis panels if outdoors.

### MK1-E: Passive Exosuit Frame

- shoulder/back belt load spreader;
- quick-release rail;
- prosthetic/brace/cane/bag/wheelchair mount options;
- no powered assist.

## 12. Review Gates

Green gate:

- cosmetic and comfort only;
- no protection claim;
- no electronics failure risk.

Amber gate:

- electronics present;
- low power;
- bench tested;
- worn short duration.

Red gate / held:

- powered movement;
- medical claim;
- battery heat;
- sealed helmet;
- respiratory protection;
- load-bearing prosthetic interface;
- any claim that needs certification.

## 13. Next Review Questions

1. What hazards does Patient A actually face: falls, impact, dust, work tools, weather, fatigue, low vision, mobility, pain, or social confidence?
2. Is the green glasses module for style, captions, blindness assist, eye PPE, or all four?
3. Does Patient A need prescription lenses?
4. Should captions appear on glasses, phone, wrist/forearm, or chest light/haptics?
5. Is Patient A expected to use a cane, wheelchair, prosthetic, brace, or other assistive device with the suit?
6. Is the suit for home, school, work, shop, outside, or public event use?
7. Maximum safe wear time goal for MK1: 10 minutes, 30 minutes, 2 hours, or all day?

## 14. Done Definition

The MK1 manual is review-ready when:

- every module is labeled certified PPE, carrier, tested prototype, cosmetic, or held;
- green caption glasses are treated as assistive/HUD unless built on certified safety glasses;
- powered exosuit functions remain held;
- Patient A can remove the suit quickly;
- no protection claim exists without evidence;
- the first build is chest + harness + glasses mockup + PPE integration, not powered armour.
