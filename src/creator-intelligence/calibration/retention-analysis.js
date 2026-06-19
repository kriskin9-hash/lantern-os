// Creator Intelligence — retention-curve analysis + edit-timeline alignment (A4)
// Pure functions over a normalized retention curve ([{position,retention}] in
// [0,1]). Produces the metrics the platforms actually reward (intro retention,
// % viewed) and locates the biggest drop-off "cliff", then attributes that cliff
// to the specific edit segment it lands in — so the editing model can learn
// which edits shed viewers. Every number traces to the real curve; sparse data
// yields null, never a guess.
//
// See docs/creator-v10/editing-analysis-model-research.md (A4)

"use strict";

function isCurve(points) {
  return Array.isArray(points) && points.length >= 2;
}

/** Linearly interpolate retention at a given position ratio in [0,1]. */
function retentionAt(points, position) {
  if (!isCurve(points)) return null;
  const pts = [...points].sort((a, b) => a.position - b.position);
  if (position <= pts[0].position) return pts[0].retention;
  if (position >= pts[pts.length - 1].position) return pts[pts.length - 1].retention;
  for (let i = 1; i < pts.length; i++) {
    if (pts[i].position >= position) {
      const a = pts[i - 1], b = pts[i];
      const span = b.position - a.position || 1e-9;
      const f = (position - a.position) / span;
      return a.retention + f * (b.retention - a.retention);
    }
  }
  return pts[pts.length - 1].retention;
}

/**
 * Curve metrics. `introSeconds`/`durationSec` define the intro window (the
 * platform's "% past 3s" signal); omit them and intro defaults to the 3% mark.
 * @returns {{introRetention, meanRetention, maxCliff:{atPosition,drop,from,to}|null, points:number}}
 */
function curveMetrics(points, opts = {}) {
  if (!isCurve(points)) {
    return { introRetention: null, meanRetention: null, maxCliff: null, points: points ? points.length : 0 };
  }
  const pts = [...points].sort((a, b) => a.position - b.position);

  const introRatio = (opts.durationSec && opts.introSeconds)
    ? Math.min(0.99, opts.introSeconds / opts.durationSec)
    : (opts.introRatio ?? 0.03);
  const introRetention = Number(retentionAt(pts, introRatio).toFixed(4));

  const meanRetention = Number(
    (pts.reduce((s, p) => s + p.retention, 0) / pts.length).toFixed(4)
  );

  // Largest single drop between consecutive samples = the steepest cliff.
  let maxCliff = null;
  for (let i = 1; i < pts.length; i++) {
    const drop = pts[i - 1].retention - pts[i].retention; // positive = viewers left
    if (drop > 0 && (!maxCliff || drop > maxCliff.drop)) {
      maxCliff = {
        atPosition: Number(((pts[i - 1].position + pts[i].position) / 2).toFixed(4)),
        drop: Number(drop.toFixed(4)),
        from: Number(pts[i - 1].retention.toFixed(4)),
        to: Number(pts[i].retention.toFixed(4)),
      };
    }
  }

  return { introRetention, meanRetention, maxCliff, points: pts.length };
}

/**
 * Attribute a cliff (position ratio) to the edit segment that contains it.
 * @param {{atPosition:number}} cliff
 * @param {Array<{start:number,end:number,label?:string}>} segments  seconds
 * @param {number} durationSec
 * @returns {{cliffTimeSec, segmentIndex, segment}|null}
 */
function attributeCliffToSegments(cliff, segments, durationSec) {
  if (!cliff || typeof cliff.atPosition !== "number") return null;
  if (!Array.isArray(segments) || !Number.isFinite(durationSec) || durationSec <= 0) return null;
  const cliffTimeSec = Number((cliff.atPosition * durationSec).toFixed(2));
  for (let i = 0; i < segments.length; i++) {
    const s = segments[i];
    if (typeof s.start === "number" && typeof s.end === "number" &&
        cliffTimeSec >= s.start && cliffTimeSec <= s.end) {
      return { cliffTimeSec, segmentIndex: i, segment: s };
    }
  }
  return { cliffTimeSec, segmentIndex: -1, segment: null }; // cliff fell outside known segments
}

/**
 * Convenience: the numeric outcome metrics a retention curve contributes to the
 * calibration set (flow straight into feature↔outcome correlations).
 */
function retentionOutcomeMetrics(points, opts = {}) {
  const m = curveMetrics(points, opts);
  const out = {};
  if (m.introRetention !== null) out.introRetention = m.introRetention;
  if (m.meanRetention !== null) out.meanRetention = m.meanRetention;
  if (m.maxCliff) out.maxCliffDrop = m.maxCliff.drop;
  return out;
}

module.exports = {
  retentionAt, curveMetrics, attributeCliffToSegments, retentionOutcomeMetrics,
};
