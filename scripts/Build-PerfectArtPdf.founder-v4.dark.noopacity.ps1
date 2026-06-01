param(
    [string]$Root = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path,
    [string]$Source,
    [string]$Output,
    [string]$RemoteUrl = "https://github.com/alex-place/lantern-os",
    [string]$ArtDir = "skills/lantern-rag-dollhouse/assets/images/comet-leap-30day",
    [string]$ChartDir = "skills/lantern-rag-dollhouse/assets/images/charts",
    [string]$MetricsPath = "data/wallet/local-cash-wallet.json",
    [string]$ArcPath = "data/arc-reactor/status.json",
    [string]$LedgerPath = "data/wallet/ledger.jsonl"
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
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib.utils import ImageReader
import math

root = Path(r"$Root")
source = root / r"$Source"
output = root / r"$Output"
remote = r"$RemoteUrl"
art_dir = root / r"$ArtDir"
chart_dir = root / r"$ChartDir"
metrics_path = root / r"$MetricsPath"
arc_path = root / r"$ArcPath"
ledger_path = root / r"$LedgerPath"

art_paths = sorted([p for p in art_dir.glob("*.png") if p.is_file()])
chart_paths = sorted([p for p in chart_dir.glob("*.png") if p.is_file()])
visual_paths = chart_paths + art_paths
wallet_cleared = 0
wallet_pending = 0
ledger_events = 0
movie1 = 80
movie2 = 50
movie3 = 20
try:
    import json
    if metrics_path.exists():
        w = json.loads(metrics_path.read_text(encoding="utf-8"))
        wallet_cleared = int(w.get("clearedCashUsd", 0) or 0)
        wallet_pending = int(w.get("pendingInvoiceUsd", 0) or 0)
    if arc_path.exists():
        a = json.loads(arc_path.read_text(encoding="utf-8"))
        movie1 = int(a.get("movie1GarageConfidence", 80) or 80)
        movie2 = int(a.get("movie2PublicPlatformConfidence", 50) or 50)
        movie3 = int(a.get("movie3DistributedFleetConfidence", 20) or 20)
    if ledger_path.exists():
        ledger_events = len([ln for ln in ledger_path.read_text(encoding="utf-8").splitlines() if ln.strip()])
except Exception:
    pass

styles = getSampleStyleSheet()
styles.add(ParagraphStyle(name="Small", parent=styles["BodyText"], fontSize=9.4, leading=12.4))
styles.add(ParagraphStyle(name="Codeish", parent=styles["BodyText"], fontName="Courier", fontSize=9.0, leading=12.0))
styles.add(ParagraphStyle(name="Callout", parent=styles["BodyText"], fontSize=11.2, leading=14.5, textColor=colors.HexColor("#eaf2ff")))
styles["Title"].fontName = "Helvetica-Bold"
styles["Title"].fontSize = 24
styles["Title"].leading = 28
styles["Heading1"].fontName = "Helvetica-Bold"
styles["Heading1"].fontSize = 17
styles["Heading1"].leading = 21
styles["Heading2"].fontName = "Helvetica-Bold"
styles["Heading2"].fontSize = 13
styles["Heading2"].leading = 17
styles["BodyText"].fontName = "Helvetica"
styles["BodyText"].fontSize = 11
styles["BodyText"].leading = 14.5
styles["BodyText"].textColor = colors.HexColor("#f3f7ff")
styles["Heading1"].textColor = colors.HexColor("#ffffff")
styles["Heading2"].textColor = colors.HexColor("#eef5ff")
styles["Title"].textColor = colors.HexColor("#ffffff")

def safe(text):
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace("`", "")

def para(text, style="BodyText"):
    return Paragraph(safe(text), styles[style])

def draw_image_cover(canvas, image_path, x, y, w, h):
    try:
        img = ImageReader(str(image_path))
        iw, ih = img.getSize()
        scale = max(w / iw, h / ih)
        sw, sh = iw * scale, ih * scale
        canvas.drawImage(img, x + (w - sw) / 2, y + (h - sh) / 2, sw, sh, mask="auto")
    except Exception:
        return

def draw_page_art(canvas, doc):
    width, height = letter
    canvas.saveState()
    canvas.setFillColor(colors.HexColor("#05080f"))
    canvas.rect(0, 0, width, height, fill=1, stroke=0)

    if visual_paths:
        art = visual_paths[(doc.page - 1) % len(visual_paths)]
        if hasattr(canvas, "setFillAlpha"):
            canvas.setFillAlpha(1)
        draw_image_cover(canvas, art, 0, 0, width, height)
        if hasattr(canvas, "setFillAlpha"):
            canvas.setFillAlpha(1)

        canvas.setStrokeColor(colors.HexColor("#4f6782"))
        canvas.setLineWidth(0.6)
        canvas.roundRect(6.38 * inch, 0.48 * inch, 1.05 * inch, 1.05 * inch, 8, fill=0, stroke=1)
        draw_image_cover(canvas, art, 6.38 * inch, 0.48 * inch, 1.05 * inch, 1.05 * inch)

    # Tesseract dot-line overlay: compressed symbolic lane kept decorative/readable-safe.
    if hasattr(canvas, "setStrokeAlpha"):
        canvas.setStrokeAlpha(1)
    if hasattr(canvas, "setFillAlpha"):
        canvas.setFillAlpha(1)
    canvas.setStrokeColor(colors.HexColor("#6e8fb1"))
    canvas.setFillColor(colors.HexColor("#6e8fb1"))
    cx, cy = width * 0.5, height * 0.52
    layers = [
        200 + min(movie1, 40),
        140 + min(movie2, 35),
        95 + min(movie3, 25),
        70 + min(ledger_events * 2, 30)
    ]
    points = []
    for ridx, r in enumerate(layers):
        ring = []
        for i in range(12):
            a = (math.pi * 2 * i / 12.0) + (ridx * 0.19)
            x = cx + math.cos(a) * r
            y = cy + math.sin(a) * r
            ring.append((x, y))
            dot = 1.1 + ((wallet_pending % 9) / 15.0)
            canvas.circle(x, y, dot if ridx < 2 else (dot - 0.2), stroke=0, fill=1)
        points.append(ring)
    canvas.setLineWidth(0.35)
    for ring in points:
        for i in range(len(ring)):
            x1, y1 = ring[i]
            x2, y2 = ring[(i + 1) % len(ring)]
            canvas.line(x1, y1, x2, y2)
    for i in range(12):
        for ridx in range(len(points) - 1):
            x1, y1 = points[ridx][i]
            x2, y2 = points[ridx + 1][(i + 2) % 12]
            canvas.line(x1, y1, x2, y2)
    if hasattr(canvas, "setStrokeAlpha"):
        canvas.setStrokeAlpha(1)
    if hasattr(canvas, "setFillAlpha"):
        canvas.setFillAlpha(1)

    canvas.setFillColor(colors.HexColor("#0f1a2b"))
    if hasattr(canvas, "setFillAlpha"):
        canvas.setFillAlpha(1)
    canvas.roundRect(0.38 * inch, 0.42 * inch, 7.74 * inch, 10.12 * inch, 8, fill=1, stroke=0)
    if hasattr(canvas, "setFillAlpha"):
        canvas.setFillAlpha(1)

    canvas.setStrokeColor(colors.HexColor("#7cc7ff"))
    canvas.setLineWidth(1.3)
    canvas.line(0.55 * inch, 10.33 * inch, 7.95 * inch, 10.33 * inch)
    canvas.setFont("Helvetica-Bold", 7.5)
    canvas.setFillColor(colors.HexColor("#e6f1ff"))
    canvas.drawString(0.55 * inch, 10.43 * inch, "Lantern OS / COMET LEAP / !perfect art edition")
    canvas.setFont("Helvetica", 7)
    canvas.setFillColor(colors.HexColor("#c8dcf4"))
    canvas.drawString(0.55 * inch, 0.30 * inch, f"Local: {root}")
    canvas.drawRightString(7.95 * inch, 0.30 * inch, f"Remote: {remote} | p. {doc.page}")
    canvas.restoreState()

story = []
lines = source.read_text(encoding="utf-8").splitlines()
i = 0
while i < len(lines):
    line = lines[i]
    if not line.strip():
        story.append(Spacer(1, 0.055 * inch))
        i += 1
        continue
    if line.strip().lower() in ("<!-- pagebreak -->", "<!-- page break -->", "\\pagebreak"):
        story.append(PageBreak())
        i += 1
        continue
    if line.startswith("# "):
        story.append(Paragraph(safe(line[2:]), styles["Title"]))
        story.append(Spacer(1, 0.12 * inch))
        i += 1
        continue
    if line.startswith("## "):
        story.append(Spacer(1, 0.08 * inch))
        story.append(Paragraph(safe(line[3:]), styles["Heading1"]))
        i += 1
        continue
    if line.startswith("### "):
        story.append(Spacer(1, 0.05 * inch))
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
            widths = [7.05 * inch / len(rows[0])] * len(rows[0])
            tbl = Table(rows, colWidths=widths, repeatRows=1)
            tbl.setStyle(TableStyle([
                ("BACKGROUND", (0,0), (-1,0), colors.HexColor("#1c3f63")),
                ("TEXTCOLOR", (0,0), (-1,0), colors.HexColor("#ffffff")),
                ("BACKGROUND", (0,1), (-1,-1), colors.HexColor("#13263d")),
                ("ROWBACKGROUNDS", (0,1), (-1,-1), [colors.HexColor("#13263d"), colors.HexColor("#17314d")]),
                ("GRID", (0,0), (-1,-1), 0.35, colors.HexColor("#6aa9d8")),
                ("TEXTCOLOR", (0,1), (-1,-1), colors.HexColor("#ffffff")),
                ("VALIGN", (0,0), (-1,-1), "TOP"),
                ("LEFTPADDING", (0,0), (-1,-1), 3),
                ("RIGHTPADDING", (0,0), (-1,-1), 3),
                ("TOPPADDING", (0,0), (-1,-1), 3),
                ("BOTTOMPADDING", (0,0), (-1,-1), 3),
            ]))
            story.append(tbl)
            story.append(Spacer(1, 0.08 * inch))
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
    story.append(para(line, "BodyText"))
    i += 1

doc = SimpleDocTemplate(
    str(output),
    pagesize=letter,
    rightMargin=0.58 * inch,
    leftMargin=0.58 * inch,
    topMargin=0.72 * inch,
    bottomMargin=0.72 * inch,
)
doc.build(story, onFirstPage=draw_page_art, onLaterPages=draw_page_art)
print(output)
"@

$temp = Join-Path $env:TEMP ("build-lantern-perfect-art-pdf-{0}-{1}.py" -f $PID, ([guid]::NewGuid().ToString("N")))
$python | Set-Content -LiteralPath $temp -Encoding UTF8
try {
    python $temp
}
finally {
    Remove-Item -LiteralPath $temp -Force -ErrorAction SilentlyContinue
}

