"""
pdf_styles.py
-------------
Shared ReportLab styles, colour palette and helper functions
used by every PDF-generating agent.
"""
import re
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import TableStyle


# ── Brand colours ────────────────────────────────────────────────────────────
BRAND_DARK   = colors.HexColor("#1A2E44")   # deep navy
BRAND_MID    = colors.HexColor("#2E6DA4")   # steel blue
BRAND_ACCENT = colors.HexColor("#F0A500")   # amber
BRAND_LIGHT  = colors.HexColor("#EAF2FB")   # very light blue
TEXT_BODY    = colors.HexColor("#2C3E50")


def get_styles():
    """Return a dict of ParagraphStyle objects."""
    base = getSampleStyleSheet()

    styles = {}

    styles["cover_title"] = ParagraphStyle(
        "cover_title",
        fontName="Helvetica-Bold",
        fontSize=26,
        textColor=colors.white,
        leading=32,
        spaceAfter=8,
    )
    styles["cover_sub"] = ParagraphStyle(
        "cover_sub",
        fontName="Helvetica",
        fontSize=13,
        textColor=colors.HexColor("#CBD8E8"),
        leading=18,
        spaceAfter=4,
    )
    styles["section_heading"] = ParagraphStyle(
        "section_heading",
        fontName="Helvetica-Bold",
        fontSize=13,
        textColor=BRAND_DARK,
        leading=18,
        spaceBefore=14,
        spaceAfter=6,
        borderPad=4,
    )
    styles["sub_heading"] = ParagraphStyle(
        "sub_heading",
        fontName="Helvetica-Bold",
        fontSize=11,
        textColor=BRAND_MID,
        leading=15,
        spaceBefore=8,
        spaceAfter=4,
    )
    styles["body"] = ParagraphStyle(
        "body",
        fontName="Helvetica",
        fontSize=10,
        textColor=TEXT_BODY,
        leading=15,
        spaceAfter=4,
    )
    styles["small"] = ParagraphStyle(
        "small",
        fontName="Helvetica",
        fontSize=8,
        textColor=colors.grey,
        leading=11,
    )
    styles["table_header"] = ParagraphStyle(
        "table_header",
        fontName="Helvetica-Bold",
        fontSize=9,
        textColor=colors.white,
    )
    styles["table_cell"] = ParagraphStyle(
        "table_cell",
        fontName="Helvetica",
        fontSize=9,
        textColor=TEXT_BODY,
        leading=13,
    )
    return styles


def default_table_style(header_col=BRAND_DARK):
    return TableStyle([
        # Header row
        ("BACKGROUND",    (0, 0), (-1, 0),  header_col),
        ("TEXTCOLOR",     (0, 0), (-1, 0),  colors.white),
        ("FONTNAME",      (0, 0), (-1, 0),  "Helvetica-Bold"),
        ("FONTSIZE",      (0, 0), (-1, 0),  9),
        ("BOTTOMPADDING", (0, 0), (-1, 0),  8),
        ("TOPPADDING",    (0, 0), (-1, 0),  8),
        # Data rows
        ("FONTNAME",      (0, 1), (-1, -1), "Helvetica"),
        ("FONTSIZE",      (0, 1), (-1, -1), 9),
        ("ROWBACKGROUNDS",(0, 1), (-1, -1), [colors.white, BRAND_LIGHT]),
        ("TOPPADDING",    (0, 1), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 1), (-1, -1), 5),
        ("LEFTPADDING",   (0, 0), (-1, -1), 6),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 6),
        # Grid
        ("GRID",          (0, 0), (-1, -1), 0.5, colors.HexColor("#C0CDD9")),
        ("BOX",           (0, 0), (-1, -1), 1,   BRAND_MID),
        ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
        ("ALIGN",         (0, 0), (-1, -1), "LEFT"),
    ])


def strip_markdown(text: str) -> str:
    """Remove bold/italic markers, headers, backticks from LLM text."""
    text = re.sub(r"\*{1,3}(.*?)\*{1,3}", r"\1", text)
    text = re.sub(r"#{1,6}\s?", "", text)
    text = re.sub(r"`{1,3}", "", text)
    return text.strip()


def nl2br(text: str) -> str:
    """Convert newlines to ReportLab <br/> tags."""
    return text.replace("\n", "<br/>")
