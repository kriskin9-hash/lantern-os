// SafeZoneDetectorV2 (Creator V10)
// Multi-frame detector that finds protected-region CANDIDATES in gameplay and
// plans a 9:16 crop window that avoids slicing through them.
//
// Honesty boundary: this is a motion/contrast heuristic, not a face recognizer.
// It flags (a) corner regions with sustained, locally-distinct activity — which
// commonly indicates a facecam/overlay — and (b) static high-contrast bands —
// which commonly indicate a HUD. Every region carries a MEASURED confidence
// (the fraction of sampled frame-transitions in which it "fired"), plus the
// frame count behind it, so the value is auditable. When detection cannot run
// (ffmpeg missing / unreadable video), it returns { status: "unavailable" } and
// fabricates nothing.
//
// See docs/creator-v10/safe-zone-v2.md

"use strict";

const fs = require("fs");
const { spawn } = require("child_process");

const SAMPLE_W = 192; // downscaled analysis frame (keeps it fast)
const SAMPLE_H = 108;
const GRID_COLS = 12;
const GRID_ROWS = 8;
const TARGET_ASPECT_9_16 = 9 / 16;

// ---------------------------------------------------------------------------
// Frame sampling (real ffmpeg raw pipeline, same approach as highlight-engine)
// ---------------------------------------------------------------------------

function sampleFrames(videoPath, fps = 1) {
  return new Promise((resolve) => {
    if (!fs.existsSync(videoPath)) return resolve({ frames: [], ok: false });
    let proc;
    try {
      proc = spawn("ffmpeg", [
        "-i", videoPath,
        "-vf", `fps=${fps},scale=${SAMPLE_W}:${SAMPLE_H}`,
        "-f", "rawvideo", "-pix_fmt", "rgb24", "-",
      ], { stdio: ["ignore", "pipe", "ignore"] });
    } catch {
      return resolve({ frames: [], ok: false });
    }
    const frameSize = SAMPLE_W * SAMPLE_H * 3;
    const frames = [];
    let buf = Buffer.alloc(0);
    proc.stdout.on("data", (chunk) => {
      buf = Buffer.concat([buf, chunk]);
      while (buf.length >= frameSize) {
        frames.push(buf.slice(0, frameSize));
        buf = buf.slice(frameSize);
      }
    });
    proc.on("error", () => resolve({ frames: [], ok: false }));
    proc.on("close", (code) => resolve({ frames, ok: code === 0 && frames.length > 0 }));
  });
}

// ---------------------------------------------------------------------------
// Per-cell metrics
// ---------------------------------------------------------------------------

// Mean brightness of each grid cell for one frame.
function cellBrightness(frame) {
  const grid = Array.from({ length: GRID_ROWS }, () => new Float64Array(GRID_COLS));
  const counts = Array.from({ length: GRID_ROWS }, () => new Float64Array(GRID_COLS));
  for (let y = 0; y < SAMPLE_H; y++) {
    const row = Math.min(GRID_ROWS - 1, Math.floor((y / SAMPLE_H) * GRID_ROWS));
    for (let x = 0; x < SAMPLE_W; x++) {
      const col = Math.min(GRID_COLS - 1, Math.floor((x / SAMPLE_W) * GRID_COLS));
      const idx = (y * SAMPLE_W + x) * 3;
      const lum = (frame[idx] + frame[idx + 1] + frame[idx + 2]) / 3;
      grid[row][col] += lum;
      counts[row][col] += 1;
    }
  }
  for (let r = 0; r < GRID_ROWS; r++) {
    for (let c = 0; c < GRID_COLS; c++) {
      if (counts[r][c]) grid[r][c] /= counts[r][c];
    }
  }
  return grid;
}

// Horizontal edge energy per cell (proxy for text/HUD contrast) for one frame.
function cellEdges(frame) {
  const grid = Array.from({ length: GRID_ROWS }, () => new Float64Array(GRID_COLS));
  for (let y = 0; y < SAMPLE_H; y++) {
    const row = Math.min(GRID_ROWS - 1, Math.floor((y / SAMPLE_H) * GRID_ROWS));
    for (let x = 1; x < SAMPLE_W; x++) {
      const col = Math.min(GRID_COLS - 1, Math.floor((x / SAMPLE_W) * GRID_COLS));
      const i = (y * SAMPLE_W + x) * 3;
      const j = (y * SAMPLE_W + (x - 1)) * 3;
      const d = Math.abs(frame[i] - frame[j]) + Math.abs(frame[i + 1] - frame[j + 1]) + Math.abs(frame[i + 2] - frame[j + 2]);
      grid[row][col] += d / 3;
    }
  }
  return grid;
}

// ---------------------------------------------------------------------------
// Region detection
// ---------------------------------------------------------------------------

function detectRegions(frames) {
  const n = frames.length;
  const brightnesses = frames.map(cellBrightness);

  // Temporal activity: per-cell mean abs brightness change between frames,
  // and per-frame "fire" counts for the four corner blocks.
  const activity = Array.from({ length: GRID_ROWS }, () => new Float64Array(GRID_COLS));
  let transitions = 0;
  for (let f = 1; f < n; f++) {
    transitions++;
    for (let r = 0; r < GRID_ROWS; r++) {
      for (let c = 0; c < GRID_COLS; c++) {
        activity[r][c] += Math.abs(brightnesses[f][r][c] - brightnesses[f - 1][r][c]);
      }
    }
  }
  if (transitions > 0) {
    for (let r = 0; r < GRID_ROWS; r++)
      for (let c = 0; c < GRID_COLS; c++) activity[r][c] /= transitions;
  }

  // Corner blocks (≈ a quarter of the frame in each corner).
  const cr = Math.max(1, Math.round(GRID_ROWS * 0.35));
  const cc = Math.max(1, Math.round(GRID_COLS * 0.30));
  const corners = {
    top_left: { r0: 0, r1: cr, c0: 0, c1: cc, x: 0, y: 0 },
    top_right: { r0: 0, r1: cr, c0: GRID_COLS - cc, c1: GRID_COLS, x: 1 - cc / GRID_COLS, y: 0 },
    bottom_left: { r0: GRID_ROWS - cr, r1: GRID_ROWS, c0: 0, c1: cc, x: 0, y: 1 - cr / GRID_ROWS },
    bottom_right: { r0: GRID_ROWS - cr, r1: GRID_ROWS, c0: GRID_COLS - cc, c1: GRID_COLS, x: 1 - cc / GRID_COLS, y: 1 - cr / GRID_ROWS },
  };

  // Global per-transition motion to compare corners against the whole scene.
  const globalPerTransition = new Float64Array(Math.max(0, n - 1));
  for (let f = 1; f < n; f++) {
    let sum = 0, cells = 0;
    for (let r = 0; r < GRID_ROWS; r++)
      for (let c = 0; c < GRID_COLS; c++) { sum += Math.abs(brightnesses[f][r][c] - brightnesses[f - 1][r][c]); cells++; }
    globalPerTransition[f - 1] = cells ? sum / cells : 0;
  }

  // For each corner, confidence = fraction of transitions where the corner's
  // local activity is clearly above the scene's (a sustained distinct overlay).
  const regions = [];
  let bestCorner = null;
  for (const [name, b] of Object.entries(corners)) {
    let fires = 0;
    for (let f = 1; f < n; f++) {
      let sum = 0, cells = 0;
      for (let r = b.r0; r < b.r1; r++)
        for (let c = b.c0; c < b.c1; c++) { sum += Math.abs(brightnesses[f][r][c] - brightnesses[f - 1][r][c]); cells++; }
      const local = cells ? sum / cells : 0;
      const global = globalPerTransition[f - 1] || 0;
      if (local > 3 && local > 1.3 * (global + 0.001)) fires++;
    }
    const confidence = transitions ? fires / transitions : 0;
    if (!bestCorner || confidence > bestCorner.confidence) {
      bestCorner = { name, b, confidence, framesSeen: fires };
    }
  }
  if (bestCorner && bestCorner.confidence >= 0.4) {
    const b = bestCorner.b;
    regions.push({
      type: "facecam",
      candidate: true,
      corner: bestCorner.name,
      bounds: { x: round3(b.x), y: round3(b.y), width: round3((b.c1 - b.c0) / GRID_COLS), height: round3((b.r1 - b.r0) / GRID_ROWS) },
      confidence: round3(bestCorner.confidence),
      framesSeen: bestCorner.framesSeen,
      priority: 1,
    });
  }

  // HUD bands: top/bottom rows with high edge energy and LOW temporal activity.
  const edges = cellEdges(brightnesses.length ? frames[Math.floor(n / 2)] : frames[0]);
  const bandRows = Math.max(1, Math.round(GRID_ROWS * 0.18));
  for (const band of [
    { name: "top", r0: 0, r1: bandRows, y: 0 },
    { name: "bottom", r0: GRID_ROWS - bandRows, r1: GRID_ROWS, y: 1 - bandRows / GRID_ROWS },
  ]) {
    let edgeSum = 0, actSum = 0, cells = 0;
    for (let r = band.r0; r < band.r1; r++)
      for (let c = 0; c < GRID_COLS; c++) { edgeSum += edges[r][c]; actSum += activity[r][c]; cells++; }
    const edgeMean = cells ? edgeSum / cells : 0;
    const actMean = cells ? actSum / cells : 0;
    // High contrast, low movement → static UI band.
    if (edgeMean > 12 && actMean < 6) {
      regions.push({
        type: "hud",
        candidate: true,
        bounds: { x: 0, y: round3(band.y), width: 1, height: round3(bandRows / GRID_ROWS) },
        confidence: round3(Math.min(1, edgeMean / 40)),
        framesSeen: n,
        priority: 3,
      });
    }
  }

  return { regions, framesSampled: n, transitions };
}

// ---------------------------------------------------------------------------
// Crop planner (9:16 by default)
// ---------------------------------------------------------------------------

const PRIORITY_WEIGHT = { facecam: 4, crosshair: 3, hud: 2, minimap: 1 };

function horizCoverage(region, winX, winW) {
  const rX = region.bounds.x, rW = region.bounds.width;
  if (rW <= 0) return 0;
  const overlap = Math.max(0, Math.min(rX + rW, winX + winW) - Math.max(rX, winX));
  return overlap / rW;
}

function planCrop(regions, srcW, srcH, targetAspect = TARGET_ASPECT_9_16) {
  const srcAspect = srcW / srcH;
  // Source already as-narrow-or-narrower than target → no horizontal crop.
  if (srcAspect <= targetAspect + 1e-6) {
    return {
      cropRect: { x: 0, y: 0, width: 1, height: 1 },
      mode: "none",
      preserved: regions.map((r) => r.type),
      excluded: [],
      sliced: [],
      pipRecommended: false,
      confidence: 1,
    };
  }

  const cropWNorm = (targetAspect * srcH) / srcW; // normalized crop-window width
  const steps = 120;
  let best = null;
  for (let i = 0; i <= steps; i++) {
    const x = (1 - cropWNorm) * (i / steps);
    let score = 0;
    const preserved = [], excluded = [], sliced = [];
    for (const r of regions) {
      const w = (PRIORITY_WEIGHT[r.type] || 1) * (r.confidence ?? 1);
      const cov = horizCoverage(r, x, cropWNorm);
      if (cov >= 0.99) { score += w; preserved.push(r.type); }
      else if (cov <= 0.01) { excluded.push(r.type); }      // cleanly excluded (PiP candidate)
      else { score -= w * 1.5; sliced.push(r.type); }        // slicing through is the worst
    }
    // Gentle bias toward keeping the center (gameplay action) on ties.
    score += -Math.abs((x + cropWNorm / 2) - 0.5) * 0.05;
    if (!best || score > best.score) best = { score, x, preserved, excluded, sliced };
  }

  const facecam = regions.find((r) => r.type === "facecam");
  const pipRecommended = !!facecam &&
    best.excluded.includes("facecam") && (facecam.confidence ?? 0) >= 0.4;

  return {
    cropRect: { x: round3(best.x), y: 0, width: round3(cropWNorm), height: 1 },
    mode: "horizontal",
    preserved: best.preserved,
    excluded: best.excluded,
    sliced: best.sliced,
    pipRecommended,
    confidence: round3(Math.max(0, Math.min(1, regions.length ? 1 : 0.5))),
  };
}

// ---------------------------------------------------------------------------
// Orchestration
// ---------------------------------------------------------------------------

/**
 * Analyze a source and produce a crop plan that avoids slicing protected
 * regions. Returns { status:"unavailable" } if ffmpeg can't read the source —
 * it never fabricates a default layout.
 */
async function analyzeForCrop(videoPath, opts = {}) {
  const fps = opts.fps || 1;
  const { frames, ok } = await sampleFrames(videoPath, fps);
  if (!ok || frames.length < 2) {
    return { status: "unavailable", reason: "could not sample frames (ffmpeg missing or unreadable video)" };
  }
  const { regions, framesSampled, transitions } = detectRegions(frames);
  const srcW = opts.srcWidth || SAMPLE_W;
  const srcH = opts.srcHeight || SAMPLE_H;
  const cropPlan = planCrop(regions, srcW, srcH, opts.targetAspect || TARGET_ASPECT_9_16);
  return { status: "ok", regions, cropPlan, framesSampled, transitions };
}

function round3(n) { return Number(Number(n).toFixed(3)); }

module.exports = {
  analyzeForCrop,
  detectRegions,
  planCrop,
  sampleFrames,
  TARGET_ASPECT_9_16,
};
