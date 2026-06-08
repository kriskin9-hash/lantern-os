// UI settings: theme, appearance preferences
const path = require("path");

const uiSettingsPath = (repoRoot) => path.join(repoRoot, "data", "ui-settings.json");

function readUiSettings(repoRoot) {
  const settingsPath = uiSettingsPath(repoRoot);
  const fs = require("fs");
  if (!fs.existsSync(settingsPath)) {
    return { theme: "dark", createdAt: new Date().toISOString() };
  }
  try {
    return JSON.parse(fs.readFileSync(settingsPath, "utf8"));
  } catch {
    return { theme: "dark", createdAt: new Date().toISOString() };
  }
}

function writeUiSettings(repoRoot, settings) {
  const fs = require("fs");
  const settingsPath = uiSettingsPath(repoRoot);
  const dir = path.dirname(settingsPath);
  if (!fs.existsSync(dir)) fs.mkdirSync(dir, { recursive: true });
  fs.writeFileSync(settingsPath, JSON.stringify(settings, null, 2), "utf8");
}

module.exports = async (req, res, url, deps) => {
  const { sendJson, repoRoot } = deps;

  // GET /api/ui/theme — retrieve current theme preference
  if (req.method === "GET" && url.pathname === "/api/ui/theme") {
    const settings = readUiSettings(repoRoot);
    return sendJson(res, 200, { theme: settings.theme });
  }

  // POST /api/ui/theme — save theme preference
  if (req.method === "POST" && url.pathname === "/api/ui/theme") {
    const body = await deps.collectRequestBody(req);
    try {
      const { theme } = JSON.parse(body);
      if (!["dark", "light"].includes(theme)) {
        return sendJson(res, 400, { error: "invalid theme" });
      }
      const settings = readUiSettings(repoRoot);
      settings.theme = theme;
      settings.updatedAt = new Date().toISOString();
      writeUiSettings(repoRoot, settings);
      return sendJson(res, 200, { theme, saved: true });
    } catch (e) {
      return sendJson(res, 400, { error: e.message });
    }
  }

  return false; // not handled by this route
};
