/**
 * Unit tests for compactHistory() and buildProviderMessages()
 * Pure unit tests — no server required.
 * Run: node tests/test_compact_history.js
 */

const assert = require("assert");

// Inline the functions under test (avoids server deps from stream-chat.js)
const FULL_FIDELITY_RECENT_TURNS = 2;
const MID_FIDELITY_TURNS = 2;
const MID_FIDELITY_CHAR_LIMIT = 200;
const LOW_FIDELITY_WORD_LIMIT = 10;

function compactHistory(history) {
  if (!Array.isArray(history) || history.length === 0) return [];
  return history.map((h, i) => {
    const text = String(h.text != null ? h.text : (h.content != null ? h.content : ""));
    const role = h.role || "user";
    if (i >= history.length - FULL_FIDELITY_RECENT_TURNS) {
      return { role, text };
    }
    if (i >= history.length - FULL_FIDELITY_RECENT_TURNS - MID_FIDELITY_TURNS) {
      const truncated = text.length > MID_FIDELITY_CHAR_LIMIT
        ? text.slice(0, MID_FIDELITY_CHAR_LIMIT) + "…"
        : text;
      return { role, text: truncated };
    }
    const words = text.trim().split(/\s+/).filter(Boolean).slice(0, LOW_FIDELITY_WORD_LIMIT).join(" ");
    const roleLabel = role === "assistant" ? "Lantern" : "Dreamer";
    const summary = words.length > 0 ? `[${roleLabel}: ${words}…]` : `[${roleLabel}]`;
    return { role, text: summary };
  });
}

function buildProviderMessages(systemPrompt, compacted, currentMessage) {
  return [
    { role: "system", content: systemPrompt },
    ...compacted.map(h => ({ role: h.role, content: h.text })),
    { role: "user", content: currentMessage },
  ];
}

let passed = 0;
let failed = 0;

function test(name, fn) {
  try {
    fn();
    process.stdout.write(`  ✓ ${name}\n`);
    passed++;
  } catch (err) {
    process.stderr.write(`  ✗ ${name}\n`);
    process.stderr.write(`    ${err.message}\n`);
    failed++;
  }
}

process.stdout.write("\ncompactHistory() unit tests\n\n");

// ── empty / null / non-array ─────────────────────────────────────────────────
test("null input returns empty array", () => {
  assert.deepStrictEqual(compactHistory(null), []);
});

test("undefined input returns empty array", () => {
  assert.deepStrictEqual(compactHistory(undefined), []);
});

test("empty array returns empty array", () => {
  assert.deepStrictEqual(compactHistory([]), []);
});

test("non-array (string) returns empty array", () => {
  assert.deepStrictEqual(compactHistory("hello"), []);
});

// ── 1–2 turns remain full fidelity ──────────────────────────────────────────
test("single turn is full fidelity", () => {
  const h = [{ role: "user", text: "hello world" }];
  const out = compactHistory(h);
  assert.strictEqual(out[0].text, "hello world");
  assert.strictEqual(out[0].role, "user");
});

test("two turns are both full fidelity", () => {
  const h = [
    { role: "user", text: "first" },
    { role: "assistant", text: "second" },
  ];
  const out = compactHistory(h);
  assert.strictEqual(out[0].text, "first");
  assert.strictEqual(out[1].text, "second");
});

// ── 3–4 turns: older ones get 200-char truncation ───────────────────────────
test("3-turn history: oldest turn gets mid-fidelity truncation at 200 chars", () => {
  const long = "x".repeat(300);
  const h = [
    { role: "user", text: long },
    { role: "assistant", text: "second" },
    { role: "user", text: "third" },
  ];
  const out = compactHistory(h);
  assert.ok(out[0].text.length <= MID_FIDELITY_CHAR_LIMIT + 1, "should be truncated to 200 + ellipsis");
  assert.ok(out[0].text.endsWith("…"), "should end with ellipsis");
  assert.strictEqual(out[1].text, "second");
  assert.strictEqual(out[2].text, "third");
});

test("4-turn history: turns 0-1 get mid-fidelity, turns 2-3 are full", () => {
  const long = "a".repeat(300);
  const h = [
    { role: "user", text: long },
    { role: "assistant", text: long },
    { role: "user", text: "recent" },
    { role: "assistant", text: "latest" },
  ];
  const out = compactHistory(h);
  assert.ok(out[0].text.endsWith("…"), "turn 0 should be mid-fidelity");
  assert.ok(out[1].text.endsWith("…"), "turn 1 should be mid-fidelity");
  assert.strictEqual(out[2].text, "recent");
  assert.strictEqual(out[3].text, "latest");
});

// ── 5+ turns: oldest turns get low-fidelity summary ─────────────────────────
test("6-turn history: turns 0-1 are low-fidelity, 2-3 are mid, 4-5 are full", () => {
  const long = "word ".repeat(20).trim();
  const h = [
    { role: "user", text: long },
    { role: "assistant", text: long },
    { role: "user", text: long },
    { role: "assistant", text: long },
    { role: "user", text: "recent" },
    { role: "assistant", text: "latest" },
  ];
  const out = compactHistory(h);
  assert.ok(out[0].text.startsWith("[Dreamer:"), "turn 0 should be low-fidelity Dreamer label");
  assert.ok(out[1].text.startsWith("[Lantern:"), "turn 1 should be low-fidelity Lantern label");
  assert.ok(!out[2].text.startsWith("["), "turn 2 should be mid-fidelity (not low-fidelity label)");
  assert.ok(!out[3].text.startsWith("["), "turn 3 should be mid-fidelity (not low-fidelity label)");
  assert.strictEqual(out[4].text, "recent");
  assert.strictEqual(out[5].text, "latest");
});

test("low-fidelity summary contains at most LOW_FIDELITY_WORD_LIMIT words", () => {
  const long = "one two three four five six seven eight nine ten eleven twelve".repeat(2);
  const h = Array.from({ length: 6 }, (_, i) => ({ role: "user", text: long }));
  const out = compactHistory(h);
  const words = out[0].text.replace(/\[Dreamer: /, "").replace("…]", "").split(" ");
  assert.ok(words.length <= LOW_FIDELITY_WORD_LIMIT, `too many words: ${words.length}`);
});

// ── edge cases: non-string text/content ─────────────────────────────────────
test("numeric text is coerced to string", () => {
  const h = [{ role: "user", text: 42 }, { role: "assistant", text: 99 }];
  const out = compactHistory(h);
  assert.strictEqual(typeof out[0].text, "string");
  assert.strictEqual(typeof out[1].text, "string");
});

test("null text falls back to content field", () => {
  const h = [{ role: "user", content: "from content" }, { role: "assistant", text: "reply" }];
  const out = compactHistory(h);
  assert.strictEqual(out[0].text, "from content");
});

test("missing text and content produces empty string, not ellipsis", () => {
  const h = Array.from({ length: 6 }, () => ({ role: "user" }));
  const out = compactHistory(h);
  assert.strictEqual(out[0].text, "[Dreamer]", "empty text should produce bare label, no ellipsis");
});

// ── missing role ─────────────────────────────────────────────────────────────
test("missing role defaults to 'user'", () => {
  const h = [{ text: "no role here" }, { text: "second" }];
  const out = compactHistory(h);
  assert.strictEqual(out[0].role, "user");
});

// ── no mutation of input ─────────────────────────────────────────────────────
test("input history is not mutated", () => {
  const original = "x".repeat(300);
  const h = [
    { role: "user", text: original },
    { role: "assistant", text: original },
    { role: "user", text: "recent" },
    { role: "assistant", text: "latest" },
  ];
  compactHistory(h);
  assert.strictEqual(h[0].text, original, "original entry should not be modified");
});

// ── buildProviderMessages ────────────────────────────────────────────────────
process.stdout.write("\nbuildProviderMessages() unit tests\n\n");

test("returns system + history + user message", () => {
  const compacted = [{ role: "user", text: "hi" }, { role: "assistant", text: "hello" }];
  const msgs = buildProviderMessages("SYS", compacted, "new message");
  assert.strictEqual(msgs[0].role, "system");
  assert.strictEqual(msgs[0].content, "SYS");
  assert.strictEqual(msgs[1].role, "user");
  assert.strictEqual(msgs[1].content, "hi");
  assert.strictEqual(msgs[2].role, "assistant");
  assert.strictEqual(msgs[2].content, "hello");
  assert.strictEqual(msgs[3].role, "user");
  assert.strictEqual(msgs[3].content, "new message");
});

test("empty compacted history produces system + user only", () => {
  const msgs = buildProviderMessages("SYS", [], "hello");
  assert.strictEqual(msgs.length, 2);
  assert.strictEqual(msgs[0].role, "system");
  assert.strictEqual(msgs[1].role, "user");
});

// ── Summary ──────────────────────────────────────────────────────────────────
const total = passed + failed;
process.stdout.write(`\n${passed}/${total} passed\n`);
if (failed > 0) {
  process.stderr.write(`${failed} failed\n`);
  process.exit(1);
}
