# SafeZoneDetectorV2

Replaces the V9 heuristic detector. Goal: **never crop the facecam, crosshair, HUD, minimap, or killfeed** when reframing gameplay to 9:16.

## V9 defects this fixes

1. **Detected zones are discarded.** `safe-zone-detector.js:238` builds a `zones` array, then returns `new SafeZoneMap(...)` *without calling `addZone`*. So every detection is silently thrown away and `safeZones` is always empty. V2 must add zones to the returned map.
2. **Single synthetic frame.** V9 detection runs on one `frameData` blob with no real multi-frame sampling. Facecams and killfeeds are defined by *change over time*; one frame can't see that.
3. **No crop-priority enforcement.** V9 lists conflicts but doesn't rank what to protect first.

## Inputs

V2 samples N frames across the clip via the existing ffmpeg raw-frame pipeline (same approach as `highlight-engine.detectMotion`):

```
ffmpeg -i <video> -vf fps=<s>,scale=<w>:<h> -f rawvideo -pix_fmt rgb24 -
```

Default: sample every 1 s, downscaled (e.g. 320×180) for speed. Per-region temporal variance distinguishes static UI (HUD) from changing content (killfeed, facecam).

## Detected region types

| Type | Typical location | Signal |
|---|---|---|
| `facecam` | a corner, 15–25% | high temporal variance + skin-tone fraction + rectangular/round edge |
| `hud_top` | top band | persistent high-contrast text/icons, low motion |
| `hud_bottom` | bottom band | persistent bars/numbers (health/ammo) |
| `minimap` | a corner, 10–15% | dense edges, colored, semi-static |
| `killfeed` | top-right | text rows that change rapidly |
| `crosshair` | center, tiny | persistent center mark |
| `subtitles` | lower third | existing burned captions |

## Protected region output

```json
{
  "videoWidth": 1920,
  "videoHeight": 1080,
  "regions": [
    { "type": "facecam", "bounds": {"x":0.75,"y":0.0,"width":0.25,"height":0.25},
      "confidence": 0.0, "framesSeen": 0, "priority": 1 }
  ],
  "cropPlan": { "format": "9:16", "x": 0.0, "width": 1.0, "preserved": ["facecam","crosshair"] },
  "detectedAt": "ISO-8601"
}
```

`confidence` is the fraction of sampled frames the region fired in — a **measured** quantity, never a constant. `framesSeen` exposes the denominator so the value is auditable.

## Crop priority

When a 9:16 window cannot contain everything, protect in this strict order:

```
1. facecam        (creator identity — losing it kills the clip)
2. crosshair      (gameplay readability)
3. hud_*          (context: health/ammo/score)
4. gameplay action (the rest)
```

The cropper picks the 9:16 window that preserves the highest-priority set possible. If facecam + action can't both fit, it emits a **picture-in-picture** plan (facecam composited as an overlay) rather than cropping the facecam out.

## Confidence & honesty

- A region with `confidence < 0.5` is reported as `candidate`, not `confirmed`, and the UI labels it as such.
- If detection can't run (ffmpeg missing / unreadable video), V2 returns `{ status: "unavailable", reason }` — it does **not** emit a fabricated default layout.

## Feature flag

Behind `safeZoneV2` (`LANTERN_CI_SAFEZONE_V2`, default off). When off, the editor uses the V9 detector (with the discard bug fixed as a minimal patch) so reframing still functions.

## Implementation steps

1. Minimal V9 patch: add detected zones to the returned `SafeZoneMap` (fixes the discard bug today).
2. Multi-frame sampler reusing the ffmpeg raw pipeline.
3. Per-region temporal-variance + skin-tone + edge-density scoring → `confidence`.
4. Crop planner with the priority ladder + PiP fallback.
5. Wire into `routes/creator-entries.js` render path behind the flag.
