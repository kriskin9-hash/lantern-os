# Legacy Home Accessibility Surface Strategy

Status: product strategy
Audience: product, accessibility, operators, implementers

## Purpose

Suzie should help users change how they interact with a PC when typing, vision strain, fatigue, pain, or old hardware make normal keyboard/mouse workflows impractical.

This is not only a disability accommodation. It is a core product surface for real home users, older PCs, K-12 labs, caregivers, and operators who need affordable ways to reduce typing and visual strain.

## Design thesis

Suzie should support a budget-friendly legacy setup:

```text
old Windows PC or Dell tower
existing monitor/keyboard/mouse
cheap microphone or headset
optional large-button/adaptive input
local-first Suzie helper
plain-language task flows
voice/text/keyboard/switch fallback
```

The goal is to let the user work with the PC through shorter commands, dictation, large controls, readback, summaries, and safe approval steps rather than constant typing and precise mouse use.

## Accessibility scope

This profile should support more than cognitive accessibility:

- low vision and eye strain;
- color/contrast sensitivity;
- typing pain and repetitive strain risk;
- limited dexterity or tremor;
- fatigue and task endurance limits;
- screen reader and magnifier use;
- voice-first and switch-friendly workflows;
- old hardware and low bandwidth.

## Standards posture

Baseline:

```text
WCAG 2.2 AA / ISO/IEC 40500:2025 for web/PWA surfaces
Section 508-style ICT thinking for hardware, local apps, documents, and support docs
Capability honesty for accessibility features and degraded hardware
```

Mission-critical flows should apply selected WCAG AAA practices where practical: enhanced contrast, plain-language help, error prevention, predictable navigation, and reduced cognitive load.

## First-party Windows surfaces to support

Suzie should be designed to work well with existing Windows accessibility features instead of replacing them.

Important Windows features:

- Voice access / voice control for Windows 11 22H2 and later;
- voice typing / dictation;
- Magnifier;
- Narrator;
- color filters and contrast themes;
- keyboard shortcuts and sticky/filter/toggle keys;
- eye control where available;
- live captions where relevant.

Suzie should expose commands and UI elements that are easy to use through these surfaces.

## Budget-friendly hardware kit

Recommended low-cost test kit:

```text
legacy Windows desktop or laptop
secondhand monitor, preferably 22 inch or larger
USB headset or desktop microphone
trackball or vertical mouse
large-print keyboard or keyboard stickers
USB foot pedal or macro keypad
optional cheap webcam for document capture
optional gamepad or adaptive controller
optional large external speaker
```

Higher-accessibility kit:

```text
Microsoft Adaptive Hub or equivalent switch interface
large adaptive buttons or 3.5 mm switches
Adaptive Mouse or trackball
mounting arm / document stand
LED desk lamp with adjustable brightness
```

The product should not require expensive equipment. These devices should improve the experience, not unlock basic access.

## Interaction modes

### 1. Voice-first command mode

Purpose: reduce typing and mouse use.

Examples:

```text
Suzie, read this screen.
Suzie, summarize this notice.
Suzie, draft a reply.
Suzie, what is waiting on me?
Suzie, show bigger text.
Suzie, save this for later.
Suzie, stop.
```

Requirements:

- every voice action has keyboard/text fallback;
- no irreversible action by voice alone;
- confirmation before send/submit/spend/delete;
- support short commands and plain language;
- visible transcript of what Suzie heard;
- correction path when voice recognition is wrong.

### 2. Dictation-assisted authoring

Purpose: reduce typing burden.

Suzie should support:

- speak rough notes;
- convert to structured draft;
- read draft back;
- edit by saying short commands;
- approve before send/export.

Example flow:

```text
User dictates messy paragraph
-> Suzie turns it into a clear email draft
-> Suzie reads it back
-> user says approve, revise, or save
```

### 3. Large-button safe actions

Purpose: reduce precision mouse/keyboard demand.

Safe buttons:

```text
Next
Back
Repeat
Read aloud
Save
Help
Stop
Call helper
Print checklist
```

Avoid mapping physical buttons to dangerous actions:

```text
send
submit
pay
delete
force push
start agents
move queue
```

### 4. Low-vision surface

Purpose: reduce eye strain and improve readability.

Requirements:

- large type presets;
- high contrast;
- dark/light/sepia modes;
- no color-only state;
- visible focus;
- screen reader labels;
- keyboard navigation;
- zoom-friendly layout;
- printable checklist mode;
- read-aloud support.

### 5. Keyboard-minimal workflow

Purpose: avoid carpal-tunnel-triggering constant typing.

Requirements:

- numbered choices;
- command palette;
- single-key shortcuts only when safe;
- macro-friendly actions;
- no long required text fields when dictation/upload can work;
- auto-save drafts;
- resume task later.

### 6. Switch/scanning compatible workflow

Purpose: support limited motor input.

Every critical task should be usable with:

```text
Next
Select
Back
Repeat
Help
Stop
```

This also benefits old/cheap hardware users with foot pedals or macro buttons.

## Legacy home test profile

Create a test environment that intentionally avoids premium assumptions:

```text
Windows 10/11 machine
4-8 GB RAM target
no dedicated GPU
720p webcam optional
cheap USB mic/headset
single 1080p monitor
keyboard/mouse only plus optional low-cost macro input
intermittent internet allowed
cloud model optional, not required
```

The profile should verify that Suzie remains useful when:

- cloud API keys are missing;
- voice is unavailable;
- microphone quality is poor;
- screen is low resolution;
- network is intermittent;
- local model is low capacity;
- user cannot type long responses.

## Capability honesty for accessibility

Suzie must not claim an accessibility surface is available unless it works in the current setup.

Examples:

```text
Voice control is not available on this machine. You can continue with keyboard shortcuts, large buttons, or text commands.
```

```text
Cloud transcription is blocked by this profile. I can use local dictation if available or help you paste typed notes.
```

```text
This display is too small for the full dashboard. I switched to one-step mode.
```

```text
The selected agent cannot edit files. It can review and draft instructions, then route implementation to an edit-capable slot.
```

## Mission-critical safeguards

For any mission-critical surface:

- no single input method dependency;
- no irreversible action without confirmation;
- always show what has and has not been sent;
- always provide stop/back/repeat/help;
- preserve a text summary for screen readers and caregivers;
- degrade visibly, never silently;
- log accessibility capability state without sensitive content.

## First demo workflow

Recommended first local-home demo:

```text
User opens Suzie on old Windows PC.
User uses voice or large-button flow to upload/read a document.
Suzie summarizes it in large text.
Suzie reads it aloud.
Suzie offers three next actions.
User dictates a draft reply.
Suzie reads it back.
User saves draft; nothing is sent without approval.
Evidence log records task using pseudonymous user ID.
```

This demo proves:

- low-typing interaction;
- low-vision readability;
- voice/text fallback;
- approval before risky action;
- old-PC compatibility posture;
- capability honesty when features are missing.

## Implementation backlog

1. Add `legacy-home-accessibility` profile.
2. Add accessibility surface schema.
3. Add status output for available/degraded accessibility surfaces.
4. Add one-step mode UI contract.
5. Add voice/text command vocabulary.
6. Add large-button action map.
7. Add low-vision display presets.
8. Add tests preventing dangerous actions from being bound to one-click physical controls.
9. Add evidence capture for local legacy-home demo.

## Non-goals

- Do not require expensive adaptive hardware.
- Do not make voice the only path.
- Do not treat cognitive accessibility as the only accessibility concern.
- Do not silently fall back to cloud services.
- Do not send, submit, delete, spend, or mutate without explicit confirmation.
