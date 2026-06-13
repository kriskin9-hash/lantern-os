module.exports = async function filesUploadRoutes(req, res, url, deps) {
  const { fs, path, sendJson, collectRequestBody, appendJsonlQueued, repoRoot } = deps;

  // POST /api/files/upload — Accept base64-encoded file in JSON
  if (url.pathname === "/api/files/upload" && req.method === "POST") {
    try {
      const raw = await collectRequestBody(req);
      const body = JSON.parse(raw || "{}");
      const fileName = String(body.fileName || "document.txt").slice(0, 256);
      const fileContent = String(body.content || "").trim();
      const mimeType = String(body.mimeType || "text/plain").slice(0, 100);

      if (!fileContent) {
        sendJson(res, { error: "content field required (base64 or plain text)" }, 400);
        return true;
      }

      const uploadDir = path.join(repoRoot, "data", "file-uploads");
      if (!fs.existsSync(uploadDir)) fs.mkdirSync(uploadDir, { recursive: true });

      const fileId = `file_${Date.now()}_${Math.random().toString(36).substr(2, 6)}`;
      const filePath = path.join(uploadDir, `${fileId}_${fileName}`);

      // Handle both base64 and plain text
      let buffer;
      if (body.isBase64) {
        buffer = Buffer.from(fileContent, "base64");
      } else {
        buffer = Buffer.from(fileContent, "utf8");
      }

      fs.writeFileSync(filePath, buffer);

      const entry = {
        fileId,
        fileName,
        mimeType,
        size: buffer.length,
        uploadedAt: new Date().toISOString(),
        processed: false,
        chunkCount: 0,
        metadata: body.metadata || {},
      };

      const uploadLogPath = path.join(uploadDir, "uploads.jsonl");
      await appendJsonlQueued(uploadLogPath, entry);

      // Queue document processing (non-blocking)
      setImmediate(() => processDocumentAsync(fileId, filePath, entry, deps));

      sendJson(res, { ...entry, message: "File queued for processing" });
    } catch (error) {
      sendJson(res, { error: error.message }, 400);
    }
    return true;
  }

  // GET /api/files/{fileId}/status — Check processing status
  if (url.pathname.match(/^\/api\/files\/[a-z0-9_-]+\/status$/) && req.method === "GET") {
    try {
      const fileId = url.pathname.split("/")[3];
      const uploadDir = path.join(repoRoot, "data", "file-uploads");
      const uploadLogPath = path.join(uploadDir, "uploads.jsonl");

      if (!fs.existsSync(uploadLogPath)) {
        sendJson(res, { error: "file not found" }, 404);
        return true;
      }

      const text = fs.readFileSync(uploadLogPath, "utf8");
      const entries = text.trim().split("\n").filter(Boolean).map(l => {
        try { return JSON.parse(l); } catch { return null; }
      }).filter(Boolean);

      const entry = entries.find(e => e.fileId === fileId);
      if (!entry) {
        sendJson(res, { error: "file not found" }, 404);
        return true;
      }

      sendJson(res, { ...entry });
    } catch (error) {
      sendJson(res, { error: error.message }, 400);
    }
    return true;
  }

  return false;
};

async function processDocumentAsync(fileId, filePath, entry, deps) {
  try {
    const { fs, appendJsonlQueued, repoRoot } = deps;
    const path = require("path");
    const { extractDocumentContent, extractFileMetadata } = require("../lib/document-extractor");
    const { isDuplicate, recordDedupEntry, buildDedupIndex } = require("../lib/document-deduplicator");

    if (!fs.existsSync(filePath)) {
      console.error(`File not found for processing: ${filePath}`);
      return;
    }

    // Extract content with appropriate method (PDF, OCR, plain text)
    const extracted = await extractDocumentContent(filePath, entry.mimeType);
    if (!extracted.content) {
      updateFileProcessingStatus(fileId, {
        processed: false,
        error: `Extraction failed: ${extracted.error}`
      }, deps);
      return;
    }

    // Extract metadata
    const metadata = await extractFileMetadata(filePath);

    // Check for duplicates
    const csfPath = path.join(repoRoot, "data", "csf-ingest", "deltas.jsonl");
    const dedupIndex = buildDedupIndex(csfPath);
    const isDup = isDuplicate(extracted.content, metadata, dedupIndex);

    if (isDup) {
      console.log(`[dedup] Skipping duplicate: ${entry.fileName} (matches ${isDup.fileName})`);
      recordDedupEntry(extracted.content, metadata, filePath);
      updateFileProcessingStatus(fileId, {
        processed: true,
        isDuplicate: true,
        duplicateOf: isDup.fileId,
        chunkCount: 0
      }, deps);
      return;
    }

    // Chunk the document
    const chunks = chunkText(extracted.content, 500);

    // Ingest chunks into CSF memory as document entries
    const { ingestEntry: csfIngest } = require("../lib/csf-delta-store");
    for (let i = 0; i < chunks.length; i++) {
      try {
        csfIngest({
          kind: "document-chunk",
          text: chunks[i],
          tags: [entry.fileName, `chunk:${i + 1}/${chunks.length}`],
          symbols: extractKeywords(chunks[i]),
          source: {
            fileId: fileId,
            fileName: entry.fileName,
            type: path.extname(filePath).slice(1),
            extractionMethod: extracted.method,
            confidence: extracted.confidence
          },
          docMetadata: {
            title: metadata.fileName,
            createdAt: metadata.createdAt,
            modifiedAt: metadata.modifiedAt,
            size: metadata.size,
            pages: extracted.pages
          },
          chunkIdx: i,
          totalChunks: chunks.length,
          timestamp: new Date().toISOString(),
        });
      } catch (e) {
        console.error(`CSF ingest failed for chunk ${i}:`, e.message);
      }
    }

    recordDedupEntry(extracted.content, metadata, filePath);

    // Update entry as processed
    updateFileProcessingStatus(fileId, {
      processed: true,
      chunkCount: chunks.length,
      extractionMethod: extracted.method,
      confidence: extracted.confidence
    }, deps);
  } catch (err) {
    console.error(`Document processing failed for ${fileId}:`, err.message);
    updateFileProcessingStatus(fileId, { processed: false, error: err.message }, deps);
  }
}

function chunkText(text, chunkSize = 500) {
  const chunks = [];
  const sentences = text.match(/[^.!?]*[.!?]+/g) || [text];

  let currentChunk = "";
  for (const sentence of sentences) {
    if ((currentChunk + sentence).length <= chunkSize) {
      currentChunk += sentence;
    } else {
      if (currentChunk) chunks.push(currentChunk.trim());
      currentChunk = sentence;
    }
  }
  if (currentChunk) chunks.push(currentChunk.trim());

  return chunks.filter(c => c.length > 20);
}

function extractKeywords(text, limit = 5) {
  const words = text.toLowerCase().split(/\W+/).filter(w => w.length > 4);
  const freq = {};
  for (const word of words) {
    freq[word] = (freq[word] || 0) + 1;
  }
  return Object.entries(freq)
    .sort((a, b) => b[1] - a[1])
    .slice(0, limit)
    .map(([w]) => w);
}

function updateFileProcessingStatus(fileId, updates, deps) {
  try {
    const { fs, repoRoot } = deps;
    const path = require("path");
    const uploadDir = path.join(repoRoot, "data", "file-uploads");
    const uploadLogPath = path.join(uploadDir, "uploads.jsonl");

    if (!fs.existsSync(uploadLogPath)) return;

    const text = fs.readFileSync(uploadLogPath, "utf8");
    const lines = text.trim().split("\n").filter(Boolean);
    const updated = lines.map(line => {
      try {
        const entry = JSON.parse(line);
        if (entry.fileId === fileId) {
          return JSON.stringify({ ...entry, ...updates });
        }
        return line;
      } catch {
        return line;
      }
    });

    fs.writeFileSync(uploadLogPath, updated.join("\n") + "\n");
  } catch (err) {
    console.error(`Status update failed for ${fileId}:`, err.message);
  }
}
