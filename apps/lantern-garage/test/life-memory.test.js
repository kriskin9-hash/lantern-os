// #1429 — personal-fact detection (Remember stage). Pure, deterministic.
// This module has no store/route/page of its own — see csf-memory-writer.test.js for the
// persistence side (recordLifeFact writes through the ONE canonical CSF memory).
//
// Run: node apps/lantern-garage/test/life-memory.test.js
const assert = require("assert");
const lm = require("../lib/life-memory");

let failures = 0;
function check(name, fn) {
  try { fn(); process.stdout.write(`  ok  - ${name}\n`); }
  catch (e) { failures++; process.stderr.write(`  FAIL- ${name}\n       ${e.message}\n`); }
}

check("extractFact parses possessive 'X's Y is Z'", () => {
  const f = lm.extractFact("my kid's shoe size is 7");
  assert.strictEqual(f.subject, "my kid");
  assert.strictEqual(f.attribute, "shoe size");
  assert.strictEqual(f.value, "7");
});

check("extractFact parses bare 'X is Y'", () => {
  const f = lm.extractFact("the landlord's name is Dana");
  assert.strictEqual(f.subject, "the landlord");
  assert.strictEqual(f.value, "Dana");
  const f2 = lm.extractFact("my favorite coffee order is an oat flat white");
  assert.strictEqual(f2.value, "an oat flat white");
});

check("extractFact strips a trailing period", () =>
  assert.strictEqual(lm.extractFact("Mom's birthday is March 3.").value, "March 3"));

// The critical correctness property: this now gates automatic capture on EVERY chat
// message, so questions must NEVER be treated as fact assertions.
check("extractFact rejects questions (wh-word, ends in '?', auxiliary-inversion)", () => {
  assert.strictEqual(lm.extractFact("what is my kid's shoe size?"), null);
  assert.strictEqual(lm.extractFact("what's my kid's shoe size"), null);  // no '?' but starts with wh-word
  assert.strictEqual(lm.extractFact("is my kid's shoe size 7?"), null);
  assert.strictEqual(lm.extractFact("do you know the landlord's name?"), null);
  assert.strictEqual(lm.extractFact("how is the weather"), null);
});

check("extractFact rejects non-assertions with no catch-all fallback", () => {
  assert.strictEqual(lm.extractFact("hey what's up"), null);
  assert.strictEqual(lm.extractFact("thanks for the help"), null);
  assert.strictEqual(lm.extractFact(""), null);
  assert.strictEqual(lm.extractFact("   "), null);
  assert.strictEqual(lm.extractFact("x".repeat(400)), null); // too long
});

check("categorize buckets by keyword", () => {
  assert.strictEqual(lm.categorize("the landlord's name is Dana"), "people");
  assert.strictEqual(lm.categorize("the project deadline is April 5"), "dates");
  assert.strictEqual(lm.categorize("my shoe size is 7"), "preferences");
  assert.strictEqual(lm.categorize("the gym address is 5th street"), "places");
  assert.strictEqual(lm.categorize("plain unrelated statement is true"), "other");
});

check("keywordsFromFact drops stopwords/short tokens, dedupes", () => {
  const kws = lm.keywordsFromFact({ subject: "my kid", attribute: "shoe size", value: "the size is 7" });
  assert.ok(kws.includes("kid") && kws.includes("shoe") && kws.includes("size"));
  assert.ok(!kws.includes("my") && !kws.includes("the") && !kws.includes("is"));
  assert.strictEqual(kws.filter((w) => w === "size").length, 1); // deduped
});

if (failures) { process.stderr.write(`\n${failures} FAILED\n`); process.exit(1); }
process.stdout.write("\nall life-memory checks passed\n");
