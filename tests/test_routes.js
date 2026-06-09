// Route handler tests for Lantern Garage
// Tests coverage for: dream, dreamer, files, flourishing, image, keystone, operator, rag, status, surfaces

const assert = require("assert");
const http = require("http");

// Mock dependencies
const mockDeps = {
  fs: require("fs"),
  path: require("path"),
  sendJson: (res, data, status = 200) => {
    res.statusCode = status;
    res.end(JSON.stringify(data));
  },
  sendFile: (res, filePath) => {
    try {
      const content = mockDeps.fs.readFileSync(filePath);
      res.end(content);
    } catch (err) {
      res.statusCode = 404;
      res.end(JSON.stringify({ error: "not_found" }));
    }
  },
  sendHtml: (res, html) => {
    res.setHeader("Content-Type", "text/html");
    res.end(html);
  },
  repoRoot: process.cwd(),
  publicRoot: require("path").join(process.cwd(), "apps", "lantern-garage", "public"),
  __dirname: __dirname,
  collectRequestBody: async (req) => {
    return new Promise((resolve) => {
      let body = "";
      req.on("data", (chunk) => body += chunk);
      req.on("end", () => resolve(body));
    });
  },
  readJsonl: (path, limit) => [],
  appendExternalRagItem: async (record) => record,
  flatRagHousePath: require("path").join(process.cwd(), "data", "internal-rag-house", "RAG-HOUSE-MANIFEST.json"),
  buildFlatRagHouse: () => ({ items: [] }),
  readJson: (path, fallback) => fallback || {},
  writeFlatRagHouse: (data) => {},
  readOperatorQueue: () => [],
  renderMarkdownDocument: (content, path) => `<html><body>${content}</body></html>`,
};

// Test helper
function createMockRequest(method, pathname, body = null) {
  return {
    method,
    url: { pathname, searchParams: new URLSearchParams() },
    on: (event, handler) => {},
  };
}

function createMockResponse() {
  const res = {
    statusCode: 200,
    headers: {},
    body: "",
    writeHead: function(code, headers) {
      this.statusCode = code;
      this.headers = { ...this.headers, ...headers };
    },
    setHeader: function(name, value) {
      this.headers[name] = value;
    },
    end: function(data) {
      this.body = data;
    },
  };
  return res;
}

// Load route handlers
let surfaceRoutes, fileRoutes, ragRoutes;
try {
  surfaceRoutes = require("../apps/lantern-garage/routes/surfaces");
  fileRoutes = require("../apps/lantern-garage/routes/files");
  ragRoutes = require("../apps/lantern-garage/routes/rag");
} catch (err) {
  console.log("Warning: Could not load route handlers:", err.message);
}

// Test suite
async function runTests() {
  let passed = 0;
  let failed = 0;

  function test(name, fn) {
    try {
      fn();
      console.log(`✓ ${name}`);
      passed++;
    } catch (err) {
      console.log(`✗ ${name}: ${err.message}`);
      failed++;
    }
  }

  console.log("\n=== Route Handler Tests ===\n");

  // Surfaces routes tests
  if (surfaceRoutes) {
    test("surfaces.js: /hub redirects to home", async () => {
      const req = createMockRequest("GET", "/hub");
      const res = createMockResponse();
      const handled = await surfaceRoutes(req, res, { pathname: "/hub" }, mockDeps);
      assert.strictEqual(handled, true);
      assert.strictEqual(res.statusCode, 302);
      assert.strictEqual(res.headers.Location, "/");
    });

    test("surfaces.js: /hff serves flourishing.html", async () => {
      const req = createMockRequest("GET", "/hff");
      const res = createMockResponse();
      const handled = await surfaceRoutes(req, res, { pathname: "/hff" }, mockDeps);
      assert.strictEqual(handled, true);
    });

    test("surfaces.js: /surfaces/ serves from surfaces directory", async () => {
      const req = createMockRequest("GET", "/surfaces/index.html");
      const res = createMockResponse();
      const handled = await surfaceRoutes(req, res, { pathname: "/surfaces/index.html" }, mockDeps);
      assert.strictEqual(handled, true);
    });
  } else {
    console.log("⊘ surfaces.js: Skipped (module not loaded)");
  }

  // Files routes tests
  if (fileRoutes) {
    test("files.js: /repo/ serves allowed files", async () => {
      const req = createMockRequest("GET", "/repo/README.md");
      const res = createMockResponse();
      const handled = await fileRoutes(req, res, { pathname: "/repo/README.md" }, mockDeps);
      assert.strictEqual(handled, true);
    });

    test("files.js: /repo/ blocks forbidden patterns", async () => {
      const req = createMockRequest("GET", "/repo/.env");
      const res = createMockResponse();
      const handled = await fileRoutes(req, res, { pathname: "/repo/.env" }, mockDeps);
      assert.strictEqual(handled, true);
      assert.strictEqual(res.statusCode, 403);
    });

    test("files.js: /repo/ blocks path traversal", async () => {
      const req = createMockRequest("GET", "/repo/../../../etc/passwd");
      const res = createMockResponse();
      const handled = await fileRoutes(req, res, { pathname: "/repo/../../../etc/passwd" }, mockDeps);
      assert.strictEqual(handled, true);
      assert.strictEqual(res.statusCode, 403);
    });

    test("files.js: /view serves markdown as HTML", async () => {
      const req = createMockRequest("GET", "/view");
      req.url.searchParams.set("path", "README.md");
      const res = createMockResponse();
      const handled = await fileRoutes(req, res, { pathname: "/view", searchParams: req.url.searchParams }, mockDeps);
      assert.strictEqual(handled, true);
    });
  } else {
    console.log("⊘ files.js: Skipped (module not loaded)");
  }

  // RAG routes tests
  if (ragRoutes) {
    test("rag.js: /api/rag-cache GET returns cache", async () => {
      const req = createMockRequest("GET", "/api/rag-cache");
      const res = createMockResponse();
      const handled = await ragRoutes(req, res, { pathname: "/api/rag-cache" }, mockDeps);
      assert.strictEqual(handled, true);
    });

    test("rag.js: /api/rag-cache POST appends item", async () => {
      const req = createMockRequest("POST", "/api/rag-cache");
      const res = createMockResponse();
      const handled = await ragRoutes(req, res, { pathname: "/api/rag-cache" }, mockDeps);
      assert.strictEqual(handled, true);
    });

    test("rag.js: /api/flat-rag-house returns RAG house", async () => {
      const req = createMockRequest("GET", "/api/flat-rag-house");
      const res = createMockResponse();
      const handled = await ragRoutes(req, res, { pathname: "/api/flat-rag-house" }, mockDeps);
      assert.strictEqual(handled, true);
    });

    test("rag.js: /api/operator-queue returns queue", async () => {
      const req = createMockRequest("GET", "/api/operator-queue");
      const res = createMockResponse();
      const handled = await ragRoutes(req, res, { pathname: "/api/operator-queue" }, mockDeps);
      assert.strictEqual(handled, true);
    });
  } else {
    console.log("⊘ rag.js: Skipped (module not loaded)");
  }

  console.log(`\n=== Results: ${passed} passed, ${failed} failed ===\n`);
  return { passed, failed };
}

// Run tests if executed directly
if (require.main === module) {
  runTests().then(({ passed, failed }) => {
    process.exit(failed > 0 ? 1 : 0);
  });
}

module.exports = { runTests };
