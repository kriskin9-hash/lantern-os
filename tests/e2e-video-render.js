#!/usr/bin/env node
// Render-guarantee E2E test. Proves the pipeline can NEVER dead-end on
// "Top variant has no segments to render", and that a real, playable, portrait
// mp4 is produced. Drives the real backend (no mocks).
//
// Usage: node tests/e2e-video-render.js
//   reuses tests/assets/test-video.mp4 (run scripts/test_creator_pipeline.js once
//   to generate it, or it will be created here if a source is available).

const path = require("path");
const fs = require("fs");
const os = require("os");
const { spawnSync } = require("child_process");

const repoRoot = process.cwd();
const entryStore = require("../apps/lantern-garage/lib/entry-store");
const { JobQueue } = require("../apps/lantern-garage/lib/job-queue");
const { JobWorker } = require("../apps/lantern-garage/lib/job-worker");
const { generateVariantsV10 } = require("../src/creator-intelligence");

process.env.LANTERN_JOB_IDLE_TIMEOUT_MS = process.env.LANTERN_JOB_IDLE_TIMEOUT_MS || "1800000";

const out = [];
function check(name, ok, detail) { out.push({ name, ok, detail }); console.log(`${ok ? "PASS" : "FAIL"}  ${name}${detail ? "  — " + detail : ""}`); if (!ok) process.exitCode = 1; }

function ensureAsset() {
  const asset = path.join(repoRoot, "tests", "assets", "test-video.mp4");
  if (fs.existsSync(asset) && fs.statSync(asset).size > 100000) return asset;
  fs.mkdirSync(path.dirname(asset), { recursive: true });
  const realSrc = path.join(repoRoot, "data", "dreamer", "videos", "1781483831769-2025-12-08 20-45-57.mkv");
  const args = fs.existsSync(realSrc)
    ? ["-y", "-ss", "300", "-i", realSrc, "-t", "30", "-c:v", "libx264", "-preset", "veryfast", "-crf", "26", "-c:a", "aac", asset]
    : ["-y", "-f", "lavfi", "-i", "testsrc=size=1280x720:rate=30:duration=30", "-f", "lavfi", "-i", "sine=frequency=440:duration=30", "-c:v", "libx264", "-preset", "veryfast", "-c:a", "aac", asset];
  spawnSync("ffmpeg", args, { stdio: "ignore" });
  return asset;
}

// 16x16 grayscale frame buffer at a timestamp (for black/frozen checks).
// Crop the center band first so letterbox pad bars (9:16 of a 16:9 source) do
// not dominate the measurement — we want the actual content, not the bars.
function frameGray(video, atSec) {
  const tmp = path.join(os.tmpdir(), `f_${Date.now()}_${Math.random().toString(36).slice(2)}.raw`);
  const r = spawnSync("ffmpeg", ["-y", "-ss", String(atSec), "-i", video, "-frames:v", "1", "-vf", "crop=iw:ih/3:0:ih/3,scale=16:16,format=gray", "-f", "rawvideo", "-pix_fmt", "gray", tmp], { stdio: "ignore" });
  if (r.status !== 0 || !fs.existsSync(tmp)) return null;
  const buf = fs.readFileSync(tmp); try { fs.unlinkSync(tmp); } catch {}
  return buf;
}
// Brightest pixel in the content band — a black render is ~0, any real content
// has bright pixels even in a dark scene (HUD, highlights, edges).
const maxLuma = (buf) => (buf && buf.length) ? Math.max(...buf) : 0;
function bufDiff(a, b) { if (!a || !b || a.length !== b.length) return 999; let d = 0; for (let i = 0; i < a.length; i++) d += Math.abs(a[i] - b[i]); return d / a.length; }

async function main() {
  const assetAbs = ensureAsset();
  const videoPath = path.relative(repoRoot, assetAbs).split(path.sep).join("/");

  // ── Structural guarantee: empty highlights -> variants STILL have segments ──
  const emptyVariants = generateVariantsV10({ duration: 40, highlights: [] }, { gaming: true });
  check("Degraded path: empty highlights still yields variants with segments",
    emptyVariants.variants.length >= 3 && emptyVariants.variants.every((v) => v.segments.length > 0),
    `usedFallback=${emptyVariants.usedFallback} segs=[${emptyVariants.variants.map((v) => v.segments.length).join(",")}]`);

  // ── Full pipeline render ───────────────────────────────────────────────────
  const queue = new JobQueue(repoRoot);
  const worker = new JobWorker(queue, repoRoot);
  const entry = entryStore.createEntry(repoRoot, { title: "E2E Render Test", filePath: videoPath, type: "video" });

  const aJob = queue.enqueue("analyze", { videoPath, entryId: entry.id, options: { gaming: true } });
  await worker.executeJob(aJob);
  const analysis = entryStore.getAnalysis(repoRoot, entry.id) || {};
  const reloaded = entryStore.getEntry(repoRoot, entry.id);
  const hls = analysis.highlights || [];
  check("Analyze produces segments (>0)", hls.length > 0, `count=${hls.length}`);
  check("analysis.debug present", !!(analysis.debug && analysis.debug.segmentCount != null),
    analysis.debug ? JSON.stringify(analysis.debug) : "missing");

  const variants = reloaded.variantsV10 || [];
  check("Variants A/B/C exist with segments", variants.length >= 3 && variants.slice(0, 3).every((v) => v.segments.length > 0),
    `variants=${variants.length}`);
  const top = variants.find((v) => v.rank === 1) || variants[0];

  const eJob = queue.enqueue("export", { videoPath, entryId: entry.id, renderKey: top.id, segments: top.segments, format: "9:16", fit: "pad", burnCaptions: false, validation: {} });
  await worker.executeJob(eJob);
  const er = eJob.result || {};
  const outFile = er.exportFile;
  check("Render output mp4 exists", !!(outFile && fs.existsSync(outFile)), outFile || "none");
  check("Render size > 1MB", er.size > 1024 * 1024, er.size ? (er.size / 1048576).toFixed(2) + "MB" : "?");

  // ffprobe: dimensions + duration
  let w = 0, h = 0, dur = 0;
  if (outFile && fs.existsSync(outFile)) {
    const p = spawnSync("ffprobe", ["-v", "error", "-select_streams", "v:0", "-show_entries", "stream=width,height:format=duration", "-of", "default=nw=1", outFile], { encoding: "utf8" });
    const text = p.stdout || "";
    w = +(text.match(/width=(\d+)/) || [])[1] || 0;
    h = +(text.match(/height=(\d+)/) || [])[1] || 0;
    dur = +(text.match(/duration=([\d.]+)/) || [])[1] || 0;
  }
  check("Duration > 0", dur > 0, `${dur.toFixed(1)}s`);
  check("Portrait 1080x1920", w === 1080 && h === 1920, `${w}x${h}`);

  // ── Phase 6: watch the output — not black, not frozen ──────────────────────
  if (outFile && fs.existsSync(outFile) && dur > 0) {
    const f1 = frameGray(outFile, Math.max(0.1, dur * 0.1));
    const f2 = frameGray(outFile, dur * 0.5);
    const f3 = frameGray(outFile, dur * 0.9);
    const lumas = [f1, f2, f3].map(maxLuma);
    check("Frames are not black", lumas.every((l) => l > 16), `maxLuma=[${lumas.map((l) => l.toFixed(0)).join(",")}]`);
    const d12 = bufDiff(f1, f2), d23 = bufDiff(f2, f3);
    check("Video is not frozen", (d12 + d23) > 2, `framediff=${(d12 + d23).toFixed(1)}`);
  } else {
    check("Frames are not black", false, "no output to inspect");
  }

  // ── Phase 7: render report exists ──────────────────────────────────────────
  const reportPath = path.join(entryStore.getEntryDir(repoRoot, entry.id), "renders", "report.json");
  let report = null; try { report = JSON.parse(fs.readFileSync(reportPath, "utf8")); } catch {}
  check("Render report.json written", !!(report && report.rendered === true && report.segments > 0),
    report ? `variant=${report.variant} segments=${report.segments} duration=${report.duration}` : "missing");

  const passed = out.filter((r) => r.ok).length;
  console.log(`\n${passed}/${out.length} checks passed`);
}

main().catch((e) => { console.error("driver error:", e); process.exit(1); });
