# Dream Journal v1.0.0

**Release date:** 2026-06-05
**Tag:** `v1.0.0`

---

## What is Dream Journal?

Dream Journal is a local-first, private journaling app for capturing and exploring your dreams. Everything runs on your machine. Nothing is uploaded to a cloud. Your entries live in your browser's local storage and in plain JSONL files you control — no account required, no subscription gate on the core experience.

---

## What's new in v1.0.0

### Voice capture

Tap the mic button (`micBtn`) to speak a dream directly into the entry field using the browser's built-in speech recognition. No third-party transcription service is involved. If the browser does not support the API, the button hides itself gracefully.

### Interactive search

A search bar filters your entries by text or tag in real time. Results appear inline without a page reload. Clear the search with the ✕ button to return to the full timeline.

### Export: CSV and JSONL

Two export buttons are available from the dashboard:

- **Export JSONL** — one JSON object per line, append-only format, readable by any text editor or script.
- **Export CSV** — spreadsheet-compatible, useful for analysis in Excel, Numbers, or Python.

Both exports are generated locally and downloaded directly to your machine.

### 8 entry types

Every entry is tagged with a kind, selectable from a dropdown in the header or inline in the input bar:

| Kind | Use for |
|---|---|
| **Dream** | An actual dream you had |
| **Note** | A waking reflection or insight |
| **Place** | A recurring location from your dreams |
| **Character** | A person or being who appears in your dreams |
| **Event** | A significant dream sequence or narrative arc |
| **Lore** | Consistent rules, worlds, or mythologies your dreams build |
| **Symbol** | A recurring image — track how its meaning evolves |
| **Mirror** | A synthesis entry connecting multiple dreams or notes |

### Local, privacy-first architecture

- Data is stored in `localStorage` and in server-side JSONL files under `data/dreams/`.
- No analytics, no telemetry, no cloud sync by default.
- The Node.js server runs entirely on `127.0.0.1`. Nothing is bound to an external interface unless you explicitly deploy to a cloud host.

### Runs from repo root with a single command

```bash
npm start
# or equivalently:
npm start --prefix apps/lantern-garage
```

No separate install step is needed beyond `node_modules` already in the repo. The server starts in 2–3 seconds.

---

## How to get it

```bash
git pull origin master
npm start --prefix apps/lantern-garage
```

Then open **http://127.0.0.1:4177** in your browser.

Node.js v20 or higher is required. No database, no Docker, no environment variables needed for local use.

---

## What's coming in v1.0.1

The 3 Door Game — an interactive symbolic gameplay layer built on top of the journal. The design document ships with v1.0.0; the full interactive experience follows in v1.0.1.

---

Thank you for being here at the beginning. Every dream you capture is yours, stored on your machine, waiting to tell you something.
