// Editor Quality Score V10 — assigns every generated Short a letter grade
// (A+ / A / B / C / D) from real component scores: retention, clarity, hook,
// captions, and safe-zone compliance. Deterministic thresholds; real inputs only.
//
// Spec: "V10 SCORING ENGINE REDESIGN" Phase 8.

"use strict";

const { clamp01 } = require("./viral-score-v10");

function round3(x) { return Number(Number(x).toFixed(3)); }

// Cropping that removes the facecam or crosshair is a real compliance failure.
// A full-width HUD being NARROWED by a vertical crop is unavoidable and not a
// failure, so it is not counted against the grade.
const CRITICAL_PROTECTED = ["facecam", "crosshair"];

function complianceFromCropPlan(cropPlan) {
  if (!cropPlan || cropPlan.mode === "none") {
    return { value: 1, source: "no-crop", note: "no crop performed; nothing removed" };
  }
  const sliced = (cropPlan.sliced || []).filter((t) => CRITICAL_PROTECTED.includes(t));
  let value = 1;
  if (sliced.length) value -= 0.5;        // sliced a facecam/crosshair
  if (cropPlan.pipRecommended) value -= 0.1; // facecam couldn't fit -> needs PiP
  return { value: clamp01(value), source: "crop-plan", slicedCritical: sliced, pipRecommended: !!cropPlan.pipRecommended };
}

const WEIGHTS = { retention: 0.30, hook: 0.25, clarity: 0.15, captions: 0.15, safeZone: 0.15 };

function letter(composite) {
  if (composite >= 0.90) return "A+";
  if (composite >= 0.80) return "A";
  if (composite >= 0.65) return "B";
  if (composite >= 0.50) return "C";
  return "D";
}

/**
 * @param {Object} viralResult  output of viralScoreV10 (componentScores)
 * @param {Object} opts         { cropPlan } from SafeZoneDetectorV2 (optional)
 */
function editorGradeV10(viralResult = {}, opts = {}) {
  const comp = {};
  for (const [k, v] of Object.entries(viralResult.componentScores || {})) comp[k] = v.score || 0;

  const compliance = complianceFromCropPlan(opts.cropPlan);

  const factors = {
    retention: comp.retention || 0,
    hook: comp.hook || 0,
    clarity: comp.visualClarity || 0,
    captions: comp.captionPotential || 0,
    safeZone: compliance.value,
  };

  const composite = clamp01(
    factors.retention * WEIGHTS.retention +
      factors.hook * WEIGHTS.hook +
      factors.clarity * WEIGHTS.clarity +
      factors.captions * WEIGHTS.captions +
      factors.safeZone * WEIGHTS.safeZone
  );

  return {
    grade: letter(composite),
    composite: round3(composite),
    factors: {
      retention: round3(factors.retention),
      hook: round3(factors.hook),
      clarity: round3(factors.clarity),
      captions: round3(factors.captions),
      safeZone: round3(factors.safeZone),
    },
    safeZoneCompliance: compliance,
    confidence: round3(viralResult.confidence || 0),
    weights: WEIGHTS,
    computedAt: new Date().toISOString(),
  };
}

module.exports = { editorGradeV10, complianceFromCropPlan };
