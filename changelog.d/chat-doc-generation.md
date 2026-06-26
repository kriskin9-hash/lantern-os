### Dream-chat: generate downloadable documents (#1203)

- Ask the chat "make me a PDF/report/brief about X" (or `!pdf <prompt>`) and it now writes the document and returns a **downloadable PDF**. New server path: `lib/document-builder.js` + `POST /api/document/generate` — the model (Claude) writes the content as Markdown, which is rendered to a clean, print-styled PDF via Playwright (already a dependency) and served from `/api/document/download`. Formats: pdf / md / html (docx/pptx/xlsx need a generator lib — tracked separately).
