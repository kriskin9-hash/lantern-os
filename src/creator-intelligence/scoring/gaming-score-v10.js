// Gaming Score V10 — gaming-specific bonuses layered on the structural viralScore.
//
// HONESTY: kills/clutches/reactions/victories are INFERRED from audio/scene/
// motion surprise proxies measured from the clip — NOT from kill-feed OCR,
// scoreboard OCR, game telemetry, or a trained vision model (see
// research/gaming_patterns.json -> detectability.not_implemented). Each bonus
// is a candidate with a measured confidence. Bonuses are capped individually
// and in total so a gaming clip can't be inflated past the structural ceiling.
//
// Spec: "V10 SCORING ENGINE REDESIGN" Phase 3.

"use strict";

const PRIORS = require("../research/gaming_patterns.json");
const { clamp01 } = require("./viral-score-v10");

function round3(x) { return Number(Number(x).toFixed(3)); }

/**
 * @param {Object} viralResult  output of viralScoreV10 (carries .viralScore and .signals)
 * @param {Object} opts         { safeZones } from SafeZoneDetectorV2 (for facecam-based reaction)
 */
function gamingScoreV10(viralResult, opts = {}) {
  const s = viralResult.signals || {};
  const caps = PRIORS.bonuses;

  // Kill: clustered audio+motion spikes.
  const killProxy = clamp01(s.multiSignalSpikesPerMin / 8);
  const killBonus = round3(killProxy * caps.kill.max);

  // Clutch: sustained tension (coverage) resolving in a late spike (endPayoff).
  const clutchProxy = clamp01((s.endPayoff || 0) * (0.5 + 0.5 * (s.coverage || 0)));
  const clutchBonus = round3(clutchProxy * caps.clutch.max);

  // Reaction: requires a detected facecam region to attribute; else low/zero.
  const facecamPresent = Array.isArray(opts.safeZones && opts.safeZones.regions)
    ? opts.safeZones.regions.some((r) => r.type === "facecam")
    : opts.facecamPresent === true;
  const reactionProxy = facecamPresent ? clamp01(s.audioPeak || 0) : 0;
  const reactionBonus = round3(reactionProxy * caps.reaction.max);

  // Victory: end-region emphasis (late payoff).
  const victoryProxy = clamp01(s.endPayoff || 0);
  const victoryBonus = round3(victoryProxy * caps.victory.max);

  // Cap the combined bonus.
  const rawTotal = killBonus + clutchBonus + reactionBonus + victoryBonus;
  const totalBonus = round3(Math.min(rawTotal, PRIORS.bonusCapTotal));

  const baseViral = viralResult.viralScore || 0;
  const gamingViralScore = round3(clamp01(baseViral + totalBonus));

  // Confidence: bonuses inferred from proxies are inherently lower-confidence;
  // facecam-less reaction is the weakest.
  const audioConf = s.hasAudioSignal ? 0.7 : 0.3;
  const confidence = round3(clamp01(
    0.5 * (viralResult.confidence || 0) + 0.5 * audioConf * (facecamPresent ? 1 : 0.85)
  ));

  return {
    gamingViralScore,
    viralScore: baseViral,
    totalBonus,
    bonusCapped: rawTotal > PRIORS.bonusCapTotal,
    bonuses: {
      kill: { value: killBonus, proxy: round3(killProxy), max: caps.kill.max, inferred: true },
      clutch: { value: clutchBonus, proxy: round3(clutchProxy), max: caps.clutch.max, inferred: true },
      reaction: { value: reactionBonus, proxy: round3(reactionProxy), max: caps.reaction.max, inferred: true, requiresFacecam: true, facecamPresent },
      victory: { value: victoryBonus, proxy: round3(victoryProxy), max: caps.victory.max, inferred: true },
    },
    confidence,
    basis: "structural_heuristic",
    calibrated: false,
    detectabilityNote: PRIORS.detectability.note,
    computedAt: new Date().toISOString(),
  };
}

module.exports = { gamingScoreV10 };
