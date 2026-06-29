/**
 * Generated lead thumbnail for Explore cards that have no natural cover image
 * (docs, builds, beliefs, image-less reads, local games). Deterministic, themed
 * per card type, and rendered as an SVG so it scales crisply and weighs nothing.
 *
 * Served same-origin at GET /api/explore/thumb.svg (see routes/explore.js) and
 * also used as the onerror fallback for external covers (archive.org art, GitHub
 * OG images, OWID charts) — so EVERY card ends with a real thumbnail, never a
 * bare "?" tile. Pure + network-free.
 */

// Type → [glyph, accent] — mirrors explore.html's ICON map and per-type --tile.
const THEME = {
  read:   ["\u{1F4F0}", "#06b6d4"],
  watch:  ["\u{1F3AC}", "#a78bfa"],
  listen: ["\u{1F3B5}", "#f472b6"],
  build:  ["\u{1F6E0}", "#10b981"],
  doc:    ["\u{1F4DA}", "#f59e0b"],
  belief: ["\u{1F30D}", "#22c55e"],
  embed:  ["\u{1F579}", "#06b6d4"],
  action: ["⚡",     "#06b6d4"],
  finance:["\u{1F4C8}", "#22c55e"],
};

// Deterministic "stock chart" polyline from a seed string, so an image-less
// finance card still gets a distinct, market-looking cover (not a bare glyph).
// Same seed → same line; different tickers → different lines. Spans the lower
// band of the 600×340 canvas.
function sparkPath(seed) {
  let h = 2166136261;
  for (let i = 0; i < String(seed).length; i++) {
    h ^= String(seed).charCodeAt(i);
    h = Math.imul(h, 16777619);
  }
  const pts = [];
  const N = 14;
  let y = 210;
  for (let i = 0; i < N; i++) {
    h = Math.imul(h ^ (h >>> 15), 2246822519);
    const step = ((h >>> 8) % 60) - 26; // pseudo-random walk, slight upward bias
    y = Math.max(150, Math.min(250, y + step));
    const x = 40 + i * (520 / (N - 1));
    pts.push(x.toFixed(0) + "," + y.toFixed(0));
  }
  return pts.join(" ");
}

const xml = (s) =>
  String(s == null ? "" : s).replace(/[&<>"']/g, (c) =>
    ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&apos;" }[c]));

// Greedy word-wrap to <= maxChars per line, <= maxLines lines (ellipsis on cut).
function wrap(title, maxChars, maxLines) {
  const words = String(title || "").trim().split(/\s+/).filter(Boolean);
  const lines = [];
  let cur = "";
  for (const w of words) {
    const next = cur ? cur + " " + w : w;
    if (next.length > maxChars && cur) {
      lines.push(cur);
      cur = w;
      if (lines.length === maxLines) break;
    } else {
      cur = next;
    }
  }
  if (cur && lines.length < maxLines) lines.push(cur);
  if (lines.length === maxLines) {
    // A title longer than the budget — mark the truncation.
    const used = lines.join(" ").split(/\s+/).length;
    if (used < words.length) lines[maxLines - 1] = lines[maxLines - 1].replace(/[.,;:]?$/, "") + "…";
  }
  return lines.slice(0, maxLines);
}

function renderThumb({ type, title, source } = {}) {
  const [glyph, accent] = THEME[type] || ["◈", "#06b6d4"];
  const lines = wrap(title || type || "", 26, 3);
  const startY = 196 - (lines.length - 1) * 17;
  const titleSvg = lines
    .map((ln, i) => `<text x="40" y="${startY + i * 34}" class="t">${xml(ln)}</text>`)
    .join("");
  const srcSvg = source
    ? `<text x="40" y="296" class="s">${xml(String(source).toUpperCase())}</text>`
    : "";
  // Finance cards render a market-chart motif instead of a plain panel — the
  // `title` here is the ticker label (e.g. "MSFT · AAPL"), never the headline,
  // so the card never shows its title twice.
  const motif = type === "finance"
    ? `<polyline points="${sparkPath(title || source || "mkt")}" fill="none" stroke="${accent}" stroke-width="3" stroke-opacity="0.85" stroke-linejoin="round" stroke-linecap="round"/>`
    : "";
  // Dark, type-tinted gradient panel — reads as a designed cover, not a glyph block.
  return `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 600 340" width="600" height="340" role="img" aria-label="${xml(title || type || "")}">
  <defs>
    <linearGradient id="g" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0" stop-color="${accent}" stop-opacity="0.42"/>
      <stop offset="0.55" stop-color="${accent}" stop-opacity="0.12"/>
      <stop offset="1" stop-color="#0b1220" stop-opacity="0.96"/>
    </linearGradient>
  </defs>
  <style>
    .t{ font:700 27px/1.2 system-ui,-apple-system,'Segoe UI',Roboto,sans-serif; fill:#f8fafc; }
    .s{ font:700 14px system-ui,sans-serif; letter-spacing:.12em; fill:${accent}; }
    .g{ font:64px 'Segoe UI Emoji','Apple Color Emoji','Noto Color Emoji',system-ui,sans-serif; }
  </style>
  <rect width="600" height="340" fill="#0b1220"/>
  <rect width="600" height="340" fill="url(#g)"/>
  <rect x="0" y="0" width="600" height="5" fill="${accent}"/>
  <text x="40" y="92" class="g">${glyph}</text>
  ${motif}
  ${titleSvg}
  ${srcSvg}
</svg>`;
}

module.exports = { renderThumb, THEME };
