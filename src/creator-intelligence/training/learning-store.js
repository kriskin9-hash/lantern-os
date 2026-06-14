// Creator Intelligence — continuous learning store
// Appends first-party EditEvents (edits, generated/selected variants, exports)
// to data/creator-intelligence/edits/. This is the operator's OWN data, always
// legitimate to keep. `outcome` stays null until real performance data exists.
//
// See docs/creator-v10/research-dataset-schema.md (EditEvent)

"use strict";

const store = require("../dataset/dataset-store");

function nowIso() {
  return new Date().toISOString();
}

function makeId(prefix) {
  return `${prefix}-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`;
}

/**
 * Record that an edit happened.
 * @param {string} entryId  links to data/creator/entries/<id>
 * @param {Object} features measured features of the edit
 */
function recordEdit(entryId, features = {}) {
  return store.appendEdit({
    id: makeId("edit"), entryId, createdAt: nowIso(),
    kind: "edit", features, choice: null, outcome: null,
  });
}

function recordVariantGenerated(entryId, variantId, features = {}) {
  return store.appendEdit({
    id: makeId("vargen"), entryId, createdAt: nowIso(),
    kind: "variant_generated", features, choice: variantId, outcome: null,
  });
}

function recordVariantSelected(entryId, variantId, features = {}) {
  return store.appendEdit({
    id: makeId("varsel"), entryId, createdAt: nowIso(),
    kind: "variant_selected", features, choice: variantId, outcome: null,
  });
}

function recordExport(entryId, features = {}) {
  return store.appendEdit({
    id: makeId("export"), entryId, createdAt: nowIso(),
    kind: "export", features, choice: null, outcome: null,
  });
}

module.exports = {
  recordEdit, recordVariantGenerated, recordVariantSelected, recordExport,
};
