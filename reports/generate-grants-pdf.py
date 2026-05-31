#!/usr/bin/env python3
"""Generate PDF from the Grants Normie Report for Shelby."""

from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
)
from reportlab.lib import colors

INPUT_MD = r'd:\tmp\lantern-os\reports\GRANTS-NORMIE-REPORT-FOR-SHELBY-2026-05-30.md'
OUTPUT_PDF = r'd:\tmp\lantern-os\reports\GRANTS-NORMIE-REPORT-FOR-SHELBY-2026-05-30.pdf'

doc = SimpleDocTemplate(
    OUTPUT_PDF,
    pagesize=letter,
    rightMargin=0.6*inch,
    leftMargin=0.6*inch,
    topMargin=0.75*inch,
    bottomMargin=0.75*inch,
    title='Grant Opportunities for Lantern OS',
    author='Alex Place'
)

styles = getSampleStyleSheet()

DARK = colors.HexColor('#1e293b')
BLUE = colors.HexColor('#2563eb')
LIGHT = colors.HexColor('#f1f5f9')
GRAY = colors.HexColor('#64748b')

# Title
title_style = ParagraphStyle(
    'TitleStyle',
    parent=styles['Heading1'],
    fontSize=22,
    textColor=DARK,
    spaceAfter=4,
    alignment=TA_CENTER,
    fontName='Helvetica-Bold'
)

subtitle_style = ParagraphStyle(
    'SubtitleStyle',
    parent=styles['Normal'],
    fontSize=10,
    textColor=GRAY,
    spaceAfter=12,
    alignment=TA_CENTER
)

section_bg = ParagraphStyle(
    'SectionBg',
    parent=styles['Heading1'],
    fontSize=14,
    textColor=colors.white,
    spaceAfter=8,
    spaceBefore=12,
    fontName='Helvetica-Bold',
    leading=18
)

h2_style = ParagraphStyle(
    'H2Style',
    parent=styles['Heading2'],
    fontSize=12,
    textColor=DARK,
    spaceAfter=6,
    spaceBefore=10,
    fontName='Helvetica-Bold'
)

body_style = ParagraphStyle(
    'BodyStyle',
    parent=styles['Normal'],
    fontSize=10,
    leading=13,
    alignment=TA_LEFT,
    spaceAfter=6,
    textColor=DARK
)

bullet_style = ParagraphStyle(
    'BulletStyle',
    parent=styles['Normal'],
    fontSize=10,
    leading=13,
    alignment=TA_LEFT,
    spaceAfter=4,
    leftIndent=16,
    textColor=DARK
)

callout_style = ParagraphStyle(
    'CalloutStyle',
    parent=styles['Normal'],
    fontSize=10,
    leading=13,
    alignment=TA_LEFT,
    spaceAfter=8,
    leftIndent=12,
    rightIndent=12,
    textColor=DARK,
    fontName='Helvetica-Bold'
)

small_style = ParagraphStyle(
    'SmallStyle',
    parent=styles['Normal'],
    fontSize=8,
    textColor=GRAY,
    alignment=TA_CENTER,
    spaceBefore=16
)

story = []

# Cover
story.append(Spacer(1, 0.3*inch))
story.append(Paragraph("Grant Opportunities for Lantern OS", title_style))
story.append(Paragraph("Normie Report for Shelby | May 30, 2026", subtitle_style))
story.append(Spacer(1, 0.15*inch))

# Big Picture
section_data = [["The Big Picture"]]
section_table = Table(section_data, colWidths=[7*inch])
section_table.setStyle(TableStyle([
    ('BACKGROUND', (0, 0), (-1, -1), BLUE),
    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ('LEFTPADDING', (0, 0), (-1, -1), 10),
    ('RIGHTPADDING', (0, 0), (-1, -1), 10),
    ('TOPPADDING', (0, 0), (-1, -1), 8),
    ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
]))
story.append(section_table)
story.append(Spacer(1, 0.1*inch))

story.append(Paragraph(
    "We found <b>real grant money</b> that could fund Lantern OS. Some deadlines are soon. "
    "None of them require giving away ownership of the company. This report lists what we found, "
    "why each one fits, and exactly what to do next.",
    body_style
))

story.append(PageBreak())

# Section helper
def add_section(title_text):
    section_data = [[title_text]]
    section_table = Table(section_data, colWidths=[7*inch])
    section_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), BLUE),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (-1, -1), 10),
        ('RIGHTPADDING', (0, 0), (-1, -1), 10),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
    ]))
    story.append(section_table)
    story.append(Spacer(1, 0.08*inch))

# Grant 1
add_section("Grant 1: Survival and Flourishing Fund (SFF) — HSEE Round")
story.append(Paragraph(
    "<b>What it is:</b> A philanthropy run by Jaan Tallinn (cofounded Skype). They give away $20-40 million per year "
    "to projects that help humans thrive alongside AI.",
    body_style
))
story.append(Paragraph(
    "<b>Why Lantern fits:</b> They have a theme round called 'Human Self-Enhancement and Empowerment' (HSEE). "
    "It funds tools that help humans stay capable and empowered as AI advances. Lantern OS is literally a local-first tool "
    "that keeps humans organized and in control of their own files and workflows.",
    body_style
))
story.append(Paragraph("<b>Money:</b> $2-4 million total in this round. Individual grants vary.", body_style))
story.append(Paragraph("<b>Deadline:</b> <font color='red'>July 8, 2026 at 11:59 PM PT</font>", body_style))
story.append(Paragraph("<b>Type:</b> You can apply as a charity or for-profit. Funding can be non-dilutive (they don't take equity).", body_style))
story.append(Paragraph(
    "<b>Real talk:</b> This is the best fit we found. The description basically reads like Lantern's mission statement.",
    callout_style
))

story.append(PageBreak())

# Grant 2
add_section("Grant 2: Survival and Flourishing Fund (SFF) — Main Round")
story.append(Paragraph(
    "<b>What it is:</b> The same fund's general grant round. Three tracks:",
    body_style
))
story.append(Paragraph("- Main Track: Broad long-term survival and flourishing of sentient life", bullet_style))
story.append(Paragraph("- Freedom Track: Individual freedom and autonomy", bullet_style))
story.append(Paragraph("- Fairness Track: Fair distribution of benefits and risks", bullet_style))
story.append(Paragraph(
    "<b>Why Lantern fits:</b> Local-first = user owns their data = freedom track fit. "
    "Safety hooks and evidence boundaries = survival track fit. Open source tooling for regular people = fairness track fit.",
    body_style
))
story.append(Paragraph("<b>Money:</b> $14-28 million total across all three tracks.", body_style))
story.append(Paragraph("<b>Deadline:</b> Rolling application open now.", body_style))
story.append(Paragraph(
    "<b>Real talk:</b> Apply here too even if you apply to the HSEE round. They run independently.",
    callout_style
))

# Grant 3
story.append(PageBreak())
add_section("Grant 3: Mozilla Open Source Support (MOSS) — Foundational Technology")
story.append(Paragraph(
    "<b>What it is:</b> Mozilla (the nonprofit behind Firefox) gives money to open source projects that make the internet healthier.",
    body_style
))
story.append(Paragraph(
    "<b>Why Lantern fits:</b> Lantern OS is open source. It keeps data local instead of feeding the cloud-everything model. "
    "It empowers users to control their own information.",
    body_style
))
story.append(Paragraph("<b>Money:</b> $10,000 to $250,000 per award.", body_style))
story.append(Paragraph("<b>Deadline:</b> Rolling / no fixed deadline, but apply sooner for faster review.", body_style))
story.append(Paragraph(
    "<b>Catch:</b> You need a 'Mozilla champion' -- someone who works at or is connected to Mozilla who will vouch for the project.",
    body_style
))
story.append(Paragraph(
    "<b>Real talk:</b> Smaller money than SFF, but easier process and no equity strings.",
    callout_style
))

story.append(PageBreak())

# Grant 4
add_section("Grant 4: NSF SBIR / America's Seed Fund")
story.append(Paragraph(
    "<b>What it is:</b> The U.S. government gives up to ~$305,000 to small businesses doing deep tech R&D. No equity taken.",
    body_style
))
story.append(Paragraph(
    "<b>Why Lantern fits:</b> AI + local-first computing qualifies as deep tech. They specifically have AI topics open.",
    body_style
))
story.append(Paragraph("<b>Money:</b> Phase I = up to ~$305,000. Phase II = up to ~$2 million.", body_style))
story.append(Paragraph(
    "<b>Deadline:</b> New solicitations opened June 2, 2026. Project pitches accepted now.",
    body_style
))
story.append(Paragraph(
    "<b>Catch:</b> Must be a U.S. small business. At least 50% owned by U.S. citizens or permanent residents. "
    "Requires a 'Project Pitch' first.",
    body_style
))
story.append(Paragraph(
    "<b>Real talk:</b> More paperwork than the others, but it's government money with no strings attached.",
    callout_style
))

story.append(PageBreak())

# Comparison Table
add_section("Quick Comparison")

table_data = [
    ['Grant', 'Money', 'Deadline', 'Fit', 'Difficulty'],
    ['SFF HSEE', '$2-4M pool', 'July 8, 2026', 'Excellent', 'Medium'],
    ['SFF Main', '$14-28M pool', 'Rolling', 'Very Good', 'Medium'],
    ['Mozilla MOSS', '$10K-$250K', 'Rolling', 'Good', 'Easy*'],
    ['NSF SBIR', 'Up to $305K', 'Open now', 'Good', 'High'],
]

tbl = Table(table_data, colWidths=[1.4*inch, 1.3*inch, 1.4*inch, 1.1*inch, 1.1*inch])
tbl.setStyle(TableStyle([
    ('BACKGROUND', (0, 0), (-1, 0), BLUE),
    ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
    ('FONTSIZE', (0, 0), (-1, 0), 9),
    ('FONTSIZE', (0, 1), (-1, -1), 9),
    ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
    ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
    ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, LIGHT]),
    ('LEFTPADDING', (0, 0), (-1, -1), 6),
    ('RIGHTPADDING', (0, 0), (-1, -1), 6),
    ('TOPPADDING', (0, 0), (-1, -1), 6),
    ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
]))
story.append(tbl)
story.append(Spacer(1, 0.1*inch))
story.append(Paragraph("*Easy if you find a Mozilla champion. Otherwise, harder.", subtitle_style))

story.append(PageBreak())

# Follow-Up Actions
add_section("Follow-Up Actions for Shelby")

story.append(Paragraph("<b>This Week (Before June 6)</b>", h2_style))
story.append(Paragraph("1. <b>Pick your top 2</b> -- Recommended: SFF HSEE + SFF Main Round. Best fit, most money, real deadline soon.", bullet_style))
story.append(Paragraph("2. <b>Read the SFF HSEE application page</b> -- URL: survivalandflourishing.fund/hsee-application | Time: 30 min", bullet_style))
story.append(Paragraph("3. <b>Draft a one-paragraph project summary</b> -- Use plain language. This paragraph will be reused across all applications.", bullet_style))

story.append(Paragraph("<b>Next Two Weeks (Before June 20)</b>", h2_style))
story.append(Paragraph("4. <b>Apply to SFF HSEE round</b> -- Step 1: Rolling Application. Step 2: HSEE Supplemental. Deadline: July 8, 2026.", bullet_style))
story.append(Paragraph("5. <b>Apply to SFF Main Round</b> -- Same rolling application. Pick the track that feels most natural.", bullet_style))
story.append(Paragraph("6. <b>Find a Mozilla champion</b> -- Ask in your network. Check LinkedIn. If no lead in 2 weeks, park this and focus on SFF.", bullet_style))

story.append(Paragraph("<b>This Month (Before June 30)</b>", h2_style))
story.append(Paragraph("7. <b>Decide on NSF SBIR</b> -- If you are a U.S. small business and have bandwidth for government paperwork, draft a Project Pitch.", bullet_style))
story.append(Paragraph("8. <b>Collect evidence</b> -- Screenshot the WOW-FACTOR report. Link to the GitHub repo. List any users, pilots, or demos.", bullet_style))

story.append(PageBreak())

# What You Need
add_section("What You Need to Have Ready")

need_data = [
    ['Item', 'Status', 'Needed For'],
    ['One-paragraph project summary', 'Need to draft', 'All applications'],
    ['GitHub repo link', 'Have it', 'All applications'],
    ['Evidence of use', 'Need to document', 'SFF, MOSS'],
    ['Financial need statement', 'Need to draft', 'All applications'],
    ['U.S. business status', 'Check', 'NSF only'],
]

need_tbl = Table(need_data, colWidths=[2.4*inch, 1.3*inch, 2.3*inch])
need_tbl.setStyle(TableStyle([
    ('BACKGROUND', (0, 0), (-1, 0), BLUE),
    ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
    ('FONTSIZE', (0, 0), (-1, 0), 9),
    ('FONTSIZE', (0, 1), (-1, -1), 9),
    ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
    ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
    ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, LIGHT]),
    ('LEFTPADDING', (0, 0), (-1, -1), 6),
    ('RIGHTPADDING', (0, 0), (-1, -1), 6),
    ('TOPPADDING', (0, 0), (-1, -1), 6),
    ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
]))
story.append(need_tbl)

story.append(PageBreak())

# Bottom Line
add_section("The Bottom Line")

story.append(Paragraph(
    "<b>There is real money available that matches what Lantern OS is building.</b>",
    body_style
))
story.append(Paragraph(
    "The best opportunities are SFF HSEE (July 8 deadline, $2-4M pool, perfect mission fit) "
    "and SFF Main ($14-28M pool, rolling, also fits well). Mozilla MOSS is smaller but easy. "
    "NSF SBIR is more paperwork.",
    body_style
))
story.append(Paragraph(
    "<b>No revenue claims needed.</b> No investor pitches. Just explain what you built, why it matters, "
    "and what you need money for.",
    callout_style
))

story.append(Spacer(1, 0.2*inch))

# Contact
story.append(Paragraph("<b>Contact Info for Questions</b>", h2_style))
story.append(Paragraph("SFF: sff-contact@googlegroups.com", body_style))
story.append(Paragraph("Mozilla MOSS: mozilla.fluxx.io/apply/MOSS", body_style))
story.append(Paragraph("NSF SBIR: seedfund@nsf.gov", body_style))

story.append(Spacer(1, 0.2*inch))

# Checklist Table
story.append(Paragraph("<b>Shelby's Checklist</b>", h2_style))

check_data = [
    ['Done', 'Action'],
    ['[ ]', 'Read this whole report'],
    ['[ ]', 'Pick top 2 grants to pursue'],
    ['[ ]', 'Draft one-paragraph project summary'],
    ['[ ]', 'Apply to SFF HSEE round (deadline: July 8)'],
    ['[ ]', 'Apply to SFF Main round'],
    ['[ ]', 'Look for Mozilla champion connection'],
    ['[ ]', 'Decide yes/no on NSF SBIR'],
    ['[ ]', 'Document any user/pilot evidence'],
]

check_tbl = Table(check_data, colWidths=[0.8*inch, 6.2*inch])
check_tbl.setStyle(TableStyle([
    ('BACKGROUND', (0, 0), (-1, 0), DARK),
    ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
    ('FONTSIZE', (0, 0), (-1, 0), 9),
    ('FONTSIZE', (0, 1), (-1, -1), 10),
    ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
    ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
    ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, LIGHT]),
    ('LEFTPADDING', (0, 0), (-1, -1), 8),
    ('RIGHTPADDING', (0, 0), (-1, -1), 8),
    ('TOPPADDING', (0, 0), (-1, -1), 6),
    ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
]))
story.append(check_tbl)

story.append(Spacer(1, 0.3*inch))
story.append(Paragraph("Made by: Alex Place | For: Shelby | Action Deadline: July 8, 2026", small_style))

# Build
doc.build(story)
print(f"[OK] PDF created: {OUTPUT_PDF}")
