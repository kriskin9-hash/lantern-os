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

function isLocalOnlyUrl(value) {
  try {
    const url = new URL(value || "", window.location.href);
    const host = url.hostname.toLowerCase();
    return (
      url.protocol === "file:" ||
      host === "localhost" ||
      host === "127.0.0.1" ||
      host === "0.0.0.0" ||
      host === "::1" ||
      host.startsWith("10.") ||
      host.startsWith("192.168.") ||
      /^172\.(1[6-9]|2\d|3[0-1])\./.test(host)
    );
  } catch {
    return true;
  }
}

function isVerifiedCloudMirror(mirror) {
  if (!mirror || isLocalOnlyUrl(mirror.url)) return false;
  const status = String(mirror.status || "").toLowerCase();
  return status.includes("verified") && status.includes("200");
}

function renderCloudMirrors(mirrors) {
  if (!mirrors) return;
  const localPrimary = mirrors.localPrimary || "http://127.0.0.1:4177";
  const cloudMirrors = mirrors.cloudMirrors || [];
  const verifiedCloudMirrors = cloudMirrors.filter(isVerifiedCloudMirror);
  const publicProofCount = verifiedCloudMirrors.length;

  $("mirrorPrimary").textContent = localPrimary;
  $("mirrorCount").textContent = String(publicProofCount);
  $("mirrorDeploy").textContent = `${mirrors.deployBranch || "master"} -> ${mirrors.deployProvider || "Render"}`;
  $("chatStatus").textContent = window.location.protocol === "file:" ? "preview via local app" : "local";
  $("tunnelStatus").textContent = publicProofCount > 0 ? "cloud verified" : "cloud unverified";
  $("chatMirrorSummary").textContent = `Local primary: ${localPrimary} | verified public mirrors: ${publicProofCount}`;
  const chatLinks = $("chatMirrorLinks");
  chatLinks.innerHTML = "";
  cloudMirrors.slice(0, 3).forEach((mirror) => {
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
  cloudMirrors.forEach((mirror) => {
    const li = document.createElement("li");
    const link = document.createElement("a");
    link.href = mirror.url;
    link.target = "_blank";
    link.rel = "noopener noreferrer";
    link.textContent = mirror.name || mirror.url;
    const meta = document.createElement("span");
    const proof = isVerifiedCloudMirror(mirror) ? "public proof verified" : "public proof missing";
    meta.textContent = ` ${mirror.status || "configured"} ${mirror.healthPath || ""} — ${proof}`;
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
    return "Checking agent fleet status via MCP orchestrator at 127.0.0.1:8787. Use Refresh Status to pull live queue and slot evidence.";
  if (lower.includes("next task") || lower.includes("queue"))
    return "Queue is managed by the orchestrator. Use the operator queue panel above or hit Refresh to see current state.";
  if (lower.includes("hold"))
    return "Holding. Current action paused for operator review.";
  if (lower.includes("approve") || lower.includes("proceed"))
    return "Acknowledged. Proceeding with current action path.";
  return "Message stored locally. Use quick-reply buttons or type for more context.";
}

function appendBubble(role, text) {
  const container = $("chatMessages");
  const empty = $("chatEmpty");
  empty.style.display = "none";
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
  el.style.height = `${Math.min(el.scrollHeight, 150)}px`;
}

function sparkline(canvasId, values) {
  const canvas = $(canvasId);
  if (!canvas) return;
  const ctx = canvas.getContext("2d");
  const width = canvas.width;
  const height = canvas.height;
  ctx.clearRect(0, 0, width, height);
  ctx.lineWidth = 2;
  ctx.beginPath();
  values.forEach((value, index) => {
    const x = (index / Math.max(values.length - 1, 1)) * width;
    const y = height - (value / 100) * height;
    if (index === 0) ctx.moveTo(x, y);
    else ctx.lineTo(x, y);
  });
  ctx.stroke();
}

function renderScores(scores) {
  $("hffHumans").textContent = `${scores.humans}%`;
  $("hffAnimals").textContent = `${scores.animals}%`;
  $("hffEcosystems").textContent = `${scores.ecosystems}%`;
  $("hffUniverse").textContent = `${scores.universe}%`;
  sparkline("scoreChart", [scores.humans, scores.animals, scores.ecosystems, scores.universe]);
}

async function init() {
  normalizeInternalLinks();
  document.querySelectorAll("[data-action]").forEach((button) => {
    button.addEventListener("click", async () => {
      try {
        await postAction(`/api/actions/${button.dataset.action}`, button.textContent.trim());
      } catch (err) {
        log(`Error: ${err.message}`);
      }
    });
  });
  $("ingestFlatRag").addEventListener("click", async () => {
    try {
      await ingestFlatRagHouse();
    } catch (err) {
      log(`Error: ${err.message}`);
    }
  });
  $("refresh").addEventListener("click", () => refresh().catch((err) => log(`Error: ${err.message}`)));
  $("autoUpdate").addEventListener("click", () => {
    if (autoUpdateTimer) {
      clearInterval(autoUpdateTimer);
      autoUpdateTimer = null;
      log("Auto update off.");
    } else {
      autoUpdateTimer = setInterval(() => refresh().catch((err) => log(`Error: ${err.message}`)), 30000);
      log("Auto update on: refreshing every 30s.");
    }
  });
  $("noteForm").addEventListener("submit", (event) => storeNote(event).catch((err) => log(`Error: ${err.message}`)));
  $("conversationForm").addEventListener("submit", (event) => {
    event.preventDefault();
    sendChat($("conversationText").value);
  });
  $("conversationText").addEventListener("input", (event) => autoGrow(event.target));
  renderScores({ humans: 43, animals: 52, ecosystems: 50, universe: 54 });
  showQuickReplies("greeting");
  refresh().catch((err) => log(`Error: ${err.message}`));
}

init();
