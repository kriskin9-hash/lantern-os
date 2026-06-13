const $ = (id) => document.getElementById(id);
const LOCAL_APP_ORIGIN = "http://127.0.0.1:4177";
const DREAMER_USER = "dreamer";

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
    item.className = "dream-empty";
    item.textContent = "The well is quiet. Drop something in when you're ready.";
    list.appendChild(item);
    return;
  }
  entries.slice().reverse().forEach((entry) => {
    const item = document.createElement("li");
    item.className = `dream-entry ${entry.kind || "note"}`;

    const header = document.createElement("div");
    header.className = "entry-header";
    const kind = document.createElement("span");
    kind.className = "entry-kind";
    kind.textContent = String(entry.kind || "note").toUpperCase();
    const time = document.createElement("span");
    time.className = "entry-time";
    time.textContent = entry.recordedAt ? new Date(entry.recordedAt).toLocaleString() : "local time unknown";
    header.appendChild(kind);
    header.appendChild(time);
    item.appendChild(header);

    if (entry.name) {
      const name = document.createElement("div");
      name.className = "entry-name";
      name.textContent = entry.name;
      item.appendChild(name);
    }

    if (entry.mood) {
      const mood = document.createElement("div");
      mood.className = "entry-mood";
      mood.textContent = `mood: ${entry.mood}`;
      item.appendChild(mood);
    }

    const text = document.createElement("p");
    text.className = "entry-text";
    text.textContent = entry.text || "";
    item.appendChild(text);

    if (entry.tags && entry.tags.length) {
      const tagLine = document.createElement("div");
      tagLine.className = "entry-tags";
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
