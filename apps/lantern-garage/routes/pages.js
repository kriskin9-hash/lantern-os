/**
 * Protected page routes with server-side role checking.
 * No client-side auth overlay - clean server-side redirects.
 */

const path = require("path");
const fs = require("fs");
const { requireAuth, requireRole } = require("../lib/auth-middleware");

// Public pages (no auth required)
const PUBLIC_PAGES = {
  "/": "index.html",
  "/index.html": "index.html",
  "/auth.html": "auth.html",
  "/auth": "auth.html",
  "/knowledgecenter.html": "knowledgecenter.html",
  "/explore.html": "explore.html",
};

// Protected pages with minimum role requirement
const PROTECTED_PAGES = {
  "/dream-chat.html": "guest", // Any authenticated user (free tier + supporters)
  "/profile.html": "guest", // Must be logged in but any role
  "/trader-dashboard.html": "supporter",
  "/create.html": "supporter",
};

module.exports = async function pagesRoute(req, res, url, deps) {
  const pathname = url.pathname;

  console.log(`[PAGES] Checking ${pathname}...`);

  // Check if this is a page request (ends with .html or is root)
  if (!pathname.match(/\.html$/) && pathname !== "/") {
    console.log(`[PAGES] Not a page request, skipping`);
    return false;
  }

  console.log(`[PAGES] ${req.method} ${pathname}, authenticated=${!!req.session?.patreon?.id}, session=${!!req.session}`);

  // Check public pages first
  if (PUBLIC_PAGES[pathname]) {
    const filename = PUBLIC_PAGES[pathname];
    const filePath = path.join(deps.publicRoot, filename);

    if (fs.existsSync(filePath)) {
      const html = fs.readFileSync(filePath, "utf-8");
      res.writeHead(200, { "Content-Type": "text/html; charset=utf-8" });
      return res.end(html);
    }
  }

  // Check protected pages
  const requiredRole = PROTECTED_PAGES[pathname];
  if (requiredRole !== undefined) {
    // Require authentication
    if (!requireAuth(req, res)) {
      return true;
    }

    // Require role
    if (!requireRole(req, res, requiredRole)) {
      return true;
    }

    // User authenticated and has required role - serve page
    const filename = requiredRole === "guest" ? pathname : PROTECTED_PAGES[pathname];
    const filePath = path.join(deps.publicRoot, filename);

    if (fs.existsSync(filePath)) {
      const html = fs.readFileSync(filePath, "utf-8");
      res.writeHead(200, { "Content-Type": "text/html; charset=utf-8" });
      return res.end(html);
    }
  }

  return false;
};
