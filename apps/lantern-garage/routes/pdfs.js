const fs = require('fs');
const path = require('path');

function getIngestBase(repoRoot) {
  return path.join(repoRoot, 'data', 'ingest');
}

function scanPdfs(ingestBase, repoRoot) {
  const pdfs = [];

  function scan(dir) {
    if (!fs.existsSync(dir)) return;
    let entries;
    try { entries = fs.readdirSync(dir, { withFileTypes: true }); } catch { return; }
    for (const entry of entries) {
      const full = path.join(dir, entry.name);
      if (entry.isDirectory()) {
        scan(full);
      } else if (entry.isFile() && entry.name.toLowerCase().endsWith('.pdf')) {
        const relative = path.relative(repoRoot, full).replace(/\\/g, '/');
        const folder = path.relative(ingestBase, path.dirname(full)).replace(/\\/g, '/');
        let stat = null;
        try { stat = fs.statSync(full); } catch { /* ignore */ }
        pdfs.push({
          name: path.basename(entry.name, '.pdf'),
          filename: entry.name,
          absolutePath: full,
          repoPath: '/repo/' + relative.split('/').map(encodeURIComponent).join('/'),
          folder,
          size: stat ? stat.size : null,
          createdAt: stat ? (stat.birthtime || stat.ctime).toISOString() : null,
          modifiedAt: stat ? stat.mtime.toISOString() : null,
        });
      }
    }
  }

  scan(ingestBase);
  return pdfs;
}

module.exports = async function pdfRoutes(req, res, url, deps) {
  const { sendJson, repoRoot } = deps;
  const ingestBase = getIngestBase(repoRoot);

  // GET /api/pdfs — list all unique PDFs
  if (url.pathname === '/api/pdfs' && req.method === 'GET') {
    const pdfs = scanPdfs(ingestBase, repoRoot);

    // Deduplicate by filename — keep first occurrence when both ingest folders have the same file
    const seen = new Set();
    const unique = pdfs.filter(p => {
      const key = p.filename.toLowerCase();
      if (seen.has(key)) return false;
      seen.add(key);
      return true;
    }).map(({ absolutePath, ...rest }) => rest); // strip internal absolutePath from response

    unique.sort((a, b) => a.name.localeCompare(b.name, undefined, { sensitivity: 'base' }));
    sendJson(res, { pdfs: unique, total: unique.length });
    return true;
  }

  // DELETE /api/pdfs?filename=<name> — remove all copies of a file from all ingest folders
  if (url.pathname === '/api/pdfs' && req.method === 'DELETE') {
    const filename = url.searchParams.get('filename');
    if (!filename || filename.includes('/') || filename.includes('\\') || !filename.toLowerCase().endsWith('.pdf')) {
      sendJson(res, { error: 'invalid filename' }, 400);
      return true;
    }

    const allPdfs = scanPdfs(ingestBase, repoRoot);
    const matches = allPdfs.filter(p => p.filename.toLowerCase() === filename.toLowerCase());

    if (!matches.length) {
      sendJson(res, { error: 'not_found' }, 404);
      return true;
    }

    const deleted = [];
    const errors = [];
    for (const match of matches) {
      // Safety: ensure path stays inside ingest folder
      if (!match.absolutePath.startsWith(ingestBase)) {
        errors.push({ path: match.absolutePath, error: 'outside ingest boundary' });
        continue;
      }
      try {
        fs.unlinkSync(match.absolutePath);
        deleted.push(match.absolutePath);
      } catch (e) {
        errors.push({ path: match.absolutePath, error: e.message });
      }
    }

    sendJson(res, { deleted: deleted.length, errors, filename });
    return true;
  }

  return false;
};
