#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Convert Markdown to PDF using reportlab.
Supports headings, paragraphs, bold, italic, lists, tables, and code blocks.
Handles UTF-8 properly with explicit encoding.
"""

import sys
import re
from pathlib import Path
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle, PageTemplate, Frame
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT, TA_JUSTIFY
from reportlab.pdfgen import canvas

# Ensure UTF-8 output
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')


class PageNumberCanvas(canvas.Canvas):
    def __init__(self, *args, **kwargs):
        canvas.Canvas.__init__(self, *args, **kwargs)
        self._pages = []

    def showPage(self):
        self._pages.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        page_count = len(self._pages)
        for page_num, page in enumerate(self._pages, 1):
            self.__dict__.update(page)
            self.setFont("Helvetica", 9)
            self.drawString(7.5 * inch, 0.5 * inch, f"Page {page_num}")
            canvas.Canvas.showPage(self)
        canvas.Canvas.save(self)


def parse_markdown_to_story(md_content, styles):
    """
    Parse markdown content and convert to reportlab story elements.

    Supports:
    - # Headings (all levels)
    - **Bold** and *Italic* text
    - Lists (- and *)
    - Code blocks (```...```)
    - Tables (| col1 | col2 |)
    - Horizontal rules (---)
    """
    story = []
    lines = md_content.split('\n')
    i = 0

    while i < len(lines):
        line = lines[i].rstrip()

        # Skip empty lines
        if not line.strip():
            story.append(Spacer(1, 0.1 * inch))
            i += 1
            continue

        # Headings
        if line.startswith('# '):
            text = line[2:].strip()
            story.append(Paragraph(text, styles['Title']))
            story.append(Spacer(1, 0.2 * inch))
            i += 1
        elif line.startswith('## '):
            text = line[3:].strip()
            story.append(Paragraph(text, styles['Heading1']))
            story.append(Spacer(1, 0.15 * inch))
            i += 1
        elif line.startswith('### '):
            text = line[4:].strip()
            story.append(Paragraph(text, styles['Heading2']))
            story.append(Spacer(1, 0.1 * inch))
            i += 1
        elif line.startswith('#### '):
            text = line[5:].strip()
            story.append(Paragraph(text, styles['Heading3']))
            story.append(Spacer(1, 0.08 * inch))
            i += 1

        # Code blocks
        elif line.startswith('```'):
            code_lines = []
            i += 1
            while i < len(lines) and not lines[i].startswith('```'):
                code_lines.append(lines[i])
                i += 1
            i += 1  # Skip closing ```

            code_text = '\n'.join(code_lines)
            story.append(Paragraph(f"<font face='Courier' size='8'><br/>{code_text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')}</font>", styles['Normal']))
            story.append(Spacer(1, 0.1 * inch))

        # Horizontal rules
        elif line.strip() in ('---', '***', '___'):
            story.append(Spacer(1, 0.1 * inch))
            i += 1

        # Tables (simple markdown tables)
        elif '|' in line:
            table_lines = [line]
            i += 1

            # Skip separator line
            if i < len(lines) and '|' in lines[i] and '-' in lines[i]:
                i += 1

            # Collect table rows
            while i < len(lines) and '|' in lines[i]:
                table_lines.append(lines[i])
                i += 1

            # Parse table
            table_data = []
            for tline in table_lines:
                cells = [cell.strip() for cell in tline.split('|')[1:-1]]
                table_data.append(cells)

            if table_data:
                table = Table(table_data, repeatRows=1)
                table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 9),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black),
                    ('FONTSIZE', (0, 1), (-1, -1), 8),
                ]))
                story.append(table)
                story.append(Spacer(1, 0.1 * inch))

        # Lists
        elif line.strip().startswith(('- ', '* ', '+ ')):
            list_items = []
            while i < len(lines) and lines[i].strip().startswith(('- ', '* ', '+ ')):
                item_text = lines[i].strip()[2:].strip()
                # Convert markdown formatting
                item_text = format_text(item_text)
                list_items.append(f"• {item_text}<br/><br/>")
                i += 1

            story.append(Paragraph(''.join(list_items), styles['Normal']))
            story.append(Spacer(1, 0.1 * inch))

        # Regular paragraphs
        else:
            para_text = format_text(line)
            story.append(Paragraph(para_text, styles['Normal']))
            story.append(Spacer(1, 0.05 * inch))
            i += 1

    return story


def sanitize_for_reportlab(text):
    """Remove or replace problematic unicode characters."""
    # Strip all non-ASCII by converting to ASCII with replace errors
    # This removes emoji, special symbols, etc. completely
    text_ascii = text.encode('ascii', errors='ignore').decode('ascii')

    # Then apply specific replacements for common markdown/doc characters
    replacements = {
        '✅': '[OK]',
        '✓': '[OK]',
        '✔': '[OK]',
        '🟢': '[OK]',
        '🟡': '[IN PROGRESS]',
        '🔴': '[FAILED]',
        '⚠️': '[WARNING]',
        '→': '->',
        '←': '<-',
        '↑': '^',
        '↓': 'v',
        '≈': '~',
        '≠': '!=',
        '≤': '<=',
        '≥': '>=',
        '™': '(TM)',
        '©': '(C)',
        '°': 'deg',
        '…': '...',
        '–': '-',
        '—': '--',
        '·': '*',
        '•': '*',
        '◆': '*',
        '○': 'o',
        '□': '[ ]',
        '"': '"',
        '"': '"',
        ''': "'",
        ''': "'",
    }

    # Apply replacements first before stripping, in case they contain non-ASCII
    for char, replacement in replacements.items():
        text = text.replace(char, replacement)

    # Final pass: strip anything remaining that's non-ASCII
    result = ''.join(char if ord(char) < 128 else '' for char in text)
    return result


def format_text(text):
    """Convert markdown formatting to reportlab formatting."""
    # Sanitize unicode first
    text = sanitize_for_reportlab(text)

    # Bold: **text** or __text__
    text = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', text)
    text = re.sub(r'__(.*?)__', r'<b>\1</b>', text)

    # Italic: *text* or _text_
    text = re.sub(r'\*(.*?)\*', r'<i>\1</i>', text)
    text = re.sub(r'_(.*?)_', r'<i>\1</i>', text)

    # Links: [text](url)
    text = re.sub(r'\[(.*?)\]\((.*?)\)', r'<u>\1</u>', text)

    # Escape special characters for XML
    text = text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
    text = text.replace('&amp;lt;', '<').replace('&amp;gt;', '>').replace('&amp;b;', '<b>').replace('&amp;/b;', '</b>')

    return text


def markdown_to_pdf(markdown_file, output_pdf=None):
    """
    Convert markdown file to PDF.

    Args:
        markdown_file: Path to .md file
        output_pdf: Path to output .pdf (defaults to same name with .pdf extension)
    """
    md_path = Path(markdown_file)
    if not md_path.exists():
        print(f"Error: {markdown_file} not found")
        return False

    if output_pdf is None:
        output_pdf = md_path.with_suffix('.pdf')

    # Read markdown with UTF-8 encoding
    try:
        with open(md_path, 'r', encoding='utf-8') as f:
            md_content = f.read()
    except UnicodeDecodeError:
        # Fallback to latin-1 if UTF-8 fails
        with open(md_path, 'r', encoding='latin-1') as f:
            md_content = f.read()

    # Replace unicode characters with ASCII equivalents
    replacements = {
        '✅': '[OK]',
        '🟢': '[OK]',
        '🟡': '[IN PROGRESS]',
        '🔴': '[FAILED]',
        '⚠️': '[WARNING]',
        '→': '->',
        '←': '<-',
        '↑': '^',
        '↓': 'v',
        '≈': '~',
        '≠': '!=',
        '≤': '<=',
        '≥': '>=',
        '™': '(TM)',
        '©': '(C)',
        '°': 'deg',
        '…': '...',
        '–': '-',
        '—': '--',
        '·': '*',
        '•': '*',
        '"': '"',
        '"': '"',
        ''': "'",
        ''': "'",
    }

    for char, replacement in replacements.items():
        md_content = md_content.replace(char, replacement)

    # Create PDF with custom canvas for page numbering
    doc = SimpleDocTemplate(
        str(output_pdf),
        pagesize=letter,
        rightMargin=0.5 * inch,
        leftMargin=0.5 * inch,
        topMargin=0.75 * inch,
        bottomMargin=1.0 * inch  # Increased for page numbers
    )

    # Get styles
    styles = getSampleStyleSheet()

    # Customize styles with better font support for Unicode
    styles.add(ParagraphStyle(
        name='CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#1e40af'),
        spaceAfter=20,
        fontName='Helvetica'
    ))
    styles.add(ParagraphStyle(
        name='CustomHeading',
        parent=styles['Heading2'],
        fontSize=14,
        textColor=colors.HexColor('#1e40af'),
        spaceAfter=12,
        fontName='Helvetica'
    ))

    # Update Normal style to use Helvetica for better Unicode support
    styles['Normal'].fontName = 'Helvetica'

    # Parse markdown and build story
    story = parse_markdown_to_story(md_content, styles)

    # Build PDF with page numbers
    try:
        doc.build(story, canvasmaker=PageNumberCanvas)
        print(f"✓ PDF created: {output_pdf}")
        print(f"  Size: {Path(output_pdf).stat().st_size / 1024:.1f} KB")
        return True
    except Exception as e:
        print(f"Error creating PDF: {e}")
        return False


if __name__ == '__main__':
    import sys

    if len(sys.argv) < 2:
        print("Usage: python markdown-to-pdf.py <input.md> [output.pdf]")
        sys.exit(1)

    md_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else None

    success = markdown_to_pdf(md_file, output_file)
    sys.exit(0 if success else 1)
