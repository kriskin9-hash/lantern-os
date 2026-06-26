// Document generation (Node) — turn a chat request into a downloadable document.
// Generates content with a model (Claude — its key works here), renders Markdown → clean,
// print-styled HTML → PDF via Playwright (already a dependency). Key stays server-side. Saves
// to data/generated-docs/ and returns an /api/document/download URL. Fail-safe by contract.
//
// Formats: pdf | md | html. docx/pptx/xlsx need a generator lib (not installed) → ok:false.
const fs = require("fs");
const path = require("path");

const repoRoot = path.resolve(__dirname, "..", "..", "..");
const DOCS_DIR = path.join(repoRoot, "data", "generated-docs");
const ANTHROPIC_URL = "https://api.anthropic.com/v1/messages";

// Compact, safe Markdown → HTML (covers what the model emits: headings, lists, tables,
// bold/italic/code/links, blockquotes, code fences, hr, paragraphs). HTML is escaped.
function mdToHtml(md) {
  const esc = (s) => String(s).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
  const inline = (s) => esc(s)
    .replace(/`([^`]+)`/g, (m, c) => `<code>${c}</code>`)
    .replace(/\*\*([^*]+)\*\*/g, "<strong>$1</strong>")
    .replace(/(^|[^*])\*([^*\n]+)\*/g, "$1<em>$2</em>")
    .replace(/\[([^\]]+)\]\(([^)\s]+)\)/g, (m, t, u) => `<a href="${esc(u)}">${t}</a>`);
  const lines = String(md).replace(/\r\n/g, "\n").split("\n");
  const out = [];
  let i = 0;
  while (i < lines.length) {
    const line = lines[i];
    if (/^```/.test(line)) { // code fence
      const buf = []; i++;
      while (i < lines.length && !/^```/.test(lines[i])) buf.push(lines[i++]);
      i++; out.push(`<pre><code>${esc(buf.join("\n"))}</code></pre>`); continue;
    }
    const h = line.match(/^(#{1,6})\s+(.+)$/);
    if (h) { out.push(`<h${h[1].length}>${inline(h[2])}</h${h[1].length}>`); i++; continue; }
    if (/^(---|\*\*\*|___)\s*$/.test(line)) { out.push("<hr>"); i++; continue; }
    if (/^\|(.+)\|\s*$/.test(line) && i + 1 < lines.length && /^\|?\s*:?-+:?\s*(\|\s*:?-+:?\s*)+\|?\s*$/.test(lines[i + 1])) {
      const head = line.split("|").slice(1, -1).map((c) => `<th>${inline(c.trim())}</th>`).join("");
      i += 2; const rows = [];
      while (i < lines.length && /^\|(.+)\|\s*$/.test(lines[i])) {
        rows.push("<tr>" + lines[i].split("|").slice(1, -1).map((c) => `<td>${inline(c.trim())}</td>`).join("") + "</tr>"); i++;
      }
      out.push(`<table><thead><tr>${head}</tr></thead><tbody>${rows.join("")}</tbody></table>`); continue;
    }
    if (/^>\s?/.test(line)) {
      const buf = [];
      while (i < lines.length && /^>\s?/.test(lines[i])) buf.push(lines[i++].replace(/^>\s?/, ""));
      out.push(`<blockquote>${inline(buf.join(" "))}</blockquote>`); continue;
    }
    if (/^\s*[-*+]\s+/.test(line)) {
      const buf = [];
      while (i < lines.length && /^\s*[-*+]\s+/.test(lines[i])) buf.push(`<li>${inline(lines[i++].replace(/^\s*[-*+]\s+/, ""))}</li>`);
      out.push(`<ul>${buf.join("")}</ul>`); continue;
    }
    if (/^\s*\d+\.\s+/.test(line)) {
      const buf = [];
      while (i < lines.length && /^\s*\d+\.\s+/.test(lines[i])) buf.push(`<li>${inline(lines[i++].replace(/^\s*\d+\.\s+/, ""))}</li>`);
      out.push(`<ol>${buf.join("")}</ol>`); continue;
    }
    if (/^\s*$/.test(line)) { i++; continue; }
    const buf = [line]; i++;
    while (i < lines.length && !/^\s*$/.test(lines[i]) && !/^(#{1,6}\s|```|>\s?|\s*[-*+]\s|\s*\d+\.\s|\|)/.test(lines[i])) buf.push(lines[i++]);
    out.push(`<p>${inline(buf.join(" "))}</p>`);
  }
  return out.join("\n");
}

function htmlDoc(title, bodyHtml) {
  const t = String(title || "Document").replace(/</g, "&lt;");
  return `<!doctype html><html><head><meta charset="utf-8"><title>${t}</title><style>
  @page { margin: 2.2cm 2cm; }
  body { font: 14px/1.6 -apple-system,Segoe UI,Roboto,Helvetica,Arial,sans-serif; color:#1a1a1a; }
  h1 { font-size:26px; border-bottom:2px solid #06b6d4; padding-bottom:6px; margin-top:0; }
  h2 { font-size:20px; margin-top:1.4em; } h3 { font-size:16px; }
  table { border-collapse:collapse; width:100%; margin:1em 0; } th,td { border:1px solid #ccc; padding:6px 10px; text-align:left; vertical-align:top; }
  th { background:#f3f4f6; } code { background:#f3f4f6; padding:1px 5px; border-radius:4px; } pre { background:#f7f7f8; padding:12px; border-radius:8px; overflow:auto; }
  pre code { background:none; padding:0; } blockquote { border-left:3px solid #06b6d4; margin:1em 0; padding:.2em 1em; color:#444; }
  a { color:#0369a1; } ul,ol { padding-left:1.4em; }
</style></head><body>${bodyHtml}</body></html>`;
}

async function claudeMarkdown(prompt, title, signal) {
  const key = process.env.ANTHROPIC_API_KEY;
  if (!key) throw new Error("ANTHROPIC_API_KEY not configured");
  const system = "You are a professional document writer. Produce a complete, well-structured document in GitHub-Flavored Markdown: a top-level # title, clear ## headings, bullet/numbered lists, and Markdown tables where useful. Output ONLY the Markdown document — no preamble, no 'here is your document'.";
  const res = await fetch(ANTHROPIC_URL, {
    method: "POST",
    headers: { "Content-Type": "application/json", "x-api-key": key, "anthropic-version": "2023-06-01" },
    body: JSON.stringify({
      model: process.env.ANTHROPIC_MODEL || "claude-haiku-4-5-20251001",
      max_tokens: 4096,
      system,
      messages: [{ role: "user", content: `Write a document${title ? ` titled "${title}"` : ""}: ${prompt}` }],
    }),
    signal,
  });
  const json = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error((json && json.error && json.error.message) || `HTTP ${res.status}`);
  const text = (json.content || []).filter((b) => b.type === "text").map((b) => b.text).join("\n").trim();
  if (!text) throw new Error("empty document response");
  return text;
}

async function renderPdf(markdown, title) {
  const { chromium } = require("playwright");
  const browser = await chromium.launch();
  try {
    const page = await browser.newPage();
    await page.setContent(htmlDoc(title, mdToHtml(markdown)), { waitUntil: "load" });
    return await page.pdf({ format: "A4", printBackground: true });
  } finally {
    await browser.close();
  }
}

// generateDocument({prompt|markdown, title, format}) → { ok, url, filename, format } | { ok:false, error }.
async function generateDocument({ prompt = "", title = "", format = "pdf", markdown = "" } = {}) {
  const fmt = String(format || "pdf").toLowerCase();
  if (!["pdf", "md", "html"].includes(fmt)) {
    return { ok: false, error: `format '${fmt}' not supported yet — pdf, md, html only (docx/pptx/xlsx need a generator lib)` };
  }
  const ctrl = new AbortController();
  const to = setTimeout(() => ctrl.abort(), 90000);
  try {
    let content = markdown;
    if (!content) {
      if (!String(prompt).trim()) return { ok: false, error: "prompt or markdown required" };
      content = await claudeMarkdown(prompt, title, ctrl.signal);
    }
    const h1 = (content.match(/^#\s+(.+)$/m) || [])[1];
    const docTitle = title || h1 || "document";
    const slug = docTitle.toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "").slice(0, 60) || "document";
    if (!fs.existsSync(DOCS_DIR)) fs.mkdirSync(DOCS_DIR, { recursive: true });
    const id = `${slug}-${Date.now().toString(36)}`;
    let filename, buffer;
    if (fmt === "pdf") { filename = `${id}.pdf`; buffer = await renderPdf(content, docTitle); }
    else if (fmt === "html") { filename = `${id}.html`; buffer = Buffer.from(htmlDoc(docTitle, mdToHtml(content)), "utf8"); }
    else { filename = `${id}.md`; buffer = Buffer.from(content, "utf8"); }
    fs.writeFileSync(path.join(DOCS_DIR, filename), buffer);
    return { ok: true, url: `/api/document/download?file=${encodeURIComponent(filename)}`, filename, format: fmt, title: docTitle, bytes: buffer.length };
  } catch (e) {
    return { ok: false, error: e.name === "AbortError" ? "document generation timed out" : (e.message || String(e)) };
  } finally {
    clearTimeout(to);
  }
}

module.exports = { generateDocument, mdToHtml, DOCS_DIR };
