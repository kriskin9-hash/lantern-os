// Entry metadata storage system for Creator Dashboard
// Stores entry metadata, analysis, renders, and thumbnails
// Structure:
//   data/creator/entries/
//     entry-id/
//       metadata.json (title, description, tags, timestamps)
//       analysis.json (highlights, scenes, scores)
//       thumbnail.jpg
//       renders/
//         highlight.mp4
//         variantA.mp4
//         variantB.mp4
//         variantC.mp4

const fs = require("fs");
const path = require("path");

const ENTRIES_DIR = "data/creator/entries";

function getEntryDir(repoRoot, entryId) {
  return path.join(repoRoot, ENTRIES_DIR, entryId);
}

function generateEntryId() {
  return `entry-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
}

async function createEntry(repoRoot, entryData) {
  const entryId = generateEntryId();
  const entryDir = getEntryDir(repoRoot, entryId);

  // Ensure directory exists
  fs.mkdirSync(entryDir, { recursive: true });
  fs.mkdirSync(path.join(entryDir, "renders"), { recursive: true });

  // Create metadata
  const metadata = {
    id: entryId,
    title: entryData.title?.trim() || "Untitled",
    description: entryData.description || "",
    project: entryData.project || "",
    tags: Array.isArray(entryData.tags)
      ? entryData.tags
      : typeof entryData.tags === "string"
      ? entryData.tags.split(",").map((t) => t.trim()).filter(Boolean)
      : [],
    type: entryData.type || "video",
    createdAt: new Date().toISOString(),
    updatedAt: new Date().toISOString(),
    filePath: entryData.filePath || null, // Path to original uploaded file
    thumbnail: null, // Path to thumbnail
    analysis: null,
    renders: {
      highlight: null,
      variantA: null,
      variantB: null,
      variantC: null,
    },
    status: "uploaded", // uploaded, analyzing, ready, failed
  };

  const metadataPath = path.join(entryDir, "metadata.json");
  fs.writeFileSync(metadataPath, JSON.stringify(metadata, null, 2));

  return metadata;
}

function getEntry(repoRoot, entryId) {
  const metadataPath = path.join(getEntryDir(repoRoot, entryId), "metadata.json");

  if (!fs.existsSync(metadataPath)) {
    return null;
  }

  const data = JSON.parse(fs.readFileSync(metadataPath, "utf8"));
  return data;
}

function updateEntry(repoRoot, entryId, updates) {
  const metadataPath = path.join(getEntryDir(repoRoot, entryId), "metadata.json");

  if (!fs.existsSync(metadataPath)) {
    throw new Error(`Entry ${entryId} not found`);
  }

  const current = JSON.parse(fs.readFileSync(metadataPath, "utf8"));
  const updated = {
    ...current,
    ...updates,
    updatedAt: new Date().toISOString(),
  };

  fs.writeFileSync(metadataPath, JSON.stringify(updated, null, 2));
  return updated;
}

function saveAnalysis(repoRoot, entryId, analysis) {
  const entryDir = getEntryDir(repoRoot, entryId);
  const analysisPath = path.join(entryDir, "analysis.json");

  fs.writeFileSync(analysisPath, JSON.stringify(analysis, null, 2));

  // Update metadata
  updateEntry(repoRoot, entryId, { analysis: "analysis.json" });
}

function getAnalysis(repoRoot, entryId) {
  const analysisPath = path.join(getEntryDir(repoRoot, entryId), "analysis.json");

  if (!fs.existsSync(analysisPath)) {
    return null;
  }

  return JSON.parse(fs.readFileSync(analysisPath, "utf8"));
}

function saveRender(repoRoot, entryId, type, filePath) {
  // filePath is relative to repo root
  const entryDir = getEntryDir(repoRoot, entryId);
  const renderDir = path.join(entryDir, "renders");

  fs.mkdirSync(renderDir, { recursive: true });

  // Copy or move file to render directory
  const filename = path.basename(filePath);
  const destPath = path.join(renderDir, filename);
  const fullSourcePath = path.join(repoRoot, filePath);
  const fullDestPath = path.join(repoRoot, destPath);

  if (fs.existsSync(fullSourcePath)) {
    fs.copyFileSync(fullSourcePath, fullDestPath);
  }

  // Update metadata
  const entry = getEntry(repoRoot, entryId);
  if (entry) {
    entry.renders[type] = path.relative(repoRoot, fullDestPath);
    updateEntry(repoRoot, entryId, { renders: entry.renders });
  }
}

function saveThumbnail(repoRoot, entryId, filePath) {
  const entryDir = getEntryDir(repoRoot, entryId);
  const thumbnailPath = path.join(entryDir, "thumbnail.jpg");
  const fullSourcePath = path.join(repoRoot, filePath);
  const fullDestPath = path.join(repoRoot, thumbnailPath);

  fs.mkdirSync(entryDir, { recursive: true });

  if (fs.existsSync(fullSourcePath)) {
    fs.copyFileSync(fullSourcePath, fullDestPath);
  }

  // Update metadata
  updateEntry(repoRoot, entryId, { thumbnail: path.relative(repoRoot, fullDestPath) });
}

function listEntries(repoRoot) {
  const entriesDir = path.join(repoRoot, ENTRIES_DIR);

  if (!fs.existsSync(entriesDir)) {
    return [];
  }

  const entries = [];
  const dirs = fs.readdirSync(entriesDir);

  for (const dir of dirs) {
    const metadataPath = path.join(entriesDir, dir, "metadata.json");
    if (fs.existsSync(metadataPath)) {
      const metadata = JSON.parse(fs.readFileSync(metadataPath, "utf8"));
      entries.push(metadata);
    }
  }

  return entries.sort((a, b) => new Date(b.createdAt) - new Date(a.createdAt));
}

function formatTimestamp(isoString) {
  try {
    const date = new Date(isoString);
    const options = {
      year: "numeric",
      month: "short",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    };
    return date.toLocaleDateString("en-US", options);
  } catch (e) {
    return "Unknown date";
  }
}

module.exports = {
  generateEntryId,
  createEntry,
  getEntry,
  updateEntry,
  saveAnalysis,
  getAnalysis,
  saveRender,
  saveThumbnail,
  listEntries,
  formatTimestamp,
  getEntryDir,
};
