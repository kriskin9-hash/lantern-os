const $ = (id) => document.getElementById(id);
const LOCAL_APP_ORIGIN = "http://127.0.0.1:4177";
const DREAMER_USER = "courtney";

function appOrigin() {
  return window.location.protocol === "file:" ? LOCAL_APP_ORIGIN : window.location.origin;
}

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

function setStatus(message) {
  $("dreamerStatus").textContent = message;
}

function threadWord(count) {
  return `${count} ${count === 1 ? "thread" : "threads"}`;
}

function tagsFromInput(value) {
  return String(value || "")
    .split(",")
    .map((tag) => tag.trim().toLowerCase())
    .filter(Boolean)
    .slice(0, 10);
}

function linksFromInput(value) {
  return String(value || "")
    .split(",")
    .map((link) => link.trim())
    .filter(Boolean)
    .slice(0, 20);
}

function renderEntries(data) {
  const entries = data.entries || [];
  const list = $("dreamerEntries");
  list.innerHTML = "";
  $("dreamerCount").textContent = threadWord(entries.length);
  $("dreamerPath").textContent = data.path || "the well";
  if (!entries.length) {
    const item = document.createElement("li");
    item.className = "dreamer-empty";
    item.textContent = "The well is quiet. Drop something in when you're ready.";
    list.appendChild(item);
    return;
  }
  entries.slice().reverse().forEach((entry) => {
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
    const mood = document.createElement("div");
    mood.className = "dreamer-entry-mood";
    if (entry.mood) mood.textContent = `mood: ${entry.mood}`;
    const text = document.createElement("p");
    text.textContent = entry.text || "";
    const meta = document.createElement("small");
    meta.className = "dreamer-entry-meta";
    const metaParts = [];
    if (entry.ternaryId) metaParts.push(`matrix: ${entry.ternaryId}`);
    if (Array.isArray(entry.links) && entry.links.length) metaParts.push(`links: ${entry.links.join(", ")}`);
    if (Array.isArray(entry.tags) && entry.tags.length) metaParts.push(`#${entry.tags.join(" #")}`);
    if (!metaParts.length) metaParts.push("private local entry");
    meta.textContent = metaParts.join(" | ");
    item.appendChild(heading);
    if (entry.name) item.appendChild(name);
    if (entry.mood) item.appendChild(mood);
    item.appendChild(text);
    item.appendChild(meta);
    list.appendChild(item);
  });
}

async function refreshEntries(query = "") {
  const params = new URLSearchParams({ user: DREAMER_USER, limit: "100" });
  if (query) params.set("q", query);
  const data = await api(`/api/dreamer?${params.toString()}`);
  renderEntries(data);
}

async function saveEntry(event) {
  event.preventDefault();
  const text = $("dreamerText").value.trim();
  if (!text) {
    setStatus("The well waits for a thread. Write what came to you.");
    return;
  }
  const result = await api("/api/dreamer", {
    method: "POST",
    body: JSON.stringify({
      user: DREAMER_USER,
      kind: $("dreamerKind").value,
      name: $("dreamerName").value.trim() || undefined,
      mood: $("dreamerMood").value.trim() || undefined,
      text,
      tags: tagsFromInput($("dreamerTags").value),
      links: linksFromInput($("dreamerLinks").value),
      source: "courtney-web",
    }),
  });
  $("dreamerText").value = "";
  $("dreamerName").value = "";
  $("dreamerMood").value = "";
  $("dreamerLinks").value = "";
  $("dreamerTags").value = "";
  setStatus(`A ${result.record.kind} dropped in the well at ${new Date(result.record.recordedAt).toLocaleTimeString()}.`);
  await refreshEntries($("recallQuery").value.trim());
}

async function recallEntries(event) {
  event.preventDefault();
  await refreshEntries($("recallQuery").value.trim());
  setStatus("The well rippled.");
}

let notebookPollTimer = null;
const NOTEBOOK_POLL_MS = 10000;

function startNotebookPolling() {
  if (notebookPollTimer) clearInterval(notebookPollTimer);
  notebookPollTimer = setInterval(() => {
    if (document.visibilityState === "visible") {
      refreshEntries($("recallQuery").value.trim()).catch(() => {});
    }
  }, NOTEBOOK_POLL_MS);
}

function stopNotebookPolling() {
  if (notebookPollTimer) { clearInterval(notebookPollTimer); notebookPollTimer = null; }
}

function init() {
  $("dreamerForm").addEventListener("submit", (event) => saveEntry(event).catch((error) => setStatus(error.message)));
  $("recallForm").addEventListener("submit", (event) => recallEntries(event).catch((error) => setStatus(error.message)));
  document.addEventListener("visibilitychange", () => {
    if (document.visibilityState === "visible") {
      refreshEntries($("recallQuery").value.trim()).catch(() => {});
      startNotebookPolling();
    } else {
      stopNotebookPolling();
    }
  });
  refreshEntries().catch((error) => setStatus(error.message));
  startNotebookPolling();
}

init();
