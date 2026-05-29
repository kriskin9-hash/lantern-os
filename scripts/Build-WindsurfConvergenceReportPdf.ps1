param(
    [string]$Root = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path,
    [string]$Source = "reports/WINDSURF-DEVELOPER-CONVERGENCE-REPORT-2026-05-29.md",
    [string]$Output = "artifacts/WINDSURF-DEVELOPER-CONVERGENCE-REPORT-2026-05-29.pdf",
    [string]$RemoteUrl = "https://github.com/alex-place/lantern-os"
)

$ErrorActionPreference = "Stop"

Write-Host "=== Windsurf Developer Convergence Report PDF ===" -ForegroundColor Cyan
Write-Host "Generating perfect PDF from convergence report" -ForegroundColor Yellow

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
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.enums import TA_LEFT

root = Path(r"$Root")
source = root / r"$Source"
output = root / r"$Output"
remote = r"$RemoteUrl"
local = str(root)

styles = getSampleStyleSheet()
styles.add(ParagraphStyle(name="Small", parent=styles["BodyText"], fontSize=7, leading=9))
styles.add(ParagraphStyle(name="Codeish", parent=styles["BodyText"], fontName="Courier", fontSize=7, leading=9))
styles.add(ParagraphStyle(name="ReportTitle", parent=styles["Heading1"], fontSize=18, fontName="Helvetica-Bold", leading=22, spaceAfter=12))
styles.add(ParagraphStyle(name="ReportSubtitle", parent=styles["Heading2"], fontSize=14, fontName="Helvetica", leading=18, spaceAfter=8, textColor=colors.HexColor("#555555")))
styles.add(ParagraphStyle(name="ReportSection", parent=styles["Heading2"], fontSize=12, fontName="Helvetica-Bold", leading=16, spaceAfter=6, textColor=colors.HexColor("#007acc")))
styles.add(ParagraphStyle(name="Success", parent=styles["BodyText"], fontName="Helvetica-Bold", textColor=colors.green))
styles.add(ParagraphStyle(name="Error", parent=styles["BodyText"], fontName="Helvetica-Bold", textColor=colors.red))
styles["Heading1"].fontSize = 20
styles["Heading2"].fontSize = 14
styles["BodyText"].fontSize = 9
styles["BodyText"].leading = 11

def footer(canvas, doc):
    canvas.saveState()
    canvas.setFont("Helvetica", 7)
    canvas.setFillColor(colors.HexColor("#555555"))
    canvas.drawString(0.55 * inch, 0.35 * inch, f"Lantern OS local: {local}")
    canvas.drawRightString(7.95 * inch, 0.35 * inch, f"Remote: {remote} | p. {doc.page}")
    canvas.restoreState()

def para(text, style="BodyText"):
    text = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    text = text.replace("`", "")
    return Paragraph(text, styles[style])

story = []
lines = source.read_text(encoding="utf-8").splitlines()
i = 0
while i < len(lines):
    line = lines[i]
    if not line.strip():
        story.append(Spacer(1, 0.06 * inch))
        i += 1
        continue
    if line.startswith("# "):
        if line == "# Windsurf Developer Convergence Report":
            story.append(para("Windsurf Developer Convergence Report", "ReportTitle"))
        else:
            story.append(para(line[2:], "ReportSubtitle"))
        story.append(Spacer(1, 0.08 * inch))
        i += 1
        continue
    if line.startswith("## "):
        story.append(para(line[3:], "ReportSection"))
        i += 1
        continue
    if line.startswith("### "):
        story.append(Spacer(1, 0.04 * inch))
        story.append(para(line[4:], "Small"))
        i += 1
        continue
    if line.startswith("- "):
        bullet_text = line[2:]
        if "✅" in bullet_text or "❌" in bullet_text:
            bullet_text = bullet_text.replace("✅", "").replace("❌", "")
            story.append(para(bullet_text, "Small"))
        else:
            story.append(para(bullet_text, "BodyText"))
        i += 1
        continue
    if line.startswith("**") and line.endswith("**"):
        story.append(para(line[2:-2], "Success"))
        i += 1
        continue
    if line.startswith("*"):
        story.append(para(line[1:], "BodyText"))
        i += 1
        continue
    if line.startswith("```"):
        block = []
        i += 1
        while i < len(lines) and not lines[i].startswith("```"):
            block.append(lines[i])
            i += 1
        i += 1
        story.append(para("<br/>".join(block), "Codeish"))
        continue
    if line.startswith("|") and i + 1 < len(lines) and lines[i+1].startswith("|"):
        table_lines = []
        while i < len(lines) and lines[i].startswith("|"):
            table_lines.append(lines[i])
            i += 1
        rows = []
        for idx, tline in enumerate(table_lines):
            cells = [c.strip().replace("`", "") for c in tline.strip("|").split("|")]
            if idx == 1 and all(set(c) <= set("-: ") for c in cells):
                continue
            rows.append([para(c, "Small") for c in cells])
        if rows:
            col_widths = [6.5 * inch / len(rows[0])] * len(rows[0])
            tbl = Table(rows, colWidths=col_widths, repeatRows=1)
            tbl.setStyle(TableStyle([
                ("BACKGROUND", (0,0), (-1,0), colors.HexColor("#22313a")),
                ("TEXTCOLOR", (0,0), (-1,0), colors.white),
                ("GRID", (0,0), (-1,-1), 0.5, colors.HexColor("#b7c0c5")),
                ("VALIGN", (0,0), (-1,-1), "TOP"),
                ("LEFTPADDING", (0,0), (-1,-1), 3),
                ("RIGHTPADDING", (0,0), (-1,-1), 3),
            ]))
            story.append(tbl)
            story.append(Spacer(1, 0.06 * inch))
        continue
    story.append(para(line, "BodyText"))
    i += 1

doc = SimpleDocTemplate(str(output), pagesize=letter, rightMargin=0.45*inch, leftMargin=0.45*inch, topMargin=0.45*inch, bottomMargin=0.6*inch)
doc.build(story, onFirstPage=footer, onLaterPages=footer)
print(output)
"@

$temp = Join-Path $env:TEMP "windsurf-convergence-pdf.py"
$python | Set-Content -LiteralPath $temp -Encoding UTF8
python $temp

Write-Host "PDF generated successfully" -ForegroundColor Green
Write-Host "File: $outputPath" -ForegroundColor Yellow