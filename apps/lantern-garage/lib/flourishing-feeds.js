// Flourishing feeds — grounds the world-model beliefs from REAL yearly public data.
//
// Ports the honesty discipline of the Human Flourishing Frameworks world_model into the
// Lantern loop: every belief is a posterior in [0,1] with an uncertainty and a *source*.
// Here the sources are real, keyless, yearly feeds (World Bank world aggregates). The
// model is "always wrong somewhere" — uncertainty is first-class, and the normalization
// from a raw indicator to a flourishing score is a value-laden CHOICE, so it carries its
// own uncertainty penalty (documented per indicator).
//
// Observe (poll feeds) -> Remember (cache) -> Reason (rank: what to ground next) ->
// Verify (provenance + uncertainty) -> Converge (domain posteriors).

const https = require("https");

// ── indicator → flourishing belief map ───────────────────────────────────────
// normalize(raw) maps the indicator's real-world units into a 0..1 flourishing score.
// `floor`/`ceil` are the chosen "bad"/"good" anchors; `uncertainty` already includes a
// penalty for that mapping being a choice, not an objective truth. `proxy:true` = the
// indicator only loosely stands in for the component (extra uncertainty).
// All codes confirmed to return a World ("WLD") aggregate value (2026-06-25).
const INDICATORS = [
  { belief: "humans:health", domain: "humans", scope: "global",
    code: "SP.DYN.LE00.IN", label: "Life expectancy at birth",
    floor: 40, ceil: 85, unit: "years", uncertainty: 0.12 },
  { belief: "humans:health:children", domain: "humans", scope: "global",
    code: "SH.DYN.MORT", label: "Under-5 mortality (inverted)",
    floor: 180, ceil: 0, unit: "per 1,000 live births", uncertainty: 0.12 },
  { belief: "humans:opportunity", domain: "humans", scope: "global",
    code: "EG.ELC.ACCS.ZS", label: "Access to electricity",
    floor: 0, ceil: 100, unit: "% of population", uncertainty: 0.14 },
  { belief: "humans:education", domain: "humans", scope: "global",
    code: "SE.SEC.ENRR", label: "Secondary school enrollment",
    floor: 0, ceil: 100, unit: "% gross", uncertainty: 0.16 },
  { belief: "ecosystems:protected_areas", domain: "ecosystems", scope: "global",
    code: "ER.PTD.TOTL.ZS", label: "Protected areas (vs 30×30 target)",
    floor: 0, ceil: 30, unit: "% of territory", uncertainty: 0.20, proxy: true },
  { belief: "ecosystems:clean_energy", domain: "ecosystems", scope: "global",
    code: "EG.FEC.RNEW.ZS", label: "Renewable energy share (vs 50% transition)",
    floor: 0, ceil: 50, unit: "% final energy", uncertainty: 0.22, proxy: true },
];

const clamp01 = (x) => Math.max(0, Math.min(1, x));
function normalize(ind, raw) {
  // linear map floor->0, ceil->1 (ceil may be < floor for "lower is better" indicators)
  return clamp01((raw - ind.floor) / (ind.ceil - ind.floor));
}

const WB = (code) =>
  `https://api.worldbank.org/v2/country/WLD/indicator/${code}?format=json&per_page=1&mrnev=1`;

function getJson(url, timeoutMs = 9000) {
  return new Promise((resolve) => {
    const req = https.get(url, { headers: { "User-Agent": "LanternOS-Flourishing/1.0" } }, (resp) => {
      let body = "";
      resp.on("data", (c) => (body += c));
      resp.on("end", () => { try { resolve(JSON.parse(body)); } catch { resolve(null); } });
    });
    req.on("error", () => resolve(null));
    req.setTimeout(timeoutMs, () => { req.destroy(); resolve(null); });
  });
}

const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

async function fetchIndicator(ind, tries = 4) {
  // The World Bank API rate-limits rapid requests by returning an XML error page
  // (getJson then yields null); retry with spacing before giving up.
  for (let i = 0; i < tries; i++) {
    const d = await getJson(WB(ind.code));
    const rec = Array.isArray(d) && Array.isArray(d[1]) ? d[1][0] : null;
    if (rec && rec.value != null) {
      const raw = Number(rec.value);
      return {
        entity: ind.belief, domain: ind.domain, scope: ind.scope,
        posterior: Number(normalize(ind, raw).toFixed(4)),
        uncertainty: ind.uncertainty,
        raw, unit: ind.unit, year: rec.date,
        label: ind.label, proxy: !!ind.proxy,
        source_name: "World Bank", source: WB(ind.code),
        kind: "grounded_feed",
      };
    }
    if (i < tries - 1) await sleep(900);
  }
  return null;
}

// ── precision-weighted domain posteriors (the "flourishing score" per domain) ──
function domainScores(beliefs) {
  const byDomain = {};
  for (const b of beliefs) (byDomain[b.domain] ||= []).push(b);
  const out = [];
  for (const [domain, list] of Object.entries(byDomain)) {
    // inverse-variance (precision) weighting — confident beliefs count more
    let wsum = 0, psum = 0;
    for (const b of list) { const w = 1 / (b.uncertainty * b.uncertainty); wsum += w; psum += w * b.posterior; }
    const score = psum / wsum;
    const uncertainty = Math.sqrt(1 / wsum);             // combined posterior std
    out.push({ domain, score: Number(score.toFixed(4)),
               uncertainty: Number(uncertainty.toFixed(4)), n: list.length });
  }
  return out.sort((a, b) => b.score - a.score);
}

// ── the Question Machine, applied: what to ground next ────────────────────────
// score = uncertainty * leverage. Leverage = how much grounding THIS belief would tighten
// its domain's posterior — for inverse-variance weighting that is largest exactly for the
// least-certain belief in a domain (raising its precision adds the most total precision).
// So the loop asks its highest-uncertainty, highest-leverage admissible question first.
function nextQuestions(beliefs, topK = 3) {
  const byDomain = {};
  for (const b of beliefs) (byDomain[b.domain] ||= []).push(b);
  const scored = beliefs.map((b) => {
    const sib = byDomain[b.domain];
    const sibU = sib.reduce((s, x) => s + x.uncertainty, 0);
    const leverage = sibU > 0 ? b.uncertainty / sibU : 1;   // share of domain uncertainty
    return { ...b, q_score: Number((b.uncertainty * leverage).toFixed(4)), leverage };
  });
  scored.sort((a, b) => b.q_score - a.q_score);
  return scored.slice(0, topK).map((b) => ({
    entity: b.entity, channel: b.source_name, source: b.source,
    uncertainty: b.uncertainty, q_score: b.q_score,
    hypothesis: `ground ${b.entity} deeper — currently ${b.posterior} ±${(b.uncertainty * 100).toFixed(0)}% via ${b.source_name}${b.proxy ? " (proxy indicator)" : ""}`,
  }));
}

// ── cache (yearly data → long TTL) ───────────────────────────────────────────
const TTL_MS = 24 * 60 * 60 * 1000;
let cache = { at: 0, beliefs: [] };

async function pollFeeds(force = false) {
  if (!force && Date.now() - cache.at < TTL_MS && cache.beliefs.length) return cache.beliefs;
  const results = [];
  for (const ind of INDICATORS) {                          // sequential — avoid WB rate limits
    const b = await fetchIndicator(ind);
    if (b) results.push(b);
    await sleep(350);
  }
  if (results.length) cache = { at: Date.now(), beliefs: results };
  return cache.beliefs;
}

async function panel(force = false) {
  const beliefs = await pollFeeds(force);
  const covered = [...new Set(beliefs.map((b) => b.domain))];
  return {
    ok: beliefs.length > 0,
    updated_at: cache.at ? new Date(cache.at).toISOString() : null,
    domains: domainScores(beliefs),
    questions: nextQuestions(beliefs),
    beliefs,
    // honesty: domains with NO live feed (animals, universe) are literature-only in HFF
    ungrounded_domains: ["animals", "universe"].filter((d) => !covered.includes(d)),
    sources: [...new Set(beliefs.map((b) => b.source_name))],
    note: "Grounded from real yearly World Bank world aggregates. Normalization to a " +
          "flourishing score is a value-laden choice — reflected in each belief's uncertainty.",
  };
}

module.exports = { pollFeeds, panel, domainScores, nextQuestions, INDICATORS };

// CLI probe: `node lib/flourishing-feeds.js`
if (require.main === module) {
  (async () => {
    const p = await panel(true);
    console.log("updated:", p.updated_at, "| domains grounded:", p.domains.length,
                "| ungrounded:", p.ungrounded_domains.join(",") || "none");
    for (const d of p.domains) console.log(`  ${d.domain.padEnd(11)} ${(d.score * 100).toFixed(0)}%  ±${(d.uncertainty * 100).toFixed(0)}%  (${d.n} feeds)`);
    console.log("next questions (Question Machine):");
    for (const q of p.questions) console.log("  -", q.hypothesis);
    for (const b of p.beliefs) console.log(`     · ${b.entity.padEnd(26)} raw ${b.raw} ${b.unit} (${b.year}) -> ${b.posterior}`);
  })();
}
