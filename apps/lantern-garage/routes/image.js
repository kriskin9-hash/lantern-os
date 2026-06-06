/**
 * Image Generation Route
 *
 * POST /api/image/generate  — generate an image
 *   Body: { prompt?: string, version?: "v8"|"v9"|"v10", width?: number, height?: number, seed?: number }
 *   If OPENAI_API_KEY is set and useApi=true, calls DALL-E 3.
 *   Otherwise falls back to procedural Python generation.
 *
 * GET /api/image/list — list generated images in data/images/
 */
const { execSync } = require("child_process");
const fs = require("fs");
const path = require("path");

const MAX_PROMPT_LEN = 1000;

module.exports = function imageRoutes(req, res, url, deps) {
  const { sendJson, collectRequestBody } = deps;

  if (req.method === "POST" && url.pathname === "/api/image/generate") {
    collectRequestBody(req, async (body) => {
      try {
        const data = JSON.parse(body || "{}");
        const prompt = (data.prompt || "").slice(0, MAX_PROMPT_LEN).trim();
        const useApi = data.useApi === true && process.env.OPENAI_API_KEY;
        const version = data.version || "v8";
        const width = data.width || 1024;
        const height = data.height || 768;
        const seed = data.seed ?? Math.floor(Math.random() * 100000);

        if (useApi) {
          // Call Python script in API mode
          const safePrompt = prompt.replace(/"/g, '\\"');
          const cmd = `python scripts/image_generator.py --api --prompt "${safePrompt}"`;
          const output = execSync(cmd, {
            cwd: deps.repoRoot || process.cwd(),
            encoding: "utf8",
            timeout: 60000,
            env: { ...process.env },
          });
          const match = output.match(/saved:\s*(.+)/);
          const imgPath = match ? match[1].trim() : null;
          sendJson(res, {
            mode: "api",
            prompt,
            path: imgPath,
            seed,
            output: output.slice(-500),
          });
          return;
        }

        // Procedural generation
        const cmd = `python scripts/image_generator.py ${version} --width ${width} --height ${height} --seed ${seed}`;
        const output = execSync(cmd, {
          cwd: deps.repoRoot || process.cwd(),
          encoding: "utf8",
          timeout: 120000,
          env: { ...process.env },
        });
        const match = output.match(/saved:\s*(.+)/);
        const imgPath = match ? match[1].trim() : null;

        sendJson(res, {
          mode: "procedural",
          version,
          width,
          height,
          seed,
          prompt: prompt || null,
          path: imgPath,
          output: output.slice(-500),
        });
      } catch (err) {
        sendJson(res, { error: err.message, stderr: err.stderr?.toString() }, 500);
      }
    });
    return true;
  }

  if (req.method === "GET" && url.pathname === "/api/image/list") {
    try {
      const imgDir = path.join(deps.repoRoot || process.cwd(), "data", "images");
      const files = fs.readdirSync(imgDir)
        .filter((f) => /\.(png|jpg|jpeg|webp)$/i.test(f))
        .map((f) => {
          const stat = fs.statSync(path.join(imgDir, f));
          return { name: f, size: stat.size, mtime: stat.mtime.toISOString() };
        })
        .sort((a, b) => new Date(b.mtime) - new Date(a.mtime))
        .slice(0, 50);
      sendJson(res, { images: files, dir: imgDir });
    } catch (err) {
      sendJson(res, { images: [], error: err.message });
    }
    return true;
  }

  return false;
};
