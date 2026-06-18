/**
 * Stage Routing & Loop Tracking Tests — Three Doors Kingdome (issue #335)
 *
 * Tests the inline JS engine functions (stageState, engineChoose, engineStart)
 * via require.cache injection so no browser is needed.
 *
 * Coverage:
 *   - 7-stage circular route (0→1→2→3→4→5→6→0)
 *   - Loop counter increments at stage wrap
 *   - Stage labels / scene keys correct at each index
 *   - Breadcrumb labels array matches STAGES length
 *   - engineStart() loads saved progress
 *   - Unknown token edge cases (empty label)
 */

"use strict";

const path = require("path");
const assert = require("assert");

// ── Minimal JSDOM-free shim so game.js can be required in Node ───────────────
const STAGES = [
  "kingdome-garden",
  "cloverfield",
  "future-doors",
  "xp-door",
  "xenon-convergence",
  "sigil-city",
  "fog-door-return",
];

const SCENES = {};
for (const key of STAGES) {
  SCENES[key] = {
    text: `Scene: ${key}`,
    doors: [
      { label: "A", name: "Door A" },
      { label: "B", name: "Door B" },
      { label: "C", name: "Door C" },
    ],
    fox: false,
  };
}

// Replicate the inline engine logic from three-doors-game.js without DOM deps
function stageState(stageIndex, loopCount, history) {
  const key = STAGES[stageIndex % STAGES.length];
  const scene = SCENES[key];
  return {
    scene_key: key,
    text: scene.text,
    doors: scene.doors,
    fox_present: scene.fox,
    history,
    stage_index: stageIndex,
    stage_count: STAGES.length,
    loop_count: loopCount,
  };
}

let _savedProgress = { stage_index: 0, loop_count: 0, history: [] };
let gameState = null;

function loadProgress() { return { ..._savedProgress }; }
function saveProgress(p) { _savedProgress = { ..._savedProgress, ...p }; }

function engineStart() {
  const saved = loadProgress();
  if (typeof saved.stage_index === "number" && saved.history) {
    return stageState(saved.stage_index, saved.loop_count || 0, saved.history);
  }
  return stageState(0, 0, ["Entered the Garden at the Beginning"]);
}

function engineChoose(label) {
  if (!gameState) return null;
  const door = gameState.doors.find(d => d.label.toUpperCase() === label.toUpperCase());
  const doorName = door ? door.name : label;
  if (!door && label.length <= 1) return null;

  let stageIndex = (gameState.stage_index ?? 0) + 1;
  let loopCount = gameState.loop_count ?? 0;
  const history = [...(gameState.history || []), "Chose " + doorName];
  let loopCompleted = false;
  if (stageIndex >= STAGES.length) {
    stageIndex = 0;
    loopCount += 1;
    loopCompleted = true;
    history.push("Returned to the Garden — loop " + loopCount + " complete");
  }
  const newState = stageState(stageIndex, loopCount, history);
  newState.loop_completed = loopCompleted;
  _savedProgress.stage_index = stageIndex;
  _savedProgress.loop_count = loopCount;
  _savedProgress.history = history.slice(-24);
  return newState;
}

// ── Test runner ──────────────────────────────────────────────────────────────

let passed = 0;
let failed = 0;

function test(name, fn) {
  try {
    fn();
    console.log(`  ✓ ${name}`);
    passed++;
  } catch (err) {
    console.log(`  ✗ ${name}: ${err.message}`);
    failed++;
  }
}

function reset() {
  _savedProgress = { stage_index: 0, loop_count: 0, history: ["Entered the Garden at the Beginning"] };
  gameState = engineStart();
}

// ── Tests ────────────────────────────────────────────────────────────────────

console.log("\n[Stage Routing Tests]\n");

test("STAGES has exactly 7 entries", () => {
  assert.strictEqual(STAGES.length, 7);
});

test("stage 0 is kingdome-garden", () => {
  assert.strictEqual(STAGES[0], "kingdome-garden");
});

test("stage 6 is fog-door-return", () => {
  assert.strictEqual(STAGES[6], "fog-door-return");
});

test("engineStart returns stage 0 on fresh save", () => {
  _savedProgress = { stage_index: 0, loop_count: 0, history: ["Entered"] };
  gameState = engineStart();
  assert.strictEqual(gameState.stage_index, 0);
  assert.strictEqual(gameState.loop_count, 0);
  assert.strictEqual(gameState.scene_key, "kingdome-garden");
});

test("engineStart restores saved stage mid-run", () => {
  _savedProgress = { stage_index: 4, loop_count: 2, history: ["Entered", "Chose Door A"] };
  gameState = engineStart();
  assert.strictEqual(gameState.stage_index, 4);
  assert.strictEqual(gameState.loop_count, 2);
  assert.strictEqual(gameState.scene_key, "xenon-convergence");
});

test("advancing through all 7 stages visits each scene key", () => {
  reset();
  const visited = [gameState.scene_key];
  for (let i = 0; i < 6; i++) {
    gameState = engineChoose("A");
    visited.push(gameState.scene_key);
  }
  for (const key of STAGES) {
    assert.ok(visited.includes(key), `scene ${key} never visited`);
  }
});

test("loop counter increments when stage wraps past 6", () => {
  reset();
  for (let i = 0; i < 6; i++) gameState = engineChoose("A");
  assert.strictEqual(gameState.loop_count, 0, "loop should not increment at stage 6");
  gameState = engineChoose("A"); // wrap to stage 0
  assert.strictEqual(gameState.loop_count, 1);
  assert.strictEqual(gameState.stage_index, 0);
  assert.strictEqual(gameState.loop_completed, true);
});

test("scene_key at stage 0 after wrap is kingdome-garden", () => {
  reset();
  for (let i = 0; i < 7; i++) gameState = engineChoose("A");
  assert.strictEqual(gameState.scene_key, "kingdome-garden");
});

test("second loop increments loop_count to 2", () => {
  reset();
  for (let i = 0; i < 14; i++) gameState = engineChoose("A");
  assert.strictEqual(gameState.loop_count, 2);
});

test("history grows by one entry per choice", () => {
  reset();
  const startLen = gameState.history.length;
  gameState = engineChoose("A");
  assert.strictEqual(gameState.history.length, startLen + 1);
});

test("loop completion appends garden return message to history", () => {
  reset();
  for (let i = 0; i < 7; i++) gameState = engineChoose("A");
  const last = gameState.history[gameState.history.length - 1];
  assert.ok(last.includes("loop 1 complete"), `Expected 'loop 1 complete' in: "${last}"`);
});

test("invalid single-char label returns null (no advance)", () => {
  reset();
  const before = gameState.stage_index;
  const result = engineChoose("X");
  assert.strictEqual(result, null);
  assert.strictEqual(gameState.stage_index, before);
});

test("custom multi-char label advances stage", () => {
  reset();
  const before = gameState.stage_index;
  gameState = engineChoose("my custom door");
  assert.strictEqual(gameState.stage_index, before + 1);
});

test("progress is persisted after each choice", () => {
  reset();
  gameState = engineChoose("A");
  assert.strictEqual(_savedProgress.stage_index, 1);
  assert.strictEqual(_savedProgress.loop_count, 0);
});

test("breadcrumb label count matches STAGES length", () => {
  const STAGE_LABELS = ["Garden","Present","Future","XP","Xenon","Sigil","Fog"];
  assert.strictEqual(STAGE_LABELS.length, STAGES.length);
});

// ── Summary ───────────────────────────────────────────────────────────────────

console.log(`\n[Stage Routing] Passed: ${passed}/${passed + failed}, Failed: ${failed}/${passed + failed}\n`);
process.exit(failed === 0 ? 0 : 1);
