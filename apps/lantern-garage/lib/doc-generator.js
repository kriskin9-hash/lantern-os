"use strict";
/**
 * doc-generator.js — template-based document generation for user artifacts.
 *
 * ADR-0008 §Decision 3: the "make a resume" capability. Renders structured
 * input → Markdown (default) or plain text, written to the user workspace.
 * DOCX/PDF is a future extension; Markdown is universally readable and the
 * local model can generate it without external dependencies.
 *
 * Supported templates: "resume", "cover_letter"
 * Output goes to user-workspace (never into the repo).
 */
const path = require("path");
const { workspaceWrite } = require("./user-workspace");

// ── Template renderers ────────────────────────────────────────────────────────

function _renderResume(fields) {
  const {
    name = "Your Name",
    email = "",
    phone = "",
    location = "",
    linkedin = "",
    github = "",
    summary = "",
    experience = [],   // [{title, company, dates, bullets:[]}]
    education = [],    // [{degree, institution, dates, details}]
    skills = [],       // string[] or [{category, items:[]}]
    certifications = [],
    projects = [],     // [{name, description, url}]
  } = fields;

  const lines = [];

  // Header
  lines.push(`# ${name}`);
  const contactParts = [email, phone, location, linkedin, github].filter(Boolean);
  if (contactParts.length) lines.push(contactParts.join(" · "));
  lines.push("");

  if (summary) {
    lines.push("## Summary");
    lines.push(summary);
    lines.push("");
  }

  if (experience.length) {
    lines.push("## Experience");
    for (const job of experience) {
      lines.push(`### ${job.title || "Role"} — ${job.company || "Company"}`);
      if (job.dates) lines.push(`*${job.dates}*`);
      for (const b of (job.bullets || [])) lines.push(`- ${b}`);
      lines.push("");
    }
  }

  if (education.length) {
    lines.push("## Education");
    for (const edu of education) {
      lines.push(`### ${edu.degree || "Degree"} — ${edu.institution || "Institution"}`);
      if (edu.dates) lines.push(`*${edu.dates}*`);
      if (edu.details) lines.push(edu.details);
      lines.push("");
    }
  }

  if (skills.length) {
    lines.push("## Skills");
    if (typeof skills[0] === "string") {
      lines.push(skills.join(", "));
    } else {
      for (const cat of skills) {
        lines.push(`**${cat.category}:** ${(cat.items || []).join(", ")}`);
      }
    }
    lines.push("");
  }

  if (projects.length) {
    lines.push("## Projects");
    for (const p of projects) {
      const title = p.url ? `[${p.name}](${p.url})` : (p.name || "Project");
      lines.push(`### ${title}`);
      if (p.description) lines.push(p.description);
      lines.push("");
    }
  }

  if (certifications.length) {
    lines.push("## Certifications");
    for (const c of certifications) lines.push(`- ${c}`);
    lines.push("");
  }

  return lines.join("\n");
}

function _renderCoverLetter(fields) {
  const {
    name = "Your Name",
    email = "",
    date = new Date().toLocaleDateString("en-US", { year: "numeric", month: "long", day: "numeric" }),
    hiring_manager = "Hiring Manager",
    company = "Company",
    role = "the open position",
    opening = "",
    body_paragraphs = [],  // string[]
    closing = "",
    signature = "",
  } = fields;

  const lines = [];

  lines.push(`**${name}**`);
  if (email) lines.push(email);
  lines.push(date);
  lines.push("");
  lines.push(`Dear ${hiring_manager},`);
  lines.push("");

  if (opening) {
    lines.push(opening);
  } else {
    lines.push(`I am writing to express my interest in the ${role} position at ${company}.`);
  }
  lines.push("");

  for (const para of body_paragraphs) {
    lines.push(para);
    lines.push("");
  }

  if (closing) {
    lines.push(closing);
  } else {
    lines.push(`Thank you for considering my application. I look forward to discussing how I can contribute to ${company}.`);
  }
  lines.push("");
  lines.push("Sincerely,");
  lines.push(signature || name);

  return lines.join("\n");
}

const TEMPLATES = {
  resume: { render: _renderResume, ext: ".md", desc: "Professional resume in Markdown" },
  cover_letter: { render: _renderCoverLetter, ext: ".md", desc: "Cover letter in Markdown" },
};

/**
 * Generate a document from a template and write it to the user workspace.
 *
 * @param {string} template  — "resume" | "cover_letter"
 * @param {object} fields    — template-specific field object
 * @param {string} [outputPath]  — workspace-relative path (auto-generated if omitted)
 * @returns {{ path: string, content: string, template: string }}
 */
function createDocument(template, fields, outputPath) {
  const tmpl = TEMPLATES[template];
  if (!tmpl) {
    throw new Error(`unknown template '${template}'. Available: ${Object.keys(TEMPLATES).join(", ")}`);
  }
  const content = tmpl.render(fields || {});
  const slug = (fields.name || "document").toLowerCase().replace(/[^a-z0-9]+/g, "-").slice(0, 40);
  const ts = new Date().toISOString().slice(0, 10);
  const rel = outputPath || path.join(template + "s", `${slug}-${ts}${tmpl.ext}`);
  const abs = workspaceWrite(rel, content);
  return { path: rel, fullPath: abs, content, template, byteLength: Buffer.byteLength(content) };
}

/**
 * List available templates with descriptions.
 */
function listTemplates() {
  return Object.entries(TEMPLATES).map(([name, t]) => ({ name, description: t.desc, extension: t.ext }));
}

module.exports = { createDocument, listTemplates, TEMPLATES };
