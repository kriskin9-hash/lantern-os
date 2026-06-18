# CaptionEngineV3

Builds on `caption-engine.js` (V9: `Caption` class, style presets, highlight-driven generation). V3 adds an **event taxonomy**, dynamic caption text tied to detected events, a 50+ style library, and visual effects.

## Event taxonomy

Captions are triggered by events derived from **real signals** the highlight engine already produces (motion spikes, audio spikes, scene cuts) plus optional speech transcript. No event is invented; each carries the timestamp and the signal that produced it.

| Event | Derived from | Example trigger |
|---|---|---|
| `kill` | audio spike + scene cut | weapon/hit transient |
| `multi_kill` | ≥2 `kill` events within window | clustered transients |
| `clutch` | sustained motion + late audio spike | end-of-round tension |
| `near_death` | motion dip + low-audio then spike | comeback moment |
| `jump_scare` | sharp scene cut + audio spike | sudden change |
| `funny` | speech/laughter (if transcript) | reaction |
| `victory` | end-region scene change + audio | win screen |
| `loss` | end-region scene change | defeat |
| `reaction` | facecam-region motion (SafeZoneV2) | streamer reacts |

Each event:

```json
{ "type": "clutch", "t": 12.4, "confidence": 0.0, "evidence": ["audio_spike@12.3","motion@12.1"] }
```

`confidence` and `evidence` make every caption auditable — you can see *why* it fired. Events below a confidence floor are dropped rather than captioned on a guess.

## Dynamic caption text

A template bank maps event → candidate phrases (the editor picks one, or the operator edits):

```
kill        → "GOT HIM" · "DOWN" · "ONE SHOT"
multi_kill  → "NO WAY" · "DOUBLE" · "HE'S CRACKED"
clutch      → "CLUTCH" · "WATCH THIS" · "WAIT FOR IT"
near_death  → "THAT WAS CLOSE" · "HOW?!"
victory     → "GG" · "THAT'S A WIN" · "THAT CHANGES EVERYTHING"
reaction    → "HE DID WHAT?" · "THIS WAS INSANE"
```

Text is a **suggestion**, always operator-editable. The engine never asserts a caption describes reality beyond the signal that triggered it.

## Style library (50+)

Styles are data, not code — defined in a `caption-styles.json` so the count is real and extensible. Families:

- `mrbeast` (bold, high-contrast, drop shadow)
- `gaming_montage` (impact, shake, glow)
- `tiktok_gaming` (rounded, bouncing)
- `reaction_creator` (speech-bubble)
- `esports` (clean, lower-third)
- `streamer_highlight` (outlined, animated entry)

Each style:

```json
{
  "id": "mrbeast_bold",
  "family": "mrbeast",
  "fontFamily": "Impact, sans-serif",
  "fontSize": 64,
  "color": "#ffffff",
  "outline": { "color": "#000000", "width": 4 },
  "shadow": { "color": "rgba(0,0,0,0.8)", "blur": 6 },
  "animation": "scale_pop",
  "safeMargin": 60
}
```

## Visual effects

`bounce · scale_pop · shake · impact_flash · glow · outline · drop_shadow` — rendered via ffmpeg/libass (ASS override tags) or a frame compositor. Effects are presentational only; they never change the underlying event truth.

## Mobile-safe placement

Captions respect SafeZoneV2 output: never placed over facecam/HUD/killfeed; default lower-third with a configurable safe margin (≥60 px at 1080×1920).

## Outputs

- `.ass`/`.vtt` subtitle track (for preview without re-encode)
- burned-in render (for final export) — verified by `ExportValidator` ("captions actually rendered")

## Feature flag

Behind `captionEngineV3` (`LANTERN_CI_CAPTION_V3`, default off). When off, V9 caption generation remains.
