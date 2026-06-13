/**
 * Three Doors / Kingdome of Hearts — lore-aware image pool
 *
 * Priority order:
 *   1. THREE_DOORS_IMAGE_POOL_DIR (local operator pool, e.g. D:\tmp\imagesandreports)
 *   2. data/images/caadi/  (repo-ingested CAAD images)
 *   3. (caller handles: existing three-doors PNGs, canvas, Pollinations)
 *
 * Matching strategy: score each candidate filename against scene keywords.
 * UUID-named files score 0 and win only as random fallback.
 * Named files with matching keywords score higher.
 *
 * Token format: base64(source + ":" + filename)
 *   source = "local" | "caadi"
 *   filename = basename only, no directories
 */

const fs = require("fs");
const path = require("path");

const IMG_EXTS = new Set([".png", ".jpg", ".jpeg", ".webp", ".gif"]);

// ── Scene keyword map (Kingdome of Hearts canonical) ─────────────────
const SCENE_KEYWORDS = {
  "moss-entry":         ["moss", "green", "forest", "fern", "lantern", "guide", "entry", "door", "garden", "tree", "nature"],
  "burrow":             ["burrow", "earth", "root", "warm", "cozy", "underground", "quilt", "amber"],
  "sunken-bell":        ["water", "bell", "submerged", "reflection", "stone", "hall", "echo"],
  "little-crown":       ["crown", "gold", "small", "stump", "tree", "royal", "tiny"],
  "garden-door":        ["garden", "door", "arch", "path", "flower", "gate", "green", "growth"],
  "kingdome-garden":    ["garden", "throne", "moss", "roots", "green", "heart", "king", "beginning", "crown", "vine", "door"],
  "cloverfield":        ["clover", "green", "luck", "fox", "field", "bead", "coin", "shiny", "grass", "meadow"],
  "lucky-door":         ["clover", "green", "luck", "fox", "field", "coin", "shiny"],
  "today-door":         ["home", "room", "warm", "ordinary", "morning", "day", "table", "window", "simple", "light"],
  "tomorrow-door":      ["future", "path", "branch", "root", "dawn", "road", "horizon", "seed", "tree", "forest"],
  "xp-door":            ["xp", "windows", "hill", "blue", "sky", "glitch", "computer", "desktop", "nostalgic", "pixel"],
  "xenon-convergence":  ["xenon", "star", "planet", "ship", "cosmic", "space", "orbit", "convergence", "geometry", "mandala", "infinity", "matrix", "mural", "blackhole"],
  "sigil":              ["city", "door", "arch", "street", "lantern", "threshold", "portal", "ring", "light"],
  "sigil-city":         ["city", "door", "arch", "street", "lantern", "threshold", "portal", "ring", "light"],
  "fog-door-return":    ["fog", "cloud", "mist", "sea", "return", "gray", "gate", "ocean", "journey"],
  "raven-tower":        ["raven", "red", "villa", "masquerade", "courtyard", "bird", "black", "tower", "night"],
  "raven-door":         ["raven", "red", "villa", "masquerade", "courtyard", "bird", "black"],
  "wish-door":          ["wish", "well", "star", "candle", "small", "light", "threshold", "hope"],
  "bathhouse-mosaic":   ["bath", "pool", "tile", "mosaic", "steam", "moon", "water", "blue"],
  "csf-archive":        ["archive", "data", "crystal", "storage", "memory", "digital"],
  "memory-vault":       ["memory", "crystal", "mirror", "vault", "past", "reflection"],
  "convergence-node":   ["convergence", "node", "geometry", "mandala", "star", "matrix"],
  "dream-thread":       ["dream", "thread", "silk", "soft", "light", "path"],
  "beacon-tower":       ["beacon", "tower", "light", "signal", "high", "lantern"],
  "choice-archive":     ["choice", "archive", "door", "portal", "record"],
  "recursion-well":     ["well", "spiral", "deep", "recursion", "infinite"],
  "echo-chamber":       ["echo", "sound", "chamber", "reflection", "ring"],
  "flux-garden":        ["garden", "flux", "growth", "organic", "green", "change"],
  "void-threshold":     ["void", "threshold", "dark", "empty", "gate", "doorway"],
  "storybook":          ["story", "book", "page", "tale", "fantasy", "forest"],
  "future-doors":       ["future", "doors", "path", "branch", "many", "choice"],
  "end-of-time":        ["end", "time", "final", "last", "eternal", "sky"],
};

// ── Token helpers ─────────────────────────────────────────────────────
function makeToken(source, filename) {
  return Buffer.from(`${source}:${filename}`).toString("base64url");
}

function decodeToken(token) {
  try {
    const raw = Buffer.from(token, "base64url").toString("utf8");
    const colon = raw.indexOf(":");
    if (colon < 1) return null;
    const source = raw.slice(0, colon);
    const filename = raw.slice(colon + 1);
    if (!["local", "caadi"].includes(source)) return null;
    if (filename.includes("..") || filename.includes("/") || filename.includes("\\")) return null;
    return { source, filename };
  } catch { return null; }
}

// ── File listing ──────────────────────────────────────────────────────
function listImages(dir) {
  if (!dir || !fs.existsSync(dir)) return [];
  try {
    return fs.readdirSync(dir)
      .filter(f => IMG_EXTS.has(path.extname(f).toLowerCase()))
      .map(f => f);
  } catch { return []; }
}

// ── Keyword scoring ───────────────────────────────────────────────────
function scoreFilename(filename, keywords) {
  if (!keywords || !keywords.length) return 0;
  const lower = filename.toLowerCase();
  let score = 0;
  for (const kw of keywords) {
    if (lower.includes(kw)) score++;
  }
  return score;
}

// ── Build candidate pool ──────────────────────────────────────────────
function buildPool(localPoolDir, caadiDir) {
  const candidates = [];

  const localFiles = listImages(localPoolDir);
  for (const f of localFiles) {
    candidates.push({ source: "local", filename: f, dir: localPoolDir });
  }

  const caadiFiles = listImages(caadiDir);
  for (const f of caadiFiles) {
    candidates.push({ source: "caadi", filename: f, dir: caadiDir });
  }

  return candidates;
}

// ── Pick best image for scene ─────────────────────────────────────────
function pickForScene(pool, sceneKey) {
  if (!pool.length) return null;

  const keywords = SCENE_KEYWORDS[sceneKey] || [];
  let scored = pool.map(c => ({ ...c, score: scoreFilename(c.filename, keywords) }));

  const maxScore = Math.max(...scored.map(c => c.score));
  if (maxScore > 0) {
    // Pick randomly from best-scoring candidates
    const best = scored.filter(c => c.score === maxScore);
    const pick = best[Math.floor(Math.random() * best.length)];
    const matched = keywords.filter(kw => pick.filename.toLowerCase().includes(kw));
    return {
      ...pick,
      reason: matched.length ? `matched keywords: ${matched.join(", ")}` : `score ${pick.score}`,
    };
  }

  // No keyword match — pick randomly from local pool first, then caadi
  const localPool = pool.filter(c => c.source === "local");
  const fallback = localPool.length ? localPool : pool;
  const pick = fallback[Math.floor(Math.random() * fallback.length)];
  return { ...pick, score: 0, reason: "random (no keyword match)" };
}

// ── Resolve token to filesystem path ─────────────────────────────────
function resolveToken(token, localPoolDir, caadiDir) {
  const decoded = decodeToken(token);
  if (!decoded) return null;

  const { source, filename } = decoded;
  const baseDir = source === "local" ? localPoolDir : caadiDir;
  if (!baseDir || !fs.existsSync(baseDir)) return null;

  const full = path.resolve(baseDir, filename);
  // Verify resolved path stays within the intended directory
  if (!full.startsWith(path.resolve(baseDir))) return null;
  if (!IMG_EXTS.has(path.extname(full).toLowerCase())) return null;
  if (!fs.existsSync(full)) return null;

  return { full, source, filename };
}

module.exports = { buildPool, pickForScene, makeToken, decodeToken, resolveToken, SCENE_KEYWORDS };
