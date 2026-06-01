import os
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.lib.colors import HexColor
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT

doc = SimpleDocTemplate(
    # CI/CD MANAGED: relative path so it resolves in pipelines and RAG-indexed clones.
    os.path.join(os.path.dirname(__file__), "CONVERGENCE-VALIDATION-REPORT-2026-05-28.pdf"),
    pagesize=letter,
    topMargin=0.6*inch, bottomMargin=0.6*inch,
    leftMargin=0.7*inch, rightMargin=0.7*inch
)

styles = getSampleStyleSheet()
title_style = ParagraphStyle('Title2', parent=styles['Title'], fontSize=18, spaceAfter=4, textColor=HexColor('#1a1a2e'))
subtitle_style = ParagraphStyle('Sub', parent=styles['Normal'], fontSize=10, textColor=HexColor('#555'), alignment=TA_CENTER, spaceAfter=12)
h2 = ParagraphStyle('H2', parent=styles['Heading2'], fontSize=13, textColor=HexColor('#0d47a1'), spaceBefore=14, spaceAfter=6)
h3 = ParagraphStyle('H3', parent=styles['Heading3'], fontSize=11, textColor=HexColor('#1565c0'), spaceBefore=10, spaceAfter=4)
body = ParagraphStyle('Body', parent=styles['Normal'], fontSize=9, leading=12, spaceAfter=3)
pass_style = ParagraphStyle('Pass', parent=body, textColor=HexColor('#2e7d32'))
pending_style = ParagraphStyle('Pending', parent=body, textColor=HexColor('#e65100'))
small = ParagraphStyle('Small', parent=styles['Normal'], fontSize=8, textColor=HexColor('#777'), spaceAfter=2)

story = []

story.append(Paragraph("Lantern OS Convergence Validation Report", title_style))
story.append(Paragraph("2026-05-28 02:25 UTC &bull; Operator: Alex Place", subtitle_style))
story.append(HRFlowable(width="100%", thickness=1, color=HexColor('#ccc')))
story.append(Spacer(1, 8))

# Summary
story.append(Paragraph("Executive Summary", h2))
story.append(Paragraph("Full convergence validation of Lantern OS surfaces after PR #228 merge (commit 069a832). "
    "10 surface tests executed, 10 convergence loops validated. Overall confidence: <b>85%</b> (9/10 loops pass, 1 pending Render redeploy).", body))
story.append(Spacer(1, 6))

# Surface Tests
story.append(Paragraph("Surface Test Results", h2))

surface_data = [
    ["#", "Surface", "Result", "Detail"],
    ["1", "/health endpoint", "PASS", 'Returns {"status":"ok"}'],
    ["2", "/ (HFF Dashboard)", "PASS", "Flourishing: Humans 54%, Animals 43%, Ecosystems 52%, Universe 50%. 62 beliefs, 9 sensors, 8 domains"],
    ["3", "/api/status", "PASS", "Running status, node_id, timestamp, research mode, write policy"],
    ["4", "/os (Lantern OS)", "PENDING", "404 on Render (rebuild in progress). Local test PASS"],
    ["5", "/art (Art Panels v2)", "PENDING", "404 on Render (rebuild in progress). Local test PASS"],
    ["6", "Local OS Dashboard", "PASS", "Full render: orchestrator, games, apps, notes, media, RetroArch, art panels (localhost:8090)"],
    ["7", "Local Art Panels", "PASS", "4 pixel panels: Lantern Glow 24x24, RAG House 32x20, Seven Anchors 28x16, Convergence 36x18"],
    ["8", "Lantern Flask Backend", "PASS", "Tycoon dashboard shell loads (localhost:5000)"],
    ["9", "GitHub PR #228", "MERGED", "Merged at 2026-05-28T02:23:03Z"],
    ["10", "Remote master", "VERIFIED", "Commit 069a832 includes all changes"],
]

t = Table(surface_data, colWidths=[0.3*inch, 1.5*inch, 0.7*inch, 4.2*inch])
t.setStyle(TableStyle([
    ('BACKGROUND', (0,0), (-1,0), HexColor('#0d47a1')),
    ('TEXTCOLOR', (0,0), (-1,0), HexColor('#ffffff')),
    ('FONTSIZE', (0,0), (-1,-1), 8),
    ('FONTSIZE', (0,0), (-1,0), 9),
    ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
    ('ALIGN', (0,0), (0,-1), 'CENTER'),
    ('ALIGN', (2,0), (2,-1), 'CENTER'),
    ('VALIGN', (0,0), (-1,-1), 'TOP'),
    ('GRID', (0,0), (-1,-1), 0.5, HexColor('#ddd')),
    ('ROWBACKGROUNDS', (0,1), (-1,-1), [HexColor('#f8f9fa'), HexColor('#ffffff')]),
    ('TOPPADDING', (0,0), (-1,-1), 4),
    ('BOTTOMPADDING', (0,0), (-1,-1), 4),
    ('LEFTPADDING', (0,0), (-1,-1), 4),
    ('RIGHTPADDING', (0,0), (-1,-1), 4),
    ('BACKGROUND', (2,4), (2,4), HexColor('#fff3e0')),
    ('BACKGROUND', (2,5), (2,5), HexColor('#fff3e0')),
]))
story.append(t)
story.append(Spacer(1, 10))

# Restored Components
story.append(Paragraph("Restored Components", h2))
restored = [
    "apps/lantern-desktop/lantern_desktop.py (1073 lines) - Tkinter + CustomTkinter desktop chat",
    "apps/lantern-desktop/lantern_operator_chat.py (330 lines) - operator chat variant",
    "apps/lantern-local-chat/local_lantern_server.py (932 lines) - local backend",
    "apps/return-door-watch/index.html (281 lines) - return door UI",
    "START_LANTERN_CHAT.bat - Windows launcher",
    "11 docs restored from git history",
    "5 desktop screenshots restored",
    "Old chat history preserved in ~/.lantern/state/convo-stream.jsonl",
]
for item in restored:
    story.append(Paragraph("&bull; " + item, body))

story.append(Spacer(1, 6))

# New Components
story.append(Paragraph("New Components", h2))
new_items = [
    "lantern-os-live.html - full OS dashboard (orchestrator, 13 games, 7 apps, 4 notes, media, RetroArch, art strip)",
    "art-panels-v2.html - 4 pixel art panels with 2-4px cell grids",
    "safe_app.py /os and /art Flask routes",
    "docs/index.html, docs/os.html, docs/art.html - static hub pages",
    "README.md updated with live URLs table",
]
for item in new_items:
    story.append(Paragraph("&bull; " + item, body))

story.append(Spacer(1, 6))

# Convergence Loops
story.append(Paragraph("Convergence Loops", h2))

loop_data = [
    ["#", "Loop", "Status"],
    ["1", "Git push -> Remote master verified", "PASS"],
    ["2", "PR create -> PR merge -> deploy trigger", "PASS"],
    ["3", "Health endpoint -> API status -> Dashboard render", "PASS"],
    ["4", "Flask server -> Template render -> Browser display", "PASS"],
    ["5", "Pixel art generation -> CSS grid render -> Screenshot capture", "PASS"],
    ["6", "Git history restore -> File checkout -> Commit -> Push", "PASS"],
    ["7", "Desktop app code -> Launch config -> Run path verified", "PASS"],
    ["8", "Old chat data -> JSONL parse -> Dashboard display", "PASS"],
    ["9", "Render deploy pipeline -> Auto-deploy on merge", "PENDING"],
    ["10", "Safe_app.py import chain -> Route registration -> Endpoint serve", "PASS"],
]

lt = Table(loop_data, colWidths=[0.3*inch, 4.5*inch, 0.8*inch])
lt.setStyle(TableStyle([
    ('BACKGROUND', (0,0), (-1,0), HexColor('#1565c0')),
    ('TEXTCOLOR', (0,0), (-1,0), HexColor('#ffffff')),
    ('FONTSIZE', (0,0), (-1,-1), 8),
    ('FONTSIZE', (0,0), (-1,0), 9),
    ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
    ('ALIGN', (0,0), (0,-1), 'CENTER'),
    ('ALIGN', (2,0), (2,-1), 'CENTER'),
    ('GRID', (0,0), (-1,-1), 0.5, HexColor('#ddd')),
    ('ROWBACKGROUNDS', (0,1), (-1,-1), [HexColor('#f8f9fa'), HexColor('#ffffff')]),
    ('TOPPADDING', (0,0), (-1,-1), 4),
    ('BOTTOMPADDING', (0,0), (-1,-1), 4),
    ('LEFTPADDING', (0,0), (-1,-1), 4),
    ('RIGHTPADDING', (0,0), (-1,-1), 4),
    ('BACKGROUND', (2,9), (2,9), HexColor('#fff3e0')),
]))
story.append(lt)
story.append(Spacer(1, 12))

# Confidence
story.append(Paragraph("Confidence Assessment", h2))
story.append(Paragraph("<b>Overall Confidence: 85%</b>", ParagraphStyle('conf', parent=body, fontSize=11, textColor=HexColor('#2e7d32'))))
story.append(Paragraph("9 of 10 convergence loops validated. Loop 9 (Render auto-deploy) pending completion of free-tier rebuild cycle. "
    "All local surfaces verified functional. Remote master confirmed at commit 069a832 with all changes merged via PR #228.", body))
story.append(Spacer(1, 8))

# Live URLs
story.append(Paragraph("Live URLs", h2))
urls = [
    ["Surface", "URL"],
    ["HFF Dashboard", "https://human-flourishing-frameworks.onrender.com/"],
    ["Lantern OS Dashboard", "https://human-flourishing-frameworks.onrender.com/os"],
    ["Art Panels v2", "https://human-flourishing-frameworks.onrender.com/art"],
    ["Health API", "https://human-flourishing-frameworks.onrender.com/health"],
    ["System Status", "https://human-flourishing-frameworks.onrender.com/api/status"],
    ["Source Code", "https://github.com/human-flourishing-frameworks/human-flourishing-frameworks"],
]
ut = Table(urls, colWidths=[1.5*inch, 5.2*inch])
ut.setStyle(TableStyle([
    ('BACKGROUND', (0,0), (-1,0), HexColor('#333')),
    ('TEXTCOLOR', (0,0), (-1,0), HexColor('#fff')),
    ('FONTSIZE', (0,0), (-1,-1), 8),
    ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
    ('GRID', (0,0), (-1,-1), 0.5, HexColor('#ddd')),
    ('ROWBACKGROUNDS', (0,1), (-1,-1), [HexColor('#f8f9fa'), HexColor('#ffffff')]),
    ('TOPPADDING', (0,0), (-1,-1), 3),
    ('BOTTOMPADDING', (0,0), (-1,-1), 3),
    ('LEFTPADDING', (0,0), (-1,-1), 4),
]))
story.append(ut)

story.append(Spacer(1, 16))
story.append(HRFlowable(width="100%", thickness=0.5, color=HexColor('#ccc')))
story.append(Spacer(1, 4))
story.append(Paragraph("Generated 2026-05-28 02:25 UTC | Lantern OS | Human Flourishing Frameworks", small))

doc.build(story)
print("PDF generated successfully.")
