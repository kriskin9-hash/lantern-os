// PCSF Live Refresh — update data/pcsf/*.pcsf.json from live provider + journal state on server start
const fs = require("fs");
const path = require("path");

const PROVIDER_KEYS = [
  "ANTHROPIC_API_KEY", "OPENAI_API_KEY", "GEMINI_API_KEY", "GOOGLE_API_KEY", "XAI_API_KEY",
];

function _now() {
  return new Date().toISOString();
}

function loadJson(p) {
  try { return JSON.parse(fs.readFileSync(p, "utf8")); } catch { return null; }
}

function saveJson(p, data) {
  try {
    fs.mkdirSync(path.dirname(p), { recursive: true });
    fs.writeFileSync(p, JSON.stringify(data, null, 2) + "\n", "utf8");
  } catch (e) {
    console.error("[PCSF] Failed to write", p, e.message);
  }
}

function envPresent(key) {
  return !!(process.env[key] && process.env[key].trim().length > 0);
}

function refreshSettingsPcsf(repoRoot) {
  const p = path.join(repoRoot, "data", "pcsf", "settings.pcsf.json");
  const data = loadJson(p);
  if (!data) return;
  let changed = false;
  for (const setting of data.settings || []) {
    const present = envPresent(setting.key);
    const newState = present ? "present" : "absent";
    if (setting.state !== newState) {
      setting.state = newState;
      changed = true;
    }
  }
  data.generated_at = _now();
  if (changed) {
    saveJson(p, data);
    console.log("[PCSF] settings.pcsf.json refreshed —", data.settings.filter(s => s.state === "present").length, "present," , data.settings.filter(s => s.state === "absent").length, "absent");
  } else {
    console.log("[PCSF] settings.pcsf.json unchanged");
  }
}

function refreshProviderPcsf(repoRoot) {
  const p = path.join(repoRoot, "data", "pcsf", "provider.pcsf.json");
  const data = loadJson(p);
  if (!data) return;
  let changed = false;
  for (const prov of data.providers || []) {
    if (!prov.env_key) continue;
    const present = envPresent(prov.env_key);
    const newState = present ? "available" : "no_key";
    if (prov.state !== newState) {
      prov.state = newState;
      changed = true;
    }
    const routable = present && prov.provider_id !== "ollama";
    if (prov.is_routable !== routable) {
      prov.is_routable = routable;
      changed = true;
    }
    prov.last_checked = _now();
  }
  data.generated_at = _now();
  saveJson(p, data);
  console.log("[PCSF] provider.pcsf.json refreshed —", changed ? "states changed" : "states unchanged");
}

function loadDreamEntries(repoRoot) {
  const dreamDir = path.join(repoRoot, "data", "dream_journal");
  if (!fs.existsSync(dreamDir)) return [];
  const files = fs.readdirSync(dreamDir).filter(f => f.endsWith(".jsonl"));
  const entries = [];
  for (const file of files) {
    const text = fs.readFileSync(path.join(dreamDir, file), "utf8");
    for (const line of text.split("\n")) {
      if (!line.trim()) continue;
      try { entries.push(JSON.parse(line)); } catch {}
    }
  }
  return entries;
}

function refreshHealthPcsf(repoRoot) {
  const p = path.join(repoRoot, "data", "pcsf", "health.pcsf.json");
  const data = loadJson(p);
  if (!data) return;
  let changed = false;

  // Update provider key snapshot
  const provCheck = data.checks.find(c => c.check_id === "settings_providers");
  if (provCheck && provCheck.current_snapshot) {
    const snap = provCheck.current_snapshot;
    for (const key of PROVIDER_KEYS) {
      const present = envPresent(key);
      if (snap[key] !== present) { snap[key] = present; changed = true; }
    }
    const any = PROVIDER_KEYS.some(envPresent) || envPresent("OLLAMA_BASE_URL");
    if (snap._any !== any) { snap._any = any; changed = true; }
  }

  // Update journal stats
  const entries = loadDreamEntries(repoRoot);
  const journal = {
    total_entries: entries.length,
    entries_by_kind: {},
    entries_with_ctf: 0,
    avg_lucidity: 0,
    generated_at: _now(),
  };
  let totalLucidity = 0;
  for (const e of entries) {
    journal.entries_by_kind[e.kind || "dream"] = (journal.entries_by_kind[e.kind || "dream"] || 0) + 1;
    if ((e.ctf_glyphs || []).length) journal.entries_with_ctf++;
    totalLucidity += e.lucidity || 0;
  }
  if (entries.length > 0) journal.avg_lucidity = +(totalLucidity / entries.length).toFixed(2);

  if (!data.journal || JSON.stringify(data.journal) !== JSON.stringify(journal)) {
    data.journal = journal;
    changed = true;
  }

  data.generated_at = _now();
  saveJson(p, data);
  console.log("[PCSF] health.pcsf.json refreshed — entries:", journal.total_entries, "CTF:", journal.entries_with_ctf, changed ? "(changed)" : "(unchanged)");
}

function refreshAllPcsf(repoRoot) {
  console.log("[PCSF] Starting live refresh…");
  refreshSettingsPcsf(repoRoot);
  refreshProviderPcsf(repoRoot);
  refreshHealthPcsf(repoRoot);
  console.log("[PCSF] Live refresh complete.");
}

module.exports = { refreshAllPcsf };
