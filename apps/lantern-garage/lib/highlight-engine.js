// Lantern V8 AI Highlight Engine
// Analyzes video content for highlights, motion, reactions, and key moments
// Output: HighlightTimeline with scored segments

const fs = require("fs");
const path = require("path");
const { spawn } = require("child_process");

// ============================================================================
// DATA STRUCTURES
// ============================================================================

class HighlightTimeline {
  constructor(videoPath, duration, fps = 30) {
    this.videoPath = videoPath;
    this.duration = duration;
    this.fps = fps;
    this.highlights = [];
    this.metadata = {
      analyzedAt: new Date().toISOString(),
      version: "8.0",
    };
  }

  addHighlight(start, end, score, reason, tags = []) {
    this.highlights.push({
      start: Number(start.toFixed(1)),
      end: Number(end.toFixed(1)),
      duration: Number((end - start).toFixed(1)),
      score: Number(score.toFixed(2)),
      reason,
      tags,
    });
  }

  sort() {
    this.highlights.sort((a, b) => a.start - b.start);
    return this;
  }

  getTopHighlights(count = 5) {
    return [...this.highlights].sort((a, b) => b.score - a.score).slice(0, count);
  }

  toJSON() {
    return {
      videoPath: this.videoPath,
      duration: this.duration,
      fps: this.fps,
      highlights: this.highlights,
      topHighlights: this.getTopHighlights(5),
      metadata: this.metadata,
    };
  }
}

// ============================================================================
// MAIN ANALYSIS FUNCTION
// ============================================================================

async function analyzeVideoForHighlights(videoPath, options = {}) {
  const {
    fps = 5, // sample every 1/5th second
    motionThreshold = 0.15,
    audioThreshold = 0.7,
    sceneThreshold = 0.3,
    minHighlightDuration = 1.0,
    maxHighlightDuration = 30.0,
  } = options;

  // Get video metadata
  const metadata = await getVideoMetadata(videoPath);
  if (!metadata) {
    throw new Error(`Could not read video: ${videoPath}`);
  }

  const timeline = new HighlightTimeline(videoPath, metadata.duration, fps);

  // Analyze video streams
  const [motionFrames, audioSpikes, sceneChanges] = await Promise.all([
    detectMotion(videoPath, fps, motionThreshold),
    detectAudioSpikes(videoPath, fps, audioThreshold),
    detectSceneChanges(videoPath, fps, sceneThreshold),
  ]);

  // Merge and score highlights
  const highlights = mergeDetections(
    motionFrames,
    audioSpikes,
    sceneChanges,
    fps,
    minHighlightDuration,
    maxHighlightDuration
  );

  highlights.forEach((hl) => {
    timeline.addHighlight(hl.start, hl.end, hl.score, hl.reason, hl.tags);
  });

  timeline.sort();
  return timeline;
}

// ============================================================================
// MOTION DETECTION
// ============================================================================

async function detectMotion(videoPath, fps = 5, threshold = 0.15) {
  const frames = [];

  return new Promise((resolve, reject) => {
    const args = [
      "-i",
      videoPath,
      "-vf",
      `fps=${fps},scale=160:90`, // Downsample for speed
      "-f",
      "rawvideo",
      "-pix_fmt",
      "rgb24",
      "-",
    ];

    const ffmpeg = spawn("ffmpeg", args);
    let frameData = Buffer.alloc(0);
    let lastFrame = null;

    ffmpeg.stdout.on("data", (chunk) => {
      frameData = Buffer.concat([frameData, chunk]);
      const frameSize = 160 * 90 * 3; // RGB24

      while (frameData.length >= frameSize) {
        const frame = frameData.slice(0, frameSize);
        frameData = frameData.slice(frameSize);

        if (lastFrame) {
          const motion = calculateMotion(lastFrame, frame);
          if (motion > threshold) {
            frames.push({
              timestamp: frames.length / fps,
              motion,
            });
          }
        }

        lastFrame = frame;
      }
    });

    ffmpeg.stderr.on("data", () => {}); // Suppress ffmpeg output
    ffmpeg.on("close", (code) => {
      if (code === 0) {
        resolve(frames);
      } else {
        reject(new Error(`FFmpeg failed with code ${code}`));
      }
    });

    ffmpeg.on("error", reject);
  });
}

function calculateMotion(frame1, frame2) {
  let diff = 0;
  for (let i = 0; i < frame1.length; i += 3) {
    const dr = Math.abs(frame1[i] - frame2[i]);
    const dg = Math.abs(frame1[i + 1] - frame2[i + 1]);
    const db = Math.abs(frame1[i + 2] - frame2[i + 2]);
    diff += (dr + dg + db) / 3;
  }
  return diff / frame1.length;
}

// ============================================================================
// AUDIO SPIKE DETECTION
// ============================================================================

async function detectAudioSpikes(videoPath, fps = 5, threshold = 0.7) {
  return new Promise((resolve) => {
    // Extract audio and analyze loudness
    const audioArgs = [
      "-i",
      videoPath,
      "-vn",
      "-acodec",
      "pcm_s16le",
      "-ar",
      "16000",
      "-ac",
      "1",
      "-f",
      "s16le",
      "-",
    ];

    const ffmpeg = spawn("ffmpeg", audioArgs);
    const audioFrames = [];
    let audioBuffer = Buffer.alloc(0);

    ffmpeg.stdout.on("data", (chunk) => {
      audioBuffer = Buffer.concat([audioBuffer, chunk]);

      const samplesPerFrame = 16000 / fps;
      const bytesPerSample = 2;
      const bytesPerFrame = samplesPerFrame * bytesPerSample;

      while (audioBuffer.length >= bytesPerFrame) {
        const frameData = audioBuffer.slice(0, bytesPerFrame);
        audioBuffer = audioBuffer.slice(bytesPerFrame);

        const loudness = calculateLoudness(frameData);
        if (loudness > threshold) {
          audioFrames.push({
            timestamp: audioFrames.length / fps,
            loudness,
          });
        }
      }
    });

    ffmpeg.stderr.on("data", () => {});
    ffmpeg.on("close", () => {
      resolve(audioFrames);
    });
    ffmpeg.on("error", () => {
      resolve([]); // Fail gracefully
    });
  });
}

function calculateLoudness(pcmData) {
  let sum = 0;
  for (let i = 0; i < pcmData.length; i += 2) {
    const sample = pcmData.readInt16LE(i);
    sum += Math.abs(sample);
  }
  const rms = Math.sqrt(sum / (pcmData.length / 2));
  return Math.min(1, rms / 32768); // Normalize to 0-1
}

// ============================================================================
// SCENE DETECTION
// ============================================================================

async function detectSceneChanges(videoPath, fps = 5, threshold = 0.3) {
  const frames = [];

  return new Promise((resolve) => {
    const args = [
      "-i",
      videoPath,
      "-vf",
      `fps=${fps},scale=160:90`,
      "-f",
      "rawvideo",
      "-pix_fmt",
      "rgb24",
      "-",
    ];

    const ffmpeg = spawn("ffmpeg", args);
    let frameData = Buffer.alloc(0);
    let lastFrame = null;
    let frameCount = 0;

    ffmpeg.stdout.on("data", (chunk) => {
      frameData = Buffer.concat([frameData, chunk]);
      const frameSize = 160 * 90 * 3;

      while (frameData.length >= frameSize) {
        const frame = frameData.slice(0, frameSize);
        frameData = frameData.slice(frameSize);

        if (lastFrame) {
          const diff = calculateHistogramDifference(lastFrame, frame);
          if (diff > threshold) {
            frames.push({
              timestamp: frameCount / fps,
              difference: diff,
            });
          }
        }

        lastFrame = frame;
        frameCount++;
      }
    });

    ffmpeg.stderr.on("data", () => {});
    ffmpeg.on("close", () => {
      resolve(frames);
    });
    ffmpeg.on("error", () => {
      resolve([]);
    });
  });
}

function calculateHistogramDifference(frame1, frame2) {
  const hist1 = buildHistogram(frame1);
  const hist2 = buildHistogram(frame2);

  let chi2 = 0;
  for (let i = 0; i < 256; i++) {
    const diff = hist1[i] - hist2[i];
    if (hist1[i] + hist2[i] > 0) {
      chi2 += (diff * diff) / (hist1[i] + hist2[i]);
    }
  }
  return Math.min(1, chi2 / 256);
}

function buildHistogram(frame) {
  const hist = new Array(256).fill(0);
  for (let i = 0; i < frame.length; i += 3) {
    const gray = (frame[i] + frame[i + 1] + frame[i + 2]) / 3;
    hist[Math.floor(gray)]++;
  }
  return hist;
}

// ============================================================================
// SCORING & MERGING
// ============================================================================

function mergeDetections(
  motionFrames,
  audioFrames,
  sceneFrames,
  fps,
  minDuration,
  maxDuration
) {
  const candidates = [];

  // Find peaks in motion
  for (let i = 0; i < motionFrames.length; i++) {
    const frame = motionFrames[i];
    const audioMatch = audioFrames.find(
      (a) => Math.abs(a.timestamp - frame.timestamp) < 0.5
    );
    const sceneMatch = sceneFrames.find(
      (s) => Math.abs(s.timestamp - frame.timestamp) < 0.5
    );

    let score = frame.motion;
    let reason = "motion";
    const tags = ["motion"];

    if (audioMatch) {
      score = Math.max(score, audioMatch.loudness);
      reason += " + audio";
      tags.push("audio");
    }

    if (sceneMatch) {
      score = Math.max(score, sceneMatch.difference);
      reason += " + scene";
      tags.push("scene");
    }

    candidates.push({
      timestamp: frame.timestamp,
      score,
      reason,
      tags,
    });
  }

  // Group adjacent candidates into highlights
  const highlights = [];
  let current = null;

  for (const cand of candidates) {
    if (!current) {
      current = { start: cand.timestamp, end: cand.timestamp, score: cand.score, reason: cand.reason, tags: cand.tags };
    } else if (cand.timestamp - current.end < 0.5) {
      current.end = cand.timestamp;
      current.score = Math.max(current.score, cand.score);
    } else {
      if (current.end - current.start >= minDuration && current.end - current.start <= maxDuration) {
        highlights.push(current);
      }
      current = { start: cand.timestamp, end: cand.timestamp, score: cand.score, reason: cand.reason, tags: cand.tags };
    }
  }

  if (
    current &&
    current.end - current.start >= minDuration &&
    current.end - current.start <= maxDuration
  ) {
    highlights.push(current);
  }

  return highlights;
}

function scoreHighlight(motion, audio, scene, weights = {}) {
  const w = { motion: 0.4, audio: 0.4, scene: 0.2, ...weights };
  return (
    motion * w.motion + audio * w.audio + scene * w.scene
  );
}

// ============================================================================
// UTILITIES
// ============================================================================

async function getVideoMetadata(videoPath) {
  return new Promise((resolve) => {
    const ffprobe = spawn("ffprobe", [
      "-v",
      "error",
      "-show_entries",
      "format=duration",
      "-of",
      "default=noprint_wrappers=1:nokey=1:nokey=1",
      videoPath,
    ]);

    let output = "";
    ffprobe.stdout.on("data", (data) => {
      output += data.toString();
    });

    ffprobe.on("close", (code) => {
      if (code === 0) {
        const duration = parseFloat(output.trim());
        resolve({
          duration: isNaN(duration) ? 0 : duration,
          fps: 30, // Default assumption
        });
      } else {
        resolve(null);
      }
    });

    ffprobe.on("error", () => {
      resolve(null);
    });
  });
}

module.exports = {
  analyzeVideoForHighlights,
  HighlightTimeline,
  detectMotion,
  detectAudioSpikes,
  detectSceneChanges,
  scoreHighlight,
};
