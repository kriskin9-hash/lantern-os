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
    item.appendChild(heading);
    if (entry.name) item.appendChild(name);
    if (entry.mood) item.appendChild(mood);
    item.appendChild(text);
    if (entry.tags && entry.tags.length) {
      const tagLine = document.createElement("div");
      tagLine.className = "dreamer-entry-tags";
      tagLine.textContent = entry.tags.join(" · ");
      item.appendChild(tagLine);
    }
    list.appendChild(item);
  });
}

async function loadEntries() {
  try {
    const data = await api(`/api/dreamer?user=${encodeURIComponent(DREAMER_USER)}`);
    renderEntries(data);
  } catch (error) {
    setStatus(`Could not reach the well: ${error.message}`);
  }
}

async function saveEntry(event) {
  event.preventDefault();
  const text = $("dreamerText").value.trim();
  if (!text) {
    setStatus("Write something before dropping it in.");
    return;
  }
  const body = {
    user: DREAMER_USER,
    kind: $("dreamerKind").value,
    name: $("dreamerName").value.trim(),
    mood: $("dreamerMood").value.trim(),
    text,
    tags: tagsFromInput($("dreamerTags").value),
  };
  try {
    setStatus("Dropping into the well...");
    await api("/api/dreamer", { method: "POST", body: JSON.stringify(body) });
    $("dreamerForm").reset();
    setStatus("Saved to your private local notebook.");
    await loadEntries();
  } catch (error) {
    setStatus(`Save failed: ${error.message}`);
  }
}

function init() {
  $("dreamerForm").addEventListener("submit", saveEntry);
  loadEntries();
}

if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", init);
} else {
  init();
}
