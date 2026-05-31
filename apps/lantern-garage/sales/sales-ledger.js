/**
 * Lantern Garage Sales Ledger
 *
 * Shared data primitives for the local-first sales system.
 * All writes are queued to avoid JSONL corruption under concurrent access.
 */

const fs = require("fs");
const path = require("path");
const crypto = require("crypto");

const repoRoot = path.resolve(__dirname, "..", "..", "..");
const salesDir = path.join(repoRoot, "data", "sales");

const writeQueues = new Map();

function enqueueFileWrite(filePath, operation) {
  const previous = writeQueues.get(filePath) || Promise.resolve();
  const next = previous
    .catch(() => {})
    .then(operation)
    .finally(() => {
      if (writeQueues.get(filePath) === next) {
        writeQueues.delete(filePath);
      }
    });
  writeQueues.set(filePath, next);
  return next;
}

async function appendJsonl(filePath, record) {
  const line = `${JSON.stringify(record)}\n`;
  return enqueueFileWrite(filePath, async () => {
    await fs.promises.mkdir(path.dirname(filePath), { recursive: true });
    await fs.promises.appendFile(filePath, line, "utf8");
  });
}

function readJsonl(filePath) {
  try {
    const text = fs.readFileSync(filePath, "utf8").trim();
    if (!text) return [];
    return text.split("\n").map((line) => {
      try {
        return JSON.parse(line);
      } catch {
        return null;
      }
    }).filter(Boolean);
  } catch {
    return [];
  }
}

function generateId(prefix) {
  const now = new Date();
  const datePart = now.toISOString().slice(0, 10).replace(/-/g, "");
  const rand = crypto.randomBytes(3).toString("hex");
  return `${prefix}_${datePart}_${rand}`;
}

function timestamp() {
  return new Date().toISOString();
}

const files = {
  leads: path.join(salesDir, "leads.jsonl"),
  opportunities: path.join(salesDir, "opportunities.jsonl"),
  outreachLog: path.join(salesDir, "outreach-log.jsonl"),
  smsConsent: path.join(salesDir, "sms-consent.jsonl"),
  paymentReceipts: path.join(salesDir, "payment-receipts.jsonl"),
};

module.exports = {
  repoRoot,
  salesDir,
  files,
  appendJsonl,
  readJsonl,
  generateId,
  timestamp,
};
