// Repo file serving and markdown viewer
module.exports = async function fileRoutes(req, res, url, deps) {
  const { fs, path, sendJson, sendFile, sendHtml, repoRoot, renderMarkdownDocument } = deps;

  if (url.pathname.startsWith("/repo/")) {
    const relative = decodeURIComponent(url.pathname.replace(/^\/repo\//, ""));
    const target = path.resolve(repoRoot, relative);
    if (!target.startsWith(repoRoot)) { sendJson(res, { error: "forbidden" }, 403); return true; }
    if (!fs.existsSync(target)) { sendJson(res, { error: "not_found" }, 404); return true; }
    const ext = path.extname(target).toLowerCase();
    if (ext === ".md" || ext === ".txt") {
      sendHtml(res, renderMarkdownDocument(fs.readFileSync(target, "utf8"), relative));
      return true;
    }
    sendFile(res, target);
    return true;
  }
  if (url.pathname === "/view") {
    const relative = decodeURIComponent(url.searchParams.get("path") || "");
    const target = path.resolve(repoRoot, relative);
    if (!relative || !target.startsWith(repoRoot)) { sendJson(res, { error: "forbidden" }, 403); return true; }
    if (!fs.existsSync(target)) { sendJson(res, { error: "not_found" }, 404); return true; }
    if (path.extname(target).toLowerCase() === ".md") {
      sendHtml(res, renderMarkdownDocument(fs.readFileSync(target, "utf8"), relative));
      return true;
    }
    sendFile(res, target);
    return true;
  }
};
