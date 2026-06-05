/**
 * Dream Journal Service Worker — offline-first caching + background sync
 *
 * Strategy:
 *   - App shell (HTML/CSS/JS) → cache-first, update in background
 *   - API calls → network-first, fall back to cache
 *   - Dream creates → queue in IndexedDB when offline, sync on reconnect
 */

const CACHE_NAME = "dream-journal-v1.0.0";
const APP_SHELL = [
  "/",
  "/dream-chat.html",
  "/manifest.json",
];

// ── Install: cache app shell ────────────────────────────────────────────────
self.addEventListener("install", (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => cache.addAll(APP_SHELL))
  );
  self.skipWaiting();
});

// ── Activate: clean old caches ──────────────────────────────────────────────
self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(keys.filter((k) => k !== CACHE_NAME).map((k) => caches.delete(k)))
    )
  );
  self.clients.claim();
});

// ── Fetch: cache-first for shell, network-first for API ─────────────────────
self.addEventListener("fetch", (event) => {
  const url = new URL(event.request.url);

  // API calls: network-first
  if (url.pathname.startsWith("/api/")) {
    event.respondWith(
      fetch(event.request)
        .then((res) => {
          // Cache GET API responses for offline fallback
          if (event.request.method === "GET" && res.ok) {
            const clone = res.clone();
            caches.open(CACHE_NAME).then((c) => c.put(event.request, clone));
          }
          return res;
        })
        .catch(() => caches.match(event.request))
    );
    return;
  }

  // App shell: cache-first, refresh in background
  event.respondWith(
    caches.match(event.request).then((cached) => {
      const fetched = fetch(event.request).then((res) => {
        if (res.ok) {
          const clone = res.clone();
          caches.open(CACHE_NAME).then((c) => c.put(event.request, clone));
        }
        return res;
      }).catch(() => cached);
      return cached || fetched;
    })
  );
});

// ── Background sync: flush queued dream entries ─────────────────────────────
self.addEventListener("sync", (event) => {
  if (event.tag === "dream-sync") {
    event.waitUntil(flushDreamQueue());
  }
});

async function flushDreamQueue() {
  // Open IndexedDB queue
  const db = await openDB();
  const tx = db.transaction("dream-queue", "readwrite");
  const store = tx.objectStore("dream-queue");
  const all = await getAllFromStore(store);

  for (const entry of all) {
    try {
      const res = await fetch("/api/dream/create", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(entry.data),
      });
      if (res.ok) {
        const delTx = db.transaction("dream-queue", "readwrite");
        delTx.objectStore("dream-queue").delete(entry.id);
      }
    } catch {
      break; // still offline, stop trying
    }
  }
}

function openDB() {
  return new Promise((resolve, reject) => {
    const req = indexedDB.open("dream-journal-sw", 1);
    req.onupgradeneeded = () => {
      req.result.createObjectStore("dream-queue", { keyPath: "id", autoIncrement: true });
    };
    req.onsuccess = () => resolve(req.result);
    req.onerror = () => reject(req.error);
  });
}

function getAllFromStore(store) {
  return new Promise((resolve) => {
    const req = store.getAll();
    req.onsuccess = () => resolve(req.result || []);
    req.onerror = () => resolve([]);
  });
}
