#!/usr/bin/env python3
"""Render a repository report README.md to a readable Chinese PDF."""

from __future__ import annotations

import argparse
import html
import re
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
from reportlab.platypus import (
    BaseDocTemplate,
    Frame,
    HRFlowable,
    Image,
    KeepTogether,
    ListFlowable,
    ListItem,
    PageBreak,
    PageTemplate,
    Paragraph,
    Preformatted,
    Spacer,
    Table,
    TableStyle,
)


FONT = "STSong-Light"
pdfmetrics.registerFont(UnicodeCIDFont(FONT))


def inline_markup(text: str) -> str:
    links: list[tuple[str, str]] = []

    def stash_link(match: re.Match[str]) -> str:
        links.append((match.group(1), match.group(2)))
        return f"@@LINK{len(links) - 1}@@"

    text = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", stash_link, text)
    text = html.escape(text, quote=False)
    text = re.sub(r"\*\*([^*]+)\*\*", r"<b>\1</b>", text)
    text = re.sub(r"`([^`]+)`", r"<font color='#425466'>\1</font>", text)
    for index, (label, url) in enumerate(links):
        safe_label = html.escape(label, quote=False)
        safe_url = html.escape(url, quote=True)
        text = text.replace(f"@@LINK{index}@@", f'<a href="{safe_url}" color="#1769aa">{safe_label}</a>')
    return text


def split_table_row(line: str) -> list[str]:
    line = line.strip().strip("|")
    cells = re.split(r"(?<!\\)\|", line)
    return [cell.strip().replace("\\|", "|") for cell in cells]


def build_styles():
    base = getSampleStyleSheet()
    return {
        "title": ParagraphStyle(
            "TitleCN", parent=base["Title"], fontName=FONT, fontSize=24,
            leading=34, textColor=colors.HexColor("#172B4D"), alignment=TA_CENTER,
            spaceAfter=12 * mm,
        ),
        "h1": ParagraphStyle(
            "H1CN", parent=base["Heading1"], fontName=FONT, fontSize=18,
            leading=25, textColor=colors.HexColor("#172B4D"), spaceBefore=6 * mm,
            spaceAfter=4 * mm,
        ),
        "h2": ParagraphStyle(
            "H2CN", parent=base["Heading2"], fontName=FONT, fontSize=15,
            leading=22, textColor=colors.HexColor("#234E70"), spaceBefore=5 * mm,
            spaceAfter=3 * mm,
        ),
        "h3": ParagraphStyle(
            "H3CN", parent=base["Heading3"], fontName=FONT, fontSize=12.5,
            leading=19, textColor=colors.HexColor("#315B7D"), spaceBefore=4 * mm,
            spaceAfter=2 * mm,
        ),
        "body": ParagraphStyle(
            "BodyCN", parent=base["BodyText"], fontName=FONT, fontSize=9.5,
            leading=16, textColor=colors.HexColor("#263238"), alignment=TA_JUSTIFY,
            spaceAfter=2.2 * mm, wordWrap="CJK",
        ),
        "small": ParagraphStyle(
            "SmallCN", parent=base["BodyText"], fontName=FONT, fontSize=7.2,
            leading=11, textColor=colors.HexColor("#263238"), wordWrap="CJK",
        ),
        "quote": ParagraphStyle(
            "QuoteCN", parent=base["BodyText"], fontName=FONT, fontSize=9.3,
            leading=15, textColor=colors.HexColor("#334E68"), leftIndent=4 * mm,
            rightIndent=3 * mm, spaceAfter=1 * mm, wordWrap="CJK",
        ),
        "code": ParagraphStyle(
            "CodeCN", parent=base["Code"], fontName=FONT, fontSize=7.2,
            leading=10, textColor=colors.HexColor("#263238"), leftIndent=2 * mm,
        ),
    }


def make_table(lines: list[str], styles, width: float):
    rows = [split_table_row(line) for line in lines]
    if len(rows) > 1 and all(re.fullmatch(r":?-{3,}:?", c.replace(" ", "")) for c in rows[1]):
        rows.pop(1)
    columns = max(len(row) for row in rows)
    rows = [row + [""] * (columns - len(row)) for row in rows]
    data = [[Paragraph(inline_markup(cell).replace("&lt;br&gt;", "<br/>"), styles["small"]) for cell in row] for row in rows]
    table = Table(data, colWidths=[width / columns] * columns, repeatRows=1, hAlign="LEFT")
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#DDEBF4")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#172B4D")),
        ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#9FB3C8")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F7FAFC")]),
    ]))
    return table


def markdown_to_flowables(path: Path, styles, content_width: float):
    lines = path.read_text(encoding="utf-8").splitlines()
    if lines and lines[0].strip() == "---":
        for index in range(1, len(lines)):
            if lines[index].strip() == "---":
                lines = lines[index + 1:]
                break

    story = []
    paragraph_buffer: list[str] = []

    def flush_paragraph():
        if paragraph_buffer:
            text = " ".join(line.strip() for line in paragraph_buffer)
            story.append(Paragraph(inline_markup(text), styles["body"]))
            paragraph_buffer.clear()

    i = 0
    seen_title = False
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()
        if not stripped:
            flush_paragraph()
            i += 1
            continue
        if stripped.startswith("```"):
            flush_paragraph()
            code = []
            i += 1
            while i < len(lines) and not lines[i].strip().startswith("```"):
                code.append(lines[i])
                i += 1
            story.append(Table([[Preformatted("\n".join(code), styles["code"]) ]], colWidths=[content_width], style=[
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F3F6F8")),
                ("BOX", (0, 0), (-1, -1), 0.4, colors.HexColor("#CBD5E0")),
                ("LEFTPADDING", (0, 0), (-1, -1), 5),
                ("RIGHTPADDING", (0, 0), (-1, -1), 5),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ]))
            story.append(Spacer(1, 2 * mm))
            i += 1
            continue
        if stripped.startswith("|") and "|" in stripped[1:]:
            flush_paragraph()
            table_lines = []
            while i < len(lines) and lines[i].strip().startswith("|"):
                table_lines.append(lines[i])
                i += 1
            story.extend([make_table(table_lines, styles, content_width), Spacer(1, 3 * mm)])
            continue
        image_match = re.fullmatch(r"!\[([^\]]*)\]\(([^)]+)\)", stripped)
        if image_match:
            flush_paragraph()
            image_path = (path.parent / image_match.group(2)).resolve()
            if image_path.exists():
                img = Image(str(image_path))
                scale = min(content_width / img.imageWidth, 90 * mm / img.imageHeight, 1)
                img.drawWidth = img.imageWidth * scale
                img.drawHeight = img.imageHeight * scale
                story.append(KeepTogether([img, Paragraph(inline_markup(image_match.group(1)), styles["small"])]))
                story.append(Spacer(1, 3 * mm))
            i += 1
            continue
        heading = re.match(r"^(#{1,6})\s+(.+)$", stripped)
        if heading:
            flush_paragraph()
            level = len(heading.group(1))
            text = heading.group(2)
            if not seen_title:
                story.append(Paragraph(inline_markup(text), styles["title"]))
                seen_title = True
            elif level <= 2:
                story.extend([Spacer(1, 2 * mm), Paragraph(inline_markup(text), styles["h1"])])
            elif level == 3:
                story.append(Paragraph(inline_markup(text), styles["h2"]))
            else:
                story.append(Paragraph(inline_markup(text), styles["h3"]))
            i += 1
            continue
        if stripped == "---":
            flush_paragraph()
            story.extend([Spacer(1, 1 * mm), HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#B8C4CE")), Spacer(1, 2 * mm)])
            i += 1
            continue
        if stripped.startswith(">"):
            flush_paragraph()
            quote_lines = []
            while i < len(lines) and lines[i].strip().startswith(">"):
                quote_lines.append(lines[i].strip().lstrip(">").strip())
                i += 1
            quote = Paragraph(inline_markup("<br/>".join(quote_lines)).replace("&lt;br/&gt;", "<br/>"), styles["quote"])
            story.append(Table([[quote]], colWidths=[content_width], style=[
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#EEF5F9")),
                ("LINEBEFORE", (0, 0), (0, -1), 3, colors.HexColor("#4C8DAE")),
                ("LEFTPADDING", (0, 0), (-1, -1), 7),
                ("RIGHTPADDING", (0, 0), (-1, -1), 7),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ]))
            story.append(Spacer(1, 2 * mm))
            continue
        bullet = re.match(r"^[-*]\s+(.+)$", stripped)
        numbered = re.match(r"^\d+[.)]\s+(.+)$", stripped)
        if bullet or numbered:
            flush_paragraph()
            ordered = bool(numbered)
            items = []
            while i < len(lines):
                current = lines[i].strip()
                match = re.match(r"^\d+[.)]\s+(.+)$", current) if ordered else re.match(r"^[-*]\s+(.+)$", current)
                if not match:
                    break
                items.append(ListItem(Paragraph(inline_markup(match.group(1)), styles["body"]), leftIndent=5 * mm))
                i += 1
            story.append(ListFlowable(items, bulletType="1" if ordered else "bullet", leftIndent=6 * mm, bulletFontName=FONT, bulletFontSize=8))
            story.append(Spacer(1, 1 * mm))
            continue
        paragraph_buffer.append(line)
        i += 1

    flush_paragraph()
    return story


def render(source: Path, output: Path):
    styles = build_styles()
    page_width, page_height = A4
    left = right = 18 * mm
    top = 20 * mm
    bottom = 18 * mm
    content_width = page_width - left - right

    def decorate(canvas, doc):
        canvas.saveState()
        canvas.setFont(FONT, 7.5)
        canvas.setFillColor(colors.HexColor("#718096"))
        canvas.drawString(left, 9 * mm, "YSY Research")
        canvas.drawRightString(page_width - right, 9 * mm, f"{doc.page}")
        canvas.setStrokeColor(colors.HexColor("#D7DEE5"))
        canvas.line(left, 13 * mm, page_width - right, 13 * mm)
        canvas.restoreState()

    frame = Frame(left, bottom, content_width, page_height - top - bottom, id="normal")
    doc = BaseDocTemplate(
        str(output), pagesize=A4, leftMargin=left, rightMargin=right,
        topMargin=top, bottomMargin=bottom, title=source.parent.name,
        author="杨三月",
    )
    doc.addPageTemplates([PageTemplate(id="report", frames=[frame], onPage=decorate)])
    doc.build(markdown_to_flowables(source, styles, content_width))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    render(args.source.resolve(), args.output.resolve())


if __name__ == "__main__":
    main()
