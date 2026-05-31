const $ = (id) => document.getElementById(id);
const LOCAL_APP_ORIGIN = "http://127.0.0.1:4177";
const DREAMER_USER = "courtney";

function appOrigin() {
  return window.location.protocol === "file:" ? LOCAL_APP_ORIGIN : window.location.origin;
}

async function api(path, options = {}) {
  const response = await fetch(`${appOrigin()}${path}`, {
    cache: "no-store",
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...(options.headers || {}),
    },
  });
  const body = await response.json();
  if (!response.ok) {
    throw new Error(body.error || `Request failed: ${response.status}`);
  }
  return body;
}

function fmtDate(iso) {
  if (!iso) return "--";
  const d = new Date(iso);
  return isNaN(d) ? "--" : d.toLocaleDateString();
}

function fmtDateShort(iso) {
  if (!iso) return "--";
  const d = new Date(iso);
  return isNaN(d) ? "--" : `${d.getMonth() + 1}/${d.getDate()}`;
}

function fmtTimeAgo(iso) {
  if (!iso) return "--";
  const d = new Date(iso);
  if (isNaN(d)) return "--";
  const diff = Date.now() - d.getTime();
  const mins = Math.floor(diff / 60000);
  if (mins < 1) return "just now";
  if (mins < 60) return `${mins}m ago`;
  const hrs = Math.floor(mins / 60);
  if (hrs < 24) return `${hrs}h ago`;
  const days = Math.floor(hrs / 24);
  return `${days}d ago`;
}

function renderStats(stats) {
  $("statTotal").textContent = stats.total ?? 0;
  $("statDreams").textContent = stats.dreams ?? 0;
  $("statNotes").textContent = stats.notes ?? 0;
  $("statPlaces").textContent = stats.places ?? 0;
  $("statCharacters").textContent = stats.characters ?? 0;
  $("statLores").textContent = stats.lores ?? 0;
  $("statSymbols").textContent = stats.symbols ?? 0;
  $("statMirrors").textContent = stats.mirrors ?? 0;
  $("statStreak").textContent = stats.streak ?? 0;
  $("statAvg").textContent = stats.averageTextLength ?? 0;
  $("statLast").textContent = fmtTimeAgo(stats.lastAt);
  $("statCells").textContent = stats.matrix?.cells ?? 0;
}

function renderTimeline(timeline) {
  const chart = $("timelineChart");
  chart.innerHTML = "";
  if (!timeline || timeline.length === 0) {
    $("timelineMeta").textContent = "The surface is still. Threads will ripple in time.";
    return;
  }
  const maxCount = Math.max(1, ...timeline.map((t) => t.count));
  timeline.slice(-30).forEach((day) => {
    const bar = document.createElement("div");
    bar.className = "timeline-bar";
    bar.style.height = `${Math.max(4, (day.count / maxCount) * 100)}%`;
    bar.title = `${day.date}: ${day.count} entries`;
    bar.setAttribute("role", "img");
    bar.setAttribute("aria-label", `${day.date}: ${day.count} entries`);
    const label = document.createElement("span");
    label.className = "timeline-label";
    label.textContent = fmtDateShort(day.date + "T00:00:00");
    bar.appendChild(label);
    chart.appendChild(bar);
  });
  $("timelineMeta").textContent = `${timeline.length} days tracked`;
}

function renderHeatmap(timeline) {
  const grid = $("heatmapGrid");
  grid.innerHTML = "";
  const days = [];
  for (let i = 29; i >= 0; i--) {
    const d = new Date();
    d.setDate(d.getDate() - i);
    d.setHours(0, 0, 0, 0);
    days.push({ date: d.toISOString().slice(0, 10), obj: d });
  }
  const byDate = new Map((timeline || []).map((t) => [t.date, t.count]));
  days.forEach((day) => {
    const cell = document.createElement("div");
    const count = byDate.get(day.date) || 0;
    cell.className = "heatmap-cell";
    cell.dataset.count = count;
    cell.title = `${day.date}: ${count} entries`;
    cell.setAttribute("role", "img");
    cell.setAttribute("aria-label", `${day.date}: ${count} entries`);
    grid.appendChild(cell);
  });
}

function renderTags(topTags) {
  const cloud = $("tagCloud");
  cloud.innerHTML = "";
  if (!topTags || topTags.length === 0) {
    $("tagMeta").textContent = "No names for the feelings yet. They will gather.";
    return;
  }
  const maxCount = Math.max(1, ...topTags.map((t) => t.count));
  topTags.forEach((tag) => {
    const span = document.createElement("span");
    span.className = "tag-pill";
    const scale = 0.85 + (tag.count / maxCount) * 0.4;
    span.style.fontSize = `${scale}rem`;
    span.textContent = `#${tag.tag} ${tag.count}`;
    cloud.appendChild(span);
  });
  $("tagMeta").textContent = `${topTags.length} top tags`;
}

function renderSources(sources) {
  const list = $("sourceList");
  list.innerHTML = "";
  const entries = Object.entries(sources || {}).sort((a, b) => b[1] - a[1]);
  if (entries.length === 0) {
    list.innerHTML = "<p class='muted'>No springs traced yet. The well draws from many places.</p>";
    return;
  }
  entries.forEach(([src, count]) => {
    const row = document.createElement("div");
    row.className = "source-row";
    const label = document.createElement("span");
    label.textContent = src;
    const value = document.createElement("span");
    value.className = "source-count";
    value.textContent = count;
    row.appendChild(label);
    row.appendChild(value);
    list.appendChild(row);
  });
}

function renderRecent(entries) {
  const list = $("recentEntries");
  list.innerHTML = "";
  if (!entries || entries.length === 0) {
    const item = document.createElement("li");
    item.className = "dreamer-empty";
    item.textContent = "The well is quiet. Threads will come.";
    list.appendChild(item);
    return;
  }
  entries.slice(0, 10).forEach((entry) => {
    const item = document.createElement("li");
    item.className = `dreamer-entry ${entry.kind || "note"}`;
    const heading = document.createElement("div");
    heading.className = "dreamer-entry-heading";
    const kind = document.createElement("strong");
    kind.textContent = String(entry.kind || "note").toUpperCase();
    const time = document.createElement("span");
    time.textContent = entry.recordedAt ? new Date(entry.recordedAt).toLocaleString() : "local time unknown";
    heading.appendChild(kind);
    heading.appendChild(time);
    const name = document.createElement("div");
    name.className = "dreamer-entry-name";
    if (entry.name) name.textContent = entry.name;
    const text = document.createElement("p");
    text.textContent = entry.text || "";
    const meta = document.createElement("small");
    meta.className = "dreamer-entry-meta";
    const metaParts = [];
    if (entry.ternaryId) metaParts.push(`matrix: ${entry.ternaryId}`);
    if (entry.mood) metaParts.push(`mood: ${entry.mood}`);
    if (Array.isArray(entry.tags) && entry.tags.length) metaParts.push(`#${entry.tags.join(" #")}`);
    if (!metaParts.length) metaParts.push("private local entry");
    meta.textContent = metaParts.join(" | ");
    item.appendChild(heading);
    if (entry.name) item.appendChild(name);
    item.appendChild(text);
    item.appendChild(meta);
    list.appendChild(item);
  });
}

function renderMatrix(nodes) {
  const canvas = $("matrixCanvas");
  if (!canvas) return;
  const ctx = canvas.getContext("2d");
  const w = canvas.width;
  const h = canvas.height;
  ctx.clearRect(0, 0, w, h);
  if (!nodes || nodes.length === 0) {
    $("matrixMeta").textContent = "The crystal is empty. Threads will form.";
    return;
  }
  const maxCoord = 80;
  const padding = 10;
  const plotW = w - padding * 2;
  const plotH = h - padding * 2;
  const nodeMap = new Map();
  const positions = [];
  nodes.forEach((node) => {
    const tid = String(node.ternaryId || "000000000000").split("").map((c) => parseInt(c, 10) % 3);
    while (tid.length < 12) tid.unshift(0);
    const x = tid[0] * 27 + tid[1] * 9 + tid[2] * 3 + tid[3];
    const y = tid[4] * 27 + tid[5] * 9 + tid[6] * 3 + tid[7];
    const px = padding + (x / maxCoord) * plotW;
    const py = padding + (y / maxCoord) * plotH;
    nodeMap.set(node.id, { x: px, y: py, z: tid[8] * 27 + tid[9] * 9 + tid[10] * 3 + tid[11], node });
    positions.push({ x: px, y: py, z: tid[8] * 27 + tid[9] * 9 + tid[10] * 3 + tid[11], node });
  });
  const maxZ = Math.max(1, ...positions.map((p) => p.z));
  const kindColors = {
    dream: "#a78bfa",
    note: "#94a3b8",
    place: "#34d399",
    character: "#fbbf24",
    event: "#f87171",
    lore: "#60a5fa",
    symbol: "#f472b6",
    mirror: "#c084fc",
  };
  ctx.strokeStyle = "rgba(148,163,184,0.25)";
  ctx.lineWidth = 1;
  positions.forEach((pos) => {
    (pos.node.links || []).forEach((linkId) => {
      const target = nodeMap.get(linkId);
      if (target) {
        ctx.beginPath();
        ctx.moveTo(pos.x, pos.y);
        ctx.lineTo(target.x, target.y);
        ctx.stroke();
      }
    });
  });
  positions.forEach((pos) => {
    const color = kindColors[pos.node.kind] || "#94a3b8";
    const radius = 2 + (pos.z / maxZ) * 4;
    ctx.beginPath();
    ctx.arc(pos.x, pos.y, radius, 0, Math.PI * 2);
    ctx.fillStyle = color;
    ctx.fill();
    ctx.strokeStyle = "rgba(0,0,0,0.2)";
    ctx.lineWidth = 0.5;
    ctx.stroke();
  });
  $("matrixMeta").textContent = `${nodes.length} facets in the crystal.`;
}

let lastStats = {};
let pollTimer = null;
const POLL_INTERVAL_MS = 8000;

function animateValue(element, from, to, duration = 400) {
  if (from === to) return;
  const start = performance.now();
  const step = (now) => {
    const progress = Math.min((now - start) / duration, 1);
    const value = Math.round(from + (to - from) * progress);
    element.textContent = value;
    if (progress < 1) requestAnimationFrame(step);
  };
  requestAnimationFrame(step);
}

function renderStatsAnimated(stats) {
  const fields = [
    { id: "statTotal", key: "total" },
    { id: "statDreams", key: "dreams" },
    { id: "statNotes", key: "notes" },
    { id: "statPlaces", key: "places" },
    { id: "statCharacters", key: "characters" },
    { id: "statLores", key: "lores" },
    { id: "statSymbols", key: "symbols" },
    { id: "statMirrors", key: "mirrors" },
    { id: "statStreak", key: "streak" },
    { id: "statAvg", key: "averageTextLength" },
    { id: "statCells", key: "matrixCells" },
  ];
  fields.forEach(({ id, key }) => {
    const el = $(id);
    const oldVal = lastStats[key] ?? 0;
    const newVal = stats[key] ?? 0;
    if (oldVal !== newVal) animateValue(el, oldVal, newVal);
  });
  $("statLast").textContent = fmtTimeAgo(stats.lastAt);
  lastStats = { ...stats };
}

function setRefreshState(busy) {
  const btn = $("refreshBtn");
  if (!btn) return;
  btn.disabled = busy;
  btn.textContent = busy ? "Looking..." : "Look again";
}

function updateLastRefreshed() {
  const el = $("lastRefreshed");
  if (!el) return;
  el.textContent = `Glimpsed at ${new Date().toLocaleTimeString()}`;
}

function renderTasks(tasks) {
  const list = $("taskList");
  list.innerHTML = "";
  const open = (tasks || []).filter((t) => t.status !== "done");
  const done = (tasks || []).filter((t) => t.status === "done");
  $("taskCount").textContent = `${open.length} open`;
  if (!tasks || tasks.length === 0) {
    $("taskMeta").textContent = "No steps yet. What small thing comes next?";
    return;
  }
  [...open, ...done.slice(-3)].forEach((task) => {
    const item = document.createElement("li");
    item.className = `task-item ${task.status}`;
    const kind = document.createElement("span");
    kind.className = "task-kind";
    kind.textContent = task.kind;
    const text = document.createElement("span");
    text.className = "task-text";
    text.textContent = task.text;
    const actions = document.createElement("span");
    actions.className = "task-actions";
    if (task.status !== "done") {
      const doneBtn = document.createElement("button");
      doneBtn.type = "button";
      doneBtn.textContent = "Done";
      doneBtn.addEventListener("click", () => completeTask(task.id));
      actions.appendChild(doneBtn);
    } else {
      actions.textContent = "done";
    }
    item.appendChild(kind);
    item.appendChild(text);
    item.appendChild(actions);
    list.appendChild(item);
  });
  $("taskMeta").textContent = `${open.length} open, ${done.length} completed.`;
}

async function addTask(event) {
  event.preventDefault();
  const text = $("taskText").value.trim();
  if (!text) return;
  try {
    await api("/api/dreamer/tasks", {
      method: "POST",
      body: JSON.stringify({ user: DREAMER_USER, kind: $("taskKind").value, text }),
    });
    $("taskText").value = "";
    await refreshTasks();
  } catch (error) {
    $("taskMeta").textContent = `Failed to add step: ${error.message}`;
  }
}

async function completeTask(taskId) {
  try {
    await api(`/api/dreamer/tasks/${encodeURIComponent(taskId)}?user=${encodeURIComponent(DREAMER_USER)}`, {
      method: "PATCH",
    });
    await refreshTasks();
  } catch (error) {
    $("taskMeta").textContent = `Failed to complete: ${error.message}`;
  }
}

async function refreshTasks() {
  try {
    const data = await api(`/api/dreamer/tasks?user=${encodeURIComponent(DREAMER_USER)}`);
    renderTasks(data.tasks || []);
  } catch (error) {
    console.error("Task refresh error:", error);
  }
}

function renderConvergence(data) {
  const grid = $("convergenceGrid");
  if (!grid) return;
  grid.innerHTML = "";
  if (!data || !data.dimensions || data.dimensions.length === 0) {
    $("convergenceMeta").textContent = "Convergence state not yet recorded.";
    $("convergenceScore").textContent = "--";
    return;
  }
  const dims = data.dimensions;
  const stateColors = {
    "-1": "var(--danger, #ff6b6b)",
    "0": "var(--muted, #94a3b8)",
    "1": "var(--success, #34d399)",
  };
  const stateLabels = {
    "-1": "held",
    "0": "ready",
    "1": "live",
  };
  dims.forEach((dim) => {
    const cell = document.createElement("div");
    cell.className = "convergence-cell";
    const state = String(dim.state ?? 0);
    cell.style.borderColor = stateColors[state] || stateColors["0"];
    const name = document.createElement("span");
    name.className = "convergence-name";
    name.textContent = dim.name;
    const badge = document.createElement("span");
    badge.className = "convergence-badge";
    badge.style.background = stateColors[state] || stateColors["0"];
    badge.textContent = stateLabels[state] || state;
    cell.appendChild(name);
    cell.appendChild(badge);
    grid.appendChild(cell);
  });
  $("convergenceScore").textContent = data.score?.base10 ?? "--";
  $("convergenceMeta").textContent = `${data.score?.activeCount ?? 0} live, ${data.score?.scaffoldedCount ?? 0} ready, ${data.score?.heldCount ?? 0} held — ${data.method || "3^12-1"}`;
}

async function loadDashboard() {
  setRefreshState(true);
  try {
    const statsData = await api(`/api/dreamer/stats?user=${encodeURIComponent(DREAMER_USER)}`);
    const stats = statsData.stats || {};
    renderStatsAnimated(stats);
    renderTimeline(stats.timeline || []);
    renderHeatmap(stats.timeline || []);
    renderTags(stats.topTags || []);
    renderSources(stats.sources || {});
  } catch (error) {
    console.error("Dashboard stats error:", error);
  }
  try {
    const entriesData = await api(`/api/dreamer?user=${encodeURIComponent(DREAMER_USER)}&limit=10`);
    renderRecent(entriesData.entries || []);
  } catch (error) {
    console.error("Dashboard recent error:", error);
  }
  try {
    const matrixData = await api(`/api/dreamer/matrix?user=${encodeURIComponent(DREAMER_USER)}`);
    renderMatrix(matrixData.nodes || []);
  } catch (error) {
    console.error("Dashboard matrix error:", error);
  }
  try {
    const convData = await api("/api/ternary-convergence");
    renderConvergence(convData);
  } catch (error) {
    console.error("Dashboard convergence error:", error);
  }
  await refreshTasks();
  updateLastRefreshed();
  setRefreshState(false);
}

async function mirrorAll() {
  const btn = $("mirrorBtn");
  if (!btn) return;
  btn.disabled = true;
  btn.textContent = "Mirroring...";
  try {
    const data = await api(`/api/dreamer?user=${encodeURIComponent(DREAMER_USER)}&limit=500`);
    const ids = (data.entries || []).filter((e) => e.kind !== "mirror").map((e) => e.id);
    if (ids.length === 0) {
      $("matrixMeta").textContent = "No facets to mirror yet.";
      return;
    }
    await api("/api/dreamer/mirror", {
      method: "POST",
      body: JSON.stringify({ user: DREAMER_USER, ids }),
    });
    $("matrixMeta").textContent = `Mirrored ${ids.length} facets.`;
    loadDashboard();
  } catch (error) {
    $("matrixMeta").textContent = `Mirror failed: ${error.message}`;
  } finally {
    btn.disabled = false;
    btn.textContent = "Mirror all";
  }
}

function startPolling() {
  if (pollTimer) clearInterval(pollTimer);
  pollTimer = setInterval(() => {
    if (document.visibilityState === "visible") loadDashboard();
  }, POLL_INTERVAL_MS);
}

function stopPolling() {
  if (pollTimer) { clearInterval(pollTimer); pollTimer = null; }
}

function init() {
  const btn = $("refreshBtn");
  if (btn) btn.addEventListener("click", () => loadDashboard());
  const mirrorBtn = $("mirrorBtn");
  if (mirrorBtn) mirrorBtn.addEventListener("click", () => mirrorAll());
  const taskForm = $("taskForm");
  if (taskForm) taskForm.addEventListener("submit", (event) => addTask(event).catch(() => {}));
  document.addEventListener("visibilitychange", () => {
    if (document.visibilityState === "visible") {
      loadDashboard();
      startPolling();
    } else {
      stopPolling();
    }
  });
  loadDashboard();
  startPolling();
}

init();
