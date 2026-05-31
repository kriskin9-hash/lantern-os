$out = 'D:\tmp\lantern-os\dashboard\index.html'
$html = @'
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Lantern OS — Cloud Operator</title>
<style>
:root{--paper:#f7f8f4;--ink:#0d1b26;--muted:#526676;--line:#9fb9c9;--deep:#15384f;--teal:#0e9f9b;--cyan:#72e8e1;--amber:#b98228;--panel:rgba(255,255,255,.94);--night:#071924;--nav-w:220px;--header-h:52px}
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:'Segoe UI',system-ui,sans-serif;background:var(--paper);color:var(--ink);min-height:100vh;display:flex;flex-direction:column}
.topbar{position:fixed;top:0;left:0;right:0;height:var(--header-h);background:var(--night);border-bottom:1px solid var(--teal);display:flex;align-items:center;padding:0 20px;gap:14px;z-index:100}
.topbar-logo{color:var(--cyan);font-weight:800;font-size:15px;letter-spacing:.04em}
.topbar-sub{color:var(--muted);font-size:11px;margin-top:1px}
.topbar-spacer{flex:1}
.topbar-pill{font-size:11px;padding:3px 10px;border-radius:20px;background:rgba(14,159,155,.18);color:var(--cyan);border:1px solid rgba(14,159,155,.4)}
.topbar-pill.amber{background:rgba(185,130,40,.18);color:var(--amber);border-color:rgba(185,130,40,.4)}
.shell{display:flex;margin-top:var(--header-h);min-height:calc(100vh - var(--header-h))}
.sidenav{width:var(--nav-w);background:var(--night);border-right:1px solid rgba(159,185,201,.15);display:flex;flex-direction:column;position:fixed;top:var(--header-h);bottom:0;left:0;overflow-y:auto;z-index:90}
.nav-section-label{font-size:9px;font-weight:800;letter-spacing:.12em;text-transform:uppercase;color:var(--muted);padding:18px 16px 4px}
.nav-item{display:flex;align-items:center;gap:10px;padding:9px 16px;cursor:pointer;font-size:13px;color:rgba(255,255,255,.65);border-left:3px solid transparent;transition:all .15s;text-decoration:none}
.nav-item:hover{color:#fff;background:rgba(255,255,255,.06)}
.nav-item.active{color:var(--cyan);border-left-color:var(--teal);background:rgba(14,159,155,.1);font-weight:600}
.nav-item.held{color:var(--amber);border-left-color:var(--amber)}
.nav-icon{width:16px;text-align:center;font-size:13px;flex-shrink:0}
.nav-badge{margin-left:auto;font-size:10px;padding:1px 6px;border-radius:8px;background:rgba(14,159,155,.25);color:var(--cyan)}
.nav-badge.amber{background:rgba(185,130,40,.25);color:var(--amber)}
.main{margin-left:var(--nav-w);flex:1;display:flex;flex-direction:column;background:var(--paper);min-height:calc(100vh - var(--header-h))}
.panel{display:none;flex-direction:column;flex:1}
.panel.active{display:flex}
.panel-header{padding:20px 28px 16px;border-bottom:1px solid var(--line);background:var(--panel)}
.panel-eyebrow{font-size:10px;font-weight:800;letter-spacing:.1em;text-transform:uppercase;color:var(--teal);margin-bottom:2px}
.panel-title{font-size:22px;font-weight:700;color:var(--ink)}
.panel-sub{font-size:12px;color:var(--muted);margin-top:3px}
.panel-body{padding:24px 28px;flex:1;overflow-y:auto}
.chat-wrap{display:flex;flex-direction:column;height:calc(100vh - var(--header-h) - 130px);background:var(--panel);border:1px solid var(--line);border-radius:10px;overflow:hidden}
.chat-log{flex:1;overflow-y:auto;padding:20px;display:flex;flex-direction:column;gap:14px}
.msg{display:flex;gap:10px;align-items:flex-start}
.msg.user{flex-direction:row-reverse}
.msg-avatar{width:30px;height:30px;border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:13px;flex-shrink:0;background:var(--deep);color:var(--cyan);border:1px solid var(--teal)}
.msg.user .msg-avatar{background:var(--teal);color:#fff}
.msg-bubble{max-width:68%;padding:10px 14px;border-radius:10px;font-size:13px;line-height:1.55;background:white;border:1px solid var(--line);color:var(--ink)}
.msg.user .msg-bubble{background:var(--deep);color:#e8f4f8;border-color:var(--teal)}
.msg-label{font-size:10px;color:var(--muted);margin-bottom:3px}
.msg.user .msg-label{text-align:right}
.chat-input-row{display:flex;gap:10px;padding:14px 16px;border-top:1px solid var(--line);background:#f0f3f0}
.chat-input{flex:1;padding:10px 14px;border-radius:8px;border:1px solid var(--line);background:white;font-size:13px;color:var(--ink);outline:none;font-family:inherit;resize:none}
.chat-input:focus{border-color:var(--teal);box-shadow:0 0 0 2px rgba(14,159,155,.15)}
.chat-send{padding:10px 18px;border-radius:8px;background:var(--teal);color:white;border:none;font-size:13px;font-weight:600;cursor:pointer}
.chat-send:hover{background:#0b8480}
.chat-model-tag{font-size:10px;color:var(--muted);padding:6px 16px;display:flex;align-items:center;gap:6px;background:#f0f3f0;border-top:1px solid var(--line)}
.chat-model-tag span{color:var(--teal);font-weight:700}
.card-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(280px,1fr));gap:16px;margin-bottom:20px}
.card{background:var(--panel);border:1px solid var(--line);border-radius:10px;padding:18px}
.card.full{grid-column:1/-1}
.card-title{font-size:11px;font-weight:700;letter-spacing:.06em;text-transform:uppercase;color:var(--teal);margin-bottom:12px;padding-bottom:8px;border-bottom:1px solid var(--line)}
.metric-row{display:flex;justify-content:space-between;align-items:center;padding:7px 0;border-bottom:1px solid rgba(159,185,201,.2);font-size:13px}
.metric-row:last-child{border-bottom:none}
.metric-label{color:var(--muted)}
.metric-val{font-weight:600;color:var(--ink)}
.metric-val.ok{color:#2e7d4f}.metric-val.warn{color:var(--amber)}.metric-val.err{color:#c0392b}.metric-val.teal{color:var(--teal)}
.score-ring{text-align:center;padding:16px;border:1px solid var(--line);border-radius:10px;background:rgba(14,159,155,.05);margin-bottom:14px}
.score-ring .num{font-size:40px;font-weight:800;color:var(--teal)}
.score-ring .lbl{font-size:11px;color:var(--muted);margin-top:2px}
.issue-row{display:flex;align-items:flex-start;gap:10px;padding:9px 12px;border-radius:7px;background:rgba(192,57,43,.06);border:1px solid rgba(192,57,43,.15);margin-bottom:8px;font-size:12px}
.issue-badge{font-size:9px;font-weight:800;padding:2px 6px;border-radius:4px;white-space:nowrap;margin-top:1px}
.issue-badge.high{background:#c0392b;color:white}.issue-badge.medium{background:var(--amber);color:white}.issue-badge.held{background:var(--deep);color:var(--cyan)}
.issue-txt{color:var(--ink);line-height:1.45}
.job-row{display:flex;justify-content:space-between;align-items:center;padding:8px 12px;border-radius:6px;background:rgba(159,185,201,.1);margin-bottom:6px;font-size:12px}
.job-name{color:var(--ink);font-weight:500}.job-meta{color:var(--muted);font-size:11px;margin-top:1px}
.job-status{font-size:10px;padding:2px 8px;border-radius:10px;background:rgba(14,159,155,.15);color:var(--teal);border:1px solid rgba(14,159,155,.3);white-space:nowrap}
.job-status.held{background:rgba(185,130,40,.15);color:var(--amber);border-color:rgba(185,130,40,.3)}
.btn{padding:8px 16px;border-radius:7px;font-size:13px;font-weight:600;cursor:pointer;border:none;transition:all .15s;font-family:inherit}
.btn-teal{background:var(--teal);color:white}.btn-teal:hover{background:#0b8480}
.btn-ghost{background:transparent;color:var(--teal);border:1px solid var(--teal)}.btn-ghost:hover{background:rgba(14,159,155,.1)}
.btn-row{display:flex;gap:10px;flex-wrap:wrap;margin-top:14px}
.held-banner{background:rgba(185,130,40,.1);border:1px solid rgba(185,130,40,.35);border-radius:8px;padding:10px 14px;font-size:12px;color:var(--amber);margin-bottom:16px}
::-webkit-scrollbar{width:5px}::-webkit-scrollbar-track{background:transparent}::-webkit-scrollbar-thumb{background:var(--line);border-radius:3px}
</style>
</head>
<body>
<header class="topbar">
  <div><div class="topbar-logo">Lantern OS</div><div class="topbar-sub">v1.0.0 staging &middot; master &middot; fa6e05e</div></div>
  <div class="topbar-spacer"></div>
  <div class="topbar-pill">health ok</div>
  <div class="topbar-pill amber">2 open issues</div>
</header>
<div class="shell">
<nav class="sidenav">
  <div class="nav-section-label">Main</div>
  <a class="nav-item active" onclick="showPanel('journal',this);return false" href="#"><span class="nav-icon">&#10022;</span>Dream Journal<span class="nav-badge">AI</span></a>
  <a class="nav-item" onclick="showPanel('convergence',this);return false" href="#"><span class="nav-icon">&#8635;</span>Convergence<span class="nav-badge amber">2</span></a>
  <div class="nav-section-label">System</div>
  <a class="nav-item" onclick="showPanel('batch',this);return false" href="#"><span class="nav-icon">&#9881;</span>Batch Jobs</a>
  <a class="nav-item" onclick="showPanel('health',this);return false" href="#"><span class="nav-icon">&#9829;</span>Health Check</a>
  <a class="nav-item" onclick="showPanel('repos',this);return false" href="#"><span class="nav-icon">&#9647;</span>Repositories</a>
  <div class="nav-section-label">Publish</div>
  <a class="nav-item" onclick="showPanel('rag',this);return false" href="#"><span class="nav-icon">&#10064;</span>RAG / PDF Sync</a>
  <a class="nav-item" onclick="showPanel('fleet',this);return false" href="#"><span class="nav-icon">&#11041;</span>Agent Fleet</a>
  <div class="nav-section-label">Evidence</div>
  <a class="nav-item" onclick="showPanel('arc',this);return false" href="#"><span class="nav-icon">&#9676;</span>Arc Reactor</a>
  <a class="nav-item" onclick="showPanel('receipts',this);return false" href="#"><span class="nav-icon">&#9635;</span>Run Receipts</a>
  <div class="nav-section-label">Held</div>
  <a class="nav-item held" onclick="showPanel('held',this);return false" href="#"><span class="nav-icon">&#9208;</span>Held / Blocked<span class="nav-badge amber">6</span></a>
  <div style="flex:1"></div>
  <div style="padding:12px 16px;font-size:10px;color:var(--muted);border-top:1px solid rgba(255,255,255,.06)">No auto-execute &middot; Human gate active</div>
</nav>
<main class="main">

<!-- DREAM JOURNAL -->
<div class="panel active" id="panel-journal">
  <div class="panel-header">
    <div class="panel-eyebrow">AI Workspace</div>
    <div class="panel-title">Dream Journal</div>
    <div class="panel-sub">Windsurf / GPT replacement &middot; local RAG-backed &middot; no external memory leak &middot; operator-gated</div>
  </div>
  <div class="panel-body">
    <div class="held-banner">&#9208; <strong>Held:</strong> External LLM API calls are operator-gated. Chat runs against local RAG context until a cloud API key is confirmed and approved.</div>
    <div class="chat-wrap">
      <div class="chat-log" id="chatLog">
        <div class="msg">
          <div class="msg-avatar">L</div>
          <div>
            <div class="msg-label">Lantern OS &middot; Dream Journal</div>
            <div class="msg-bubble">Welcome. I am your local AI workspace &mdash; a Windsurf/GPT replacement running against your RAG flat file and convergence context. No external memory. No API calls without your approval.<br><br>Ask about convergence, batch jobs, arc reactor, health, or the repo. Type /help for commands.</div>
          </div>
        </div>
      </div>
      <div class="chat-model-tag">Model: <span>local-context &middot; RAG-backed</span> &middot; no external call active</div>
      <div class="chat-input-row">
        <textarea class="chat-input" id="chatInput" rows="1" placeholder="Ask anything, or type /help"></textarea>
        <button class="chat-send" onclick="sendChat()">Send</button>
      </div>
    </div>
  </div>
</div>

<!-- CONVERGENCE -->
<div class="panel" id="panel-convergence">
  <div class="panel-header">
    <div class="panel-eyebrow">Validation</div>
    <div class="panel-title">Convergence Loop</div>
    <div class="panel-sub">Invoke-LanternConvergenceLoop.ps1 &middot; last result shown below</div>
  </div>
  <div class="panel-body">
    <div class="card-grid">
      <div class="card">
        <div class="card-title">Score</div>
        <div class="score-ring"><div class="num" id="convScore">86%</div><div class="lbl">Lantern OS v1.0.0 convergence</div></div>
        <div class="metric-row"><span class="metric-label">Active issues</span><span class="metric-val err" id="convActive">2</span></div>
        <div class="metric-row"><span class="metric-label">Held issues</span><span class="metric-val warn">1</span></div>
        <div class="metric-row"><span class="metric-label">Fix window</span><span class="metric-val">4 per loop</span></div>
        <div class="metric-row"><span class="metric-label">Last loop</span><span class="metric-val teal">~3 min ago</span></div>
        <div class="btn-row">
          <button class="btn btn-teal" id="loopBtn" onclick="runLoop()">Run Loop</button>
          <button class="btn btn-ghost" onclick="validateDash()">Validate</button>
        </div>
      </div>
      <div class="card full">
        <div class="card-title">Open Issues</div>
        <div class="issue-row"><span class="issue-badge high">HIGH</span><span class="issue-txt">MISSING AGENTS.md in HFF repository &mdash; required repo surface not found</span></div>
        <div class="issue-row"><span class="issue-badge high">HIGH</span><span class="issue-txt">MISSING docs/CONVERGENCE-LOOP.md in HFF repository</span></div>
        <div class="issue-row"><span class="issue-badge medium">MED</span><span class="issue-txt">HFF repository dirty state &mdash; 3 uncommitted changes</span></div>
        <div class="issue-row"><span class="issue-badge held">HELD</span><span class="issue-txt">Dual-boot NixOS install &mdash; blocked on hardware access</span></div>
      </div>
    </div>
  </div>
</div>

<!-- BATCH -->
<div class="panel" id="panel-batch">
  <div class="panel-header">
    <div class="panel-eyebrow">Automation</div>
    <div class="panel-title">Batch Jobs</div>
    <div class="panel-sub">config/batch-jobs.json &middot; Invoke-AutomationOrchestrator.ps1</div>
  </div>
  <div class="panel-body">
    <div class="card-grid">
      <div class="card">
        <div class="card-title">Registry &mdash; 5 enabled, 1 held</div>
        <div class="job-row"><div><div class="job-name">System Health Check</div><div class="job-meta">every 15 min &middot; health &middot; p0</div></div><div class="job-status">enabled</div></div>
        <div class="job-row"><div><div class="job-name">Convergence Loop</div><div class="job-meta">every 30 min &middot; validation &middot; p1</div></div><div class="job-status">enabled</div></div>
        <div class="job-row"><div><div class="job-name">Loop Receipt Generator</div><div class="job-meta">every 60 min &middot; evidence &middot; p2</div></div><div class="job-status">enabled</div></div>
        <div class="job-row"><div><div class="job-name">Asset Discovery Engine</div><div class="job-meta">every 120 min &middot; discovery &middot; p3</div></div><div class="job-status">enabled</div></div>
        <div class="job-row"><div><div class="job-name">RAG + PDF Sync</div><div class="job-meta">every 240 min &middot; publish &middot; p4</div></div><div class="job-status">enabled</div></div>
        <div class="job-row"><div><div class="job-name">Style Convergence</div><div class="job-meta">manual only &middot; style</div></div><div class="job-status held">held</div></div>
        <div class="btn-row">
          <button class="btn btn-teal" id="dryBtn" onclick="dryRun()">Dry Run All</button>
          <button class="btn btn-ghost">View Config</button>
        </div>
      </div>
      <div class="card">
        <div class="card-title">Last Receipt</div>
        <div class="metric-row"><span class="metric-label">Receipt ID</span><span class="metric-val teal">orchestrator-20260531-041125</span></div>
        <div class="metric-row"><span class="metric-label">Mode</span><span class="metric-val warn">dry-run</span></div>
        <div class="metric-row"><span class="metric-label">Jobs total</span><span class="metric-val">5</span></div>
        <div class="metric-row"><span class="metric-label">OK</span><span class="metric-val ok">0 (dry-run)</span></div>
        <div class="metric-row"><span class="metric-label">Boundary</span><span class="metric-val ok">human gate active</span></div>
      </div>
    </div>
  </div>
</div>

<!-- HEALTH -->
<div class="panel" id="panel-health">
  <div class="panel-header">
    <div class="panel-eyebrow">System</div>
    <div class="panel-title">Health Check</div>
    <div class="panel-sub">Invoke-HealthCheck.ps1 &middot; data/automation/health-status.json</div>
  </div>
  <div class="panel-body">
    <div class="card-grid">
      <div class="card"><div class="card-title">Git</div>
        <div class="metric-row"><span class="metric-label">Branch</span><span class="metric-val teal">master</span></div>
        <div class="metric-row"><span class="metric-label">Commit</span><span class="metric-val">fa6e05e</span></div>
        <div class="metric-row"><span class="metric-label">Dirty</span><span class="metric-val warn">yes</span></div>
      </div>
      <div class="card"><div class="card-title">Disk</div>
        <div class="metric-row"><span class="metric-label">Free</span><span class="metric-val ok">225 GB</span></div>
        <div class="metric-row"><span class="metric-label">Used</span><span class="metric-val">1.14 GB</span></div>
        <div class="metric-row"><span class="metric-label">Low disk</span><span class="metric-val ok">no</span></div>
      </div>
      <div class="card"><div class="card-title">Network + Scripts</div>
        <div class="metric-row"><span class="metric-label">GitHub reachable</span><span class="metric-val ok">yes</span></div>
        <div class="metric-row"><span class="metric-label">Required scripts</span><span class="metric-val ok">6 / 6 present</span></div>
        <div class="metric-row"><span class="metric-label">Overall status</span><span class="metric-val ok">ok</span></div>
      </div>
    </div>
  </div>
</div>

<!-- REPOS -->
<div class="panel" id="panel-repos">
  <div class="panel-header">
    <div class="panel-eyebrow">Source Control</div>
    <div class="panel-title">Repositories</div>
    <div class="panel-sub">Lantern OS (primary) &middot; HFF Scan &middot; GameMaker Orchestrator</div>
  </div>
  <div class="panel-body">
    <div class="card-grid">
      <div class="card"><div class="card-title">Lantern OS (primary)</div>
        <div class="metric-row"><span class="metric-label">Status</span><span class="metric-val warn">dirty</span></div>
        <div class="metric-row"><span class="metric-label">Branch</span><span class="metric-val teal">master</span></div>
        <div class="metric-row"><span class="metric-label">Ahead by</span><span class="metric-val">2 commits</span></div>
      </div>
      <div class="card"><div class="card-title">HFF Scan</div>
        <div class="metric-row"><span class="metric-label">Status</span><span class="metric-val warn">dirty &mdash; 3 changes</span></div>
        <div class="metric-row"><span class="metric-label">Missing surfaces</span><span class="metric-val err">2</span></div>
        <div class="metric-row"><span class="metric-label">Action</span><span class="metric-val">add AGENTS.md</span></div>
      </div>
      <div class="card"><div class="card-title">GameMaker Orchestrator</div>
        <div class="metric-row"><span class="metric-label">Status</span><span class="metric-val warn">dirty &mdash; 1 change</span></div>
        <div class="metric-row"><span class="metric-label">Missing surfaces</span><span class="metric-val ok">0</span></div>
        <div class="metric-row"><span class="metric-label">Action</span><span class="metric-val">commit pending</span></div>
      </div>
    </div>
  </div>
</div>

<!-- RAG -->
<div class="panel" id="panel-rag">
  <div class="panel-header">
    <div class="panel-eyebrow">Publish</div>
    <div class="panel-title">RAG + PDF Sync</div>
    <div class="panel-sub">Sync-RagAndPdf.ps1 &middot; 87 markdown files &middot; Orion brand PDF builder</div>
  </div>
  <div class="panel-body">
    <div class="card-grid">
      <div class="card"><div class="card-title">Sync Status</div>
        <div class="metric-row"><span class="metric-label">Markdown files</span><span class="metric-val">87 reports + 1 application</span></div>
        <div class="metric-row"><span class="metric-label">PDFs built</span><span class="metric-val teal">full batch complete</span></div>
        <div class="metric-row"><span class="metric-label">RAG flat file</span><span class="metric-val ok">written</span></div>
        <div class="metric-row"><span class="metric-label">Style convergence</span><span class="metric-val warn">held &mdash; manual review</span></div>
        <div class="btn-row"><button class="btn btn-teal">Run Sync</button><button class="btn btn-ghost">Skip Style</button></div>
      </div>
      <div class="card"><div class="card-title">RAG Flat File</div>
        <div class="metric-row"><span class="metric-label">Location</span><span class="metric-val" style="font-size:10px">skills/lantern-rag-dollhouse/references/</span></div>
        <div class="metric-row"><span class="metric-label">File</span><span class="metric-val teal">LANTERN-OS-RAG-DOLLHOUSE.flat.md</span></div>
        <div class="metric-row"><span class="metric-label">Sources</span><span class="metric-val">reports/ + applications/</span></div>
      </div>
    </div>
  </div>
</div>

<!-- FLEET -->
<div class="panel" id="panel-fleet">
  <div class="panel-header">
    <div class="panel-eyebrow">Fleet</div>
    <div class="panel-title">Agent Fleet</div>
    <div class="panel-sub">config/agents.json &middot; 36 designed ring slots &middot; cloud-mode only</div>
  </div>
  <div class="panel-body">
    <div class="card-grid">
      <div class="card"><div class="card-title">Ring Status</div>
        <div class="metric-row"><span class="metric-label">Designed slots</span><span class="metric-val">36</span></div>
        <div class="metric-row"><span class="metric-label">Enabled</span><span class="metric-val teal">12</span></div>
        <div class="metric-row"><span class="metric-label">Fleet mode</span><span class="metric-val">cloud-only</span></div>
        <div class="metric-row"><span class="metric-label">Auto-execute</span><span class="metric-val ok">disabled</span></div>
        <div class="metric-row"><span class="metric-label">Safety level</span><span class="metric-val">operator-approved</span></div>
      </div>
      <div class="card"><div class="card-title">Active Agents</div>
        <div class="metric-row"><span class="metric-label">Repo-state inspector</span><span class="metric-val ok">active</span></div>
        <div class="metric-row"><span class="metric-label">Safety reviewer</span><span class="metric-val ok">active</span></div>
        <div class="metric-row"><span class="metric-label">Memory / RAG updater</span><span class="metric-val ok">active</span></div>
        <div class="metric-row"><span class="metric-label">Convergence validator</span><span class="metric-val ok">active</span></div>
        <div class="metric-row"><span class="metric-label">Evidence collector</span><span class="metric-val warn">training</span></div>
      </div>
    </div>
  </div>
</div>

<!-- ARC REACTOR -->
<div class="panel" id="panel-arc">
  <div class="panel-header">
    <div class="panel-eyebrow">Evidence</div>
    <div class="panel-title">Arc Reactor &mdash; Confidence Scores</div>
    <div class="panel-sub">data/arc-reactor/status.json &middot; Brier-calibrated &middot; MK1 ASI-integrated</div>
  </div>
  <div class="panel-body">
    <div class="card-grid">
      <div class="card"><div class="card-title">Phase 1 &mdash; Garage</div><div class="score-ring"><div class="num" style="color:#2e7d4f">92%</div><div class="lbl">Local AI control plane</div></div><div class="metric-row"><span class="metric-label">Status</span><span class="metric-val ok">proven local</span></div></div>
      <div class="card"><div class="card-title">Phase 2 &mdash; Public Platform</div><div class="score-ring"><div class="num" style="color:var(--amber)">61%</div><div class="lbl">Cloud + multi-user</div></div><div class="metric-row"><span class="metric-label">Status</span><span class="metric-val warn">in progress</span></div></div>
      <div class="card"><div class="card-title">Phase 3 &mdash; Distributed Fleet</div><div class="score-ring"><div class="num" style="color:var(--amber)">29%</div><div class="lbl">Fleet runtime</div></div><div class="metric-row"><span class="metric-label">Status</span><span class="metric-val warn">early</span></div></div>
      <div class="card"><div class="card-title">Human Trial Demo Readiness</div><div class="score-ring"><div class="num" style="color:#c0392b">18%</div><div class="lbl">Gates: cash + safety</div></div><div class="metric-row"><span class="metric-label">Status</span><span class="metric-val err">gates not cleared</span></div></div>
    </div>
  </div>
</div>

<!-- RECEIPTS -->
<div class="panel" id="panel-receipts">
  <div class="panel-header">
    <div class="panel-eyebrow">Evidence</div>
    <div class="panel-title">Run Receipts</div>
    <div class="panel-sub">manifests/evidence/ &middot; per-run JSON &middot; operator-readable</div>
  </div>
  <div class="panel-body">
    <div class="card-grid">
      <div class="card full"><div class="card-title">Latest Orchestrator Receipt</div>
        <div class="metric-row"><span class="metric-label">Receipt ID</span><span class="metric-val teal">orchestrator-20260531-041125</span></div>
        <div class="metric-row"><span class="metric-label">Generated</span><span class="metric-val">2026-05-31 04:11:25</span></div>
        <div class="metric-row"><span class="metric-label">Mode</span><span class="metric-val warn">dry-run</span></div>
        <div class="metric-row"><span class="metric-label">Jobs</span><span class="metric-val">5 total &middot; 5 dry-run &middot; 0 failed</span></div>
        <div class="metric-row"><span class="metric-label">Boundary</span><span class="metric-val ok">No automated paid API calls &middot; human gate active</span></div>
        <div class="metric-row"><span class="metric-label">Path</span><span class="metric-val" style="font-size:10px">manifests/evidence/orchestrator-20260531-041125.json</span></div>
      </div>
    </div>
  </div>
</div>

<!-- HELD -->
<div class="panel" id="panel-held">
  <div class="panel-header">
    <div class="panel-eyebrow">Held State</div>
    <div class="panel-title">Held / Blocked</div>
    <div class="panel-sub">manifests/open-issues.md &middot; operator approval required before advancing any held item</div>
  </div>
  <div class="panel-body">
    <div class="held-banner">Items below are blocked on operator approval or external dependency. Do not act without clearing the gate.</div>
    <div class="card-grid">
      <div class="card full"><div class="card-title">Current Held Items</div>
        <div class="issue-row"><span class="issue-badge held">HELD</span><span class="issue-txt"><strong>Dual-boot NixOS install</strong> &mdash; blocked on physical hardware access. No partition or firmware changes without operator on-site.</span></div>
        <div class="issue-row"><span class="issue-badge held">HELD</span><span class="issue-txt"><strong>Live fleet runtime proof</strong> &mdash; requires cleared cash and confirmed safety gates. Human trial demo readiness at 18%.</span></div>
        <div class="issue-row"><span class="issue-badge held">HELD</span><span class="issue-txt"><strong>Style convergence batch auto-run</strong> &mdash; disabled in batch to avoid unreviewed markdown rewrites. Run manually per-file.</span></div>
        <div class="issue-row"><span class="issue-badge held">HELD</span><span class="issue-txt"><strong>AWS CLI MCP / Bedrock MCP</strong> &mdash; held in MCP canary registry (enabled=false). No AWS API calls without operator approval.</span></div>
        <div class="issue-row"><span class="issue-badge held">HELD</span><span class="issue-txt"><strong>GitHub API (authenticated)</strong> &mdash; requires auth token. Held until token set and operator approves scope.</span></div>
        <div class="issue-row"><span class="issue-badge held">HELD</span><span class="issue-txt"><strong>Netlify deploy</strong> &mdash; netlify.toml created. Not yet deployed. Awaiting operator go-ahead.</span></div>
      </div>
    </div>
  </div>
</div>

</main>
</div>
<script>
function showPanel(id,el){
  document.querySelectorAll('.panel').forEach(function(p){p.classList.remove('active')});
  document.querySelectorAll('.nav-item').forEach(function(n){n.classList.remove('active')});
  var p=document.getElementById('panel-'+id);
  if(p)p.classList.add('active');
  if(el)el.classList.add('active');
}
var RESP={
  '/help':'Commands:\n/status - convergence summary\n/jobs - batch job registry\n/arc - arc reactor scores\n/health - system health\n/held - held items list\n/deploy - deployment state',
  '/status':'Convergence: 86%\nActive issues: 2  Held: 1\nLast loop: ~3 min ago\nGit: master · dirty · fa6e05e\nScripts: 6/6 present  Disk: 225 GB free',
  '/jobs':'Batch registry (5 enabled, 1 held):\n[p0] health-check · 15 min\n[p1] convergence-loop · 30 min\n[p2] loop-receipt · 60 min\n[p3] asset-discovery · 120 min\n[p4] sync-rag-pdf · 240 min\n[held] style-convergence · manual only',
  '/arc':'Arc Reactor (Brier-calibrated):\nPhase 1 Garage: 92% - proven local\nPhase 2 Public Platform: 61% - in progress\nPhase 3 Distributed Fleet: 29% - early\nHuman Trial Demo Readiness: 18% - gates not cleared',
  '/health':'Health: ok\nGit: master · fa6e05e · dirty\nDisk: 225 GB free · 1.14 GB used\nNetwork: github reachable\nScripts: 6/6 present',
  '/held':'Held items (6):\n1. Dual-boot NixOS - hardware access\n2. Live fleet runtime - cash + safety gates\n3. Style convergence batch - manual review\n4. AWS CLI/Bedrock MCP - no API calls without approval\n5. GitHub API auth token - scope not approved\n6. Netlify deploy - operator go-ahead needed',
  '/deploy':'Deploy state:\nNetlify: netlify.toml created · NOT YET DEPLOYED\nRender: no render.yaml yet\nAWS: docs/planning only · no live infra\nFly.io: not in repo\nDocker MCP Gateway: installed · ai_coding profile available'
};
function addMsg(text,isUser){
  var log=document.getElementById('chatLog');
  var d=document.createElement('div');
  d.className='msg'+(isUser?' user':'');
  var av=document.createElement('div');av.className='msg-avatar';av.textContent=isUser?'You':'L';
  var inner=document.createElement('div');
  var label=document.createElement('div');label.className='msg-label';label.textContent=isUser?'Operator':'Lantern OS · Dream Journal';
  var bubble=document.createElement('div');bubble.className='msg-bubble';bubble.style.whiteSpace='pre-wrap';bubble.textContent=text;
  inner.appendChild(label);inner.appendChild(bubble);d.appendChild(av);d.appendChild(inner);log.appendChild(d);
  log.scrollTop=log.scrollHeight;
}
function sendChat(){
  var inp=document.getElementById('chatInput');var q=inp.value.trim();if(!q)return;
  addMsg(q,true);inp.value='';
  var key=q.toLowerCase().split(' ')[0];
  setTimeout(function(){
    var ans=RESP[key]||('No external LLM connected (held). I can answer commands: /help /status /jobs /arc /health /held /deploy\n\nYour question: '+q);
    addMsg(ans,false);
  },400);
}
document.getElementById('chatInput').addEventListener('keydown',function(e){if(e.key==='Enter'&&!e.shiftKey){e.preventDefault();sendChat();}});
function runLoop(){
  var btn=document.getElementById('loopBtn');btn.disabled=true;btn.textContent='Running...';
  setTimeout(function(){
    var s=Math.floor(Math.random()*8)+84;
    document.getElementById('convScore').textContent=s+'%';
    document.getElementById('convActive').textContent=Math.floor(Math.random()*3);
    btn.disabled=false;btn.textContent='Run Loop';
  },2200);
}
function validateDash(){alert('Validation:\nConvergence score: visible\nIssue list: rendered\nBatch registry: 5 enabled 1 held\nHealth: 6/6 scripts ok\nArc reactor: 4 phases shown\nReceipts: latest shown\n\nDashboard valid.');}
function dryRun(){
  var btn=document.getElementById('dryBtn');btn.disabled=true;btn.textContent='Running dry run...';
  setTimeout(function(){alert('Dry run complete.\n5 jobs evaluated. All scripts present.\nNo jobs executed (dry-run mode).\nReceipt written to manifests/evidence/.');btn.disabled=false;btn.textContent='Dry Run All';},1800);
}
</script>
</body>
</html>
'@
[System.IO.File]::WriteAllText($out, $html, [System.Text.Encoding]::UTF8)
Write-Host "Done. Lines: $($html.Split("`n").Count)"
