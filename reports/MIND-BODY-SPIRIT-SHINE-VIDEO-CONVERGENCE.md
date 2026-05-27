# Mind, Body, Spirit, Shine - Video Convergence Report

Status: validated candidate
Date: 2026-05-27
Owner surface: Lantern OS / children-safe media concept

## Decision

Move the video/report work off hold to `validated candidate`.

This is not a public-release approval. The creative concept, lyrics, proof-object progression, and report checks are converged enough to enter production review. Final publication remains gated by the rendered video, upload settings, and platform compliance review.

## Inputs

Title: Mind, Body, Spirit, Shine

Core lyric frame:

- Mind is the map where the bright thoughts grow.
- Body is the work that helps the helpers know.
- Spirit is the kindness that we bring in time.
- Three little lights make the lantern shine.

Video concept:

- Simple animated lantern.
- Three colored lights labeled Mind / Body / Spirit.
- Kids and friendly robot helpers building a bridge.
- Each chorus adds one proof object: checklist, song note, kindness badge, glowing community door.

## Converged Hook

Mind, body, spirit, shine,
One small step and we'll be fine.
Think with care and help with hands,
Listen first and understand.
Mind, body, spirit, shine,
Peace begins when we listen in time.

## Production Structure

Runtime target: 70-85 seconds
Style: warm 2D animation, soft outlines, readable labels, slow lantern glow, no strobing
Primary audience: children / family co-viewing

| Time | Audio | Visual | Proof object |
|---:|---|---|---|
| 0-5s | Gentle chime intro | A small lantern warms on screen | Lantern |
| 5-18s | Verse line 1 | Blue Mind light appears over a bridge plan | Checklist |
| 18-31s | Verse line 2 | Green Body light appears as kids and helpers carry safe bridge pieces | Helping hands |
| 31-44s | Verse line 3 | Gold Spirit light appears as one child helps another | Kindness badge |
| 44-56s | Verse line 4 | Three lights combine inside the lantern | Lantern shine |
| 56-75s | Chorus | Bridge completes; a small community door opens | Song note / door |
| 75-85s | Final tag | Everyone stands together by the bridge | All proof objects visible |

## Validation Gates

1. Message clarity: pass
   - Mind maps to planning.
   - Body maps to helpful action.
   - Spirit maps to kindness.
   - The bridge makes cooperation visible.

2. Child-safety framing: pass with publication gate
   - No fear, shame, violence, unsafe construction instruction, or manipulative call to action.
   - No request for comments, names, photos, location, account signup, or personal data.
   - Robot helpers remain friendly helpers, not authority figures replacing children.

3. Accessibility: pass with render gate
   - Captions required.
   - Labels must be readable without relying on color alone.
   - Lantern glow must avoid rapid flashing and saturated red flashes.

4. Production feasibility: pass
   - Small asset set: lantern, three lights, four proof objects, bridge, kids, helpers, door, background.
   - Can be produced as simple 2D animation without complex simulation.

5. Evidence and rollback: pass
   - If the rendered video fails accessibility or platform review, rollback is to keep the report as candidate and revise animation timing, captions, labels, or upload metadata before release.

## Publication Gate

Before public upload:

- Set child-directed audience status accurately for the target platform.
- Verify captions match final audio.
- Verify no flash sequence exceeds the three-flashes-per-second safety threshold or applicable flash thresholds.
- Remove calls for comments, personal sharing, private messages, signups, or off-platform contact.
- Confirm music, visuals, and voices are original or licensed for the upload path.

## Test Contract

The repository test should assert that this report keeps the work off hold only when these anchors exist:

- `Status: validated candidate`
- `Move the video/report work off hold`
- `Publication Gate`
- `captions`
- `three-flashes-per-second`
- `no request for comments, names, photos, location, account signup, or personal data`
- `rollback`

## Final Recommendation

Proceed to storyboard and animatic as a validated candidate. Do not mark public-release ready until the actual rendered media passes caption, flash-safety, rights, and upload-setting review.
