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
import re
from pathlib import Path
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT, TA_CENTER
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, HRFlowable

root   = Path(r"$Root")
source = root / r"$Source"
output = root / r"$Output"
title  = r"$Title"

# --- Orion brand tokens ---
PAPER       = colors.HexColor("#f7f8f4")
INK         = colors.HexColor("#0d1b26")
MUTED       = colors.HexColor("#526676")
BLUE_LINE   = colors.HexColor("#9fb9c9")
BLUE_DEEP   = colors.HexColor("#15384f")
TEAL        = colors.HexColor("#0e9f9b")
CYAN        = colors.HexColor("#72e8e1")
AMBER       = colors.HexColor("#b98228")
AMBER_BG    = colors.HexColor("#fdf6e3")
PANEL_BG    = colors.HexColor("#ffffff")
GRID_LINE   = colors.HexColor("#dde8ec")

styles = getSampleStyleSheet()

styles.add(ParagraphStyle(
    name="OrionTitle", parent=styles["Normal"],
    fontName="Helvetica-Bold", fontSize=22, leading=27,
    textColor=INK, spaceBefore=0, spaceAfter=4))
styles.add(ParagraphStyle(
    name="OrionEyebrow", parent=styles["Normal"],
    fontName="Helvetica-Bold", fontSize=7.5, leading=10,
    textColor=TEAL, spaceAfter=2, spaceBefore=0,
    wordWrap="LTR"))
styles.add(ParagraphStyle(
    name="OrionH1", parent=styles["Normal"],
    fontName="Helvetica-Bold", fontSize=12, leading=15,
    textColor=BLUE_DEEP, spaceBefore=10, spaceAfter=3))
styles.add(ParagraphStyle(
    name="OrionH2", parent=styles["Normal"],
    fontName="Helvetica-Bold", fontSize=9.5, leading=12,
    textColor=INK, spaceBefore=6, spaceAfter=2))
styles.add(ParagraphStyle(
    name="OrionBody", parent=styles["Normal"],
    fontName="Helvetica", fontSize=8.8, leading=12,
    textColor=INK, spaceBefore=1, spaceAfter=1))
styles.add(ParagraphStyle(
    name="OrionMuted", parent=styles["Normal"],
    fontName="Helvetica", fontSize=8, leading=11,
    textColor=MUTED, spaceBefore=1, spaceAfter=1))
styles.add(ParagraphStyle(
    name="OrionBullet", parent=styles["Normal"],
    fontName="Helvetica", fontSize=8.8, leading=12,
    textColor=INK, leftIndent=10, firstLineIndent=0,
    spaceBefore=1, spaceAfter=1))
styles.add(ParagraphStyle(
    name="OrionCode", parent=styles["Normal"],
    fontName="Courier", fontSize=7.5, leading=10,
    textColor=BLUE_DEEP, backColor=colors.HexColor("#eef3f6"),
    spaceBefore=2, spaceAfter=2, leftIndent=6))
styles.add(ParagraphStyle(
    name="OrionAmber", parent=styles["Normal"],
    fontName="Helvetica-Oblique", fontSize=8, leading=11,
    textColor=AMBER, spaceBefore=1, spaceAfter=1))
styles.add(ParagraphStyle(
    name="OrionSmall", parent=styles["Normal"],
    fontName="Helvetica", fontSize=7.5, leading=9.5, textColor=INK))

def safe(text):
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

_bt = chr(96)
_code_pat = _bt + r'([^' + _bt + r']+)' + _bt

def md(text):
    text = safe(text)
    text = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', text)
    text = re.sub(r'__(.+?)__',     r'<b>\1</b>', text)
    text = re.sub(r'\*([^*]+?)\*',  r'<i>\1</i>', text)
    text = re.sub(_code_pat, lambda m: '<font name="Courier" size="7.5" color="#15384f">' + m.group(1) + '</font>', text)
    return text

def para(text, style="OrionBody"):
    return Paragraph(md(text), styles[style])

def divider():
    return HRFlowable(width="100%", thickness=0.5, color=BLUE_LINE, spaceAfter=4, spaceBefore=2)

def section_label(text):
    return Paragraph(text.upper(), styles["OrionEyebrow"])

def draw_page(canvas, doc):
    width, height = letter
    canvas.saveState()

    # Header bar — teal left stripe + limestone band
    canvas.setFillColor(TEAL)
    canvas.rect(0, height - 0.62*inch, 4, 0.62*inch, fill=1, stroke=0)
    canvas.setFillColor(colors.HexColor("#eef3f6"))
    canvas.rect(4, height - 0.62*inch, width - 4, 0.62*inch, fill=1, stroke=0)

    # Header text
    canvas.setFillColor(BLUE_DEEP)
    canvas.setFont("Helvetica-Bold", 9)
    canvas.drawString(0.35*inch, height - 0.38*inch, title)
    canvas.setFont("Helvetica", 7.5)
    canvas.setFillColor(MUTED)
    canvas.drawRightString(width - 0.35*inch, height - 0.38*inch, f"Page {doc.page}")

    # Subtle grid lines (horizontal only, every 0.5in in body area)
    canvas.setStrokeColor(GRID_LINE)
    canvas.setLineWidth(0.3)
    y = height - 0.62*inch - 0.5*inch
    while y > 0.5*inch:
        canvas.line(0.35*inch, y, width - 0.35*inch, y)
        y -= 0.5*inch

    # Footer bar
    canvas.setFillColor(colors.HexColor("#eef3f6"))
    canvas.rect(0, 0, width, 0.42*inch, fill=1, stroke=0)
    canvas.setFillColor(TEAL)
    canvas.rect(0, 0, 4, 0.42*inch, fill=1, stroke=0)
    canvas.setFont("Helvetica", 7)
    canvas.setFillColor(MUTED)
    canvas.drawString(0.35*inch, 0.15*inch, "Lantern OS  \u2022  lantern-os.local")
    from datetime import date
    canvas.drawRightString(width - 0.35*inch, 0.15*inch, f"Generated {date.today().isoformat()}")

    canvas.restoreState()

story = []
lines = source.read_text(encoding="utf-8").splitlines()

# Detect DRAFT/APPROVED status for amber banner
full_text = source.read_text(encoding="utf-8")
status_match = re.search(r'\*\*Status:\*\*\s*(.+)', full_text)
status_text = status_match.group(1).strip() if status_match else ""
is_draft = "draft" in status_text.lower() or "requires operator" in status_text.lower()

i = 0
while i < len(lines):
    line = lines[i]

    if not line.strip():
        story.append(Spacer(1, 0.04*inch))
        i += 1
        continue

    if line.strip() in ("---", "***", "___"):
        story.append(divider())
        i += 1
        continue

    if line.strip().lower() in ("<!-- pagebreak -->", "<!-- page break -->"):
        story.append(PageBreak())
        i += 1
        continue

    if line.startswith("# "):
        story.append(Spacer(1, 0.06*inch))
        story.append(para(line[2:], "OrionTitle"))
        if is_draft:
            story.append(Spacer(1, 0.04*inch))
            story.append(para("\u26a0  DRAFT \u2014 Requires operator review before submission", "OrionAmber"))
        story.append(Spacer(1, 0.06*inch))
        i += 1
        continue

    if line.startswith("## "):
        story.append(Spacer(1, 0.05*inch))
        label = line[3:]
        story.append(section_label(label))
        story.append(HRFlowable(width="100%", thickness=1, color=TEAL, spaceAfter=3, spaceBefore=1))
        i += 1
        continue

    if line.startswith("### "):
        story.append(para(line[4:], "OrionH2"))
        i += 1
        continue

    # Table
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
            rows.append([para(c, "OrionSmall") for c in cells])
        if rows:
            ncols = len(rows[0])
            widths = [6.5*inch / ncols] * ncols
            tbl = Table(rows, colWidths=widths, repeatRows=1)
            tbl.setStyle(TableStyle([
                ("BACKGROUND",   (0,0), (-1,0),  colors.HexColor("#d8eaef")),
                ("TEXTCOLOR",    (0,0), (-1,0),  BLUE_DEEP),
                ("FONTNAME",     (0,0), (-1,0),  "Helvetica-Bold"),
                ("FONTSIZE",     (0,0), (-1,0),  8),
                ("ROWBACKGROUNDS",(0,1),(-1,-1), [PANEL_BG, colors.HexColor("#f4f8f9")]),
                ("GRID",         (0,0), (-1,-1), 0.4, GRID_LINE),
                ("VALIGN",       (0,0), (-1,-1), "TOP"),
                ("LEFTPADDING",  (0,0), (-1,-1), 5),
                ("RIGHTPADDING", (0,0), (-1,-1), 5),
                ("TOPPADDING",   (0,0), (-1,-1), 4),
                ("BOTTOMPADDING",(0,0), (-1,-1), 4),
            ]))
            story.append(tbl)
            story.append(Spacer(1, 0.06*inch))
        continue

    # Code block
    if line.startswith("```"):
        block = []
        i += 1
        while i < len(lines) and not lines[i].startswith("```"):
            block.append(safe(lines[i]))
            i += 1
        i += 1
        code_text = "<br/>".join(block) if block else " "
        story.append(Paragraph(code_text, styles["OrionCode"]))
        story.append(Spacer(1, 0.03*inch))
        continue

    # Bullets: - or * or numbered  1.
    if re.match(r'^[-*]\s', line):
        story.append(para("\u2022\u2002" + line[2:], "OrionBullet"))
        i += 1
        continue

    if re.match(r'^\d+\.\s', line):
        num_match = re.match(r'^(\d+)\.\s+(.*)', line)
        if num_match:
            story.append(para(f"<b>{num_match.group(1)}.</b>\u2002{num_match.group(2)}", "OrionBullet"))
        i += 1
        continue

    # Metadata / muted lines (key: value pattern at top)
    if re.match(r'^\*\*[A-Za-z ]+:\*\*', line) and len(story) < 10:
        story.append(para(line, "OrionMuted"))
        i += 1
        continue

    story.append(para(line, "OrionBody"))
    i += 1

doc = SimpleDocTemplate(
    str(output),
    pagesize=letter,
    rightMargin=0.45*inch,
    leftMargin=0.45*inch,
    topMargin=0.78*inch,
    bottomMargin=0.58*inch,
)
doc.build(story, onFirstPage=draw_page, onLaterPages=draw_page)
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
