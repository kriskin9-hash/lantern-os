// Score V10 orchestrator — one call that produces the full V10 scoring bundle
// for an analyzed clip: structural viral score, optional gaming score, retention
// prediction, and editor grade. Every number is computed from real analysis
// signals; nothing is mocked.
//
// Spec: "V10 SCORING ENGINE REDESIGN" Phases 2-4, 8.

"use strict";

const { viralScoreV10 } = require("./viral-score-v10");
const { gamingScoreV10 } = require("./gaming-score-v10");
const { retentionPredictV10 } = require("./retention-predictor-v10");
const { editorGradeV10 } = require("./editor-grade");

/**
 * @param {Object} analysis  HighlightTimeline.toJSON()-shaped: { duration, highlights[] }
 * @param {Object} opts       { gaming, safeZones, cropPlan }
 *   - gaming:    boolean — also compute the gaming-specific score
 *   - safeZones: SafeZoneDetectorV2 region output (for facecam-based reaction)
 *   - cropPlan:  SafeZoneDetectorV2 crop plan (for safe-zone compliance in grade)
 */
function scoreVideoV10(analysis = {}, opts = {}) {
  const viral = viralScoreV10(analysis);
  const retention = retentionPredictV10(viral);
  const grade = editorGradeV10(viral, { cropPlan: opts.cropPlan });

  const result = {
    version: "10.0",
    basis: "structural_heuristic",
    calibrated: false,
    viral,
    retention,
    editorGrade: grade,
    computedAt: new Date().toISOString(),
  };

  if (opts.gaming) {
    result.gaming = gamingScoreV10(viral, { safeZones: opts.safeZones, facecamPresent: opts.facecamPresent });
  }

  // Top-level headline numbers for convenience (all traceable to the above).
  result.headline = {
    viralScore: viral.viralScore,
    gamingViralScore: opts.gaming ? result.gaming.gamingViralScore : null,
    predictedCompletionRate: retention.predictedCompletionRate,
    predictedShareRate: retention.predictedShareRate,
    editorGrade: grade.grade,
    confidence: viral.confidence,
  };

  return result;
}

module.exports = { scoreVideoV10 };
