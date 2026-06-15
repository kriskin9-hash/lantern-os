// Creator Intelligence — dataset row schemas + validators
// See docs/creator-v10/research-dataset-schema.md
//
// Validators are intentionally strict: a row that does not match is rejected
// at append time, so the store can never silently accumulate malformed/"fake"
// rows that would pollute later aggregates.

"use strict";

const HOOK_STYLES = [
  "instant_payoff", "question", "text", "shock", "reaction", "countdown", "unknown",
];
const PLATFORMS = ["youtube", "tiktok", "instagram", "facebook"];
const GAMES = [
  "fortnite", "cod", "warzone", "valorant", "cs2", "minecraft",
  "rocket_league", "apex", "league", "overwatch", "other",
];
const MOMENT_TYPES = [
  "kill", "clutch", "fail", "funny", "reaction", "boss", "ranked", "tournament", "unknown",
];
const FACECAM_CORNERS = ["top_left", "top_right", "bottom_left", "bottom_right", "none"];
const EDIT_KINDS = ["edit", "variant_generated", "variant_selected", "export"];

function isFiniteNumberOrNull(v) {
  return v === null || (typeof v === "number" && Number.isFinite(v));
}
function isNonEmptyString(v) {
  return typeof v === "string" && v.length > 0;
}

/**
 * @returns {{ valid: boolean, errors: string[] }}
 */
function validateGeneralShort(row) {
  const errors = [];
  if (!row || typeof row !== "object") return { valid: false, errors: ["row is not an object"] };
  if (!isNonEmptyString(row.id)) errors.push("id required");
  if (!PLATFORMS.includes(row.platform)) errors.push(`platform must be one of ${PLATFORMS.join("|")}`);
  if (!isNonEmptyString(row.source)) errors.push("source required (provenance)");
  if (!isNonEmptyString(row.collectedAt)) errors.push("collectedAt (ISO-8601) required");
  if (!isNonEmptyString(row.title)) errors.push("title required");
  // Numeric measures may be null (metadata-only rows) but never garbage.
  for (const f of ["duration", "viewCount", "likeCount", "commentCount",
                   "captionDensity", "cutFrequency", "zoomFrequency", "hookLength"]) {
    if (!isFiniteNumberOrNull(row[f])) errors.push(`${f} must be a finite number or null`);
  }
  if (row.hookStyle !== undefined && !HOOK_STYLES.includes(row.hookStyle)) {
    errors.push(`hookStyle must be one of ${HOOK_STYLES.join("|")}`);
  }
  if (row.musicPresence !== undefined && typeof row.musicPresence !== "boolean") {
    errors.push("musicPresence must be boolean");
  }
  return { valid: errors.length === 0, errors };
}

function validateGamingShort(row) {
  const base = validateGeneralShort(row);
  const errors = [...base.errors];
  if (!GAMES.includes(row.game)) errors.push(`game must be one of ${GAMES.join("|")}`);
  if (row.momentType !== undefined && !MOMENT_TYPES.includes(row.momentType)) {
    errors.push(`momentType must be one of ${MOMENT_TYPES.join("|")}`);
  }
  if (row.facecamCorner !== undefined && !FACECAM_CORNERS.includes(row.facecamCorner)) {
    errors.push(`facecamCorner must be one of ${FACECAM_CORNERS.join("|")}`);
  }
  if (row.facecamPresent !== undefined && typeof row.facecamPresent !== "boolean") {
    errors.push("facecamPresent must be boolean");
  }
  return { valid: errors.length === 0, errors };
}

function validateEditEvent(row) {
  const errors = [];
  if (!row || typeof row !== "object") return { valid: false, errors: ["row is not an object"] };
  if (!isNonEmptyString(row.id)) errors.push("id required");
  if (!isNonEmptyString(row.entryId)) errors.push("entryId required");
  if (!isNonEmptyString(row.createdAt)) errors.push("createdAt (ISO-8601) required");
  if (!EDIT_KINDS.includes(row.kind)) errors.push(`kind must be one of ${EDIT_KINDS.join("|")}`);
  if (row.features !== undefined && (typeof row.features !== "object" || row.features === null)) {
    errors.push("features must be an object when present");
  }
  // outcome stays null unless real performance data is supplied — never invented.
  if (row.outcome !== undefined && row.outcome !== null && typeof row.outcome !== "object") {
    errors.push("outcome must be null or an object");
  }
  return { valid: errors.length === 0, errors };
}

module.exports = {
  HOOK_STYLES, PLATFORMS, GAMES, MOMENT_TYPES, FACECAM_CORNERS, EDIT_KINDS,
  validateGeneralShort, validateGamingShort, validateEditEvent,
};
