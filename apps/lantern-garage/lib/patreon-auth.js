/**
 * Patreon OAuth 2.0 authentication module.
 * Handles login/logout, session management, and role mapping from Patreon tier data.
 * Requires: Node 18+ (native fetch), express-session, crypto, querystring
 */

const crypto = require("crypto");
const querystring = require("querystring");

// Use native fetch (Node 18+) or require a polyfill
const fetchFn = typeof fetch !== "undefined" ? fetch : require("node-fetch");

// Tier ID to Lantern role mapping.
// Campaign: Dream Journal By Lantern OS (ID: 16143763)
const TIER_TO_ROLE = {
  "28764312": "supporter",     // Wanderer ($5)
  "28740619": "founder",       // Deep Dreamer ($20)
  "28764307": "admin",         // Synthesasia Guild ($200)
};

/**
 * Generate PKCE code challenge for OAuth security.
 */
function generatePkce() {
  const verifier = crypto.randomBytes(32).toString("hex");
  const challenge = crypto
    .createHash("sha256")
    .update(verifier)
    .digest("base64")
    .replace(/\+/g, "-")
    .replace(/\//g, "_")
    .replace(/=/g, "");
  return { verifier, challenge };
}

/**
 * Start OAuth flow: redirect to Patreon login.
 */
function handlePatreonStart(req, res, returnTo) {
  const clientId = process.env.PATREON_CLIENT_ID;
  const redirectUri = process.env.PATREON_REDIRECT_URI;

  if (!clientId || !redirectUri) {
    res.writeHead(500, { "Content-Type": "application/json" });
    return res.end(JSON.stringify({ error: "Patreon OAuth not configured" }));
  }

  const { verifier, challenge } = generatePkce();
  const state = crypto.randomBytes(16).toString("hex");

  // Store in session for verification
  req.session.pkce_verifier = verifier;
  req.session.oauth_state = state;
  req.session.return_to = returnTo || "/";

  const params = querystring.stringify({
    response_type: "code",
    client_id: clientId,
    redirect_uri: redirectUri,
    scope: "identity identity.memberships",
    state,
    code_challenge: challenge,
    code_challenge_method: "S256",
  });

  res.writeHead(302, { Location: `https://www.patreon.com/oauth2/authorize?${params}` });
  res.end();
}

/**
 * Handle OAuth callback from Patreon.
 */
async function handlePatreonCallback(req, res, query, deps) {
  const { code, state } = query;
  const { sendJson } = deps;

  if (!code || !state) {
    res.writeHead(400, { "Content-Type": "application/json" });
    return res.end(JSON.stringify({ error: "Missing code or state" }));
  }

  // Verify state
  if (state !== req.session.oauth_state) {
    res.writeHead(403, { "Content-Type": "application/json" });
    return res.end(JSON.stringify({ error: "State mismatch" }));
  }

  try {
    // Exchange code for token (server-side, never expose client secret to browser)
    const token = await exchangePatreonCode(code, req.session.pkce_verifier);

    // Fetch user identity and membership data
    const user = await getPatreonUserWithMemberships(token);

    // Map tier to role
    const role = mapPatreonTierToRole(user.memberships);

    // Store in session
    req.session.patreon = {
      id: user.id,
      email: user.email,
      name: user.name,
      tier: user.primaryTier,
      role,
      token: token.access_token,
      expiresAt: Date.now() + (token.expires_in * 1000),
    };
    req.session.authenticated = true;

    // Clear PKCE
    delete req.session.pkce_verifier;
    delete req.session.oauth_state;

    const returnTo = req.session.return_to || "/dream-chat.html";
    delete req.session.return_to;

    res.writeHead(302, { Location: returnTo });
    res.end();
  } catch (err) {
    console.error("Patreon callback error:", err.message);
    res.writeHead(500, { "Content-Type": "application/json" });
    res.end(JSON.stringify({ error: err.message }));
  }
}

/**
 * Exchange authorization code for access token (server-side).
 */
async function exchangePatreonCode(code, verifier) {
  const clientId = process.env.PATREON_CLIENT_ID;
  const clientSecret = process.env.PATREON_CLIENT_SECRET;
  const redirectUri = process.env.PATREON_REDIRECT_URI;

  const body = querystring.stringify({
    code,
    grant_type: "authorization_code",
    client_id: clientId,
    client_secret: clientSecret,
    redirect_uri: redirectUri,
    code_verifier: verifier,
  });

  const res = await fetchFn("https://www.patreon.com/api/oauth2/token", {
    method: "POST",
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
    body,
  });

  if (!res.ok) {
    const err = await res.text();
    throw new Error(`Token exchange failed: ${err}`);
  }

  return res.json();
}

/**
 * Fetch user identity and membership data from Patreon.
 */
async function getPatreonUserWithMemberships(token) {
  const res = await fetchFn(
    "https://www.patreon.com/api/oauth2/v2/identity?" +
    "include=memberships&" +
    "fields[user]=email,full_name&" +
    "fields[member]=currently_entitled_tiers",
    {
      headers: { Authorization: `Bearer ${token.access_token}` },
    }
  );

  if (!res.ok) throw new Error(`User fetch failed: ${res.statusText}`);

  const { data, included } = await res.json();

  // Get membership (tied to campaign)
  const membership = (included || []).find((r) => r.type === "member");
  const tierIds = membership?.attributes?.currently_entitled_tiers || [];

  return {
    id: data.id,
    email: data.attributes.email,
    name: data.attributes.full_name,
    memberships: tierIds,
    primaryTier: tierIds[0] || null,
  };
}

/**
 * Map Patreon tier to Lantern role.
 */
function mapPatreonTierToRole(tierIds) {
  // Check tiers in order (highest privilege first)
  for (const tierId of tierIds) {
    if (TIER_TO_ROLE[tierId]) {
      return TIER_TO_ROLE[tierId];
    }
  }
  // Default to supporter if member but no tier mapping
  return tierIds.length > 0 ? "supporter" : "guest";
}

/**
 * Get current session info (for /api/auth/session).
 */
function getSessionInfo(req) {
  if (req.session && req.session.authenticated) {
    return {
      authenticated: true,
      role: req.session.patreon.role,
      user: {
        id: req.session.patreon.id,
        name: req.session.patreon.name,
        email: req.session.patreon.email,
        tier: req.session.patreon.tier,
      },
    };
  }
  return { authenticated: false, role: "guest" };
}

/**
 * Logout: clear session.
 */
function handleLogout(req, res) {
  if (req.session) {
    req.session.destroy((err) => {
      if (err) {
        res.writeHead(500, { "Content-Type": "application/json" });
        return res.end(JSON.stringify({ error: err.message }));
      }
      res.writeHead(200, { "Content-Type": "application/json" });
      res.end(JSON.stringify({ ok: true }));
    });
  } else {
    res.writeHead(200, { "Content-Type": "application/json" });
    res.end(JSON.stringify({ ok: true }));
  }
}

/**
 * Middleware: require specific role.
 */
function requirePatreonRole(requiredRole) {
  const roleHierarchy = { guest: 0, supporter: 1, founder: 2, admin: 3 };
  const requiredLevel = roleHierarchy[requiredRole] || 0;

  return (req, res, next) => {
    const session = getSessionInfo(req);
    const userLevel = roleHierarchy[session.role] || 0;

    if (userLevel < requiredLevel) {
      res.writeHead(403, { "Content-Type": "application/json" });
      return res.end(
        JSON.stringify({
          error: "Insufficient permissions",
          required: requiredRole,
          current: session.role,
        })
      );
    }

    // Attach to request for downstream handlers
    req.patreonSession = session;
    next();
  };
}

module.exports = {
  handlePatreonStart,
  handlePatreonCallback,
  getSessionInfo,
  handleLogout,
  requirePatreonRole,
  mapPatreonTierToRole,
};
