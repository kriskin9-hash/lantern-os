// Training data collection and LoRA training management
// POST /api/dream/training/collect  — save a Pollinations image + prompt as training sample
// GET  /api/dream/training/status   — image count, training state
// POST /api/dream/training/start    — launch Python LoRA training

const https = require("https");
const http = require("http");

function downloadImage(url, destPath, fs) {
  return new Promise((resolve, reject) => {
    const client = url.startsWith("https") ? https : http;
    const file = fs.createWriteStream(destPath);
    const req = client.get(url, (res) => {
      if (res.statusCode !== 200) {
        file.destroy();
        fs.unlink(destPath, () => {});
        return reject(new Error(`HTTP ${res.statusCode}`));
      }
      res.pipe(file);
      file.on("finish", () => { file.close(); resolve(); });
    });
    req.setTimeout(30000, () => { req.destroy(); reject(new Error("download timeout")); });
    req.on("error", (e) => { file.destroy(); fs.unlink(destPath, () => {}); reject(e); });
  });
}

module.exports = async function trainingRoutes(req, res, url, deps) {
  const { fs, path, sendJson, collectRequestBody, appendJsonlQueued, repoRoot } = deps;

  const imageDir = path.join(repoRoot, "data", "images", "generated-doors");
  const manifestPath = path.join(repoRoot, "data", "training", "lora-training.jsonl");

  // ── Collect a Pollinations-generated image ───────────────────────
  if (url.pathname === "/api/dream/training/collect" && req.method === "POST") {
    try {
      const body = JSON.parse(await collectRequestBody(req));
      const { sceneKey, prompt, imageUrl, playerChoice, loopCount, stageIndex } = body;
      if (!sceneKey || !imageUrl) { sendJson(res, { error: "sceneKey and imageUrl required" }, 400); return true; }

      // Ensure directories exist
      if (!fs.existsSync(imageDir)) fs.mkdirSync(imageDir, { recursive: true });
      const trainingDir = path.join(repoRoot, "data", "training");
      if (!fs.existsSync(trainingDir)) fs.mkdirSync(trainingDir, { recursive: true });

      const timestamp = Date.now();
      const baseName = `${sceneKey}_${timestamp}`;
      const imgPath = path.join(imageDir, `${baseName}.jpg`);
      const captionPath = path.join(imageDir, `${baseName}.txt`);

      await downloadImage(imageUrl, imgPath, fs);

      // Caption — rich enough for LoRA to learn the style
      const caption = `three doors dreamworld, ${prompt || sceneKey}, fantasy dreamscape, painterly, cinematic light, mystical atmosphere, lantern-lit`;
      fs.writeFileSync(captionPath, caption, "utf8");

      const entry = {
        id: baseName,
        sceneKey,
        prompt: caption,
        imagePath: imgPath,
        playerChoice: playerChoice || "",
        loopCount: loopCount || 0,
        stageIndex: stageIndex || 0,
        collectedAt: new Date().toISOString(),
      };
      await appendJsonlQueued(manifestPath, entry);

      // Count total
      let total = 0;
      try { total = fs.readFileSync(manifestPath, "utf8").trim().split("\n").filter(Boolean).length; } catch {}

      sendJson(res, { ok: true, id: baseName, total });
    } catch (e) {
      sendJson(res, { error: e.message }, 500);
    }
    return true;
  }

  // ── Training status ──────────────────────────────────────────────
  if (url.pathname === "/api/dream/training/status" && req.method === "GET") {
    let imageCount = 0;
    let lastCheckpoint = null;
    let trainingActive = false;
    let latestModelPath = null;

    try {
      if (fs.existsSync(imageDir)) {
        imageCount = fs.readdirSync(imageDir).filter(f => f.endsWith(".jpg")).length;
      }
    } catch {}

    try {
      const loraDir = path.join(repoRoot, "data", "models", "lora");
      if (fs.existsSync(loraDir)) {
        const runs = fs.readdirSync(loraDir).filter(d =>
          d.startsWith("three-doors-") && fs.statSync(path.join(loraDir, d)).isDirectory()
        ).sort().reverse();
        if (runs.length) {
          latestModelPath = path.join(loraDir, runs[0]);
          const contents = fs.readdirSync(latestModelPath);
          const checkpoints = contents.filter(f => f.includes("checkpoint") || f.endsWith(".safetensors"));
          if (checkpoints.length) lastCheckpoint = checkpoints.sort().pop();
          trainingActive = contents.includes("training.pid");
        }
      }
    } catch {}

    sendJson(res, { imageCount, trainingActive, lastCheckpoint, latestModelPath, minImagesForTraining: 15 });
    return true;
  }

  // ── Launch LoRA training ─────────────────────────────────────────
  if (url.pathname === "/api/dream/training/start" && req.method === "POST") {
    let imageCount = 0;
    try { imageCount = fs.readdirSync(imageDir).filter(f => f.endsWith(".jpg")).length; } catch {}
    if (imageCount < 15) {
      sendJson(res, { error: `Need at least 15 images, have ${imageCount}. Keep playing!` }, 400);
      return true;
    }

    const loraDir = path.join(repoRoot, "data", "models", "lora");
    if (!fs.existsSync(loraDir)) fs.mkdirSync(loraDir, { recursive: true });
    const sessionName = `three-doors-${new Date().toISOString().slice(0, 10)}`;
    const outputDir = path.join(loraDir, sessionName);
    if (!fs.existsSync(outputDir)) fs.mkdirSync(outputDir, { recursive: true });

    const py = process.platform === "win32" ? "python" : "python3";
    const scriptPath = path.join(repoRoot, "scripts", "train-three-doors-lora.py");
    const logPath = path.join(outputDir, "training.log");
    const pidPath = path.join(outputDir, "training.pid");

    const { spawn } = require("child_process");
    const proc = spawn(py, [
      scriptPath,
      "--image_dir", imageDir,
      "--output_dir", outputDir,
      "--manifest", manifestPath,
    ], {
      cwd: repoRoot,
      detached: true,
      stdio: ["ignore", fs.openSync(logPath, "w"), fs.openSync(logPath, "a")],
    });

    fs.writeFileSync(pidPath, String(proc.pid), "utf8");
    proc.unref();

    sendJson(res, { started: true, pid: proc.pid, outputDir, logPath, sessionName });
    return true;
  }

  return false;
};
