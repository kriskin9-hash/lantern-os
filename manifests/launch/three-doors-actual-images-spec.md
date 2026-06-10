# Three Doors: Actual Door Images Feature Spec

**Status:** Proposed  
**Priority:** Medium  
**Target:** Dream Journal v1 launch  
**Issue Reference:** #285, #252, #182

---

## Problem Statement

Current `three-doors-game.html` uses procedural canvas art for door scenes. While functional and offline-capable, it lacks the visual impact of actual generated door images. The LoRA image generation sidecar service (Commit 3) exists but is not integrated into the Three Doors UI.

**Current State:**
- Canvas-based procedural rendering with palette-based gradients
- SD prompts defined per scene but not used for image generation
- 5 pre-generated door images exist in `data/images/generated-doors/`
- `data/images/three-doors/` directory exists but empty

**User Impact:**
- Lower visual engagement compared to AI-generated art
- Missed opportunity to showcase LoRA-trained door images
- Canvas art feels "engineered" rather than "dreamlike"

---

## Proposed Solution

Replace canvas rendering with actual door images using a three-tier fallback system:

1. **Tier 1 (Live):** LoRA-generated images from sidecar service (if available)
2. **Tier 2 (Cached):** Pre-generated images in `data/images/three-doors/`
3. **Tier 3 (Fallback):** Canvas procedural art (current implementation)

---

## Implementation Plan

### Phase 1: Image Generation Pipeline

**1.1 Generate scene-specific door images**

Run LoRA generation for each of the 7 scenes:
```bash
# For each scene in SCENES (moss-entry, burrow, sunken-bell, little-crown, garden-door, xenon-convergence, end-of-time)
python scripts/generate-with-trained-lora.py \
  --prompt "<SD_PROMPTS[scene_key]>" \
  --adapter models/csf-image/checkpoints/lantern-door-lora-final.safetensors \
  --out data/images/three-doors/<scene_key>.png
```

**Expected output:**
- `data/images/three-doors/moss-entry.png`
- `data/images/three-doors/burrow.png`
- `data/images/three-doors/sunken-bell.png`
- `data/images/three-doors/little-crown.png`
- `data/images/three-doors/garden-door.png`
- `data/images/three-doors/xenon-convergence.png`
- `data/images/three-doors/end-of-time.png`

**1.2 Integrate with sidecar service**

Modify `image-generation.js` to accept a `sceneKey` parameter and save to `data/images/three-doors/`:

```javascript
function generateDoorSceneImage({ sceneKey, cleanText, doors, symbolMesh, entryId }) {
  const prompt = buildThreeDoorsImagePrompt({ cleanText, doors, symbolMesh });
  const outputPath = `data/images/three-doors/${sceneKey || entryId}.png`;
  // ... existing spawn logic
}
```

---

### Phase 2: UI Updates to three-doors-game.html

**2.1 Replace canvas with `<img>` element**

Current code (lines 443-446):
```html
<div class="scene-image">
  <canvas id="${canvasId}" width="800" height="450"></canvas>
  <div class="sd-badge">SD prompt — hover to copy</div>
</div>
```

New code:
```html
<div class="scene-image">
  <img id="${imgId}" src="" alt="Scene art" loading="lazy" onerror="fallbackToCanvas('${canvasId}')">
  <canvas id="${canvasId}" width="800" height="450" style="display:none"></canvas>
  <div class="sd-badge">SD prompt — hover to copy</div>
</div>
```

**2.2 Add image loading logic**

```javascript
function loadSceneImage(imgId, canvasId, sceneKey) {
  const img = document.getElementById(imgId);
  const canvas = document.getElementById(canvasId);
  
  // Try cached image first
  img.src = `/data/images/three-doors/${sceneKey}.png`;
  
  img.onload = () => {
    // Image loaded successfully
  };
  
  img.onerror = () => {
    // Fallback to canvas
    img.style.display = 'none';
    canvas.style.display = 'block';
    drawScene(canvas, sceneKey);
  };
}
```

**2.3 Trigger live generation (optional enhancement)**

If server is available and no cached image exists, trigger LoRA generation:

```javascript
async function triggerLiveGeneration(sceneKey) {
  if (!serverAvailable) return;
  
  try {
    await fetch('/api/doors/generate-image', {
      method: 'POST',
      body: JSON.stringify({ sceneKey }),
    });
    // Reload image after generation
    setTimeout(() => {
      const img = document.getElementById(imgId);
      img.src = `/data/images/three-doors/${sceneKey}.png?t=${Date.now()}`;
    }, 5000);
  } catch { /* silent fail */ }
}
```

---

### Phase 3: API Endpoint (Optional)

**3.1 Add `/api/doors/generate-image` endpoint**

In `routes/dream.js`:

```javascript
app.post('/api/doors/generate-image', async (req, res) => {
  const { sceneKey } = req.body;
  const prompt = SD_PROMPTS[sceneKey];
  
  if (!prompt) {
    return res.status(400).json({ error: 'Invalid scene key' });
  }
  
  try {
    const result = await generateDoorSceneImage({
      sceneKey,
      cleanText: prompt,
      doors: [],
      symbolMesh: [],
      entryId: sceneKey,
    });
    
    res.json({ ok: result.ok, path: `data/images/three-doors/${sceneKey}.png` });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});
```

---

## Fallback Behavior

| Condition | Display | Source |
|-----------|---------|--------|
| Cached image exists | `<img>` element | `data/images/three-doors/<scene>.png` |
| No cache, server available | `<img>` → canvas | Live generation → canvas fallback |
| No cache, server offline | Canvas only | Procedural art (current) |
| Image load error | Canvas only | Procedural art (current) |

---

## Performance Considerations

- **Lazy loading:** Use `loading="lazy"` on `<img>` elements
- **Image sizing:** Target 800x450 (16:9) matching canvas dimensions
- **Compression:** Use WebP format for smaller file sizes
- **Cache headers:** Set long cache headers for static door images
- **Preload:** Preload next scene images during gameplay

---

## Testing Checklist

- [ ] Generate all 7 scene images using LoRA
- [ ] Verify images load correctly in dev (port 4178)
- [ ] Verify canvas fallback works when images missing
- [ ] Test offline mode (no server, no cached images)
- [ ] Test with cached images but no server
- [ ] Verify image hover-to-copy SD prompt still works
- [ ] Check mobile rendering (aspect ratio, loading times)
- [ ] Verify theme compatibility (dark/light mode)

---

## Rollout Plan

1. **Pre-launch:** Generate and commit 7 scene images to `data/images/three-doors/`
2. **Launch:** Deploy UI changes with image loading logic
3. **Post-launch:** Monitor image load times, fallback rates
4. **Enhancement:** Add live generation endpoint if demand exists

---

## Alternatives Considered

| Alternative | Pros | Cons | Decision |
|-------------|------|------|----------|
| Canvas only | Fast, offline, no assets | Low visual impact | Current state |
| Live generation only | Always fresh images | Slow, requires server | Rejected |
| Pre-generated only | Fast, reliable | Static, no updates | Partial (Tier 2) |
| Three-tier fallback | Best of all worlds | More complex | **Selected** |

---

## Success Metrics

- **Image load success rate:** >95% in production
- **Fallback rate:** <5% (canvas usage)
- **Page load time:** <2s with images
- **User engagement:** +20% session duration vs canvas-only

---

## Usage Metrics & Retraining Pipeline

### Current Gap

The 4 Convergance OS models are deployed but lack:
- Usage tracking (which models called, how often, success rates)
- Data collection for retraining (user interactions, preferences)
- Feedback loops for model improvement

### Models in Use

| Model | Purpose | Current State | Retraining Need |
|-------|---------|---------------|-----------------|
| `lantern-csf-dream` | Three Doors game narrative | Static Modelfile | **High** - user choices inform narrative quality |
| `lantern-pcsf` | Privacy/provider receipts | Static Modelfile | **Medium** - boundary violations inform safety |
| `lantern-convergance` | Promote/hold/archive decisions | Static Modelfile | **High** - user decisions inform classification |
| `lantern-csf-dream-image` | Door image generation | LoRA weights | **High** - user preferences inform visual style |

### Metrics to Collect

**For all models:**
- Call count per session
- Response time (p50, p95, p99)
- Error rate (timeouts, failures)
- Provider fallback rate (Ollama → Gemini → OpenAI)

**For text models (lantern-csf-dream, lantern-pcsf, lantern-convergance):**
- Token usage (input/output)
- User satisfaction (implicit: session length, return rate)
- Door choice distribution (which doors users pick)
- Decision distribution (promote/hold/archive ratios)

**For image model (lantern-csf-dream-image):**
- Image generation success rate
- Image load time
- Fallback rate (canvas vs image)
- User hover/copy actions on SD prompts

### Data Collection Implementation

**Phase 1: Local JSONL logging**

Add to `routes/dream.js`:
```javascript
// Log model usage
async function logModelUsage({ modelId, provider, action, metadata }) {
  const entry = {
    timestamp: new Date().toISOString(),
    modelId,
    provider,
    action, // 'generate', 'classify', 'decide'
    metadata,
  };
  await appendJsonlQueued('data/metrics/model-usage.jsonl', entry);
}
```

**Phase 2: In-memory aggregation**

Add to `routes/status.js`:
```javascript
// Aggregate metrics for /api/status
const modelMetrics = {
  'lantern-csf-dream': { calls: 0, errors: 0, avgLatency: 0 },
  'lantern-pcsf': { calls: 0, errors: 0, avgLatency: 0 },
  'lantern-convergance': { calls: 0, errors: 0, avgLatency: 0 },
  'lantern-csf-dream-image': { calls: 0, errors: 0, avgLatency: 0 },
};
```

**Phase 3: Retraining triggers**

Define thresholds for retraining:
- **lantern-csf-dream:** >1000 door choices with <60% diversity
- **lantern-pcsf:** >50 boundary violations in 30 days
- **lantern-convergance:** >200 hold decisions with <10% promote rate
- **lantern-csf-dream-image:** >500 image generations with >20% fallback rate

### Retraining Pipeline

**For text models (Ollama):**

```bash
# 1. Extract recent usage data
python scripts/extract-model-usage.py --days 30 --model lantern-csf-dream

# 2. Generate fine-tuning dataset
python scripts/generate-finetune-dataset.py --input data/metrics/model-usage.jsonl --output models/lantern-csf-dream/training-data.jsonl

# 3. Fine-tune with Unsloth (QLoRA)
python scripts/fine-tune-ollama-model.py --model lantern-csf-dream --data models/lantern-csf-dream/training-data.jsonl

# 4. Deploy new model
ollama create lantern-csf-dream-v2 -f models/lantern-csf-dream/Modelfile
```

**For image model (LoRA):**

```bash
# 1. Collect user-generated images (if users upload)
# 2. Add high-rated images to training set
# 3. Re-run LoRA fine-tuning
python scripts/train-lora-diffusion.py --data models/csf-image/training-data-v2.jsonl

# 4. Update LoRA weights
cp models/csf-image/checkpoints/lantern-door-lora-v2.safetensors models/csf-image/checkpoints/lantern-door-lora-final.safetensors
```

### Privacy Considerations

- **Local-only:** All metrics stored locally in `data/metrics/`
- **No PII:** Log model IDs, not user content
- **Opt-out:** Add setting to disable metrics collection
- **Retention:** Rotate logs after 90 days

### Integration with Three Doors UI

Add metrics collection to `three-doors-game.html`:

```javascript
// Log door choice
async function logDoorChoice(sceneKey, doorLabel) {
  await fetch('/api/metrics/door-choice', {
    method: 'POST',
    body: JSON.stringify({ sceneKey, doorLabel, timestamp: Date.now() }),
  });
}

// Log image load
async function logImageLoad(sceneKey, source) {
  await fetch('/api/metrics/image-load', {
    method: 'POST',
    body: JSON.stringify({ sceneKey, source, timestamp: Date.now() }),
  });
}
```

### Success Metrics for Retraining

- **Model update frequency:** Quarterly for text models, monthly for image model
- **Training data quality:** >90% of samples labeled/validated
- **Retraining success:** New model passes existing test suite
- **User impact:** No regression in satisfaction metrics

## Open Questions

1. Should we regenerate images periodically (weekly/monthly)?
2. Should users be able to upload custom door images?
3. Should we add image quality settings (low/medium/high)?
4. Should we support animated GIFs for door transitions?
5. **Should metrics collection be opt-in or opt-out?** (Recommend: opt-out with clear UI)
6. **Should we share anonymized metrics for community model improvement?** (Recommend: no, keep local-only)

---

## Related Issues

- #285: Three Doors model training expansion
- #252: Load convergence and Three Doors context with full door and memory set
- #182: Queue Three Doors projection-engine refinement for Dream Journal v1
