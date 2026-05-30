param(
    [string]$Root = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path,
    [string]$Source,
    [string]$Output,
    [string]$Title = "Lantern OS Report"
)

$ErrorActionPreference = "Stop"

if (-not $Source) { throw "Source is required." }
if (-not $Output) { throw "Output is required." }

$sourcePath = Join-Path $Root $Source
$outputPath = Join-Path $Root $Output
$outputDir = Split-Path -Parent $outputPath
New-Item -ItemType Directory -Force -Path $outputDir | Out-Null

$python = @"
from pathlib import Path
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak

root = Path(r"$Root")
source = root / r"$Source"
output = root / r"$Output"
title = r"$Title"

styles = getSampleStyleSheet()
styles.add(ParagraphStyle(name="Small", parent=styles["BodyText"], fontSize=8, leading=10))
styles.add(ParagraphStyle(name="Callout", parent=styles["BodyText"], fontSize=9, leading=12, textColor=colors.HexColor("#35506b")))
styles["Title"].fontName = "Helvetica-Bold"
styles["Title"].fontSize = 18
styles["Title"].leading = 22
styles["Heading1"].fontName = "Helvetica-Bold"
styles["Heading1"].fontSize = 13
styles["Heading1"].leading = 16
styles["Heading2"].fontName = "Helvetica-Bold"
styles["Heading2"].fontSize = 10
styles["Heading2"].leading = 13
styles["BodyText"].fontName = "Helvetica"
styles["BodyText"].fontSize = 9
styles["BodyText"].leading = 12

def safe(text):
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace("`", "")

def para(text, style="BodyText"):
    return Paragraph(safe(text), styles[style])

def draw_page_header(canvas, doc):
    width, height = letter
    canvas.saveState()
    canvas.setFillColor(colors.HexColor("#f5f5f5"))
    canvas.rect(0, height - 0.75 * inch, width, 0.75 * inch, fill=1, stroke=0)
    canvas.setFillColor(colors.HexColor("#333333"))
    canvas.setFont("Helvetica-Bold", 10)
    canvas.drawString(0.5 * inch, height - 0.55 * inch, title)
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(colors.HexColor("#666666"))
    canvas.drawRightString(width - 0.5 * inch, height - 0.55 * inch, f"Page {doc.page}")
    canvas.restoreState()

def draw_page_footer(canvas, doc):
    width, height = letter
    canvas.saveState()
    canvas.setFillColor(colors.HexColor("#f5f5f5"))
    canvas.rect(0, 0, width, 0.5 * inch, fill=1, stroke=0)
    canvas.setFillColor(colors.HexColor("#666666"))
    canvas.setFont("Helvetica", 7)
    canvas.drawString(0.5 * inch, 0.35 * inch, f"Lantern OS Report")
    canvas.drawRightString(width - 0.5 * inch, 0.35 * inch, f"Generated: {doc.page}")
    canvas.restoreState()

story = []
lines = source.read_text(encoding="utf-8").splitlines()
i = 0
while i < len(lines):
    line = lines[i]
    if not line.strip():
        story.append(Spacer(1, 0.05 * inch))
        i += 1
        continue
    if line.strip().lower() in ("<!-- pagebreak -->", "<!-- page break -->", "\\pagebreak"):
        story.append(PageBreak())
        i += 1
        continue
    if line.startswith("# "):
        story.append(Paragraph(safe(line[2:]), styles["Title"]))
        story.append(Spacer(1, 0.1 * inch))
        i += 1
        continue
    if line.startswith("## "):
        story.append(Spacer(1, 0.06 * inch))
        story.append(Paragraph(safe(line[3:]), styles["Heading1"]))
        i += 1
        continue
    if line.startswith("### "):
        story.append(Spacer(1, 0.04 * inch))
        story.append(Paragraph(safe(line[4:]), styles["Heading2"]))
        i += 1
        continue
    if line.startswith("|") and i + 1 < len(lines) and lines[i+1].startswith("|"):
        table_lines = []
        while i < len(lines) and lines[i].startswith("|"):
            table_lines.append(lines[i])
            i += 1
        rows = []
        for idx, tline in enumerate(table_lines):
            cells = [c.strip() for c in tline.strip("|").split("|")]
            if idx == 1 and all(set(c) <= set("-: ") for c in cells):
                continue
            rows.append([para(c, "Small") for c in cells])
        if rows:
            widths = [6.5 * inch / len(rows[0])] * len(rows[0])
            tbl = Table(rows, colWidths=widths, repeatRows=1)
            tbl.setStyle(TableStyle([
                ("BACKGROUND", (0,0), (-1,0), colors.HexColor("#e8e8e8")),
                ("TEXTCOLOR", (0,0), (-1,0), colors.HexColor("#333333")),
                ("GRID", (0,0), (-1,-1), 0.5, colors.HexColor("#cccccc")),
                ("VALIGN", (0,0), (-1,-1), "TOP"),
                ("LEFTPADDING", (0,0), (-1,-1), 4),
                ("RIGHTPADDING", (0,0), (-1,-1), 4),
                ("TOPPADDING", (0,0), (-1,-1), 4),
                ("BOTTOMPADDING", (0,0), (-1,-1), 4),
            ]))
            story.append(tbl)
            story.append(Spacer(1, 0.06 * inch))
        continue
    if line.startswith("```"):
        block = []
        i += 1
        while i < len(lines) and not lines[i].startswith("```"):
            block.append(lines[i])
            i += 1
        i += 1
        story.append(para("<br/>".join(block), "Small"))
        continue
    if line.startswith("- "):
        story.append(para("• " + safe(line[2:]), "BodyText"))
        i += 1
        continue
    story.append(para(line, "BodyText"))
    i += 1

doc = SimpleDocTemplate(
    str(output),
    pagesize=letter,
    rightMargin=0.5 * inch,
    leftMargin=0.5 * inch,
    topMargin=0.85 * inch,
    bottomMargin=0.6 * inch,
)
doc.build(story, onFirstPage=draw_page_header, onLaterPages=draw_page_header)
print(output)
"@

$temp = Join-Path $env:TEMP ("build-simple-report-pdf-{0}-{1}.py" -f $PID, ([guid]::NewGuid().ToString("N")))
$python | Set-Content -LiteralPath $temp -Encoding UTF8
try {
    python $temp
}
finally {
    Remove-Item -LiteralPath $temp -Force -ErrorAction SilentlyContinue
}
