#!/usr/bin/env python3

from __future__ import annotations

import argparse
import html
import re
import sys
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import LETTER
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.platypus import (
    ListFlowable,
    ListItem,
    Paragraph,
    Preformatted,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


PAGE_MARGIN = 0.7 * inch
PAGE_CONTENT_WIDTH = LETTER[0] - (PAGE_MARGIN * 2)
SECTION_INDENTS = {
    0: 0,
    2: 0,
    3: 16,
    4: 30,
}


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate a PDF document from a Markdown file."
    )
    parser.add_argument("markdown_file", help="Path to the Markdown file")
    parser.add_argument(
        "-o",
        "--output",
        help="Output PDF file path (default: same name as input with .pdf extension)",
    )
    return parser.parse_args(argv)


def slugify_heading(heading: str) -> str:
    slug = heading.strip().lower()
    allowed: list[str] = []
    for char in slug:
        if char.isalnum() or char in {" ", "-"}:
            allowed.append(char)
    return "".join(allowed).replace(" ", "-")


def convert_markdown_links(text: str) -> str:
    def replace_link(match: re.Match[str]) -> str:
        label = html.escape(match.group(1))
        target = match.group(2).strip()
        href = f"#{target[1:]}" if target.startswith("#") else html.escape(target, quote=True)
        return f"<link href='{href}' color='blue'>{label}</link>"

    return re.sub(r"\[([^\]]+)\]\(([^)]+)\)", replace_link, text)


def convert_inline_markdown(text: str) -> str:
    escaped = convert_markdown_links(text)
    escaped = re.sub(r"(?<!<)\*\*(.+?)\*\*", r"<b>\1</b>", escaped)
    escaped = re.sub(r"(?<!<)`(.+?)`", r"<font name='Courier'>\1</font>", escaped)
    return escaped


def text_width(text: str, font_name: str = "Helvetica", font_size: int = 9) -> float:
    sanitized = re.sub(r"<[^>]+>", "", text).replace("<br/>", " ")
    return stringWidth(sanitized, font_name, font_size)


def longest_token_width(text: str, font_name: str = "Helvetica", font_size: int = 9) -> float:
    sanitized = re.sub(r"<[^>]+>", "", text).replace("<br/>", " ")
    tokens = [token for token in re.split(r"\s+", sanitized) if token]
    if not tokens:
        return 0
    return max(stringWidth(token, font_name, font_size) for token in tokens)


def is_table_line(line: str) -> bool:
    stripped = line.strip()
    return stripped.startswith("|") and stripped.endswith("|")


def is_separator_row(line: str) -> bool:
    cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
    return bool(cells) and all(cell and set(cell) <= {"-", ":"} for cell in cells)


def parse_table(lines: list[str]) -> list[list[str]]:
    rows: list[list[str]] = []
    for line in lines:
        if is_separator_row(line):
            continue
        rows.append([cell.strip() for cell in line.strip().strip("|").split("|")])
    return rows


def collect_paragraph(lines: list[str], start_index: int) -> tuple[list[str], int]:
    collected: list[str] = []
    index = start_index

    while index < len(lines):
        line = lines[index]
        stripped = line.strip()
        if (
            not stripped
            or stripped.startswith("#")
            or stripped.startswith("```")
            or stripped.startswith(("- ", "* "))
            or is_table_line(line)
        ):
            break
        collected.append(stripped)
        index += 1

    return collected, index


def collect_bullets(lines: list[str], start_index: int) -> tuple[list[str], int]:
    collected: list[str] = []
    index = start_index

    while index < len(lines):
        stripped = lines[index].strip()
        if stripped.startswith(("- ", "* ")):
            collected.append(stripped[2:].strip())
            index += 1
            continue
        break

    return collected, index


def collect_table(lines: list[str], start_index: int) -> tuple[list[str], int]:
    collected: list[str] = []
    index = start_index

    while index < len(lines) and is_table_line(lines[index]):
        collected.append(lines[index])
        index += 1

    return collected, index


def collect_code_block(lines: list[str], start_index: int) -> tuple[list[str], int]:
    collected: list[str] = []
    index = start_index + 1

    while index < len(lines):
        stripped = lines[index].strip()
        if stripped.startswith("```"):
            return collected, index + 1
        collected.append(lines[index].rstrip())
        index += 1

    return collected, index


def build_styles() -> dict[str, ParagraphStyle]:
    stylesheet = getSampleStyleSheet()
    return {
        "title": ParagraphStyle(
            "TitleCustom",
            parent=stylesheet["Title"],
            fontName="Helvetica-Bold",
            fontSize=20,
            leading=24,
            spaceAfter=14,
            textColor=colors.HexColor("#1f2937"),
        ),
        "h2": ParagraphStyle(
            "Heading2Custom",
            parent=stylesheet["Heading2"],
            fontName="Helvetica-Bold",
            fontSize=15,
            leading=19,
            spaceBefore=10,
            spaceAfter=8,
            textColor=colors.HexColor("#111827"),
        ),
        "h3": ParagraphStyle(
            "Heading3Custom",
            parent=stylesheet["Heading3"],
            fontName="Helvetica-Bold",
            fontSize=12,
            leading=15,
            spaceBefore=8,
            spaceAfter=6,
            leftIndent=SECTION_INDENTS[3],
            textColor=colors.HexColor("#111827"),
        ),
        "h4": ParagraphStyle(
            "Heading4Custom",
            parent=stylesheet["Heading4"],
            fontName="Helvetica-Bold",
            fontSize=11,
            leading=14,
            spaceBefore=6,
            spaceAfter=4,
            leftIndent=SECTION_INDENTS[4],
            textColor=colors.HexColor("#111827"),
        ),
        "body": ParagraphStyle(
            "BodyCustom",
            parent=stylesheet["BodyText"],
            fontName="Helvetica",
            fontSize=10,
            leading=14,
            spaceAfter=8,
            allowWidows=1,
            allowOrphans=1,
            wordWrap="LTR",
            textColor=colors.HexColor("#1f2937"),
        ),
        "code": ParagraphStyle(
            "CodeLabel",
            parent=stylesheet["BodyText"],
            fontName="Helvetica-Bold",
            fontSize=9,
            leading=11,
            spaceBefore=4,
            spaceAfter=4,
            textColor=colors.HexColor("#374151"),
        ),
    }


def build_indented_style(style: ParagraphStyle, left_indent: int) -> ParagraphStyle:
    return ParagraphStyle(
        f"{style.name}Indented{left_indent}",
        parent=style,
        leftIndent=left_indent,
        firstLineIndent=0,
    )


def build_heading_paragraph(text: str, style: ParagraphStyle, anchor_name: str) -> Paragraph:
    return Paragraph(f"<a name='{anchor_name}'/>{convert_inline_markdown(text)}", style)


def build_body_paragraph(text: str, style: ParagraphStyle, left_indent: int = 0) -> Paragraph:
    return Paragraph(convert_inline_markdown(text), build_indented_style(style, left_indent))


def table_cell_paragraph(text: str, style: ParagraphStyle) -> Paragraph:
    return Paragraph(convert_inline_markdown(text.replace("<br>", "<br/>")), style)


def compute_table_col_widths(rows: list[list[str]], available_width: float) -> list[float]:
    column_count = max(len(row) for row in rows)
    normalized_rows = [row + [""] * (column_count - len(row)) for row in rows]

    preferred: list[float] = []
    minimum: list[float] = []
    for column_index in range(column_count):
        column_cells = [row[column_index] for row in normalized_rows]
        preferred_width = max(text_width(cell) for cell in column_cells) + 16
        token_width = max(longest_token_width(cell) for cell in column_cells) + 18
        minimum_width = min(max(preferred_width * 0.4, token_width, 68), 170)
        preferred.append(preferred_width)
        minimum.append(minimum_width)

    total_preferred = sum(preferred)
    if total_preferred <= available_width:
        preferred[-1] += available_width - total_preferred
        return preferred

    scale = available_width / total_preferred
    widths = [max(width * scale, minimum[index]) for index, width in enumerate(preferred)]
    total_width = sum(widths)

    while total_width > available_width + 0.5:
        adjustable = [index for index, width in enumerate(widths) if width - minimum[index] > 1]
        if not adjustable:
            break
        overflow = total_width - available_width
        reduction = overflow / len(adjustable)
        for index in adjustable:
            widths[index] = max(minimum[index], widths[index] - reduction)
        total_width = sum(widths)

    if total_width < available_width:
        widths[-1] += available_width - total_width

    return widths


def build_table(rows: list[list[str]], body_style: ParagraphStyle, left_indent: int = 0) -> Table:
    column_count = max(len(row) for row in rows)
    normalized_rows = [row + [""] * (column_count - len(row)) for row in rows]
    paragraph_rows = [[table_cell_paragraph(cell, body_style) for cell in row] for row in normalized_rows]
    available_width = PAGE_CONTENT_WIDTH - left_indent
    col_widths = compute_table_col_widths(normalized_rows, available_width)
    table = Table(paragraph_rows, repeatRows=1, hAlign="LEFT", colWidths=col_widths)
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e5e7eb")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#111827")),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8fafc")]),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                ("LEFTPADDING", (0, 0), (0, -1), 6 + min(left_indent, 10)),
            ]
        )
    )
    return table


def section_indent_for_level(level: int) -> int:
    return SECTION_INDENTS.get(level, 0)


def build_markdown_flowables(markdown_text: str) -> list[object]:
    lines = markdown_text.splitlines()
    styles = build_styles()
    flowables: list[object] = []
    index = 0
    current_section_level = 2

    while index < len(lines):
        raw_line = lines[index]
        stripped = raw_line.strip()

        if not stripped:
            flowables.append(Spacer(1, 0.08 * inch))
            index += 1
            continue

        if stripped.startswith("# "):
            current_section_level = 0
            heading_text = stripped[2:].strip()
            flowables.append(build_heading_paragraph(heading_text, styles["title"], slugify_heading(heading_text)))
            index += 1
            continue

        if stripped.startswith("## "):
            current_section_level = 2
            heading_text = stripped[3:].strip()
            flowables.append(build_heading_paragraph(heading_text, styles["h2"], slugify_heading(heading_text)))
            index += 1
            continue

        if stripped.startswith("### "):
            current_section_level = 3
            heading_text = stripped[4:].strip()
            flowables.append(build_heading_paragraph(heading_text, styles["h3"], slugify_heading(heading_text)))
            index += 1
            continue

        if stripped.startswith("#### "):
            current_section_level = 4
            heading_text = stripped[5:].strip()
            flowables.append(build_heading_paragraph(heading_text, styles["h4"], slugify_heading(heading_text)))
            index += 1
            continue

        if stripped.startswith("```"):
            code_lines, index = collect_code_block(lines, index)
            code_indent = section_indent_for_level(current_section_level)
            flowables.append(build_body_paragraph("Code Block", styles["code"], code_indent))
            flowables.append(
                Preformatted(
                    "\n".join(code_lines),
                    ParagraphStyle(
                        f"CodeBlock{code_indent}",
                        fontName="Courier",
                        fontSize=8.5,
                        leading=10,
                        leftIndent=10 + code_indent,
                        rightIndent=10,
                        borderWidth=0.5,
                        borderColor=colors.HexColor("#d1d5db"),
                        borderPadding=8,
                        backColor=colors.HexColor("#f3f4f6"),
                        spaceAfter=10,
                    ),
                )
            )
            continue

        if is_table_line(raw_line):
            table_lines, index = collect_table(lines, index)
            table_rows = parse_table(table_lines)
            flowables.append(build_table(table_rows, styles["body"], section_indent_for_level(current_section_level)))
            flowables.append(Spacer(1, 0.12 * inch))
            continue

        if stripped.startswith(("- ", "* ")):
            bullet_lines, index = collect_bullets(lines, index)
            bullet_items = [ListItem(build_body_paragraph(item, styles["body"])) for item in bullet_lines]
            flowables.append(
                ListFlowable(
                    bullet_items,
                    bulletType="bullet",
                    leftIndent=18 + section_indent_for_level(current_section_level),
                    bulletFontName="Helvetica",
                    bulletFontSize=10,
                )
            )
            flowables.append(Spacer(1, 0.08 * inch))
            continue

        paragraph_lines, index = collect_paragraph(lines, index)
        paragraph_text = " ".join(paragraph_lines)
        flowables.append(build_body_paragraph(paragraph_text, styles["body"], section_indent_for_level(current_section_level)))

    return flowables


def render_markdown_to_pdf(markdown_text: str, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    document = SimpleDocTemplate(
        str(output_path),
        pagesize=LETTER,
        leftMargin=PAGE_MARGIN,
        rightMargin=PAGE_MARGIN,
        topMargin=PAGE_MARGIN,
        bottomMargin=PAGE_MARGIN,
        title=output_path.stem,
    )
    document.build(build_markdown_flowables(markdown_text))


def default_output_path(input_path: Path) -> Path:
    if input_path.parent.name == "md" and input_path.parent.parent.exists():
        demo_root = input_path.parent.parent
        return demo_root / "pdf" / f"{input_path.stem}.pdf"
    return input_path.with_suffix(".pdf")


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    input_path = Path(args.markdown_file)
    output_path = Path(args.output) if args.output else default_output_path(input_path)

    try:
        markdown_text = input_path.read_text(encoding="utf-8")
        render_markdown_to_pdf(markdown_text, output_path)
        print(f"PDF generated successfully: {output_path}")
        return 0
    except FileNotFoundError:
        print(f"Error: Markdown file '{input_path}' not found.", file=sys.stderr)
    except Exception as error:  # pragma: no cover
        print(f"Error: {error}", file=sys.stderr)

    return 1
