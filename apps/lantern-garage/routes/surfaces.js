// Hub, surfaces directory, and static file catch-all
module.exports = async function surfaceRoutes(req, res, url, deps) {
  const { fs, path, sendJson, sendFile, repoRoot, publicRoot, __dirname: dir } = deps;

  if (url.pathname === "/hub") {
    sendFile(res, path.resolve(repoRoot, "central-hub.html"));
    return true;
  }
  if (url.pathname.startsWith("/surfaces/")) {
    const surfacesRoot = path.resolve(dir, "../../surfaces");
    const surfacePath = url.pathname.slice("/surfaces/".length) || "index.html";
    const target = path.resolve(surfacesRoot, surfacePath);
    if (target.startsWith(surfacesRoot)) { sendFile(res, target); return true; }
  }

  // Static file catch-all
  const staticPath = url.pathname === "/" ? "index.html" : url.pathname.slice(1);
  const target = path.resolve(publicRoot, staticPath);
  if (!target.startsWith(publicRoot)) { sendJson(res, { error: "forbidden" }, 403); return true; }
  sendFile(res, target);
  return true;
};
