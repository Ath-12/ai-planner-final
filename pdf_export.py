"""Turn a NomadSquad plan (Markdown text) into a clean, readable PDF.

Uses fpdf2 with the bundled DejaVu Sans font, so the rupee sign, accented
letters and dashes print correctly. Characters the font cannot draw
(colour emoji) are removed instead of showing up as empty boxes.
"""
from datetime import date
from pathlib import Path
import re

from fontTools.ttLib import TTFont
from fpdf import FPDF

FONT_DIR = Path(__file__).parent / "fonts"
REGULAR = FONT_DIR / "DejaVuSans.ttf"
BOLD = FONT_DIR / "DejaVuSans-Bold.ttf"

# Every character the font can draw. Anything else (e.g. colour emoji) is dropped.
# Emoji "joiners" and "variation selectors" are invisible helpers for emoji, so
# they are removed too, otherwise they leave stray marks.
_INVISIBLE = {0xFE0E, 0xFE0F, 0x200D}
_SUPPORTED = set(TTFont(str(REGULAR)).getBestCmap().keys()) - _INVISIBLE

ACCENT = (255, 99, 71)   # NomadSquad tomato orange
INK = (30, 30, 30)
MUTED = (110, 110, 110)


def clean_text(text: str) -> str:
    """Drop characters the font lacks and tidy the spaces they leave behind."""
    kept = "".join(ch for ch in text if ord(ch) in _SUPPORTED or ch in "\n\t")
    kept = re.sub(r"[ \t]{2,}", " ", kept)
    kept = re.sub(r" +([.,!?;:])", r"\1", kept)   # "sunset 🌅." -> "sunset."
    return "\n".join(line.strip() for line in kept.splitlines())


def _inline(text: str) -> str:
    """Prepare a line for fpdf2's mini-markdown: keep **bold**, neutralise the
    other markers (__ = italic, -- = underline) so normal text isn't mangled."""
    text = text.replace("--", "–").replace("__", "")
    # *single-star italics* aren't supported by the PDF font setup: keep the words.
    text = re.sub(r"(?<!\*)\*(?!\*)([^*\n]+?)(?<!\*)\*(?!\*)", r"\1", text)
    # A lone or unbalanced ** would make the rest of the line bold: drop it.
    if text.count("**") % 2:
        text = text.replace("**", "")
    return text


class _PlanPDF(FPDF):
    def footer(self):
        self.set_y(-12)
        self.set_font("DejaVu", size=8)
        self.set_text_color(*MUTED)
        self.cell(0, 6, f"NomadSquad · page {self.page_no()}/{{nb}}", align="C")


def build_pdf_bytes(markdown_text: str, title: str = "NomadSquad Itinerary") -> bytes:
    pdf = _PlanPDF(format="A4")
    pdf.add_font("DejaVu", "", str(REGULAR))
    pdf.add_font("DejaVu", "B", str(BOLD))
    pdf.set_margins(18, 18, 18)
    pdf.set_auto_page_break(auto=True, margin=18)
    pdf.add_page()

    # Title block
    pdf.set_font("DejaVu", "B", 20)
    pdf.set_text_color(*ACCENT)
    pdf.multi_cell(0, 10, clean_text(title), new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("DejaVu", size=9)
    pdf.set_text_color(*MUTED)
    pdf.cell(0, 6, f"Generated on {date.today():%d %b %Y}", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(4)

    for raw in clean_text(markdown_text).splitlines():
        line = raw.strip()
        if not line:
            pdf.ln(2)
            continue

        if re.fullmatch(r"[-*_]{3,}", line):                      # horizontal rule
            y = pdf.get_y() + 2
            pdf.set_draw_color(220, 220, 220)
            pdf.line(pdf.l_margin, y, pdf.w - pdf.r_margin, y)
            pdf.ln(5)
            continue

        heading = re.match(r"^(#{1,6})\s*(.+)$", line)
        if heading:
            level = len(heading.group(1))
            pdf.ln(3)
            pdf.set_font("DejaVu", "B", 15 if level <= 3 else 12)
            pdf.set_text_color(*(ACCENT if level <= 3 else INK))
            pdf.multi_cell(0, 8, heading.group(2).replace("**", ""), new_x="LMARGIN", new_y="NEXT")
            pdf.ln(1)
            continue

        pdf.set_font("DejaVu", size=10.5)
        pdf.set_text_color(*INK)
        bullet = re.match(r"^[-*+]\s+(.*)$", line)
        if bullet:
            pdf.set_x(pdf.l_margin + 4)
            pdf.multi_cell(0, 5.8, "•  " + _inline(bullet.group(1)), markdown=True,
                           new_x="LMARGIN", new_y="NEXT")
        else:
            pdf.multi_cell(0, 5.8, _inline(line), markdown=True, new_x="LMARGIN", new_y="NEXT")

    return bytes(pdf.output())
