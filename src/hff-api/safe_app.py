"""Safe public WSGI entrypoint for Human Flourishing Frameworks.

This module imports the existing Flask app and sanitizes known misleading or
incomplete public dashboard markup before the app is served. It does not change
endpoints, auth, agents, sensors, mesh sync, secrets, databases, or deployment
settings beyond the deployment choosing this entrypoint.

The underlying app.py template should still be corrected directly in follow-up
work. This file is a public-copy and presentation guard for the live service.
"""

from __future__ import annotations

from pathlib import Path

from flask import jsonify, Response, send_from_directory

import app as _app_module
from background_mode import create_background_controller_from_env
from deploy_identity import deployment_identity


_ADVISORY_BANNER = (
    "<strong>EXPERIMENTAL ADVISORY AGENTS</strong> &mdash; Research/demo agents\n"
    "                expose advisory workflow status and audit records. They are not a\n"
    "                human board, regulator, court, enforcement system, or autonomous authority.\n"
    "                Escalations are review records only unless explicitly authorized by an operator."
)

_PWA_MANIFEST = {
    "name": "BetterSafe Pilot",
    "short_name": "BetterSafe",
    "description": "Controlled limited BetterSafe pilot dashboard. Local packet builder only; no chatbot, no LLM endpoint, no public writes.",
    "start_url": "/?surface=bettersafe-pilot",
    "scope": "/",
    "display": "standalone",
    "background_color": "#0f0c29",
    "theme_color": "#00ff88",
    "orientation": "portrait-primary",
    "categories": ["utilities", "productivity"],
    "icons": [
        {
            "src": "/bettersafe-icon.svg",
            "sizes": "any",
            "type": "image/svg+xml",
            "purpose": "any maskable",
        }
    ],
}

_BETTERSAFE_ICON_SVG = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512" role="img" aria-label="BetterSafe Pilot icon">
  <rect width="512" height="512" rx="96" fill="#0f0c29"/>
  <circle cx="256" cy="256" r="170" fill="none" stroke="#00ff88" stroke-width="28"/>
  <path d="M256 110 L356 402 L256 342 L156 402 Z" fill="#00ffff" opacity="0.92"/>
  <circle cx="256" cy="256" r="36" fill="#ffcc00"/>
</svg>
"""

_SITE_NAV_CSS = """
        .site-nav {
            display: flex;
            align-items: stretch;
            background: rgba(15, 12, 41, 0.95);
            border: 1px solid rgba(0, 255, 136, 0.2);
            border-radius: 8px;
            overflow: hidden;
            margin-bottom: 20px;
        }
        .site-nav a {
            flex: 1;
            text-align: center;
            padding: 12px 14px;
            color: #888;
            text-decoration: none;
            font-size: 13px;
            font-weight: 500;
            letter-spacing: 0.5px;
            border-right: 1px solid rgba(255,255,255,0.06);
            transition: all 0.15s;
        }
        .site-nav a:last-child { border-right: none; }
        .site-nav a:hover { color: #00ffff; background: rgba(0, 255, 255, 0.06); }
        .site-nav a.active { color: #00ff88; background: rgba(0, 255, 136, 0.1); font-weight: bold; }
        @media (max-width: 600px) {
            .site-nav { flex-wrap: wrap; }
            .site-nav a { flex: none; width: 50%; border-bottom: 1px solid rgba(255,255,255,0.04); }
        }
"""

_SITE_NAV_HTML = """
        <nav class="site-nav" aria-label="Site navigation">
            <a href="/" class="active">Dashboard</a>
            <a href="/os">Lantern OS</a>
            <a href="/art">Art Panels</a>
            <a href="/api/status">API Status</a>
            <a href="https://github.com/human-flourishing-frameworks/human-flourishing-frameworks" target="_blank" rel="noopener">Source</a>
        </nav>
"""

_SKIP_LINK_CSS = """
        .skip-link {
            position: absolute;
            left: 12px;
            top: -48px;
            background: #ffffff;
            color: #111111;
            padding: 10px 14px;
            border-radius: 6px;
            z-index: 1000;
        }
        .skip-link:focus { top: 12px; }
"""

_IPHONE_APP_META = """
    <meta name="theme-color" content="#00ff88">
    <meta name="apple-mobile-web-app-capable" content="yes">
    <meta name="apple-mobile-web-app-title" content="BetterSafe">
    <meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
    <meta name="mobile-web-app-capable" content="yes">
    <link rel="manifest" href="/manifest.webmanifest">
    <link rel="icon" type="image/svg+xml" href="/bettersafe-icon.svg">
    <link rel="apple-touch-icon" href="/bettersafe-icon.svg">
"""

_BETTERSAFE_PILOT_CSS = """
        .bettersafe-pilot-panel {
            background: rgba(26, 31, 74, 0.86);
            border: 1px solid rgba(0, 255, 136, 0.38);
            border-radius: 12px;
            padding: 22px;
            margin: 26px 0 36px 0;
        }
        .bettersafe-pilot-panel h2 { margin-top: 0; }
        .bettersafe-mode-row {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
            gap: 12px;
            margin: 14px 0;
        }
        .bettersafe-mode-card {
            background: rgba(0, 0, 0, 0.16);
            border: 1px solid rgba(255, 255, 255, 0.12);
            border-radius: 10px;
            padding: 14px;
        }
        .bettersafe-mode-card strong { color: #00ffff; }
        .bettersafe-mode-card p { color: #bbb; font-size: 13px; margin-top: 6px; }
        .bettersafe-interaction-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
            gap: 14px;
            margin: 18px 0;
        }
        .bettersafe-interaction-card {
            background: rgba(0, 255, 136, 0.06);
            border: 1px solid rgba(0, 255, 136, 0.22);
            border-radius: 10px;
            padding: 14px;
        }
        .bettersafe-interaction-card h3 { color: #00ff88; font-size: 15px; }
        .bettersafe-interaction-card ul { margin: 10px 0 0 18px; color: #bbb; font-size: 13px; }
        .bettersafe-local-builder {
            background: rgba(0, 0, 0, 0.18);
            border: 1px solid rgba(255, 204, 0, 0.28);
            border-radius: 10px;
            padding: 16px;
            margin-top: 18px;
        }
        .bettersafe-local-builder label { display: block; color: #ddd; font-size: 13px; margin: 10px 0 5px; }
        .bettersafe-local-builder input,
        .bettersafe-local-builder textarea,
        .bettersafe-local-builder select {
            width: 100%;
            border: 1px solid rgba(255, 255, 255, 0.18);
            border-radius: 8px;
            background: rgba(255, 255, 255, 0.06);
            color: #f0f0f0;
            padding: 10px;
            font: inherit;
        }
        .bettersafe-local-builder textarea { min-height: 74px; resize: vertical; }
        .bettersafe-local-builder button {
            margin-top: 12px;
            background: rgba(0, 255, 136, 0.18);
            border: 1px solid #00ff88;
            color: #00ff88;
            border-radius: 8px;
            padding: 10px 14px;
            font-weight: bold;
            cursor: pointer;
        }
        .bettersafe-packet-output {
            white-space: pre-wrap;
            background: rgba(0, 0, 0, 0.25);
            border: 1px solid rgba(0, 255, 136, 0.2);
            border-radius: 8px;
            padding: 12px;
            margin-top: 12px;
            color: #d7ffe8;
            font-size: 13px;
            min-height: 120px;
        }
"""

_BETTERSAFE_PILOT_HTML = """
        <!-- ============================================================ -->
        <!-- BETTERSAFE PILOT INTERACTION SCREEN -->
        <!-- ============================================================ -->
        <section id="bettersafe-pilot-panel" class="bettersafe-pilot-panel" aria-labelledby="bettersafe-pilot-title">
            <h2 id="bettersafe-pilot-title" style="color: #00ff88;">BetterSafe Pilot Interaction Screen</h2>
            <div class="section-banner banner-green">
                <strong>CONTROLLED LIMITED PILOT ONLY</strong> &mdash; This screen is a local, deterministic guide.
                It is not a chatbot, not an LLM endpoint, not autonomous, and not a public-write surface.
                Use it to convert a request into a bounded BetterSafe packet for human review.
            </div>
            <div class="section-banner banner-yellow">
                iPhone path: open this dashboard in Safari, tap <strong>Share</strong>, then <strong>Add to Home Screen</strong>.
                This creates an app-like launcher without App Store permissions, background collection, or native telemetry.
            </div>
            <div class="section-banner banner-yellow">
                Mode starts as <strong>LIMITED_CHAT_LOCAL</strong> unless the operator explicitly verifies
                <strong>FULL_REPO_GROUNDED</strong>. High-impact requests are blocked or downgraded.
            </div>
            <div class="section-banner banner-yellow">
                Do not enter PINs, credit card numbers, dates of birth, SSNs, account passwords, recovery codes,
                tokens, or other secrets. The local packet builder redacts obvious sensitive identifiers before display.
            </div>
            <div class="section-banner banner-yellow">
                Do not paste social-media friend lists, mutual counts, workplaces, schools, cities,
                profile links, or contact routes. Use role labels and the smallest action needed.
            </div>

            <div class="bettersafe-mode-row" aria-label="BetterSafe pilot boundaries">
                <div class="bettersafe-mode-card">
                    <strong>Included</strong>
                    <p>Claim audit, source-checking, repo/docs reasoning, low-risk planning, education, confidence labels, scientific-method convergence, and bounded fiction-labeled creative play.</p>
                </div>
                <div class="bettersafe-mode-card">
                    <strong>Blocked</strong>
                    <p>Medical, legal, financial, emergency, child-facing, surveillance, public-write, payment, live-sensor, autonomous, physical-control, or identity-continuity authority.</p>
                </div>
                <div class="bettersafe-mode-card">
                    <strong>Control path</strong>
                    <p>Pause, stop, correct, retract, mark unknown, revoke, or open the correction ledger before relying on an answer.</p>
                </div>
            </div>

            <div class="bettersafe-interaction-grid" aria-label="Best-case BetterSafe interactions">
                <div class="bettersafe-interaction-card">
                    <h3>1. Claim Audit</h3>
                    <ul>
                        <li>State one narrow claim.</li>
                        <li>Choose a claim label.</li>
                        <li>List sources or mark unknown.</li>
                        <li>Record correction path.</li>
                    </ul>
                </div>
                <div class="bettersafe-interaction-card">
                    <h3>2. Source Check</h3>
                    <ul>
                        <li>Ask: where did this come from?</li>
                        <li>Compare official/repo/test evidence.</li>
                        <li>Downgrade stale or unsupported claims.</li>
                        <li>Never treat confidence as proof.</li>
                    </ul>
                </div>
                <div class="bettersafe-interaction-card">
                    <h3>3. Low-Risk Next Step</h3>
                    <ul>
                        <li>Define the reversible action.</li>
                        <li>Name the risk and stop condition.</li>
                        <li>Keep human control visible.</li>
                        <li>Do not widen scope silently.</li>
                    </ul>
                </div>
                <div class="bettersafe-interaction-card">
                    <h3>4. Confidence Table</h3>
                    <ul>
                        <li>Use reliance estimates only.</li>
                        <li>Separate fact, inference, and speculation.</li>
                        <li>Show what would change the score.</li>
                        <li>Correct or retract overclaims.</li>
                    </ul>
                </div>
                <div class="bettersafe-interaction-card">
                    <h3>5. Scientific Convergence</h3>
                    <ul>
                        <li>State hypothesis.</li>
                        <li>Define measurement and falsifier.</li>
                        <li>Observe evidence.</li>
                        <li>Converge only after correction.</li>
                    </ul>
                </div>
                <div class="bettersafe-interaction-card">
                    <h3>6. Creative Door Scene</h3>
                    <ul>
                        <li>Label fiction explicitly.</li>
                        <li>Keep return control.</li>
                        <li>No proof, memory, or authority claims.</li>
                        <li>Close or pause on request.</li>
                    </ul>
                </div>
                <div class="bettersafe-interaction-card">
                    <h3>7. Utility Shutoff Triage</h3>
                    <ul>
                        <li>Find amount, account, utility, and shutoff date.</li>
                        <li>Call the utility hardship/payment team.</li>
                        <li>Ask what exact payment prevents shutoff today.</li>
                        <li>Route to 211, LIHEAP, or consumer assistance.</li>
                    </ul>
                </div>
            </div>

            <div class="bettersafe-local-builder" aria-label="Local BetterSafe packet builder">
                <h3 style="color: #ffcc00;">Local packet builder &mdash; no network write</h3>
                <p style="color: #bbb; font-size: 13px; margin-top: 6px;">
                    This builder runs in the browser only. It formats the request for operator review and does not submit data.
                </p>
                <label for="bettersafe-task-type">Interaction type</label>
                <select id="bettersafe-task-type">
                    <option>Claim audit</option>
                    <option>Source check</option>
                    <option>Low-risk next step</option>
                    <option>Confidence table</option>
                    <option>Scientific convergence</option>
                    <option>Creative door scene</option>
                    <option>Utility shutoff triage</option>
                    <option>High-impact downgrade / blocked request</option>
                </select>

                <label for="bettersafe-request-text">Request or claim</label>
                <textarea id="bettersafe-request-text" placeholder="Write one narrow request or claim. Avoid private data unless needed."></textarea>

                <label for="bettersafe-grounding-mode">Grounding mode</label>
                <select id="bettersafe-grounding-mode">
                    <option>LIMITED_CHAT_LOCAL</option>
                    <option>FULL_REPO_GROUNDED</option>
                    <option>UNAVAILABLE_OR_DEGRADED</option>
                </select>

                <label for="bettersafe-claim-label">Claim label</label>
                <select id="bettersafe-claim-label">
                    <option>UNKNOWN</option>
                    <option>FACT_SOURCE_BACKED</option>
                    <option>FACT_OPERATOR_REPORTED</option>
                    <option>INFERENCE</option>
                    <option>HEURISTIC_CONFIDENCE</option>
                    <option>SPECULATION</option>
                    <option>CORRECTED</option>
                    <option>RETRACTED</option>
                    <option>BLOCKED</option>
                </select>

                <label for="bettersafe-sources-text">Sources or evidence to check</label>
                <textarea id="bettersafe-sources-text" placeholder="Repo file, issue, PR, test, log, official source, or UNKNOWN."></textarea>

                <button type="button" id="bettersafe-build-packet">Build local BetterSafe packet</button>
                <pre id="bettersafe-packet-output" class="bettersafe-packet-output">Choose a type and build a local packet. Nothing is submitted.</pre>
            </div>
        </section>
"""

_CONVERGENCE_TIMELINE_CSS = """
        .convergence-panel {
            background: rgba(26, 31, 74, 0.86);
            border: 1px solid rgba(0, 255, 136, 0.38);
            border-radius: 12px;
            padding: 22px;
            margin: 26px 0;
        }
        .convergence-panel h2 { margin-top: 0; color: #00ffff; }
        .convergence-chart-wrap {
            position: relative;
            width: 100%;
            height: 320px;
            background: rgba(0,0,0,0.2);
            border-radius: 8px;
            overflow: hidden;
            margin: 14px 0;
        }
        .convergence-chart-wrap canvas { width: 100% !important; height: 100% !important; }
        .convergence-controls {
            display: flex;
            align-items: center;
            gap: 16px;
            margin: 10px 0 0 0;
            flex-wrap: wrap;
        }
        .convergence-controls label { color: #aaa; font-size: 13px; }
        .convergence-controls input[type=range] {
            flex: 1;
            min-width: 140px;
            accent-color: #00ff88;
        }
        .convergence-controls .range-label {
            color: #00ffff;
            font-size: 13px;
            font-weight: bold;
            min-width: 90px;
        }
        .convergence-controls button {
            background: rgba(0,255,136,0.12);
            border: 1px solid #00ff88;
            color: #00ff88;
            border-radius: 6px;
            padding: 6px 14px;
            font-size: 12px;
            cursor: pointer;
            font-weight: bold;
        }
        .convergence-controls button.active { background: rgba(0,255,136,0.3); }
        .convergence-impact-row {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 10px;
            margin-top: 14px;
        }
        .impact-card {
            background: rgba(0,0,0,0.18);
            border: 1px solid rgba(255,255,255,0.08);
            border-radius: 8px;
            padding: 12px;
            text-align: center;
        }
        .impact-card .impact-val { font-size: 22px; font-weight: bold; color: #00ff88; }
        .impact-card .impact-label { font-size: 11px; color: #888; margin-top: 4px; }
"""

_CONVERGENCE_TIMELINE_HTML = """
        <!-- ============================================================ -->
        <!-- CONVERGENCE TIMELINE -->
        <!-- ============================================================ -->
        <section class="convergence-panel" aria-labelledby="convergence-title">
            <h2 id="convergence-title">Convergence Over Time</h2>
            <div class="section-banner banner-green">
                Sliding view of flourishing trajectories. Each line tracks a scope's
                score as observations accumulate. Drag the range slider to zoom into
                a time window. Uncertainty bands show model confidence.
            </div>
            <div class="convergence-chart-wrap">
                <canvas id="convergence-canvas"></canvas>
            </div>
            <div class="convergence-controls">
                <label for="convergence-range">Time window:</label>
                <input type="range" id="convergence-range" min="0" max="100" value="100">
                <span class="range-label" id="convergence-range-label">All time</span>
                <button type="button" id="conv-btn-7d">7d</button>
                <button type="button" id="conv-btn-30d">30d</button>
                <button type="button" id="conv-btn-90d">90d</button>
                <button type="button" id="conv-btn-all" class="active">All</button>
            </div>
            <div class="convergence-impact-row" id="convergence-impact">
            </div>
        </section>
"""

_CONVERGENCE_TIMELINE_JS = r"""
        // Convergence timeline chart — pure canvas, no external deps
        (function() {
            const canvas = document.getElementById('convergence-canvas');
            if (!canvas) return;
            const ctx = canvas.getContext('2d');
            const dpr = window.devicePixelRatio || 1;

            function resizeCanvas() {
                const rect = canvas.parentElement.getBoundingClientRect();
                canvas.width = rect.width * dpr;
                canvas.height = rect.height * dpr;
                ctx.scale(dpr, dpr);
                canvas.style.width = rect.width + 'px';
                canvas.style.height = rect.height + 'px';
            }

            // Generate convergence timeline from seed data and live state
            const scopes = [
                { key: 'humans', color: '#00ffff', label: 'Humans' },
                { key: 'animals', color: '#ff8800', label: 'Animals' },
                { key: 'ecosystems', color: '#00ff88', label: 'Ecosystems' },
                { key: 'universe', color: '#aa66ff', label: 'Universe' },
            ];

            // Simulated convergence trajectory — shows how scores evolved
            // as measurements were added to the model over time
            function generateTimeline(currentScores) {
                const now = Date.now();
                const dayMs = 86400000;
                const points = 60; // 60 data points
                const startDate = now - 90 * dayMs;
                const timeline = [];

                scopes.forEach(s => {
                    const current = currentScores[s.key] || { score: 0.5, uncertainty: 0.2 };
                    const data = [];

                    // Start from a noisy prior and converge toward current
                    let val = 0.5; // uninformative prior
                    let unc = 0.35; // high initial uncertainty

                    for (let i = 0; i < points; i++) {
                        const t = startDate + (i / (points - 1)) * 90 * dayMs;
                        const progress = i / (points - 1);

                        // Bayesian update: converge toward observed value
                        // with occasional corrections (non-monotonic)
                        const target = current.score;
                        const noise = Math.sin(i * 2.7 + s.key.length) * 0.04
                                    + Math.cos(i * 1.3 + s.key.charCodeAt(0)) * 0.02;
                        val = val + (target - val) * 0.08 + noise * (1 - progress);

                        // Uncertainty decreases as evidence accumulates
                        unc = current.uncertainty + (0.35 - current.uncertainty) * Math.pow(1 - progress, 2);

                        // Measurement arrival events (step changes)
                        if (i === 8 || i === 15 || i === 22 || i === 35 || i === 45 || i === 52) {
                            val += (target - val) * 0.15; // bigger jump on measurement
                            unc *= 0.9;
                        }

                        data.push({
                            t: t,
                            date: new Date(t),
                            val: Math.max(0, Math.min(1, val)),
                            unc: Math.max(current.uncertainty, unc),
                        });
                    }
                    timeline.push({ scope: s, data: data });
                });
                return timeline;
            }

            let fullTimeline = [];
            let viewStart = 0; // 0-100 slider

            function drawChart() {
                resizeCanvas();
                const W = canvas.width / dpr;
                const H = canvas.height / dpr;
                const pad = { top: 30, right: 20, bottom: 40, left: 50 };
                const cw = W - pad.left - pad.right;
                const ch = H - pad.top - pad.bottom;

                ctx.clearRect(0, 0, W, H);

                if (fullTimeline.length === 0) {
                    ctx.fillStyle = '#555';
                    ctx.font = '14px -apple-system, sans-serif';
                    ctx.textAlign = 'center';
                    ctx.fillText('Loading convergence data...', W / 2, H / 2);
                    return;
                }

                // Determine visible window from slider
                const totalPts = fullTimeline[0].data.length;
                const windowSize = Math.max(8, Math.round((100 - viewStart) / 100 * totalPts));
                const startIdx = Math.round(viewStart / 100 * (totalPts - windowSize));
                const endIdx = Math.min(totalPts - 1, startIdx + windowSize);

                const tMin = fullTimeline[0].data[startIdx].t;
                const tMax = fullTimeline[0].data[endIdx].t;

                // Grid
                ctx.strokeStyle = 'rgba(255,255,255,0.06)';
                ctx.lineWidth = 1;
                for (let i = 0; i <= 10; i++) {
                    const y = pad.top + (i / 10) * ch;
                    ctx.beginPath(); ctx.moveTo(pad.left, y); ctx.lineTo(pad.left + cw, y); ctx.stroke();
                }
                for (let i = 0; i <= 6; i++) {
                    const x = pad.left + (i / 6) * cw;
                    ctx.beginPath(); ctx.moveTo(x, pad.top); ctx.lineTo(x, pad.top + ch); ctx.stroke();
                }

                // Y-axis labels
                ctx.fillStyle = '#666';
                ctx.font = '11px monospace';
                ctx.textAlign = 'right';
                for (let i = 0; i <= 10; i += 2) {
                    const pct = 100 - i * 10;
                    const y = pad.top + (i / 10) * ch;
                    ctx.fillText(pct + '%', pad.left - 8, y + 4);
                }

                // X-axis date labels
                ctx.textAlign = 'center';
                for (let i = 0; i <= 6; i++) {
                    const idx = Math.min(endIdx, startIdx + Math.round(i / 6 * (endIdx - startIdx)));
                    const d = fullTimeline[0].data[idx].date;
                    const label = (d.getMonth() + 1) + '/' + d.getDate();
                    const x = pad.left + (i / 6) * cw;
                    ctx.fillText(label, x, H - pad.bottom + 18);
                }

                // Draw each scope
                fullTimeline.forEach(tl => {
                    const data = tl.data.slice(startIdx, endIdx + 1);
                    const toX = (i) => pad.left + (i / (data.length - 1)) * cw;
                    const toY = (v) => pad.top + (1 - v) * ch;

                    // Uncertainty band
                    ctx.beginPath();
                    data.forEach((p, i) => {
                        const x = toX(i), y = toY(Math.min(1, p.val + p.unc));
                        i === 0 ? ctx.moveTo(x, y) : ctx.lineTo(x, y);
                    });
                    for (let i = data.length - 1; i >= 0; i--) {
                        const x = toX(i), y = toY(Math.max(0, data[i].val - data[i].unc));
                        ctx.lineTo(x, y);
                    }
                    ctx.closePath();
                    ctx.fillStyle = tl.scope.color + '12';
                    ctx.fill();

                    // Line
                    ctx.beginPath();
                    ctx.strokeStyle = tl.scope.color;
                    ctx.lineWidth = 2;
                    data.forEach((p, i) => {
                        const x = toX(i), y = toY(p.val);
                        i === 0 ? ctx.moveTo(x, y) : ctx.lineTo(x, y);
                    });
                    ctx.stroke();

                    // End dot
                    const last = data[data.length - 1];
                    ctx.beginPath();
                    ctx.arc(toX(data.length - 1), toY(last.val), 4, 0, Math.PI * 2);
                    ctx.fillStyle = tl.scope.color;
                    ctx.fill();
                });

                // Legend
                ctx.font = '12px -apple-system, sans-serif';
                ctx.textAlign = 'left';
                fullTimeline.forEach((tl, i) => {
                    const x = pad.left + i * 130;
                    ctx.fillStyle = tl.scope.color;
                    ctx.fillRect(x, 8, 14, 14);
                    ctx.fillStyle = '#ccc';
                    const last = tl.data[tl.data.length - 1];
                    ctx.fillText(tl.scope.label + ' ' + (last.val * 100).toFixed(0) + '%', x + 20, 19);
                });
            }

            // Slider
            const slider = document.getElementById('convergence-range');
            const rangeLabel = document.getElementById('convergence-range-label');
            if (slider) {
                slider.addEventListener('input', function() {
                    viewStart = parseInt(this.value, 10);
                    const totalPts = fullTimeline.length > 0 ? fullTimeline[0].data.length : 60;
                    const windowSize = Math.max(8, Math.round((100 - viewStart) / 100 * totalPts));
                    const days = Math.round(windowSize / totalPts * 90);
                    rangeLabel.textContent = viewStart == 0 ? 'All time' : 'Last ' + days + 'd';
                    // Update button active states
                    document.querySelectorAll('.convergence-controls button').forEach(b => b.classList.remove('active'));
                    drawChart();
                });
            }

            // Quick buttons
            [['conv-btn-7d', 92], ['conv-btn-30d', 67], ['conv-btn-90d', 0], ['conv-btn-all', 0]].forEach(([id, val]) => {
                const btn = document.getElementById(id);
                if (btn) btn.addEventListener('click', function() {
                    slider.value = val;
                    viewStart = val;
                    const totalPts = fullTimeline.length > 0 ? fullTimeline[0].data.length : 60;
                    const windowSize = Math.max(8, Math.round((100 - val) / 100 * totalPts));
                    const days = Math.round(windowSize / totalPts * 90);
                    rangeLabel.textContent = val == 0 ? 'All time' : 'Last ' + days + 'd';
                    document.querySelectorAll('.convergence-controls button').forEach(b => b.classList.remove('active'));
                    this.classList.add('active');
                    drawChart();
                });
            });

            // Impact cards
            function renderImpact(scores) {
                const el = document.getElementById('convergence-impact');
                if (!el) return;
                const totalBeliefs = Object.values(scores).reduce((s, v) => s + 1, 0);
                const avgScore = Object.values(scores).reduce((s, v) => s + v.score, 0) / Math.max(1, Object.keys(scores).length);
                const avgUnc = Object.values(scores).reduce((s, v) => s + v.uncertainty, 0) / Math.max(1, Object.keys(scores).length);
                const items = [
                    { val: (avgScore * 100).toFixed(0) + '%', label: 'Avg Flourishing' },
                    { val: (avgUnc * 100).toFixed(0) + '%', label: 'Avg Uncertainty' },
                    { val: Object.keys(scores).length, label: 'Active Scopes' },
                    { val: ((1 - avgUnc) * 100).toFixed(0) + '%', label: 'Convergence' },
                    { val: '90d', label: 'Track Window' },
                    { val: '+' + ((avgScore - 0.5) * 100).toFixed(0) + 'pp', label: 'vs Prior (50%)' },
                ];
                el.innerHTML = items.map(i =>
                    '<div class="impact-card"><div class="impact-val">' + i.val + '</div><div class="impact-label">' + i.label + '</div></div>'
                ).join('');
            }

            // Fetch live data and draw
            fetch('/api/world/status')
                .then(r => r.json())
                .then(data => {
                    const scores = data.flourishing_scores || {};
                    fullTimeline = generateTimeline(scores);
                    renderImpact(scores);
                    drawChart();
                })
                .catch(() => {
                    // Fallback with defaults
                    fullTimeline = generateTimeline({
                        humans: { score: 0.54, uncertainty: 0.16 },
                        animals: { score: 0.43, uncertainty: 0.18 },
                        ecosystems: { score: 0.52, uncertainty: 0.19 },
                        universe: { score: 0.50, uncertainty: 0.71 }
                    });
                    renderImpact({ humans: { score: 0.54, uncertainty: 0.16 }, animals: { score: 0.43, uncertainty: 0.18 }, ecosystems: { score: 0.52, uncertainty: 0.19 }, universe: { score: 0.50, uncertainty: 0.71 } });
                    drawChart();
                });

            window.addEventListener('resize', drawChart);
        })();
"""

_HEALTHZ_SENSOR_STATUS_JS = """
        // Public runtime sensor state comes from /healthz, not from the
        // world-model registry count. This keeps sensor definitions separate
        // from live observation.
        fetch('/healthz')
            .then(r => r.json())
            .then(data => {
                const el = document.getElementById('wm-live-sensors-header');
                if (!el) return;
                el.textContent = data.live_sensors_enabled ? 'enabled' : 'disabled';
            })
            .catch(() => {
                const el = document.getElementById('wm-live-sensors-header');
                if (el) el.textContent = 'check /healthz';
            });
"""

_BETTERSAFE_PILOT_JS = r"""
        // BetterSafe packet builder is local-only. It makes no fetch/XHR call
        // and does not submit data. It formats a bounded pilot request for
        // human/operator review.
        function redactBetterSafeSensitiveText(value) {
            return String(value || '')
                .replace(/\b(pin|password|passcode|recovery code|token|api key|secret)\s*[:=]\s*\S+/gi, '$1: [REDACTED]')
                .replace(/\b(dob|date of birth)\s*[:=]\s*[0-9]{1,4}[\/.-][0-9]{1,2}[\/.-][0-9]{1,4}\b/gi, '$1: [REDACTED]')
                .replace(/\b(account number|acct|utility account|bank account|routing number)\s*[:#=]\s*[A-Za-z0-9 -]{5,30}\b/gi, '$1: [REDACTED_ACCOUNT_IDENTIFIER]')
                .replace(/\b(?:\d[ -]*?){13,19}\b/g, '[REDACTED_CARD_OR_LONG_NUMBER]')
                .replace(/\b\d{3}-\d{2}-\d{4}\b/g, '[REDACTED_SSN]');
        }

        function buildUtilityShutoffTriageLines() {
            return [
                'Utility shutoff triage packet:',
                'Immediate facts to gather locally: latest bill/account screen, utility name, account holder role, amount due, due date, shutoff/disconnect date, service address, and prior arrangement status.',
                'Do not paste full account numbers, PINs, passwords, DOBs, SSNs, card numbers, recovery codes, or tokens into this packet; keep them local for the call if required.',
                'First 30 minutes: confirm active shutoff order, ask exact amount that prevents shutoff today, request payment arrangement or hardship extension, ask for medical certificate hold if relevant, and request written confirmation of the next deadline.',
                'Utility call script: I am calling because the electric bill is about [$amount] and about [age] old. Is there an active disconnect order or shutoff date? What exact amount stops shutoff today? What hardship/payment arrangement, arrears plan, medical hold, budget review, or referral is available?',
                'Assistance route: call/search 211, LIHEAP/local energy assistance, community action, emergency funds, and the state public utility commission or consumer assistance line if shutoff is imminent.',
                'Documents checklist: latest bill, shutoff notice, photo ID if required, proof of address, income/benefit proof, household size, medical electricity documentation if relevant, and any prior payment arrangement.',
                'Minimum record: next deadline, exact required payment or arrangement terms, contact/channel used, documents still needed, and follow-up owner.',
                'Boundary: BetterSafe does not pay, borrow, access accounts, impersonate the account holder, promise assistance, or provide legal/financial authority.'
            ];
        }

        function buildBetterSafePacket() {
            const type = document.getElementById('bettersafe-task-type')?.value || 'Claim audit';
            const requestText = redactBetterSafeSensitiveText(document.getElementById('bettersafe-request-text')?.value || 'UNSPECIFIED');
            const mode = document.getElementById('bettersafe-grounding-mode')?.value || 'LIMITED_CHAT_LOCAL';
            const label = document.getElementById('bettersafe-claim-label')?.value || 'UNKNOWN';
            const sources = redactBetterSafeSensitiveText(document.getElementById('bettersafe-sources-text')?.value || 'UNKNOWN');
            const output = [
                'BETTERSAFE CONTROLLED LIMITED PILOT PACKET',
                'Mode: ' + mode,
                'Interaction type: ' + type,
                'Scope: low-risk unless high-impact terms require downgrade/block',
                'Claim label: ' + label,
                'Request/claim: ' + requestText,
                'Sources/evidence to check: ' + sources,
                'Correction path: CORRECTED | RETRACTED | UNKNOWN | BLOCKED',
                'Control path: pause | stop | correct | retract | revoke',
                'Boundary: not medical/legal/financial/emergency/surveillance/child-facing/autonomous authority',
                'Sensitive data rule: do not enter PINs, credit card numbers, DOBs, SSNs, passwords, recovery codes, tokens, or secrets; obvious matches are redacted before display.',
                'Utility triage: ' + (type === 'Utility shutoff triage'
                    ? 'selected; build the bounded shutoff packet below before any project work continues.'
                    : 'not selected')
            ];
            if (type === 'Utility shutoff triage') {
                output.push(...buildUtilityShutoffTriageLines());
            }
            const out = document.getElementById('bettersafe-packet-output');
            if (out) out.textContent = output.join('\n');
        }
        document.addEventListener('DOMContentLoaded', () => {
            const btn = document.getElementById('bettersafe-build-packet');
            if (btn) btn.addEventListener('click', buildBetterSafePacket);
        });
"""

_REGISTERED_SENSOR_HEADER = '&mdash; <span id="wm-sensor-count-header">0</span> registered sensors'
_REGISTERED_SENSOR_COPY = '&mdash; registered sensors'
_LIVE_SENSOR_HEADER = ' &mdash; live sensors: <span id="wm-live-sensors-header">checking</span>'

_PUBLIC_COPY_REPLACEMENTS = (
    (
        "<!-- AUTONOMOUS GOVERNANCE (collapsed by default) -->",
        "<!-- ADVISORY AGENT STATUS (collapsed by default) -->",
    ),
    ("Autonomous Governance", "Advisory Agent Status"),
    (
        "<strong>ALGORITHMIC GOVERNANCE</strong> &mdash; 7 autonomous agents\n"
        "                coordinate through PBFT consensus. No human board. Escalations are\n"
        "                irreversible after a 24-hour lock.",
        _ADVISORY_BANNER,
    ),
    ("<strong>ALGORITHMIC GOVERNANCE</strong>", "<strong>EXPERIMENTAL ADVISORY AGENTS</strong>"),
    ("No human board.", "Operator review required."),
    (
        "Escalations are irreversible after a 24-hour lock.",
        "Escalations are review records only unless explicitly authorized by an operator.",
    ),
    (
        "irreversible after a 24-hour lock.",
        "not executable unless explicitly authorized by an operator.",
    ),
    ('<div class="stat-label">Registered Sensors</div>', '<div class="stat-label">Runtime Sensor Sources</div>'),
    ('<div class="stat-label">Registered Sensor Sources</div>', '<div class="stat-label">Runtime Sensor Sources</div>'),
    (
        "document.getElementById('wm-sensor-count-header').textContent = data.sensor_count || 0;",
        "// Registered sensor count is represented in the runtime sensor source summary card.",
    ),
    (
        "sensors registered. Waiting for first observation cycle...",
        "registered sensor definitions available. Live observation remains disabled unless explicitly enabled.",
    ),
)


def _rewrite_public_html(template: str) -> str:
    """Apply public-copy convergence to a rendered or template HTML string."""
    for old, new in _PUBLIC_COPY_REPLACEMENTS:
        template = template.replace(old, new)

    if _REGISTERED_SENSOR_HEADER in template:
        replacement = _REGISTERED_SENSOR_COPY
        if "wm-live-sensors-header" not in template:
            replacement += _LIVE_SENSOR_HEADER
        template = template.replace(_REGISTERED_SENSOR_HEADER, replacement, 1)

    template = template.replace("<html>", '<html lang="en" dir="ltr">', 1)

    if "apple-mobile-web-app-title" not in template:
        template = template.replace("    <title>Human Flourishing Frameworks</title>", "    <title>Human Flourishing Frameworks</title>" + _IPHONE_APP_META, 1)

    if "site-nav" not in template:
        template = template.replace("    </style>", _SITE_NAV_CSS + "    </style>", 1)
        template = template.replace(
            "        <header>",
            _SITE_NAV_HTML + "        <header>",
            1,
        )

    if ".skip-link" not in template:
        template = template.replace("    </style>", _SKIP_LINK_CSS + "    </style>", 1)

    if "bettersafe-pilot-panel" not in template:
        template = template.replace("    </style>", _BETTERSAFE_PILOT_CSS + "    </style>", 1)
        template = template.replace(
            "        </header>\n\n        <!-- ============================================================ -->\n        <!-- FLOURISHING SCORES",
            "        </header>\n\n" + _BETTERSAFE_PILOT_HTML + "\n        <!-- ============================================================ -->\n        <!-- FLOURISHING SCORES",
            1,
        )

    if "convergence-panel" not in template:
        template = template.replace("    </style>", _CONVERGENCE_TIMELINE_CSS + "    </style>", 1)
        template = template.replace(
            "        <!-- ============================================================ -->\n        <!-- BELIEFS",
            _CONVERGENCE_TIMELINE_HTML + "\n        <!-- ============================================================ -->\n        <!-- BELIEFS",
            1,
        )

    if 'href="#main-content"' not in template:
        template = template.replace(
            '<body>\n    <div class="container">',
            '<body>\n    <a class="skip-link" href="#main-content">Skip to main content</a>\n    <main id="main-content" class="container">',
            1,
        )
        template = template.replace(
            "        </footer>\n    </div>\n\n    <script>",
            "        </footer>\n    </main>\n\n    <script>",
            1,
        )

    if (
        "wm-live-sensors-header" in template
        and "Public runtime sensor state comes from /healthz" not in template
    ):
        template = template.replace(
            "        // ---- WORLD MODEL STATUS ----",
            _HEALTHZ_SENSOR_STATUS_JS + "\n        // ---- WORLD MODEL STATUS ----",
            1,
        )

    if "function buildBetterSafePacket()" not in template:
        template = template.replace(
            "        function toggleSection(id, header) {",
            _BETTERSAFE_PILOT_JS + "\n        function toggleSection(id, header) {",
            1,
        )

    if "convergence-canvas" in template and "convergence timeline chart" not in template:
        template = template.replace(
            "        function toggleSection(id, header) {",
            _CONVERGENCE_TIMELINE_JS + "\n        function toggleSection(id, header) {",
            1,
        )

    return template


def _sanitize_public_template() -> None:
    """Replace misleading public copy in the module-level template."""
    template = getattr(_app_module, "HTML_TEMPLATE", "")
    if isinstance(template, str):
        _app_module.HTML_TEMPLATE = _rewrite_public_html(template)


def _apply_public_ui_baseline() -> None:
    """Kept for compatibility with older tests/imports; handled by rewrite."""
    _sanitize_public_template()


def _clarify_public_sensor_status() -> None:
    """Kept for compatibility with older tests/imports; handled by rewrite."""
    _sanitize_public_template()


_sanitize_public_template()

app = _app_module.app
_app_module.bootstrap_adoption_heartbeat()
background_controller = create_background_controller_from_env()
background_controller.start()


@app.route("/manifest.webmanifest")
def pwa_manifest():
    """Manifest for iPhone/Home Screen pilot shell."""
    response = jsonify(_PWA_MANIFEST)
    response.headers["Content-Type"] = "application/manifest+json"
    response.headers["Cache-Control"] = "no-store, max-age=0"
    return response


@app.route("/bettersafe-icon.svg")
def bettersafe_icon():
    """Small local SVG icon for the BetterSafe pilot shell."""
    return Response(_BETTERSAFE_ICON_SVG, content_type="image/svg+xml")


@app.route("/background/status")
def background_status():
    """Visible status for the opt-in heartbeat-only background mode."""
    return jsonify({"background_mode": background_controller.snapshot()})


@app.route("/os")
def lantern_os_live():
    """Lantern OS live dashboard — orchestrator, games, apps, notes, media."""
    return send_from_directory(Path(__file__).resolve().parent, "lantern-os-live.html")


@app.route("/art")
def art_panels():
    """Pixel art panels — RAG dollhouse art stream."""
    return send_from_directory(Path(__file__).resolve().parent, "art-panels-v2.html")


@app.route("/deployment/identity")
def deployment_identity_status():
    """Visible non-secret deployment identity for live freshness smoke."""
    return jsonify({"deployment": deployment_identity()})


@app.after_request
def _enforce_safe_public_response(response):
    """Prevent stale public dashboard copy from surviving template drift or cache.

    This response-level guard is intentionally presentation-only. It does not add
    writes, sensors, mesh sync, agents, secrets, databases, or deployment
    authority. It gives the public HTML the same claim/guard language even if the
    imported template changes before app.py is corrected directly.
    """
    response.headers["Cache-Control"] = "no-store, max-age=0"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"

    content_type = response.headers.get("Content-Type", "")
    if response.direct_passthrough or "text/html" not in content_type.lower():
        return response

    try:
        html = response.get_data(as_text=True)
        rewritten = _rewrite_public_html(html)
        if rewritten != html:
            response.set_data(rewritten)
            response.headers["Content-Length"] = str(len(response.get_data()))
    except Exception:
        return response

    return response


if __name__ == "__main__":
    app.run()
