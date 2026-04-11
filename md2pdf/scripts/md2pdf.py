#!/usr/bin/env python3
"""md2pdf — Markdown to PDF converter using ReportLab. Full Chinese support."""

import argparse
import os
import re
import sys
from pathlib import Path

import yaml
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import A4, LETTER
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    HRFlowable,
    PageBreak,
    Paragraph,
    Preformatted,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

# ---------------------------------------------------------------------------
# Theme system
# ---------------------------------------------------------------------------

THEMES = {
    "navy":     {"accent": "#1C3A5E", "dark": "#1A1A2E", "muted": "#888888"},
    "forest":   {"accent": "#2D5A27", "dark": "#1A2E1A", "muted": "#888888"},
    "minimal":  {"accent": "#333333", "dark": "#111111", "muted": "#999999"},
    "warm":     {"accent": "#7B4F2E", "dark": "#2E1A0E", "muted": "#999999"},
    "coral":    {"accent": "#C0392B", "dark": "#2C1810", "muted": "#888888"},
    "slate":    {"accent": "#4A5568", "dark": "#1A202C", "muted": "#888888"},
    "purple":   {"accent": "#553C9A", "dark": "#1A0E2E", "muted": "#888888"},
    "teal":     {"accent": "#2C7A7B", "dark": "#0E2E2E", "muted": "#888888"},
    "gold":     {"accent": "#B7791F", "dark": "#2E1E0E", "muted": "#888888"},
    "rose":     {"accent": "#B83280", "dark": "#2E0E1E", "muted": "#888888"},
    "midnight": {"accent": "#2D3748", "dark": "#0A0A0A", "muted": "#999999"},
    "olive":    {"accent": "#556B2F", "dark": "#1A2010", "muted": "#888888"},
}

THEME_ANSI = {
    "navy": "\033[44m", "forest": "\033[42m", "minimal": "\033[100m",
    "warm": "\033[43m", "coral": "\033[41m", "slate": "\033[100m",
    "purple": "\033[45m", "teal": "\033[46m", "gold": "\033[33m",
    "rose": "\033[35m", "midnight": "\033[100m", "olive": "\033[32m",
}

THEMES_LIST = [
    ("navy",     "Navy",     "深海军蓝，专业商务 / Deep navy, professional"),
    ("forest",   "Forest",   "深绿，学术自然 / Deep green, academic"),
    ("minimal",  "Minimal",  "黑白极简 / Black & white minimal"),
    ("warm",     "Warm",     "暖棕，人文学术 / Warm brown, humanities"),
    ("coral",    "Coral",    "珊瑚红，活力现代 / Coral red, vibrant"),
    ("slate",    "Slate",    "石板灰，低调稳重 / Slate grey, understated"),
    ("purple",   "Purple",   "深紫，科技感 / Deep purple, tech"),
    ("teal",     "Teal",     "青绿，清新简洁 / Teal, fresh & clean"),
    ("gold",     "Gold",     "金棕，高端商务 / Gold brown, premium"),
    ("rose",     "Rose",     "玫瑰粉，轻奢优雅 / Rose pink, elegant"),
    ("midnight", "Midnight", "午夜黑，极简暗色 / Midnight black, dark minimal"),
    ("olive",    "Olive",    "橄榄绿，自然沉稳 / Olive green, natural"),
]


def hex_to_color(hex_str: str):
    """Convert #RRGGBB string to ReportLab Color."""
    h = hex_str.lstrip("#")
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return colors.Color(r / 255, g / 255, b / 255)


def resolve_theme(theme_name: str, style_data: dict) -> dict:
    """Return {accent, dark, muted} Color objects for the given theme."""
    if theme_name == "custom":
        accent = style_data.get("custom_accent", "#333333")
        dark   = style_data.get("custom_dark",   "#111111")
        muted  = style_data.get("custom_muted",  "#888888")
    else:
        t = THEMES.get(theme_name, THEMES["navy"])
        accent, dark, muted = t["accent"], t["dark"], t["muted"]
    return {
        "accent": hex_to_color(accent),
        "dark":   hex_to_color(dark),
        "muted":  hex_to_color(muted),
    }


def print_theme_selector():
    print("请选择主题 / Select theme:")
    for i, (key, name, desc) in enumerate(THEMES_LIST, 1):
        ansi = THEME_ANSI[key]
        print(f" {i:2}  {ansi}      \033[0m  {name:<10} {desc}")
    print("  0             Custom      自定义 hex 颜色 / Custom hex colors")


# ---------------------------------------------------------------------------
# Font registration
# ---------------------------------------------------------------------------

_REGISTERED_FONTS: set = set()


def register_font(font_path: str, font_name: str = "CustomFont") -> str:
    """Register a TTF/OTF font with ReportLab. Returns the registered name."""
    if font_name in _REGISTERED_FONTS:
        return font_name
    path = Path(font_path)
    if not path.exists():
        raise FileNotFoundError(f"Font not found: {font_path}")
    # .ttc files need index 0
    if path.suffix.lower() == ".ttc":
        from reportlab.pdfbase.ttfonts import TTFont as _TTFont
        pdfmetrics.registerFont(_TTFont(font_name, str(path), subfontIndex=0))
    else:
        pdfmetrics.registerFont(TTFont(font_name, str(path)))
    _REGISTERED_FONTS.add(font_name)
    return font_name


# ---------------------------------------------------------------------------
# Style builder
# ---------------------------------------------------------------------------

def build_styles(font_name: str, theme_colors: dict) -> dict:
    """Return a dict of ParagraphStyle objects keyed by role."""
    accent = theme_colors["accent"]
    dark   = theme_colors["dark"]
    muted  = theme_colors["muted"]

    base = dict(fontName=font_name, textColor=dark, leading=20)

    return {
        "h1": ParagraphStyle("h1", fontSize=24, spaceAfter=12, spaceBefore=18,
                             textColor=accent, fontName=font_name, leading=30),
        "h2": ParagraphStyle("h2", fontSize=18, spaceAfter=8,  spaceBefore=14,
                             textColor=accent, fontName=font_name, leading=24),
        "h3": ParagraphStyle("h3", fontSize=14, spaceAfter=6,  spaceBefore=10,
                             textColor=accent, fontName=font_name, leading=20),
        "h4": ParagraphStyle("h4", fontSize=12, spaceAfter=4,  spaceBefore=8,
                             textColor=dark,   fontName=font_name, leading=18),
        "body": ParagraphStyle("body", fontSize=11, spaceAfter=6, spaceBefore=2,
                               **base),
        "bullet": ParagraphStyle("bullet", fontSize=11, spaceAfter=4, spaceBefore=2,
                                 leftIndent=18, bulletIndent=6, **base),
        "code_inline": ParagraphStyle("code_inline", fontSize=10, spaceAfter=4,
                                      fontName="Courier", textColor=dark, leading=16),
        "code_block": ParagraphStyle("code_block", fontSize=9, spaceAfter=8,
                                     spaceBefore=4, fontName="Courier",
                                     textColor=dark, leading=14,
                                     leftIndent=12, backColor=colors.Color(0.95, 0.95, 0.95)),
        "blockquote": ParagraphStyle("blockquote", fontSize=11, spaceAfter=6,
                                     spaceBefore=4, leftIndent=20,
                                     textColor=muted, fontName=font_name, leading=18),
        "cover_title": ParagraphStyle("cover_title", fontSize=32, spaceAfter=16,
                                      alignment=TA_CENTER, textColor=accent,
                                      fontName=font_name, leading=40),
        "cover_subtitle": ParagraphStyle("cover_subtitle", fontSize=18, spaceAfter=10,
                                         alignment=TA_CENTER, textColor=dark,
                                         fontName=font_name, leading=24),
        "cover_meta": ParagraphStyle("cover_meta", fontSize=12, spaceAfter=6,
                                     alignment=TA_CENTER, textColor=muted,
                                     fontName=font_name, leading=18),
        "table_header": ParagraphStyle("table_header", fontSize=10, fontName=font_name,
                                       textColor=colors.white, leading=14),
        "table_cell": ParagraphStyle("table_cell", fontSize=10, fontName=font_name,
                                     textColor=dark, leading=14),
    }


# ---------------------------------------------------------------------------
# Inline markdown → ReportLab XML
# ---------------------------------------------------------------------------

def inline_to_xml(text: str, font_name: str) -> str:
    """Convert inline markdown (bold, italic, code, links) to ReportLab XML."""
    # Escape XML special chars first (except & which we handle carefully)
    text = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    # Bold+italic ***text*** or ___text___
    text = re.sub(r'\*\*\*(.+?)\*\*\*', r'<b><i>\1</i></b>', text)
    text = re.sub(r'___(.+?)___',        r'<b><i>\1</i></b>', text)
    # Bold **text** or __text__
    text = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', text)
    text = re.sub(r'__(.+?)__',     r'<b>\1</b>', text)
    # Italic *text* or _text_
    text = re.sub(r'\*(.+?)\*', r'<i>\1</i>', text)
    text = re.sub(r'_([^_]+?)_', r'<i>\1</i>', text)
    # Inline code `text`
    text = re.sub(r'`([^`]+?)`', r'<font name="Courier">\1</font>', text)
    # Links [text](url) — show text only
    text = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', text)
    return text


# ---------------------------------------------------------------------------
# Markdown parser → list of (type, data) tokens
# ---------------------------------------------------------------------------

def parse_markdown(md_text: str) -> list:
    """
    Parse markdown into a flat list of tokens.
    Each token is a dict with 'type' and relevant fields.
    """
    tokens = []
    lines = md_text.splitlines()
    i = 0
    in_code_block = False
    code_lines = []
    code_lang = ""

    while i < len(lines):
        line = lines[i]

        # Fenced code block
        if line.strip().startswith("```"):
            if not in_code_block:
                in_code_block = True
                code_lang = line.strip()[3:].strip()
                code_lines = []
            else:
                in_code_block = False
                tokens.append({"type": "code_block", "lang": code_lang,
                                "text": "\n".join(code_lines)})
                code_lines = []
                code_lang = ""
            i += 1
            continue

        if in_code_block:
            code_lines.append(line)
            i += 1
            continue

        # Blank line
        if not line.strip():
            tokens.append({"type": "blank"})
            i += 1
            continue

        # Headings
        m = re.match(r'^(#{1,6})\s+(.*)', line)
        if m:
            level = len(m.group(1))
            tokens.append({"type": f"h{level}", "text": m.group(2).strip()})
            i += 1
            continue

        # Horizontal rule
        if re.match(r'^[-*_]{3,}\s*$', line.strip()):
            tokens.append({"type": "hr"})
            i += 1
            continue

        # Blockquote
        if line.startswith(">"):
            text = re.sub(r'^>\s?', '', line)
            tokens.append({"type": "blockquote", "text": text})
            i += 1
            continue

        # Unordered list item
        m = re.match(r'^(\s*)[-*+]\s+(.*)', line)
        if m:
            indent = len(m.group(1)) // 2
            tokens.append({"type": "bullet", "text": m.group(2), "indent": indent})
            i += 1
            continue

        # Ordered list item
        m = re.match(r'^(\s*)\d+\.\s+(.*)', line)
        if m:
            indent = len(m.group(1)) // 2
            tokens.append({"type": "ordered", "text": m.group(2), "indent": indent})
            i += 1
            continue

        # Table — collect all consecutive table lines
        if "|" in line:
            table_lines = []
            while i < len(lines) and "|" in lines[i]:
                table_lines.append(lines[i])
                i += 1
            tokens.append({"type": "table", "lines": table_lines})
            continue

        # Paragraph
        tokens.append({"type": "para", "text": line.strip()})
        i += 1

    return tokens


# ---------------------------------------------------------------------------
# Flowable builder
# ---------------------------------------------------------------------------

def tokens_to_flowables(tokens: list, styles: dict, theme_colors: dict,
                         font_name: str) -> list:
    """Convert parsed tokens into ReportLab Flowable objects."""
    flowables = []
    accent = theme_colors["accent"]
    ordered_counters = {}  # indent -> count

    for tok in tokens:
        t = tok["type"]

        if t == "blank":
            flowables.append(Spacer(1, 4))

        elif t in ("h1", "h2", "h3", "h4"):
            level = int(t[1])
            xml = inline_to_xml(tok["text"], font_name)
            flowables.append(Paragraph(xml, styles[t]))
            if level <= 2:
                flowables.append(HRFlowable(width="100%", thickness=1,
                                            color=accent, spaceAfter=4))

        elif t == "para":
            xml = inline_to_xml(tok["text"], font_name)
            flowables.append(Paragraph(xml, styles["body"]))

        elif t == "bullet":
            indent = tok.get("indent", 0)
            xml = inline_to_xml(tok["text"], font_name)
            style = ParagraphStyle(
                f"bullet_{indent}",
                parent=styles["bullet"],
                leftIndent=18 + indent * 16,
                bulletIndent=6 + indent * 16,
            )
            flowables.append(Paragraph(f"\u2022 {xml}", style))

        elif t == "ordered":
            indent = tok.get("indent", 0)
            ordered_counters[indent] = ordered_counters.get(indent, 0) + 1
            # reset deeper levels
            for k in list(ordered_counters):
                if k > indent:
                    ordered_counters[k] = 0
            num = ordered_counters[indent]
            xml = inline_to_xml(tok["text"], font_name)
            style = ParagraphStyle(
                f"ordered_{indent}",
                parent=styles["bullet"],
                leftIndent=18 + indent * 16,
                bulletIndent=6 + indent * 16,
            )
            flowables.append(Paragraph(f"{num}. {xml}", style))

        elif t == "blockquote":
            xml = inline_to_xml(tok["text"], font_name)
            flowables.append(Paragraph(xml, styles["blockquote"]))

        elif t == "code_block":
            # Preformatted preserves whitespace and line breaks without XML processing
            flowables.append(Preformatted(tok["text"], styles["code_block"]))

        elif t == "hr":
            flowables.append(HRFlowable(width="100%", thickness=1,
                                        color=theme_colors["muted"], spaceAfter=6))

        elif t == "table":
            tbl = _build_table(tok["lines"], styles, theme_colors, font_name)
            if tbl:
                flowables.append(tbl)

    return flowables


def _build_table(lines: list, styles: dict, theme_colors: dict, font_name: str):
    """Parse GFM table lines into a ReportLab Table."""
    rows = []
    for line in lines:
        # Skip separator rows (---|---)
        if re.match(r'^[\s|:\-]+$', line):
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        rows.append(cells)

    if not rows:
        return None

    # Build Paragraph cells
    table_data = []
    for r_idx, row in enumerate(rows):
        cell_row = []
        for cell in row:
            xml = inline_to_xml(cell, font_name)
            style = styles["table_header"] if r_idx == 0 else styles["table_cell"]
            cell_row.append(Paragraph(xml, style))
        table_data.append(cell_row)

    accent = theme_colors["accent"]
    tbl = Table(table_data, repeatRows=1, hAlign="LEFT")
    tbl.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), accent),
        ("TEXTCOLOR",  (0, 0), (-1, 0), colors.white),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1),
         [colors.Color(0.97, 0.97, 0.97), colors.white]),
        ("GRID",       (0, 0), (-1, -1), 0.5, colors.Color(0.8, 0.8, 0.8)),
        ("TOPPADDING",    (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING",   (0, 0), (-1, -1), 6),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 6),
    ]))
    return tbl


# ---------------------------------------------------------------------------
# Cover page
# ---------------------------------------------------------------------------

def build_cover(style_data: dict, styles: dict, first_h1: str) -> list:
    """Return flowables for a cover page."""
    flowables = []
    flowables.append(Spacer(1, 6 * cm))

    title = style_data.get("cover_title") or first_h1 or "Document"
    flowables.append(Paragraph(title, styles["cover_title"]))

    subtitle = style_data.get("cover_subtitle", "")
    if subtitle:
        flowables.append(Paragraph(subtitle, styles["cover_subtitle"]))

    meta = style_data.get("cover_meta", "")
    if meta:
        flowables.append(Spacer(1, 1 * cm))
        flowables.append(Paragraph(meta, styles["cover_meta"]))

    flowables.append(PageBreak())
    return flowables


# ---------------------------------------------------------------------------
# Header / footer
# ---------------------------------------------------------------------------

class HeaderFooterCanvas:
    """Mixin-style page template with header and footer."""

    def __init__(self, doc, style_data: dict, theme_colors: dict, font_name: str,
                 title: str):
        self.doc = doc
        self.style_data = style_data
        self.theme_colors = theme_colors
        self.font_name = font_name
        self.title = title

    def on_page(self, canvas, doc):
        canvas.saveState()
        w, h = doc.pagesize
        accent = self.theme_colors["accent"]
        muted  = self.theme_colors["muted"]

        if self.style_data.get("header", True):
            canvas.setStrokeColor(accent)
            canvas.setLineWidth(0.5)
            canvas.line(doc.leftMargin, h - doc.topMargin + 10,
                        w - doc.rightMargin, h - doc.topMargin + 10)
            canvas.setFont(self.font_name, 9)
            canvas.setFillColor(muted)
            canvas.drawString(doc.leftMargin, h - doc.topMargin + 14, self.title)

        if self.style_data.get("footer", True):
            canvas.setStrokeColor(accent)
            canvas.setLineWidth(0.5)
            canvas.line(doc.leftMargin, doc.bottomMargin - 10,
                        w - doc.rightMargin, doc.bottomMargin - 10)
            if self.style_data.get("footer_page_number", True):
                canvas.setFont(self.font_name, 9)
                canvas.setFillColor(muted)
                page_str = str(doc.page)
                canvas.drawRightString(w - doc.rightMargin, doc.bottomMargin - 20,
                                       page_str)

        canvas.restoreState()


# ---------------------------------------------------------------------------
# Main conversion function
# ---------------------------------------------------------------------------

def convert(input_path: str, output_path: str, font_path: str,
            theme_name: str = "navy", style_path: str = None,
            custom_accent: str = None, custom_dark: str = None,
            custom_muted: str = None, no_cover: bool = False) -> str:
    """
    Convert a Markdown file to PDF.
    Returns the output path.
    """
    # Load style config
    style_data = {}
    if style_path and Path(style_path).exists():
        with open(style_path, "r", encoding="utf-8") as f:
            style_data = yaml.safe_load(f) or {}

    # CLI custom colors override style file values
    if custom_accent:
        style_data["custom_accent"] = custom_accent
    if custom_dark:
        style_data["custom_dark"] = custom_dark
    if custom_muted:
        style_data["custom_muted"] = custom_muted

    # Register font
    font_name = register_font(font_path, "CustomFont")

    # Resolve theme
    theme_colors = resolve_theme(theme_name, style_data)

    # Build styles
    styles = build_styles(font_name, theme_colors)

    # Read markdown
    try:
        with open(input_path, "r", encoding="utf-8") as f:
            md_text = f.read()
    except FileNotFoundError:
        print(f"错误：找不到文件 / Error: file not found: {input_path}")
        sys.exit(1)
    except PermissionError:
        print(f"错误：无法读取文件 / Error: cannot read file: {input_path}")
        sys.exit(1)

    # Parse
    tokens = parse_markdown(md_text)

    # Find first H1 for cover/header
    first_h1 = ""
    for tok in tokens:
        if tok["type"] == "h1":
            first_h1 = tok["text"]
            break

    # Page setup
    page_size_name = style_data.get("page_size", "A4").upper()
    page_size = LETTER if page_size_name == "LETTER" else A4
    margin = float(style_data.get("margin_cm", 2.5)) * cm

    doc = SimpleDocTemplate(
        output_path,
        pagesize=page_size,
        leftMargin=margin, rightMargin=margin,
        topMargin=margin, bottomMargin=margin,
    )

    # Header/footer handler
    hf = HeaderFooterCanvas(doc, style_data, theme_colors, font_name, first_h1)

    # Build flowables
    story = []

    if not no_cover and style_data.get("cover", True):
        story.extend(build_cover(style_data, styles, first_h1))

    story.extend(tokens_to_flowables(tokens, styles, theme_colors, font_name))

    doc.build(story, onFirstPage=hf.on_page, onLaterPages=hf.on_page)
    return output_path


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Convert Markdown to PDF with theme support and Chinese fonts."
    )
    parser.add_argument("--print-themes", action="store_true",
                        help="Print ANSI theme selector and exit")
    parser.add_argument("--input",  help="Input .md file path")
    parser.add_argument("--output", help="Output .pdf file path")
    parser.add_argument("--font",   help="Path to TTF/OTF/TTC font file")
    parser.add_argument("--theme",  default="navy",
                        help="Theme name (navy|forest|minimal|warm|coral|slate|"
                             "purple|teal|gold|rose|midnight|olive|custom)")
    parser.add_argument("--style",  default=None, help="Path to pdf_style.yaml")
    parser.add_argument("--accent", default=None,
                        help="Custom accent color hex (e.g. #FF0000), used when --theme custom")
    parser.add_argument("--dark",   default=None,
                        help="Custom dark color hex (e.g. #000000), used when --theme custom")
    parser.add_argument("--muted",  default=None,
                        help="Custom muted color hex (e.g. #999999), used when --theme custom")
    parser.add_argument("--no-cover", action="store_true",
                        help="Skip cover page even if cover: true in yaml")
    args = parser.parse_args()

    if args.print_themes:
        print_theme_selector()
        sys.exit(0)

    if not args.input or not args.output or not args.font:
        parser.error("--input, --output, and --font are required for conversion")

    out = convert(
        input_path=args.input,
        output_path=args.output,
        font_path=args.font,
        theme_name=args.theme,
        style_path=args.style,
        custom_accent=args.accent,
        custom_dark=args.dark,
        custom_muted=args.muted,
        no_cover=args.no_cover,
    )
    size_kb = Path(out).stat().st_size // 1024
    print(f"完成 / Done: {out} ({size_kb} KB)")


if __name__ == "__main__":
    main()
