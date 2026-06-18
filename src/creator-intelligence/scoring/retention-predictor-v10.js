// Retention Predictor V10
//
// HONESTY: these are bounded STRUCTURAL-HEURISTIC estimates — deterministic
// functions of the component scores measured from the user's own clip. They are
// NOT outcome-calibrated predictions of real-world performance. Output always
// carries calibrated:false and a disclaimer so the UI shows the qualifier.
// It only switches to calibrated mode when outcome-labeled EditEvents exist in
// data/creator-intelligence/edits (none ship by default), so we never present
// a fabricated "92% completion" as a real prediction.
//
// Spec: "V10 SCORING ENGINE REDESIGN" Phase 4.

"use strict";

const MODEL = require("../research/retention_signals.json");
const store = require("../dataset/dataset-store");

function clamp(x, [lo, hi]) { return Math.max(lo, Math.min(hi, x)); }
function round3(x) { return Number(Number(x).toFixed(3)); }
function pct(x) { return Math.round(x * 100); }

/**
 * How many first-party edit events carry a real outcome (e.g. actual views
 * after posting). Until these exist, prediction stays structural/uncalibrated.
 */
function outcomeLabeledCount() {
  try {
    return store.readAll("edits").filter((e) => e && e.outcome && typeof e.outcome === "object").length;
  } catch {
    return 0;
  }
}

const MIN_OUTCOMES_FOR_CALIBRATION = 100;

/**
 * @param {Object} viralResult  output of viralScoreV10 (componentScores + signals)
 */
function retentionPredictV10(viralResult = {}) {
  const comp = {};
  for (const [k, v] of Object.entries(viralResult.componentScores || {})) comp[k] = v.score || 0;
  const durationSec = (viralResult.signals && viralResult.signals.durationSec) || 0;

  // Longer clips (toward/over the 60s cap) lose completion.
  const durationPenaltyInput = clamp((durationSec - 30) / 60, [0, 1]);

  const cM = MODEL.models.completion;
  const completion = clamp(
    cM.intercept +
      cM.coefficients.hook * (comp.hook || 0) +
      cM.coefficients.pacing * (comp.pacing || 0) +
      cM.coefficients.retention * (comp.retention || 0) +
      cM.coefficients.durationPenalty * durationPenaltyInput,
    cM.bounds
  );

  const sM = MODEL.models.shareRate;
  const shareRate = clamp(
    sM.intercept +
      sM.coefficients.surprise * (comp.surprise || 0) +
      sM.coefficients.emotion * (comp.emotion || 0) +
      sM.coefficients.rewatch * (comp.rewatch || 0),
    sM.bounds
  );

  const rM = MODEL.models.rewatchRate;
  const rewatchRate = clamp(
    rM.intercept +
      rM.coefficients.rewatch * (comp.rewatch || 0) +
      rM.coefficients.surprise * (comp.surprise || 0),
    rM.bounds
  );

  const averageWatchTimeSec = round3(completion * durationSec);

  // Confidence inherits from the structural score and signal availability.
  const hlCount = (viralResult.signals && viralResult.signals.highlightsCount) || 0;
  const confidence = round3(clamp(
    0.7 * (viralResult.confidence || 0) + (hlCount >= 3 ? 0.2 : 0.05),
    [0, 0.8] // structural estimates are capped below high confidence by design
  ));

  const calibrated = outcomeLabeledCount() >= MIN_OUTCOMES_FOR_CALIBRATION;

  return {
    predictedCompletionRate: round3(completion),
    predictedAverageWatchTimeSec: averageWatchTimeSec,
    predictedShareRate: round3(shareRate),
    predictedRewatchRate: round3(rewatchRate),
    // Human-facing percentages with the required qualifier baked in.
    display: {
      completion: `${pct(completion)}% (structural estimate, not calibrated)`,
      shareRate: `${pct(shareRate)}% (structural estimate, not calibrated)`,
      rewatchRate: `${pct(rewatchRate)}% (structural estimate, not calibrated)`,
    },
    basis: "structural_heuristic",
    calibrated,
    disclaimer:
      "Structural estimate derived from this clip's measured signals — NOT an outcome-calibrated prediction of real-world performance. Calibrates only after >=" +
      MIN_OUTCOMES_FOR_CALIBRATION + " outcome-labeled posts are recorded.",
    confidence,
    inputs: { components: comp, durationSec: round3(durationSec), outcomeLabeled: outcomeLabeledCount() },
    computedAt: new Date().toISOString(),
  };
}

module.exports = { retentionPredictV10, MIN_OUTCOMES_FOR_CALIBRATION };
