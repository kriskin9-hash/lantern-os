// Short-form video export (real ffmpeg re-encode)
// Converts an arbitrary source clip into an output that conforms to the
// short-form spec checked by the ExportValidator:
//   exact target resolution (default 1080x1920), h264 video, aac audio present,
//   target fps, duration clamped to the max window, +faststart.
//
// Modes (how the source aspect is mapped into 9:16):
//   "pad"  (default) scale-to-fit + black bars  — never crops content
//   "crop"            scale-to-cover + center crop — fills frame, may crop edges
//   "blur"            blurred-cover background + fitted foreground — "shorts" look
//
// Honesty note: this re-encodes real pixels/audio. It does NOT fabricate
// duration — a source shorter than the minimum stays short, and the validator
// will honestly block it. We only TRIM sources longer than the max window.

"use strict";

const fs = require("fs");
const path = require("path");
const { spawn } = require("child_process");

const DEFAULTS = {
  width: 1080,
  height: 1920,
  fps: 30, // >= validator minFps; pass fps:60 to match the 60fps target
  fit: "pad", // pad | crop | blur
  maxDuration: 60, // trim sources longer than this
  crf: 20,
  preset: "veryfast",
  audioBitrate: "128k",
  sampleRate: 44100,
  timeoutMs: 10 * 60 * 1000,
};

/**
 * Probe a source for the basics we need to plan the encode.
 * @returns {Promise<{duration:number|null, hasAudio:boolean, width:number|null, height:number|null}>}
 */
function probeSource(inputPath) {
  return new Promise((resolve) => {
    let proc;
    try {
      proc = spawn("ffprobe", [
        "-v", "error", "-print_format", "json",
        "-show_format", "-show_streams", inputPath,
      ]);
    } catch {
      return resolve({ duration: null, hasAudio: false, width: null, height: null });
    }
    let out = "";
    proc.stdout.on("data", (d) => { out += d.toString(); });
    proc.stderr.on("data", () => {});
    proc.on("error", () => resolve({ duration: null, hasAudio: false, width: null, height: null }));
    proc.on("close", () => {
      try {
        const data = JSON.parse(out);
        const streams = Array.isArray(data.streams) ? data.streams : [];
        const v = streams.find((s) => s.codec_type === "video");
        const hasAudio = streams.some((s) => s.codec_type === "audio");
        const duration = data.format && Number.isFinite(Number(data.format.duration))
          ? Number(data.format.duration) : null;
        resolve({ duration, hasAudio, width: v ? v.width : null, height: v ? v.height : null });
      } catch {
        resolve({ duration: null, hasAudio: false, width: null, height: null });
      }
    });
  });
}

/**
 * Build the video filtergraph for a given fit mode.
 * Returns { vf } for simple modes or { filterComplex, mapV } for blur.
 */
function buildVideoFilter(fit, w, h, fps) {
  const fpsEnd = `fps=${fps},format=yuv420p,setsar=1`;
  if (fit === "crop") {
    return { vf: `scale=${w}:${h}:force_original_aspect_ratio=increase,crop=${w}:${h},${fpsEnd}` };
  }
  if (fit === "blur") {
    return {
      filterComplex:
        `[0:v]split=2[bg][fg];` +
        `[bg]scale=${w}:${h}:force_original_aspect_ratio=increase,crop=${w}:${h},boxblur=20:2[bgb];` +
        `[fg]scale=${w}:${h}:force_original_aspect_ratio=decrease[fgs];` +
        `[bgb][fgs]overlay=(W-w)/2:(H-h)/2,${fpsEnd}[vout]`,
      mapV: "[vout]",
    };
  }
  // default: pad (scale-to-fit + black bars) — never crops content
  return {
    vf: `scale=${w}:${h}:force_original_aspect_ratio=decrease,` +
        `pad=${w}:${h}:(ow-iw)/2:(oh-ih)/2:color=black,${fpsEnd}`,
  };
}

/**
 * Re-encode a source video to a short-form-conforming output.
 * @param {string} inputPath  absolute path to source
 * @param {string} outputPath absolute path to write
 * @param {Object} options    overrides for DEFAULTS + optional { start, duration }
 * @returns {Promise<{outputPath, durationTarget, fit, hadAudioSource, fps, width, height}>}
 */
async function reencodeToShortForm(inputPath, outputPath, options = {}) {
  const cfg = { ...DEFAULTS, ...options };
  if (!fs.existsSync(inputPath)) {
    throw new Error(`source not found: ${inputPath}`);
  }
  fs.mkdirSync(path.dirname(outputPath), { recursive: true });

  const meta = await probeSource(inputPath);

  // Plan duration: trim only when the source exceeds the max window.
  // An explicit options.duration wins (clamped to the max).
  let durationTarget = null;
  if (Number.isFinite(Number(options.duration))) {
    durationTarget = Math.min(Number(options.duration), cfg.maxDuration);
  } else if (meta.duration && meta.duration > cfg.maxDuration) {
    durationTarget = cfg.maxDuration;
  }
  const start = Number.isFinite(Number(options.start)) ? Number(options.start) : null;

  const { vf, filterComplex, mapV } = buildVideoFilter(cfg.fit, cfg.width, cfg.height, cfg.fps);

  // Assemble ffmpeg args.
  const args = ["-y"];
  if (start !== null) args.push("-ss", String(start));
  args.push("-i", inputPath);

  // If the source has no audio, synthesize a silent track so the output has
  // an audio stream (the validator requires one). Sized to the encode length.
  const needSilentAudio = !meta.hasAudio;
  if (needSilentAudio) {
    args.push("-f", "lavfi", "-i",
      `anullsrc=channel_layout=stereo:sample_rate=${cfg.sampleRate}`);
  }

  if (durationTarget !== null) args.push("-t", String(durationTarget));

  // Video filtergraph
  if (filterComplex) {
    args.push("-filter_complex", filterComplex, "-map", mapV);
  } else {
    args.push("-vf", vf, "-map", "0:v:0");
  }

  // Audio mapping
  if (needSilentAudio) {
    args.push("-map", `${filterComplex ? 1 : 1}:a:0`);
  } else {
    args.push("-map", "0:a:0?"); // optional in case probe was wrong
  }

  args.push(
    "-r", String(cfg.fps),
    "-c:v", "libx264", "-preset", cfg.preset, "-crf", String(cfg.crf),
    "-pix_fmt", "yuv420p",
    "-c:a", "aac", "-b:a", cfg.audioBitrate, "-ar", String(cfg.sampleRate),
    "-movflags", "+faststart",
  );
  if (needSilentAudio) args.push("-shortest");
  args.push(outputPath);

  await runFfmpeg(args, cfg.timeoutMs);

  if (!fs.existsSync(outputPath)) {
    throw new Error("ffmpeg completed but output file was not created");
  }

  return {
    outputPath,
    durationTarget,
    fit: cfg.fit,
    hadAudioSource: meta.hasAudio,
    fps: cfg.fps,
    width: cfg.width,
    height: cfg.height,
  };
}

function runFfmpeg(args, timeoutMs) {
  return new Promise((resolve, reject) => {
    let proc;
    try {
      proc = spawn("ffmpeg", args, { stdio: ["ignore", "ignore", "pipe"] });
    } catch (e) {
      return reject(new Error(`failed to spawn ffmpeg: ${e.message}`));
    }
    let stderr = "";
    let settled = false;
    proc.stderr.on("data", (d) => {
      stderr += d.toString();
      if (stderr.length > 8000) stderr = stderr.slice(-8000); // keep tail only
    });
    const timer = setTimeout(() => {
      if (settled) return;
      settled = true;
      proc.kill("SIGKILL");
      reject(new Error("ffmpeg re-encode timed out"));
    }, timeoutMs);
    proc.on("error", (e) => {
      if (settled) return;
      settled = true;
      clearTimeout(timer);
      reject(new Error(`ffmpeg error: ${e.message}`));
    });
    proc.on("close", (code) => {
      if (settled) return;
      settled = true;
      clearTimeout(timer);
      if (code === 0) return resolve();
      reject(new Error(`ffmpeg exited ${code}: ${stderr.split("\n").slice(-4).join(" | ").trim()}`));
    });
  });
}

module.exports = { reencodeToShortForm, probeSource, DEFAULTS };
