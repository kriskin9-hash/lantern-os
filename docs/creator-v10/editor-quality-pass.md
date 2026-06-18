# Editor Quality Pass (V10) — gameplay-first selection + frame-filling crop

Targets the two concrete failures from the last render: it picked a **conversation
instead of gameplay**, and the output looked like a **center-letterboxed horizontal
video** (gameplay in a small middle band). Both are now fixed and verified. This
doc is also explicit about what is **not** honestly buildable here — the engine
must never claim detection it cannot actually perform.

## Fixed (real, verified)

### 1. Gameplay-first highlight scoring (`lib/highlight-engine.js`)
The old merge used `score = max(motion, audioLoudness, sceneDiff)`, so any loud
moment (a conversation) set a high score. Replaced with a **gameplay-first
composite** over per-clip-normalized signals:

```
density = 0.40·motion + 0.25·combat + 0.15·scene + 0.10·audioPeak(when action)
combat  = audio TRANSIENT, credited only when visual action is present
```

Plus a **conversation penalty**: loud + *sustained* (low transient) + static scene
+ modest motion → `score ×= 0.35` (and such regions are dropped below the 0.12
floor, so they don't even form highlights).

- New audio signal: `detectAudioSpikes` now records a **transient** (sudden
  loudness rise) per window — combat is transient-heavy, speech is sustained.
  This is the honest discriminator (real PCM math), not speech recognition.
- New output: a per-second **gameplay-density heatmap**
  (`timeline.metadata.gameplayDensity`) — highlights come from density peaks.

**Verified (unit, 7/7):** on a clip with a loud static *conversation* (t=2–6s) and
a *combat* burst (t=12–16s, motion+scene+transient audio), the conversation is
fully suppressed/dropped, the action scores 0.835, the top-ranked highlight and
the density peak both land in the action window, and it's tagged `combat`.

### 2. Frame-filling 9:16 crop (`public/entry.html`)
The dashboard rendered with `fit:'pad'` — scale-to-fit + **black bars**, so a 16:9
gameplay clip shrank into a middle band. Both render paths now default to
`fit:'crop'` (cover) + `useSafeZones:true`, so gameplay **fills** the 9:16 frame
with no bars, and the SafeZoneV2 crop planner shifts the window to avoid slicing
facecam/HUD.

**Verified (live e2e, 4/4):** a 1280×720 source renders to **exactly 1080×1920,
no bars**, fit recorded as `crop`, passing the ExportValidator.

### 3. Recommended Upload (`public/entry.html`)
The rank-1 variant (already chosen by viral score across the 5 strategies) now
carries a **★ Recommended Upload** badge.

## NOT built — needs real computer vision / ML (won't be faked)

The handoff asks for detections this engine cannot honestly perform without
models it does not have. Per the subsystem's honesty contract, these are left
explicitly unimplemented rather than stubbed with fabricated confidence:

| Requested | Why not | Honest substitute in place |
|---|---|---|
| Kill-feed / hitmarker / damage-flash / weapon-swap / ADS / reload detection | Needs OCR + trained CV per game | `combat` proxy = audio transient + visual action; tagged, not claimed as event detection |
| Facecam x/y/w/h via face detection + track through video, ≥95% visibility | Needs a face detector + tracker | SafeZoneV2 measured-confidence corner detection (temporal-activity proxy); crop avoids slicing it when found |
| Dynamic crop following crosshair / player model / combat cluster | Needs object tracking | Cover-crop centered + safe-zone shift (static per render) |
| OCR caption-presence verification (>80% of frames) | Needs tesseract/OCR (not installed) | Validator records captions **burned** from the real encode step, not pixel OCR |
| "Gameplay occupies >80% of screen" | Needs CV to know where gameplay is | Not asserted; crop-fill removes bars, but coverage isn't measured |

These would be a genuine next milestone (bundle an OCR/CV model). Until then the
engine reports what it actually measured and nothing more.

## Tunables
`mergeDetections(..., weights)` and `analyzeVideoForHighlights(video, { weights })`
accept weight overrides (`GAMEPLAY_WEIGHTS` defaults). Conversation-penalty
thresholds live in `mergeDetections`.
