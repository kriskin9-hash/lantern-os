const $ = (id) => document.getElementById(id);

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
  const response = await fetch(path, {
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
  const [[status, rag, conversationState, flatHouse]] = await Promise.all([
    Promise.all([
      api("/api/status"),
      api("/api/rag-cache"),
      api("/api/conversations?limit=8"),
      api("/api/flat-rag-house"),
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

function renderConversations(conversations) {
  const list = $("conversationList");
  list.innerHTML = "";

  if (!conversations.length) {
    const li = document.createElement("li");
    li.textContent = "No local conversation notes stored yet.";
    list.appendChild(li);
    return;
  }

  conversations.slice().reverse().forEach((entry) => {
    const li = document.createElement("li");
    const stamp = new Date(entry.recordedAt).toLocaleString();
    li.textContent = `${stamp} | ${entry.role}: ${entry.text}`;
    list.appendChild(li);
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

async function storeConversation(event) {
  event.preventDefault();
  const text = $("conversationText").value.trim();
  if (!text) {
    log("Conversation text required.");
    return;
  }

  await api("/api/conversations", {
    method: "POST",
    body: JSON.stringify({
      surface: "lantern-garage",
      role: $("conversationRole").value,
      text,
    }),
  });
  $("conversationText").value = "";
  log("Conversation stored locally.");
  await refresh();
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

$("refresh").addEventListener("click", () => refresh().catch((error) => log(error.message)));
$("runLoop").addEventListener("click", () => postAction("/api/actions/run-loop", "Loop").catch((error) => log(error.message)));
$("localControls").addEventListener("click", () => postAction("/api/actions/local-controls", "Local controls").catch((error) => log(error.message)));
$("flatRagIngest").addEventListener("click", () => ingestFlatRagHouse().catch((error) => log(error.message)));
$("autoUpdate").addEventListener("click", toggleAutoUpdate);
$("conversationForm").addEventListener("submit", (event) => storeConversation(event).catch((error) => log(error.message)));
$("ragForm").addEventListener("submit", (event) => storeRagItem(event).catch((error) => log(error.message)));
$("noteForm").addEventListener("submit", (event) => storeNote(event).catch((error) => log(error.message)));

refresh().catch((error) => log(error.message));
