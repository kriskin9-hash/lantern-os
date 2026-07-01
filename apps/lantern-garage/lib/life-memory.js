"use strict";
/**
 * Personal-fact detection for the Remember stage (#1429).
 *
 * The durable-memory capability ("remembers your kid's shoe size across months") does not
 * get its own store, route, or page — per the architectural-convergence gate, it rides on
 * the ONE canonical CSF memory (data/csf_memory) via csf-memory-writer.js::recordLifeFact(),
 * exactly like recordConvergance() does for council interactions. Recall is not a bespoke
 * lookup either: every chat turn already calls formatCSFContextForPromptAsync(message)
 * (stream-chat.js/dream-chat.js), which retrieves + IDF-ranks relevant memories (#1689/#1690)
 * into context — a fact written here is recalled by that existing pipeline, automatically.
 *
 * This module is just the pure, reusable pattern-matching: does a message assert a fact worth
 * persisting, and if so, what bucket does it belong to. No I/O, no persistence — that's
 * csf-memory-writer.js's job (single canonical writer, not a second one).
 */

const STOP = new Set("the a an is are was were be of to in on at my your his her their our its and".split(" "));
const QUESTION_START = /^\s*(?:what|who|whom|when|where|why|how|is|are|was|were|do|does|did|can|could|would|should|will|shall|may|might)\b/i;

const CATEGORIES = [
  { name: "people", re: /\b(name|brother|sister|mom|dad|mother|father|kid|son|daughter|wife|husband|friend|landlord|boss|doctor|neighbor|partner)\b/i },
  { name: "dates", re: /\b(birthday|anniversary|due date|appointment|deadline|march|april|may|june|july|august|january|february|october|november|december|\d{4})\b/i },
  { name: "places", re: /\b(address|street|city|live|lives|home|office|restaurant|gym|school)\b/i },
  { name: "preferences", re: /\b(size|favorite|favourite|allergic|allergy|likes?|loves?|hates?|prefers?|order|coffee)\b/i },
  { name: "events", re: /\b(argument|fight|met|trip|vacation|wedding|moved|started|quit|happened)\b/i },
];

function categorize(text) {
  for (const c of CATEGORIES) if (c.re.test(text)) return c.name;
  return "other";
}

// Strict fact-assertion detector. Returns null unless the message is unambiguously a
// declarative statement ("my kid's shoe size is 7", "the landlord's name is Dana") — no
// catch-all fallback, because this now gates automatic capture against EVERY chat message,
// not a form the user deliberately submitted. Questions ("what is my kid's shoe size?",
// "is my kid's shoe size 7?") must NOT match, or every question would get stored as a fact.
function extractFact(text) {
  const t = String(text || "").trim();
  if (!t || t.length > 300) return null;          // too long to be a single fact statement
  if (/\?\s*$/.test(t)) return null;               // ends in "?" — a question, not an assertion
  if (QUESTION_START.test(t)) return null;         // starts with a question word/auxiliary
  const body = t.replace(/\.$/, "");

  let m = body.match(/^(.{2,60}?)'s\s+(.{2,60}?)\s+(?:is|are|was)\s+(.{1,200})$/i);
  if (m) return { subject: m[1].trim(), attribute: m[2].trim(), value: m[3].trim() };

  m = body.match(/^(.{2,80}?)\s+(?:is|are|was)\s+(.{1,200})$/i);
  if (m) return { subject: m[1].trim(), attribute: m[1].trim(), value: m[2].trim() };

  return null;
}

function keywordsFromFact(fact) {
  const seen = new Set();
  const out = [];
  for (const w of `${fact.subject} ${fact.attribute} ${fact.value}`.toLowerCase().split(/[^a-z0-9]+/)) {
    if (w.length <= 2 || STOP.has(w) || seen.has(w)) continue;
    seen.add(w);
    out.push(w);
  }
  return out;
}

module.exports = { CATEGORIES, categorize, extractFact, keywordsFromFact };
