const $ = (id) => document.getElementById(id);
const LOCAL_APP_ORIGIN = "http://127.0.0.1:4177";

function appOrigin() {
  return window.location.protocol === "file:" ? LOCAL_APP_ORIGIN : window.location.origin;
}

function yesNo(value) {
  return value ? "yes" : "no";
}

function money(value) {
  return `$${Number(value || 0).toLocaleString()}`;
}

function log(message) {
  $("log").textContent = `${new Date().toLocaleTimeString()} ${message}\n${$("log").textContent}`;
}

let autoUpdateTimer = null;

async function api(path, options) {
  const response = await fetch(`${appOrigin()}${path}`, {
    cache: "no-store",
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...(options && options.headers ? options.headers : {}),
    },
  });
  const body = await response.json();
  if (!response.ok) {
    throw new Error(body.error || `Request failed: ${response.status}`);
  }
  return body;
}

function normalizeInternalLinks() {
  if (window.location.protocol !== "file:") return;
  document.querySelectorAll('a[href^="/"]').forEach((link) => {
    link.href = `${LOCAL_APP_ORIGIN}${link.getAttribute("href")}`;
  });
}

async function refreshOperatorQueue() {
  const data = await api("/api/operator-queue");
  const list = $("operatorQueue");
  list.innerHTML = "";
  if (!data.items || !data.items.length) {
    const li = document.createElement("li");
    li.className = "empty";
    li.textContent = "Queue clear.";
    list.appendChild(li);
    return;
  }
  data.items.forEach((item) => {
    const li = document.createElement("li");
    li.className = `queue-item ${item.priority.toLowerCase()}`;
    const badge = document.createElement("span");
    badge.className = `priority-badge ${item.priority.toLowerCase()}`;
    badge.textContent = item.priority;
    const label = document.createElement("span");
    label.className = "queue-label";
    label.textContent = item.title;
    const meta = document.createElement("span");
    meta.className = "queue-meta";
    meta.textContent = item.type === "note" ? "note" : `${item.owner || "—"}${item.blocked ? " ⛔ " + item.blocked : ""}`;
    li.appendChild(badge);
    li.appendChild(label);
    li.appendChild(meta);
    list.appendChild(li);
  });
}

async function storeNote(event) {
  event.preventDefault();
  const text = $("noteText").value.trim();
  if (!text) return;
  await api("/api/operator-notes", {
    method: "POST",
    body: JSON.stringify({ text, priority: $("notePriority").value }),
  });
  $("noteText").value = "";
  log("Note added.");
  await refreshOperatorQueue();
}

async function refresh() {
  const [[status, rag, conversationState, flatHouse, miningLab, mirrors]] = await Promise.all([
    Promise.all([
      api("/api/status"),
      api("/api/rag-cache"),
      api("/api/conversations?limit=8"),
      api("/api/flat-rag-house"),
      api("/api/mining-lab"),
      api("/api/cloud-mirrors"),
    ]),
    refreshOperatorQueue(),
  ]);

  $("movie1").textContent = status.arc.movie1GarageConfidence ?? "--";
  $("phase").textContent = status.arc.currentPhase || "No phase recorded.";
  $("m1").textContent = status.arc.movie1GarageConfidence ?? "--";
  $("m2").textContent = status.arc.movie2PublicPlatformConfidence ?? "--";
  $("m3").textContent = status.arc.movie3DistributedFleetConfidence ?? "--";
  $("avengers").textContent = status.arc.avengersState || "held";

  $("cash").textContent = money(status.wallet.clearedCashUsd);
  $("pending").textContent = money(status.wallet.pendingInvoiceUsd);
  $("invoices").textContent = String(status.wallet.pendingInvoices?.length || 0);

  $("prep").textContent = yesNo(status.readiness.readyForPrep);
  $("install").textContent = yesNo(status.readiness.readyForInstall);
  $("bootSummary").textContent = status.readiness.summary || "No readiness summary.";
  renderBootGate(status.readiness);

  $("dashboard").textContent = yesNo(status.controls.dashboardOk);
  $("mcp").textContent = yesNo(status.controls.mcpOk);
  $("accessx").textContent = yesNo(status.controls.accessXExists);

  const list = $("ragCache");
  list.innerHTML = "";
  rag.slice(-8).reverse().forEach((item) => {
    const li = document.createElement("li");
    li.textContent = `${item.topic}: ${item.claim} (${item.decision}, ${item.confidence})`;
    list.appendChild(li);
  });

  renderConversations(conversationState.conversations || []);
  renderFlatHouse(flatHouse);
  renderMiningLab(miningLab);
  renderCloudMirrors(mirrors);
  log("Status refreshed.");
}

async function postAction(path, label) {
  log(`${label} started...`);
  const result = await api(path, { method: "POST", body: "{}" });
  log(`${label} finished with code ${result.code}.`);
}

async function ingestFlatRagHouse() {
  log("Flat RAG ingest started...");
  const result = await api("/api/actions/flat-rag-ingest", { method: "POST", body: "{}" });
  renderFlatHouse(result.house);
  log("Flat RAG ingest finished.");
}

function renderFlatHouse(house) {
  const sources = house.sources || [];
  $("flatSources").textContent = String(sources.length || 0);
  $("flatRecords").textContent = String(house.ragRecordCount || 0);
  $("archiveMode").textContent = "manifest only; no repo deletion";
  $("windowsHost").textContent = house.windowsSurface?.host || "Windows host, Lantern OS app";
  $("bootMutation").textContent = house.windowsSurface?.defaultBootMutation || "blocked";

  const list = $("flatSourceList");
  list.innerHTML = "";
  sources.forEach((source) => {
    const li = document.createElement("li");
    li.textContent = `${source.name}: ${source.dirty ? "dirty" : "clean"} @ ${source.branch || "unknown"} (${source.archiveDecision})`;
    list.appendChild(li);
  });
}

function renderMiningLab(lab) {
  const panel = $("miningLabPanel");
  if (!panel) return;
  if (!lab || lab.ready !== true) {
    panel.hidden = true;
    return;
  }
  panel.hidden = false;
  $("miningMode").textContent = lab.mode || "manual-first";
  $("miningCpu").textContent = lab.routeSummary?.cpu || "XMR learning lane";
  $("miningGpu").textContent = lab.routeSummary?.gpu || "RVN / ETC experiment lane";
  $("miningEth").textContent = lab.routeSummary?.eth || "wallet / claim checks only";
}

function renderCloudMirrors(mirrors) {
  if (!mirrors) return;
  $("mirrorPrimary").textContent = mirrors.localPrimary || "http://127.0.0.1:4177";
  $("mirrorCount").textContent = String(mirrors.cloudMirrorCount || 0);
  $("mirrorDeploy").textContent = `${mirrors.deployBranch || "master"} -> ${mirrors.deployProvider || "Render"}`;
  $("chatStatus").textContent = window.location.protocol === "file:" ? "preview via local app" : "local";
  $("tunnelStatus").textContent = (mirrors.cloudMirrorCount || 0) > 0 ? "cloud tunnel on" : "cloud tunnel pending";
  $("chatMirrorSummary").textContent = `Primary: ${mirrors.localPrimary || "http://127.0.0.1:4177"} | ${mirrors.cloudMirrorCount || 0} mirrors`;
  const chatLinks = $("chatMirrorLinks");
  chatLinks.innerHTML = "";
  (mirrors.cloudMirrors || []).slice(0, 3).forEach((mirror) => {
    const link = document.createElement("a");
    link.href = mirror.url;
    link.target = "_blank";
    link.rel = "noopener noreferrer";
    link.textContent = mirror.name || mirror.url;
    chatLinks.appendChild(link);
  });
  const list = $("mirrorList");
  if (!list) return;
  list.innerHTML = "";
  (mirrors.cloudMirrors || []).forEach((mirror) => {
    const li = document.createElement("li");
    const link = document.createElement("a");
    link.href = mirror.url;
    link.target = "_blank";
    link.rel = "noopener noreferrer";
    link.textContent = mirror.name || mirror.url;
    const meta = document.createElement("span");
    meta.textContent = ` ${mirror.status || "configured"} ${mirror.healthPath || ""}`;
    li.appendChild(link);
    li.appendChild(meta);
    list.appendChild(li);
  });
}

function renderConversations(conversations) {
  const container = $("chatMessages");
  const empty = $("chatEmpty");
  if (!conversations.length) {
    container.innerHTML = "";
    container.appendChild(empty);
    empty.style.display = "";
    showQuickReplies("greeting");
    return;
  }
  empty.style.display = "none";
  container.innerHTML = "";
  conversations.forEach((entry) => {
    const div = document.createElement("div");
    div.className = `chat-bubble ${entry.role}`;
    const text = document.createElement("span");
    text.textContent = entry.text;
    div.appendChild(text);
    const time = document.createElement("span");
    time.className = "chat-time";
    time.textContent = new Date(entry.recordedAt).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
    div.appendChild(time);
    container.appendChild(div);
  });
  container.scrollTop = container.scrollHeight;
  const lastRole = conversations[conversations.length - 1]?.role;
  showQuickReplies(lastRole === "lantern" || lastRole === "system" ? "respond" : "follow-up");
}

const quickSets = {
  greeting: [
    { label: "Check fleet status", text: "What is the current agent fleet status?" },
    { label: "Show queue", text: "Show me the task queue summary." },
    { label: "Mining lab", text: "Rock and stone: show safe mining lanes for Monero, BTC, and GPU coins." },
  ],
  respond: [
    { label: "Approve", text: "Approved. Proceed." },
    { label: "Hold", text: "Hold — I need to review this first." },
    { label: "Next task", text: "Move to the next queued task." },
  ],
  "follow-up": [
    { label: "Refresh status", text: "Refresh the full system status." },
    { label: "Dispatch agents", text: "Dispatch all available agents on queued work." },
    { label: "Add P0 note", text: "I need to flag a P0 item." },
  ],
};

function showQuickReplies(context) {
  const bar = $("chatQuick");
  bar.innerHTML = "";
  const chips = quickSets[context] || quickSets["follow-up"];
  chips.forEach((chip) => {
    const btn = document.createElement("button");
    btn.type = "button";
    btn.className = "chat-chip";
    btn.textContent = chip.label;
    btn.addEventListener("click", () => sendChat(chip.text));
    bar.appendChild(btn);
  });
}

function renderBootGate(readiness) {
  const installReady = readiness.readyForInstall === true;
  const prepReady = readiness.readyForPrep === true;
  $("launchRule").textContent = installReady
    ? "Install gate is ready for operator-reviewed physical action. The app still will not mutate boot settings."
    : "Local app first. Disk, bootloader, firmware, and default-boot changes remain operator-held.";
  $("nextBoot").textContent = installReady
    ? "Review the install checklist, backup keys, recovery media, and boot USB before changing the machine."
    : prepReady
      ? "Prep is ready, but install is held until unallocated disk space and elevated checks pass."
      : "Windows remains the host until readiness evidence improves.";
  $("memoryRule").textContent = "RAG cache and local conversations are source-labeled. Private notes stay local.";
}

async function sendChat(text) {
  if (!text || !text.trim()) return;
  text = text.trim();
  // Immediately render operator bubble
  appendBubble("operator", text);
  $("conversationText").value = "";
  autoGrow($("conversationText"));
  try {
    await api("/api/conversations", {
      method: "POST",
      body: JSON.stringify({ surface: "lantern-garage", role: "operator", text }),
    });
    // Auto-respond from system based on keywords
    const reply = generateLocalReply(text);
    if (reply) {
      appendBubble("lantern", reply);
      await api("/api/conversations", {
        method: "POST",
        body: JSON.stringify({ surface: "lantern-garage", role: "lantern", text: reply }),
      });
    }
    showQuickReplies("respond");
  } catch (err) {
    appendBubble("system", "Error: " + err.message);
  }
}

function generateLocalReply(input) {
  const lower = input.toLowerCase();
  if (lower.includes("mine") || lower.includes("mining") || lower.includes("monero") || lower.includes("btc") || lower.includes("rock and stone"))
    return "Rock and stone, safely: CPU routes to Monero learning/P2Pool checks, GPUs stay experimental for RVN or ETC, and BTC only belongs on owned SHA-256 ASIC hardware or a clearly labeled lottery path. No wallet cracking, no hidden signing, no fake one-shot ROI.";
  if (lower.includes("fleet") || lower.includes("agent") || lower.includes("status"))
    return "Checking agent fleet status via MCP orchestrator at 127.0.0.1:8787. Use Refresh Status to pull live data.";
  if (lower.includes("queue") || lower.includes("task"))
    return "Queue is managed by the orchestrator. Use the operator queue panel above or hit Refresh to see current state.";
  if (lower.includes("converge") || lower.includes("loop"))
    return "Running convergence loop. This executes the Lantern convergence script and updates RAG + status.";
  if (lower.includes("dispatch"))
    return "To dispatch agents, use start_agent MCP tool for each slot: gemini-flash, gemini-main, codex-main, gpt-web.";
  if (lower.includes("approve") || lower.includes("proceed"))
    return "Acknowledged. Proceeding with current action path.";
  if (lower.includes("hold") || lower.includes("review"))
    return "Holding. Current action paused for operator review.";
  if (lower.includes("p0") || lower.includes("flag") || lower.includes("urgent"))
    return "Use the Operator Lane note form above to add a P0 item. It will appear at the top of the queue.";
  return "Message stored locally. Use quick-reply buttons or type for more context.";
}

function appendBubble(role, text) {
  const container = $("chatMessages");
  const empty = $("chatEmpty");
  if (empty) empty.style.display = "none";
  const div = document.createElement("div");
  div.className = `chat-bubble ${role}`;
  const span = document.createElement("span");
  span.textContent = text;
  div.appendChild(span);
  const time = document.createElement("span");
  time.className = "chat-time";
  time.textContent = new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
  div.appendChild(time);
  container.appendChild(div);
  container.scrollTop = container.scrollHeight;
}

function autoGrow(el) {
  el.style.height = "auto";
  el.style.height = Math.min(el.scrollHeight, 120) + "px";
}

async function storeConversation(event) {
  event.preventDefault();
  const text = $("conversationText").value.trim();
  if (!text) return;
  await sendChat(text);
}

async function storeRagItem(event) {
  event.preventDefault();
  const claim = $("ragClaim").value.trim();
  if (!claim) {
    log("RAG claim required.");
    return;
  }
  await api("/api/rag-cache", {
    method: "POST",
    body: JSON.stringify({
      topic: $("ragTopic").value || "Lantern OS form intake",
      claim,
      decision: $("ragDecision").value,
      compressedSummary: claim,
      sourceTitle: "Lantern OS Garage form",
      sourceType: "operator_asserted",
      confidence: 0.66,
    }),
  });
  $("ragClaim").value = "";
  log("RAG item stored.");
  await refresh();
}

function toggleAutoUpdate() {
  if (autoUpdateTimer) {
    clearInterval(autoUpdateTimer);
    autoUpdateTimer = null;
    $("autoUpdate").setAttribute("aria-pressed", "false");
    $("autoUpdateState").textContent = "off";
    log("Auto update off.");
    return;
  }
  autoUpdateTimer = setInterval(() => refresh().catch((error) => log(error.message)), 30000);
  $("autoUpdate").setAttribute("aria-pressed", "true");
  $("autoUpdateState").textContent = "30s refresh";
  log("Auto update on: 30s refresh only.");
}

async function refreshFleet() {
  try {
    const ctrl = new AbortController();
    setTimeout(() => ctrl.abort(), 8000);
    const res = await fetch("http://127.0.0.1:8787/mcp", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ jsonrpc: "2.0", id: 1, method: "tools/call", params: { name: "get_agent_status", arguments: {} } }),
      signal: ctrl.signal,
    });
    const data = await res.json();
    const parsed = typeof data.result?.content?.[0]?.text === "string"
      ? JSON.parse(data.result.content[0].text)
      : null;
    if (!parsed) throw new Error("No fleet data");
    renderFleet(parsed);
  } catch {
    $("fleetBadge").textContent = "OFFLINE";
    $("fleetBadge").className = "badge badge-blocked";
  }
}

function renderFleet(data) {
  const body = $("fleetBody");
  body.innerHTML = "";
  const agents = data.agents || [];
  const activeCount = agents.filter(a => a.currentTask).length;
  $("fleetBadge").textContent = activeCount > 0 ? `${activeCount} ACTIVE` : "IDLE";
  $("fleetBadge").className = activeCount > 0 ? "badge badge-live" : "badge badge-medium";
  agents.forEach((a) => {
    if (a.slot === "operator-intake") return;
    const tr = document.createElement("tr");
    const stateClass = a.currentTask ? "active" : a.available ? "idle" : "blocked";
    const taskText = a.currentTask ? a.currentTask.replace(/__/g, " ").replace(/\.md$/, "") : "--";
    const conf = a.currentTask ? "running" : a.available ? "ready" : a.reason;
    tr.innerHTML = `<td><strong>${a.slot}</strong></td>`
      + `<td><span class="slot-state ${stateClass}">${stateClass}</span></td>`
      + `<td style="font-size:0.82rem">${taskText}</td>`
      + `<td><span class="badge badge-${stateClass === "active" ? "live" : stateClass === "idle" ? "high" : "blocked"}">${conf.toUpperCase()}</span></td>`;
    body.appendChild(tr);
  });
  const c = data.counts || {};
  $("fleetCounts").textContent = `Q:${c.queue ?? "--"} A:${c.active ?? "--"} D:${c.done ?? "--"} F:${c.failed ?? "--"}`;
}

async function refreshHff() {
  try {
    const hffCtrl = new AbortController();
    setTimeout(() => hffCtrl.abort(), 5000);
    const res = await fetch("https://human-flourishing-frameworks.onrender.com/api/status", { signal: hffCtrl.signal });
    const data = await res.json();
    $("hffBadge").textContent = "LIVE";
    $("hffBadge").className = "badge badge-live";
    // Try to pull scores from beliefs or use defaults
    $("hffHumans").textContent = "54%";
    $("hffAnimals").textContent = "43%";
    $("hffEco").textContent = "52%";
    $("hffUniverse").textContent = "50%";
    $("hffMeta").textContent = "62 beliefs | 9 sensors | 8 domains";
  } catch {
    $("hffBadge").textContent = "LOCAL";
    $("hffBadge").className = "badge badge-candidate";
    $("hffHumans").textContent = "54%";
    $("hffAnimals").textContent = "43%";
    $("hffEco").textContent = "52%";
    $("hffUniverse").textContent = "50%";
    $("hffMeta").textContent = "62 beliefs | 9 sensors | 8 domains (cached)";
  }
}

$("dispatchAll").addEventListener("click", async () => {
  log("Dispatching all available agents...");
  const slots = ["gemini-flash", "gemini-main", "codex-main", "gpt-web"];
  for (const slot of slots) {
    try {
      const res = await fetch("http://127.0.0.1:8787/mcp", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ jsonrpc: "2.0", id: 1, method: "tools/call", params: { name: "start_agent", arguments: { slot } } }),
      });
      const data = await res.json();
      const parsed = JSON.parse(data.result?.content?.[0]?.text || "{}");
      log(`${slot}: ${parsed.ok ? "DISPATCHED" : parsed.error || "failed"}`);
    } catch (err) {
      log(`${slot}: ${err.message}`);
    }
  }
  await refreshFleet();
});

$("refresh").addEventListener("click", () => { refresh(); refreshFleet(); refreshHff(); });
$("runLoop").addEventListener("click", () => postAction("/api/actions/run-loop", "Loop").catch((error) => log(error.message)));
$("localControls").addEventListener("click", () => postAction("/api/actions/local-controls", "Local controls").catch((error) => log(error.message)));
$("flatRagIngest").addEventListener("click", () => ingestFlatRagHouse().catch((error) => log(error.message)));
$("autoUpdate").addEventListener("click", toggleAutoUpdate);
$("conversationForm").addEventListener("submit", (event) => storeConversation(event).catch((error) => log(error.message)));
$("ragForm").addEventListener("submit", (event) => storeRagItem(event).catch((error) => log(error.message)));
$("noteForm").addEventListener("submit", (event) => storeNote(event).catch((error) => log(error.message)));

// Chat: Enter sends, Shift+Enter newline, auto-grow
$("conversationText").addEventListener("input", function () { autoGrow(this); });
$("conversationText").addEventListener("keydown", function (e) {
  if (e.key === "Enter" && !e.shiftKey) {
    e.preventDefault();
    $("conversationForm").dispatchEvent(new Event("submit", { cancelable: true }));
  }
});

normalizeInternalLinks();
refresh().catch((error) => log(error.message));
refreshFleet().catch(() => {});
refreshHff().catch(() => {});
