/**
 * Web Image Proxy Route
 *
 * GET /api/web-image?url={encodeURIComponent(url)}  — fetch and proxy image from web
 * GET /api/image-search?q={query}  — search for images on the web
 * POST /api/dream/image  — send image URL to dream chat (SSE stream)
 */

const https = require("https");
const http = require("http");

const ALLOWED_DOMAINS = [
  "unsplash.com",
  "pexels.com",
  "pixabay.com",
  "commons.wikimedia.org",
  "upload.wikimedia.org",
  "raw.githubusercontent.com",
  "imgur.com",
  "giphy.com",
  "wikipedia.org",
];

function isAllowedDomain(url) {
  try {
    const urlObj = new URL(url);
    return ALLOWED_DOMAINS.some((d) => urlObj.hostname.includes(d));
  } catch {
    return false;
  }
}

module.exports = function webImageRoutes(req, res, url, deps) {
  const { sendJson, collectRequestBody } = deps;

  // Proxy image from URL with safety checks
  if (req.method === "GET" && url.pathname === "/api/web-image") {
    const imageUrl = url.searchParams.get("url");

    if (!imageUrl) {
      sendJson(res, { error: "Missing url parameter" }, 400);
      return true;
    }

    if (!isAllowedDomain(imageUrl)) {
      sendJson(
        res,
        { error: "Domain not allowed. Supported: unsplash, pexels, pixabay, wikimedia, github, imgur, giphy" },
        403
      );
      return true;
    }

    // Fetch the image
    const protocol = imageUrl.startsWith("https") ? https : http;
    protocol
      .get(imageUrl, { timeout: 10000 }, (imgRes) => {
        if (imgRes.statusCode !== 200) {
          sendJson(res, { error: `Image fetch failed: ${imgRes.statusCode}` }, imgRes.statusCode);
          return;
        }

        // Copy image headers
        const contentType = imgRes.headers["content-type"] || "image/jpeg";
        res.writeHead(200, {
          "Content-Type": contentType,
          "Cache-Control": "public, max-age=3600",
          "Access-Control-Allow-Origin": "*",
        });

        // Stream the image
        imgRes.pipe(res);
      })
      .on("error", (err) => {
        sendJson(res, { error: `Failed to fetch image: ${err.message}` }, 500);
      });

    return true;
  }

  // Search for images (returns direct URLs, no proxy)
  if (req.method === "GET" && url.pathname === "/api/image-search") {
    const query = url.searchParams.get("q");

    if (!query) {
      sendJson(res, { error: "Missing q parameter" }, 400);
      return true;
    }

    // Return URLs to popular image sources
    const sources = [
      {
        title: "Unsplash",
        url: `https://unsplash.com/napi/search/photos?query=${encodeURIComponent(query)}&per_page=1`,
        format: (data) => {
          const results = JSON.parse(data);
          return results.results?.[0]?.urls?.regular || null;
        },
      },
      {
        title: "Pixabay",
        url: `https://pixabay.com/api/?key=DEMO&q=${encodeURIComponent(query)}&per_page=1`,
        format: (data) => {
          const results = JSON.parse(data);
          return results.hits?.[0]?.webformatURL || null;
        },
      },
    ];

    const result = {};
    let completed = 0;

    sources.forEach((source) => {
      https
        .get(source.url, { timeout: 5000 }, (apiRes) => {
          let data = "";
          apiRes.on("data", (chunk) => {
            data += chunk;
          });
          apiRes.on("end", () => {
            try {
              const imageUrl = source.format(data);
              if (imageUrl) result[source.title] = imageUrl;
            } catch {}
            completed++;
            if (completed === sources.length) {
              sendJson(res, result);
            }
          });
        })
        .on("error", () => {
          completed++;
          if (completed === sources.length) {
            sendJson(res, result);
          }
        });
    });

    return true;
  }

  return false;
};
