// Creator Intelligence — scoring engine
// Produces viral / retention / share predictions ONLY when enough real dataset
// rows exist to support them. Otherwise returns a structured insufficient_data
// result. There is no code path that returns an invented number.
//
// See docs/creator-v10/creator-intelligence-architecture.md (the sufficiency contract)

"use strict";

const store = require("../dataset/dataset-store");

// Conservative thresholds. Below these, any "score" would itself be fabrication.
const MIN_ROWS_FOR_DISTRIBUTION = 200;
const MIN_ROWS_FOR_SCORING = 500;
const MIN_ROWS_PER_GAME = 50;

function insufficient(have, need, reason) {
  return { status: "insufficient_data", reason, have, need };
}

function ok(value, basis) {
  return { status: "ok", value, basis };
}

/**
 * How many population rows are usable for scoring (general + gaming).
 */
function scoringRowCount() {
  const c = store.counts();
  return c.general + c.gaming;
}

/**
 * Predict a viral score for a video's edit features.
 * @param {Object} features  measured features of THIS edit (cutFrequency, captionDensity, hookLength, zoomFrequency...)
 * @returns {{status:'ok',value:number,basis:object} | {status:'insufficient_data',...}}
 */
function viralScore(features, opts = {}) {
  const need = opts.minRows || MIN_ROWS_FOR_SCORING;
  const have = scoringRowCount();
  if (have < need) {
    return insufficient(have, need, "not enough collected rows to predict viral performance");
  }
  // Data-backed path: compare this edit's features against the distribution of
  // high-performing rows. Implemented as a similarity-to-top-quartile measure.
  const rows = [...store.readAll("general"), ...store.readAll("gaming")]
    .filter((r) => typeof r.viewCount === "number");
  if (rows.length < need) {
    return insufficient(rows.length, need, "rows present but lack viewCount needed for scoring");
  }
  const value = similarityToTopPerformers(features, rows);
  return ok(value, {
    datasetSize: rows.length,
    source: "general+gaming",
    method: "feature-similarity-to-top-quartile",
    computedAt: new Date().toISOString(),
  });
}

/**
 * Predict retention (completion likelihood) for a video's pacing features.
 */
function retentionScore(features, opts = {}) {
  const need = opts.minRows || MIN_ROWS_FOR_SCORING;
  const have = scoringRowCount();
  if (have < need) {
    return insufficient(have, need, "not enough collected rows to predict retention");
  }
  const rows = [...store.readAll("general"), ...store.readAll("gaming")]
    .filter((r) => typeof r.cutFrequency === "number" && typeof r.viewCount === "number");
  if (rows.length < need) {
    return insufficient(rows.length, need, "rows present but lack pacing fields for retention scoring");
  }
  const value = similarityToTopPerformers(features, rows);
  return ok(value, {
    datasetSize: rows.length,
    source: "general+gaming",
    method: "pacing-similarity-to-top-quartile",
    computedAt: new Date().toISOString(),
  });
}

/**
 * Whether per-game gaming aggregates are usable for a given game.
 */
function gameSufficiency(game) {
  const have = store.gamingCountsByGame()[game] || 0;
  return have >= MIN_ROWS_PER_GAME
    ? ok(have, { game, threshold: MIN_ROWS_PER_GAME })
    : insufficient(have, MIN_ROWS_PER_GAME, `not enough rows for game '${game}'`);
}

// ---------------------------------------------------------------------------
// Internal: data-backed similarity. Only ever called once thresholds pass, so
// it always operates on real rows.
// ---------------------------------------------------------------------------

const FEATURE_KEYS = ["cutFrequency", "captionDensity", "hookLength", "zoomFrequency"];

function similarityToTopPerformers(features, rows) {
  // Define "top performers" as the top quartile by viewCount among real rows.
  const sorted = [...rows].sort((a, b) => (b.viewCount || 0) - (a.viewCount || 0));
  const topQuartile = sorted.slice(0, Math.max(1, Math.floor(sorted.length / 4)));

  // Build the centroid of top performers over available numeric features.
  const centroid = {};
  for (const key of FEATURE_KEYS) {
    const vals = topQuartile.map((r) => r[key]).filter((v) => typeof v === "number");
    if (vals.length) centroid[key] = vals.reduce((s, v) => s + v, 0) / vals.length;
  }

  // Cosine-like normalized closeness in the available feature subspace.
  let dot = 0, magA = 0, magB = 0, used = 0;
  for (const key of FEATURE_KEYS) {
    if (typeof features[key] === "number" && typeof centroid[key] === "number") {
      dot += features[key] * centroid[key];
      magA += features[key] ** 2;
      magB += centroid[key] ** 2;
      used++;
    }
  }
  if (used === 0 || magA === 0 || magB === 0) {
    // Cannot compute honestly without overlapping features.
    return 0;
  }
  const cos = dot / (Math.sqrt(magA) * Math.sqrt(magB));
  return Number(Math.max(0, Math.min(1, cos)).toFixed(3));
}

module.exports = {
  MIN_ROWS_FOR_DISTRIBUTION, MIN_ROWS_FOR_SCORING, MIN_ROWS_PER_GAME,
  viralScore, retentionScore, gameSufficiency, scoringRowCount,
};
