#!/usr/bin/env python3

from __future__ import annotations

import argparse
import html
import re
import sys
from pathlib import Path
from typing import Iterable

from reportlab.lib import colors
from reportlab.lib.pagesizes import LETTER
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
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


def convert_inline_markdown(text: str) -> str:
    escaped = html.escape(text)
    escaped = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", escaped)
    escaped = re.sub(r"`(.+?)`", r"<font name='Courier'>\1</font>", escaped)
    return escaped


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
            textColor=colors.HexColor("#111827"),
        ),
        "body": ParagraphStyle(
            "BodyCustom",
            parent=stylesheet["BodyText"],
            fontName="Helvetica",
            fontSize=10,
            leading=14,
            spaceAfter=8,
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


def build_markdown_flowables(markdown_text: str) -> list[object]:
    lines = markdown_text.splitlines()
    styles = build_styles()
    flowables: list[object] = []
    index = 0

    while index < len(lines):
        raw_line = lines[index]
        stripped = raw_line.strip()

        if not stripped:
            flowables.append(Spacer(1, 0.08 * inch))
            index += 1
            continue

        if stripped.startswith("# "):
            flowables.append(Paragraph(convert_inline_markdown(stripped[2:].strip()), styles["title"]))
            index += 1
            continue

        if stripped.startswith("## "):
            flowables.append(Paragraph(convert_inline_markdown(stripped[3:].strip()), styles["h2"]))
            index += 1
            continue

        if stripped.startswith("### "):
            flowables.append(Paragraph(convert_inline_markdown(stripped[4:].strip()), styles["h3"]))
            index += 1
            continue

        if stripped.startswith("#### "):
            flowables.append(Paragraph(convert_inline_markdown(stripped[5:].strip()), styles["h4"]))
            index += 1
            continue

        if stripped.startswith("```"):
            code_lines, index = collect_code_block(lines, index)
            flowables.append(Paragraph("Code Block", styles["code"]))
            flowables.append(
                Preformatted(
                    "\n".join(code_lines),
                    ParagraphStyle(
                        "CodeBlock",
                        fontName="Courier",
                        fontSize=8.5,
                        leading=10,
                        leftIndent=10,
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
            table = Table(table_rows, repeatRows=1, hAlign="LEFT")
            table.setStyle(
                TableStyle(
                    [
                        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e5e7eb")),
                        ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#111827")),
                        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
                        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                        ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
                        ("FONTSIZE", (0, 0), (-1, -1), 9),
                        ("LEADING", (0, 0), (-1, -1), 11),
                        ("VALIGN", (0, 0), (-1, -1), "TOP"),
                        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8fafc")]),
                        ("LEFTPADDING", (0, 0), (-1, -1), 6),
                        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                        ("TOPPADDING", (0, 0), (-1, -1), 5),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                    ]
                )
            )
            flowables.append(table)
            flowables.append(Spacer(1, 0.12 * inch))
            continue

        if stripped.startswith(("- ", "* ")):
            bullet_lines, index = collect_bullets(lines, index)
            bullet_items = [
                ListItem(Paragraph(convert_inline_markdown(item), styles["body"]))
                for item in bullet_lines
            ]
            flowables.append(
                ListFlowable(
                    bullet_items,
                    bulletType="bullet",
                    leftIndent=18,
                    bulletFontName="Helvetica",
                    bulletFontSize=10,
                )
            )
            flowables.append(Spacer(1, 0.08 * inch))
            continue

        paragraph_lines, index = collect_paragraph(lines, index)
        paragraph_text = " ".join(paragraph_lines)
        flowables.append(Paragraph(convert_inline_markdown(paragraph_text), styles["body"]))

    return flowables


def render_markdown_to_pdf(markdown_text: str, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    document = SimpleDocTemplate(
        str(output_path),
        pagesize=LETTER,
        leftMargin=0.7 * inch,
        rightMargin=0.7 * inch,
        topMargin=0.7 * inch,
        bottomMargin=0.7 * inch,
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
    except Exception as error:  # pragma: no cover - last-resort CLI safeguard
        print(f"Error: {error}", file=sys.stderr)

    return 1


if __name__ == "__main__":
    raise SystemExit(main())
