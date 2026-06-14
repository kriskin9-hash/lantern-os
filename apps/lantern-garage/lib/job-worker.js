// Lantern Creator Suite Job Worker
// Processes queued analysis, caption, and export jobs
// Runs async, updates progress, persists results

const fs = require("fs");
const path = require("path");
const { analyzeVideoForHighlights } = require("./highlight-engine");
const { generateVariants } = require("./retention-engine");
const { generateCaptions } = require("./caption-engine");
const { detectSafeZones } = require("./safe-zone-detector");
const { reencodeToShortForm } = require("./video-export");
const ci = require("../../../src/creator-intelligence");

class JobWorker {
  constructor(jobQueue, repoRoot) {
    this.jobQueue = jobQueue;
    this.repoRoot = repoRoot;
    this.running = false;
    this.currentJob = null;
  }

  start(intervalMs = 2000) {
    if (this.running) return;
    this.running = true;
    console.log("[job-worker] Started");

    this.loopInterval = setInterval(() => this.processNextJob(), intervalMs);
  }

  stop() {
    this.running = false;
    if (this.loopInterval) clearInterval(this.loopInterval);
    console.log("[job-worker] Stopped");
  }

  async processNextJob() {
    if (this.currentJob) return; // Already processing

    const pending = this.jobQueue.getPending();
    if (pending.length === 0) return;

    const job = pending[0];
    await this.executeJob(job);
  }

  async executeJob(job) {
    this.currentJob = job;

    try {
      job.start();
      this.jobQueue.updateJob(job);

      console.log(`[job-worker] Processing job ${job.id} (${job.type})`);

      let result;

      switch (job.type) {
        case "analyze":
          result = await processAnalyzeJob(job, this.repoRoot, (percent, msg) => {
            job.setProgress(percent, msg);
            this.jobQueue.updateJob(job);
          });
          break;

        case "caption":
          result = await processCaptionJob(job, this.repoRoot, (percent, msg) => {
            job.setProgress(percent, msg);
            this.jobQueue.updateJob(job);
          });
          break;

        case "export":
          result = await processExportJob(job, this.repoRoot, (percent, msg) => {
            job.setProgress(percent, msg);
            this.jobQueue.updateJob(job);
          });
          break;

        default:
          throw new Error(`Unknown job type: ${job.type}`);
      }

      job.complete(result);
      console.log(`[job-worker] Completed job ${job.id}`);
    } catch (error) {
      job.fail(error);
      console.error(`[job-worker] Failed job ${job.id}:`, error.message);
    } finally {
      this.jobQueue.updateJob(job);
      this.currentJob = null;
    }
  }
}

// ============================================================================
// JOB HANDLERS
// ============================================================================

async function processAnalyzeJob(job, repoRoot, updateProgress) {
  const { videoPath, options } = job.input;

  // Verify file exists
  const fullPath = path.join(repoRoot, videoPath);
  if (!fs.existsSync(fullPath)) {
    throw new Error(`Video file not found: ${videoPath}`);
  }

  updateProgress(10, "Starting video analysis");

  // Run highlight analysis
  const timeline = await analyzeVideoForHighlights(fullPath, options || {});

  updateProgress(70, "Analyzing highlights");

  // Generate variants automatically
  const variants = generateVariants(timeline);
  updateProgress(85, "Generated 3 variants");

  // Generate captions automatically
  const captions = generateCaptions(timeline, null, "gaming");
  updateProgress(95, "Generated captions");

  // Store results
  const resultsDir = path.join(repoRoot, "data", "creator", "analyses");
  if (!fs.existsSync(resultsDir)) {
    fs.mkdirSync(resultsDir, { recursive: true });
  }

  const resultFile = path.join(resultsDir, `${job.id}-results.json`);
  const results = {
    jobId: job.id,
    videoPath,
    analysisTimestamp: new Date().toISOString(),
    timeline: timeline.toJSON(),
    variants: variants.map((v) => v.toJSON()),
    captions: captions.map((c) => c.toJSON()),
  };

  fs.writeFileSync(resultFile, JSON.stringify(results, null, 2));

  updateProgress(100, "Analysis complete");

  return {
    timeline: timeline.toJSON(),
    variants: variants.map((v) => v.toJSON()),
    captions: captions.map((c) => c.toJSON()),
    resultsFile: resultFile,
  };
}

async function processCaptionJob(job, repoRoot, updateProgress) {
  const { highlightTimeline, strategy } = job.input;

  updateProgress(20, "Parsing timeline");

  // Generate captions with specified strategy
  const captions = generateCaptions(highlightTimeline, null, strategy || "gaming");

  updateProgress(60, `Generated ${captions.length} captions`);

  // Store captions in multiple formats
  const captionsDir = path.join(repoRoot, "data", "creator", "captions");
  if (!fs.existsSync(captionsDir)) {
    fs.mkdirSync(captionsDir, { recursive: true });
  }

  const vttPath = path.join(captionsDir, `${job.id}.vtt`);
  const srtPath = path.join(captionsDir, `${job.id}.srt`);
  const jsonPath = path.join(captionsDir, `${job.id}.json`);

  const { generateVTT, generateSRT, generateJSON } = require("./caption-engine");
  fs.writeFileSync(vttPath, generateVTT(captions));
  fs.writeFileSync(srtPath, generateSRT(captions));
  fs.writeFileSync(jsonPath, generateJSON(captions));

  updateProgress(100, "Captions saved");

  return {
    captionCount: captions.length,
    files: { vtt: vttPath, srt: srtPath, json: jsonPath },
  };
}

async function processExportJob(job, repoRoot, updateProgress) {
  const { videoPath, variant, format } = job.input;

  updateProgress(10, `Starting export (${format})`);

  // Verify video exists
  const fullPath = path.join(repoRoot, videoPath);
  if (!fs.existsSync(fullPath)) {
    throw new Error(`Video not found: ${videoPath}`);
  }

  // Create export directory
  const exportsDir = path.join(repoRoot, "data", "creator", "exports");
  if (!fs.existsSync(exportsDir)) {
    fs.mkdirSync(exportsDir, { recursive: true });
  }

  updateProgress(30, "Re-encoding to short-form (1080x1920)");

  const exportFile = path.join(exportsDir, `${job.id}-${format}.mp4`);

  // Real re-encode to short-form spec. Mapping/fps/duration are overridable via
  // job.input; defaults produce exact 1080x1920, h264 + aac, <=60s, +faststart.
  const encodeInfo = await reencodeToShortForm(fullPath, exportFile, {
    width: job.input.width,
    height: job.input.height,
    fps: job.input.fps,
    fit: job.input.fit, // pad (default) | crop | blur
    start: job.input.start,
    duration: job.input.duration,
    maxDuration: job.input.maxDuration,
  });

  updateProgress(90, "Validating output");

  // Verify output exists
  if (!fs.existsSync(exportFile)) {
    throw new Error("Export file was not created");
  }

  // ── Quality gate (Phase 7): validate with real ffprobe before completing ──
  // If the export does not meet short-form spec, block it: delete the invalid
  // file and fail the job with the concrete reasons. Honors exportValidator flag.
  const validation = await ci.validateExport(exportFile, job.input.validation || {});
  if (!validation.ok && !validation.skipped) {
    try { fs.unlinkSync(exportFile); } catch { /* best-effort cleanup */ }
    const reasons = (validation.blockedReasons || []).join("; ") || "did not meet short-form spec";
    throw new Error(`Export blocked by ExportValidator: ${reasons}`);
  }

  const stats = fs.statSync(exportFile);

  updateProgress(100, "Export complete");

  return {
    format,
    exportFile,
    size: stats.size,
    created: stats.birthtime,
    encode: encodeInfo,
    validation,
  };
}

async function processJob(job, repoRoot) {
  // Standalone job processor (used by single-job handlers)
  const worker = new JobWorker(null, repoRoot);
  await worker.executeJob(job);
  return job;
}
module.exports = {
  JobWorker,
  processJob,
};
