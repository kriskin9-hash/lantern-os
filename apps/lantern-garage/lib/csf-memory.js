const fs = require("fs");
const path = require("path");
const { readFileViaMcp } = require("./mcp-resource-client");

const repoRoot = path.resolve(__dirname, "..", "..", "..");

const CSF_MEMORY_PATH = path.join(repoRoot, "data", "csf_memory");
const CSF_INGEST_PATH = path.join(repoRoot, "csf", "ingest");
const DREAM_JOURNAL_PATH = path.join(repoRoot, "data", "dream_journal");
const DOOR_STATE_PATH = path.join(DREAM_JOURNAL_PATH, "door_state.json");
const RAG_HOUSE_PATH = path.join(repoRoot, "data", "rag-house", "flat-rag-house-latest.json");

let _cache = { memories: null, ingest: null, ts: 0 };
const CACHE_TTL_MS = 10_000;

// Helper: read a file via MCP resource client, falling back to fs.readFileSync
function _readText(filePath) {
  const result = readFileViaMcp(filePath);
  if (result && result.text) return result.text;
  if (!fs.existsSync(filePath)) return "";
  try { return fs.readFileSync(filePath, "utf8"); } catch { return ""; }
}

function readMemoryRecords(limit = 20) {
  const records = [];
  if (!fs.existsSync(CSF_MEMORY_PATH)) return records;
  const files = fs.readdirSync(CSF_MEMORY_PATH, { recursive: true })
    .filter(f => String(f).endsWith(".jsonl"));
  for (const file of files) {
    const text = _readText(path.join(CSF_MEMORY_PATH, file));
    const lines = text.trim().split("\n").filter(Boolean);
    for (const line of lines) {
      try { records.push(JSON.parse(line)); } catch {}
    }
    if (records.length >= limit) break;
  }
  return records.slice(0, limit);
}

function readIngestDocs(limit = 3) {
  if (!fs.existsSync(CSF_INGEST_PATH)) return [];
  return fs.readdirSync(CSF_INGEST_PATH, { recursive: true })
    .filter(f => String(f).endsWith(".md"))
    .sort().reverse()
    .slice(0, limit)
    .map(f => {
      const content = _readText(path.join(CSF_INGEST_PATH, String(f))).trim();
      return { name: String(f), content: content.slice(0, 400) };
    });
}

// Keyword relevance scoring — returns 0-1 score for how relevant a text is to the query
function relevanceScore(text, query) {
  if (!text || !query) return 0;
  const lower = text.toLowerCase();
  const words = query.toLowerCase().split(/\s+/).filter(w => w.length > 2);
  if (words.length === 0) return 0;
  const hits = words.filter(w => lower.includes(w)).length;
  return hits / words.length;
}

// Query-filtered memory: only return records relevant to the user's message
function queryMemories(message, limit = 3) {
  const allRecords = readMemoryRecords(50);
  if (allRecords.length === 0) return [];
  const scored = allRecords.map(r => {
    const text = r.content?.text || r.content?.raw_input || (r.tags || []).join(" ");
    const tagText = (r.tags || []).join(" ");
    const score = Math.max(relevanceScore(text, message), relevanceScore(tagText, message));
    return { record: r, score };
  });
  scored.sort((a, b) => b.score - a.score);
  // Always return top-N records regardless of score so CSF context is never empty
  return scored.slice(0, limit).map(s => s.record);
}

// Query-filtered ingest docs: only return docs relevant to the message
function queryIngestDocs(message, limit = 2) {
  const allDocs = readIngestDocs(10);
  if (allDocs.length === 0) return [];
  const scored = allDocs.map(d => ({
    doc: d,
    score: Math.max(relevanceScore(d.name, message), relevanceScore(d.content, message)),
  }));
  scored.sort((a, b) => b.score - a.score);
  // Always return top-N docs so context is never empty
  return scored.slice(0, limit).map(s => s.doc);
}

// Query dream journal entries for relevant context
function queryDreamEntries(message, limit = 3) {
  const journalFile = path.join(DREAM_JOURNAL_PATH, `dreams_${new Date().toISOString().slice(0, 7)}.jsonl`);
  const text = _readText(journalFile);
  if (!text) return [];
  const lines = text.trim().split("\n").filter(Boolean);
  const entries = [];
  for (const line of lines) {
    try { entries.push(JSON.parse(line)); } catch {}
  }
  // Score by relevance, prefer entries with actual content
  const scored = entries
    .filter(e => e.text && e.text.length > 10)
    .map(e => {
      const combined = `${e.text} ${(e.tags || []).join(" ")} ${(e.symbols || []).join(" ")}`;
      return { entry: e, score: relevanceScore(combined, message) };
    });
  scored.sort((a, b) => b.score - a.score);
  return scored.slice(0, limit).map(s => s.entry);
}

function loadDoorState() {
  try {
    const text = _readText(DOOR_STATE_PATH);
    if (text) return JSON.parse(text);
  } catch {}
  return { doors: [], lastChoice: null, history: [] };
}

function saveDoorState(state) {
  const dir = path.dirname(DOOR_STATE_PATH);
  if (!fs.existsSync(dir)) fs.mkdirSync(dir, { recursive: true });
  fs.writeFileSync(DOOR_STATE_PATH, JSON.stringify(state, null, 2));
}

function saveDoorChoice(doorText, allDoors) {
  const state = loadDoorState();
  if (doorText) state.lastChoice = doorText;
  state.doors = allDoors;
  state.history.push({
    type: doorText ? "choice" : "offered",
    choice: doorText || null,
    doors: allDoors,
    ts: new Date().toISOString(),
  });
  if (state.history.length > 50) state.history = state.history.slice(-50);
  saveDoorState(state);
}

// Query RAG house knowledge base — returns relevant records by keyword matching
function queryRagHouse(message, limit = 2) {
  try {
    const text = _readText(RAG_HOUSE_PATH);
    if (!text) return [];
    const house = JSON.parse(text);
    if (!house?.ragRecords || !Array.isArray(house.ragRecords)) return [];

    const scored = house.ragRecords.map(r => ({
      ...r,
      score: Math.max(
        relevanceScore(r.content || "", message),
        relevanceScore(r.title || "", message),
        relevanceScore((r.tags || []).join(" "), message)
      ),
    }));

    return scored
      .filter(r => r.score > 0)
      .sort((a, b) => b.score - a.score)
      .slice(0, limit);
  } catch {
    return [];
  }
}

// Old broad context loader (cached, for backwards compat)
function buildCSFContext() {
  const now = Date.now();
  if (_cache.ts && (now - _cache.ts) < CACHE_TTL_MS) {
    return { memories: _cache.memories, ingest: _cache.ingest, doors: loadDoorState() };
  }
  const memories = readMemoryRecords(5);
  const ingest = readIngestDocs(3);
  _cache = { memories, ingest, ts: now };
  return { memories, ingest, doors: loadDoorState() };
}

// New: query-time relevance-filtered context — compact, ~500-1500 chars max
function formatCSFContextForPrompt(message) {
  const parts = [];

  // Relevant memories only (scored by keyword match to message)
  if (message) {
    const memories = queryMemories(message, 3);
    if (memories.length > 0) {
      const memText = memories.map(m => {
        const text = m.content?.text || m.content?.raw_input || "";
        return `- ${text.slice(0, 120)}`;
      }).join("\n");
      parts.push(`Memories:\n${memText}`);
    }

    const ingest = queryIngestDocs(message, 1);
    if (ingest.length > 0) {
      parts.push(`Context: ${ingest[0].content.slice(0, 300)}`);
    }

    const dreams = queryDreamEntries(message, 2);
    if (dreams.length > 0) {
      const dreamText = dreams.map(e => `- ${e.text.slice(0, 100)}`).join("\n");
      parts.push(`Recent dreams:\n${dreamText}`);
    }
  }

  // Door state — compact, always included
  const doors = loadDoorState();
  if (doors.lastChoice || doors.doors.length > 0) {
    const last3 = doors.history.slice(-3).map(h =>
      h.choice ? `chose "${h.choice}"` : `offered [${h.doors.join(" | ")}]`
    ).join("; ");
    parts.push(`Doors: ${last3 || "none yet"}`);
  }

  // RAG house knowledge base — relevant external records
  if (message) {
    const ragRecords = queryRagHouse(message, 2);
    if (ragRecords.length > 0) {
      const ragText = ragRecords.map(r =>
        `- ${r.title || "Knowledge"}: ${(r.content || "").slice(0, 150)}`
      ).join("\n");
      parts.push(`Knowledge base (RAG):\n${ragText}`);
    }
  }

  // CSF delta layer — recurring symbols, mood arc, convergence trend
  try {
    const { formatDeltaContextForPrompt } = require("./csf-delta-store");
    const deltaCtx = formatDeltaContextForPrompt(message);
    if (deltaCtx) parts.push(deltaCtx);
  } catch { /* non-fatal */ }

  return parts.join("\n\n");
}

module.exports = {
  readMemoryRecords,
  readIngestDocs,
  queryMemories,
  queryIngestDocs,
  queryDreamEntries,
  queryRagHouse,
  loadDoorState,
  saveDoorState,
  saveDoorChoice,
  buildCSFContext,
  formatCSFContextForPrompt,
};
