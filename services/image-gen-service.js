#!/usr/bin/env node
/**
 * Three Doors Game - Lightweight Image Generation Service
 * Generates images from Stable Diffusion prompts using Hugging Face or local models
 *
 * Run: node services/image-gen-service.js
 * Or via npm: npm run start:image-gen --prefix apps/lantern-garage
 */

const http = require("http");
const fs = require("fs");
const path = require("path");

const PORT = process.env.IMAGE_GEN_PORT || 5555;
const CACHE_DIR = path.join(__dirname, "..", "data", "images", "three-doors");

// Ensure cache directory exists
if (!fs.existsSync(CACHE_DIR)) {
  fs.mkdirSync(CACHE_DIR, { recursive: true });
}

// Mock image generator - in production, call actual Stable Diffusion or local model
async function generateImage(prompt, sceneKey) {
  // Check cache first
  const hash = require("crypto").createHash("md5").update(sceneKey).digest("hex");
  const cachedPath = path.join(CACHE_DIR, `${sceneKey}_${hash}.png`);

  if (fs.existsSync(cachedPath)) {
    return {
      success: true,
      cached: true,
      path: `/images/three-doors/${sceneKey}_${hash}.png`,
      prompt,
      sceneKey
    };
  }

  console.log(`[GEN] Would generate image for: ${sceneKey}`);
  console.log(`[GEN] Prompt: ${prompt.substring(0, 100)}...`);

  // In a real implementation, this would call:
  // - Hugging Face API (requires key)
  // - Local Stable Diffusion WebUI
  // - Local ComfyUI
  // - Ollama with CLIP + Diffusion (if available)

  // For now, return a placeholder that the UI can show
  return {
    success: false,
    reason: "image_generation_not_configured",
    prompt,
    sceneKey,
    message: "Image generation is not configured. Configure STABLE_DIFFUSION_URL, HF_API_KEY, or SD_WEBUI_URL to enable.",
    suggestions: [
      "Install Stable Diffusion WebUI: https://github.com/AUTOMATIC1111/stable-diffusion-webui",
      "Or use ComfyUI: https://github.com/comfyanonymous/ComfyUI",
      "Or set HF_API_KEY for Hugging Face API",
      "Prompts are cached and ready to use with any image generator"
    ]
  };
}

// HTTP Server
const server = http.createServer(async (req, res) => {
  const url = new URL(req.url, `http://localhost:${PORT}`);

  // CORS headers
  res.setHeader("Access-Control-Allow-Origin", "*");
  res.setHeader("Access-Control-Allow-Methods", "GET, POST, OPTIONS");
  res.setHeader("Access-Control-Allow-Headers", "Content-Type");
  res.setHeader("Content-Type", "application/json");

  if (req.method === "OPTIONS") {
    res.writeHead(204);
    res.end();
    return;
  }

  // Health check
  if (url.pathname === "/health") {
    res.writeHead(200);
    res.end(JSON.stringify({ status: "ok", service: "image-gen", port: PORT }));
    return;
  }

  // Generate image endpoint
  if (url.pathname === "/api/generate" && req.method === "POST") {
    let body = "";
    req.on("data", (chunk) => (body += chunk));
    req.on("end", async () => {
      try {
        const data = JSON.parse(body);
        const result = await generateImage(data.prompt, data.scene_key);
        res.writeHead(200);
        res.end(JSON.stringify(result));
      } catch (err) {
        res.writeHead(400);
        res.end(JSON.stringify({ error: err.message }));
      }
    });
    return;
  }

  // List prompts from scenes
  if (url.pathname === "/api/scenes" && req.method === "GET") {
    const prompts = {
      "moss-entry": "atmospheric dreamscape, moss-covered ancient forest doorway...",
      "garden-door": "infinite botanical sanctuary, ancient sequoias beside moon-flowers...",
      "xenon-convergence": "interdimensional space where all choices exist at once...",
      "end-of-time": "the edge of all things, ancient smooth door standing eternal..."
    };
    res.writeHead(200);
    res.end(JSON.stringify(prompts));
    return;
  }

  res.writeHead(404);
  res.end(JSON.stringify({ error: "not found" }));
});

server.listen(PORT, "127.0.0.1", () => {
  console.log(`
╔════════════════════════════════════════════════════════════════╗
║ Three Doors Image Generation Service                          ║
╠════════════════════════════════════════════════════════════════╣
║ Status: Ready                                                   ║
║ Port:   ${PORT}                                                    ║
║ Health: http://127.0.0.1:${PORT}/health                           ║
╠════════════════════════════════════════════════════════════════╣
║ To enable actual image generation:                             ║
║                                                                ║
║ Option 1 - Stable Diffusion WebUI (recommended)               ║
║   git clone https://github.com/AUTOMATIC1111/...              ║
║   export SD_WEBUI_URL=http://127.0.0.1:7860                   ║
║                                                                ║
║ Option 2 - Hugging Face API                                   ║
║   export HF_API_KEY=your_token_here                           ║
║                                                                ║
║ Option 3 - ComfyUI (advanced)                                 ║
║   git clone https://github.com/comfyanonymous/ComfyUI         ║
║   export COMFYUI_URL=http://127.0.0.1:8188                    ║
╚════════════════════════════════════════════════════════════════╝
  `);
});

process.on("SIGINT", () => {
  console.log("[IMG] Shutting down...");
  process.exit(0);
});
