param(
    [string]$Root = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path,
    [string]$Source = "reports/LANTERN-DAY-ONE-NORMIE-PACKET.md",
    [string]$Output = "artifacts/LANTERN-DAY-ONE-NORMIE-PACKET.pdf",
    [string]$ArtDir = "reports/assets/day-one-normie",
    [string]$RemoteUrl = "https://github.com/alex-place/lantern-os"
)

$ErrorActionPreference = "Stop"

$outputPath = Join-Path $Root $Output
New-Item -ItemType Directory -Force -Path (Split-Path -Parent $outputPath) | Out-Null

$python = @"
from pathlib import Path
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas
from reportlab.platypus import Paragraph
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER
import re

root = Path(r"$Root")
source = root / r"$Source"
output = root / r"$Output"
art_dir = root / r"$ArtDir"
remote = r"$RemoteUrl"

W, H = letter
M = 0.48 * inch

styles = {
    "title": ParagraphStyle("title", fontName="Helvetica-Bold", fontSize=30, leading=34, textColor=colors.HexColor("#18272c"), alignment=TA_LEFT),
    "subtitle": ParagraphStyle("subtitle", fontName="Helvetica-Bold", fontSize=15, leading=20, textColor=colors.HexColor("#24383d"), alignment=TA_LEFT),
    "h1": ParagraphStyle("h1", fontName="Helvetica-Bold", fontSize=18, leading=22, textColor=colors.HexColor("#1d3035")),
    "h2": ParagraphStyle("h2", fontName="Helvetica-Bold", fontSize=13, leading=16, textColor=colors.HexColor("#1d3035")),
    "body": ParagraphStyle("body", fontName="Helvetica", fontSize=9.5, leading=13, textColor=colors.HexColor("#233238")),
    "small": ParagraphStyle("small", fontName="Helvetica", fontSize=8, leading=10.5, textColor=colors.HexColor("#36474d")),
    "label": ParagraphStyle("label", fontName="Helvetica-Bold", fontSize=8.3, leading=10.5, textColor=colors.HexColor("#1d3035")),
    "center": ParagraphStyle("center", fontName="Helvetica-Bold", fontSize=13, leading=17, textColor=colors.HexColor("#1d3035"), alignment=TA_CENTER),
}

art = {
    "cover": art_dir / "cover.png",
    "memory": art_dir / "memory-rag.png",
    "learning": art_dir / "learning-packet.png",
    "pro": art_dir / "pro-cleanup.png",
    "token": art_dir / "token-time.png",
    "wins": art_dir / "practical-wins.png",
}

def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace("`", "")

def p(c, text, style, x, y, w, h):
    para = Paragraph(esc(text), styles[style])
    _, used = para.wrap(w, h)
    para.drawOn(c, x, y + h - used)
    return used

def image_cover(c, path, x, y, w, h, alpha=1):
    if not path.exists():
        return
    c.saveState()
    if hasattr(c, "setFillAlpha"):
        c.setFillAlpha(alpha)
    img = ImageReader(str(path))
    iw, ih = img.getSize()
    scale = max(w / iw, h / ih)
    sw, sh = iw * scale, ih * scale
    c.drawImage(img, x + (w - sw) / 2, y + (h - sh) / 2, sw, sh, mask="auto")
    c.restoreState()

def panel(c, x, y, w, h, fill="#ffffff", stroke="#cbd5da"):
    c.saveState()
    c.setFillColor(colors.HexColor(fill))
    c.setStrokeColor(colors.HexColor(stroke))
    c.setLineWidth(0.8)
    c.roundRect(x, y, w, h, 12, fill=1, stroke=1)
    c.restoreState()

def footer(c, page):
    c.saveState()
    c.setFont("Helvetica", 7)
    c.setFillColor(colors.HexColor("#54656b"))
    c.drawString(M, 0.28 * inch, f"Lantern OS local: {root}")
    c.drawRightString(W - M, 0.28 * inch, f"{remote} | p. {page}")
    c.restoreState()

def new_page(c, page, bg):
    c.setFillColor(colors.white)
    c.rect(0, 0, W, H, fill=1, stroke=0)
    image_cover(c, bg, 0, 0, W, H, alpha=0.10)
    footer(c, page)

def bullet(c, text, x, y, w):
    c.setFillColor(colors.HexColor("#2f6f70"))
    c.circle(x + 4, y + 8, 2.5, fill=1, stroke=0)
    return p(c, text, "body", x + 14, y, w - 14, 36)

def draw_card(c, title, plain, pro, win, art_path, x, y, w, h):
    panel(c, x, y, w, h)
    image_cover(c, art_path, x + 10, y + h - 122, w - 20, 105, alpha=1)
    p(c, title, "h2", x + 16, y + h - 156, w - 32, 28)
    p(c, "Plain version", "label", x + 16, y + h - 188, w - 32, 14)
    p(c, plain, "small", x + 16, y + h - 250, w - 32, 58)
    p(c, "Pro version", "label", x + 16, y + h - 274, w - 32, 14)
    p(c, pro, "small", x + 16, y + h - 336, w - 32, 58)
    c.setFillColor(colors.HexColor("#eef6f4"))
    c.roundRect(x + 16, y + 16, w - 32, 44, 10, fill=1, stroke=0)
    p(c, "Day One win: " + win, "label", x + 28, y + 24, w - 56, 28)

packages = [
    ("1. Normie Starter Handout",
     "A simple PDF for someone who has never heard of Lantern OS. It says what it does, what it does not do, and what a first useful result looks like.",
     "Use it before a call so the buyer understands the offer without a long explanation.",
     "faster explanation", art["cover"]),
    ("2. RAG Cleanup Packet",
     "RAG means searchable memory. The cleanup packet turns scattered material into labeled records.",
     "A cleaner intake layer before expensive AI context windows, with fewer repeated prompts.",
     "less repeated context", art["memory"]),
    ("3. Learning Packet",
     "School, art, science, math, or project material becomes a readable packet.",
     "A tutor, parent, or teacher gets a weekly lesson draft instead of a folder pile.",
     "easier review", art["learning"]),
    ("4. Discord Community Setup",
     "A soft setup for welcome rooms, project updates, study rooms, and listening rooms.",
     "A moderator gets a channel map and dry run before anything changes.",
     "less confusion", art["wins"]),
    ("5. Local Garage Setup",
     "The local app shows status, pages, RAG memory, wallet state, and boundaries in one place.",
     "A local control surface before cloud spend, starting from evidence instead of a blank chat.",
     "less restart friction", art["memory"]),
    ("6. Pro Cleanup Sprint",
     "A manual cleanup sprint: intake messy material, label sources, make a packet, return next actions.",
     "A reusable handoff artifact that saves coordination time, not a vague AI promise.",
     "billable time saved", art["pro"]),
]

c = canvas.Canvas(str(output), pagesize=letter)

# Page 1 cover
new_page(c, 1, art["cover"])
image_cover(c, art["cover"], M, H - 4.55 * inch, W - 2*M, 3.65 * inch, alpha=1)
panel(c, M, 0.9 * inch, W - 2*M, 2.15 * inch, fill="#ffffff")
p(c, "Lantern Day One", "title", M + 28, 2.25 * inch, W - 2*M - 56, 58)
p(c, "Bring the mess. Leave with one useful packet.", "subtitle", M + 28, 1.78 * inch, W - 2*M - 56, 34)
p(c, "A local-first handout for regular people, families, builders, homeschoolers, people in vans, and pro users who need less mess and more useful next steps.", "body", M + 28, 1.15 * inch, W - 2*M - 56, 62)
c.showPage()

# Page 2 what it is
new_page(c, 2, art["wins"])
p(c, "What Lantern Is", "h1", M, H - 1.05*inch, W - 2*M, 30)
image_cover(c, art["wins"], M, H - 3.45*inch, W - 2*M, 2.05*inch, alpha=1)
left_x, right_x = M, W/2 + 0.1*inch
panel(c, left_x, 3.95*inch, 3.55*inch, 2.05*inch)
panel(c, right_x, 3.95*inch, 3.55*inch, 2.05*inch)
p(c, "It is", "h2", left_x+18, 5.55*inch, 3.2*inch, 22)
for i, text in enumerate(["a local-first garage", "a way to sort messy notes", "a packet maker", "a next-step finder"]):
    bullet(c, text, left_x+18, 5.18*inch - i*0.33*inch, 3.15*inch)
p(c, "It is not", "h2", right_x+18, 5.55*inch, 3.2*inch, 22)
for i, text in enumerate(["a proven business yet", "a replacement for judgment", "a live server change", "a revenue claim"]):
    bullet(c, text, right_x+18, 5.18*inch - i*0.33*inch, 3.15*inch)
panel(c, M, 1.0*inch, W - 2*M, 2.45*inch, fill="#fbfcfb")
p(c, "Validated Money State", "h2", M+18, 3.05*inch, W - 2*M - 36, 22)
money = "Cleared cash: $0. First invoice draft: $199 RAG cleanup pilot. Best first sale: manual cleanup/report service. Good claim: this can turn messy material into a useful packet and save setup time."
p(c, money, "body", M+18, 2.1*inch, W - 2*M - 36, 70)
c.showPage()

# Package pages
for page, pair in enumerate([packages[0:2], packages[2:4], packages[4:6]], start=3):
    new_page(c, page, pair[0][4])
    p(c, "Day One Packages", "h1", M, H - 1.0*inch, W - 2*M, 30)
    draw_card(c, *pair[0], x=M, y=5.25*inch, w=W-2*M, h=4.45*inch)
    draw_card(c, *pair[1], x=M, y=0.68*inch, w=W-2*M, h=4.35*inch)
    c.showPage()

# Page 6 token and savings
new_page(c, 6, art["token"])
p(c, "Token Time And Pro Value", "h1", M, H - 1.0*inch, W - 2*M, 30)
image_cover(c, art["token"], M, H - 3.25*inch, W - 2*M, 1.85*inch, alpha=1)
panel(c, M, 4.2*inch, W - 2*M, 1.65*inch)
p(c, "Token rule", "h2", M+18, 5.45*inch, W - 2*M - 36, 22)
p(c, "Do cheap local sorting first. Keep reusable facts in local RAG records. Use cloud AI for synthesis only when the packet is ready. Use batch processing for non-urgent bulk jobs when available.", "body", M+18, 4.65*inch, W - 2*M - 36, 60)
panel(c, M, 1.0*inch, W - 2*M, 2.75*inch)
p(c, "Pro savings logic", "h2", M+18, 3.32*inch, W - 2*M - 36, 22)
p(c, "If a pro user's loaded time is $50/hour, saving 3 hours is about $150. A $199 cleanup pilot needs to save roughly 4 hours or create a reusable handoff packet that prevents repeated setup later.", "body", M+18, 2.55*inch, W - 2*M - 36, 62)
p(c, "Packet estimate: about 1,300-1,600 words and about 1,800-2,200 tokens after this redesign. Input cost for this packet alone is far below one cent on low-cost models; the real savings come from reducing large messy projects before repeated AI calls.", "body", M+18, 1.72*inch, W - 2*M - 36, 72)
c.showPage()

# Page 7 close/signoff
new_page(c, 7, art["pro"])
p(c, "Day One Signoff", "h1", M, H - 1.0*inch, W - 2*M, 30)
image_cover(c, art["pro"], M, H - 3.15*inch, W - 2*M, 1.75*inch, alpha=1)
panel(c, M, 3.1*inch, W - 2*M, 2.35*inch)
p(c, "Value prop", "h2", M+18, 5.05*inch, W - 2*M - 36, 22)
p(c, "For normies: Bring the mess. Leave with one useful packet. For pros: Lantern turns messy project material into a clean, source-labeled handoff so you spend less time explaining, searching, and re-sending context.", "body", M+18, 4.18*inch, W - 2*M - 36, 74)
panel(c, M, 0.9*inch, W - 2*M, 1.75*inch, fill="#f8fbfa")
p(c, "Signoff checklist", "h2", M+18, 2.25*inch, W - 2*M - 36, 22)
for i, text in enumerate(["No fake revenue claim.", "Money logic is time-saved logic.", "Each package has a plain version and pro version.", "Next step is one real cleanup packet, not a giant launch."]):
    bullet(c, text, M+18, 1.88*inch - i*0.28*inch, W - 2*M - 36)
c.showPage()

c.save()
print(output)
"@

$temp = Join-Path $env:TEMP ("build-day-one-normie-pdf-{0}-{1}.py" -f $PID, ([guid]::NewGuid().ToString("N")))
$python | Set-Content -LiteralPath $temp -Encoding UTF8
try {
    python $temp
}
finally {
    Remove-Item -LiteralPath $temp -Force -ErrorAction SilentlyContinue
}
