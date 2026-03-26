#!/usr/bin/env python3

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from reportlab.lib.pagesizes import LETTER
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.pdfgen import canvas


PAGE_SIZE = LETTER
LEFT_MARGIN = 54
RIGHT_MARGIN = 54
TOP_MARGIN = 54
BOTTOM_MARGIN = 54
BODY_FONT = "Helvetica"
BODY_FONT_SIZE = 11
CODE_FONT = "Courier"
CODE_FONT_SIZE = 9
LINE_GAP = 4


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


def wrap_text(text: str, font_name: str, font_size: int, max_width: float) -> list[str]:
    words = text.split()
    if not words:
        return [""]

    lines: list[str] = []
    current_line = words[0]

    for word in words[1:]:
        candidate = f"{current_line} {word}"
        if stringWidth(candidate, font_name, font_size) <= max_width:
            current_line = candidate
        else:
            lines.append(current_line)
            current_line = word

    lines.append(current_line)
    return lines


def iter_markdown_lines(markdown_text: str) -> list[tuple[str, str, int]]:
    lines: list[tuple[str, str, int]] = []
    in_code_block = False

    for raw_line in markdown_text.splitlines():
        stripped = raw_line.strip()

        if stripped.startswith("```"):
            in_code_block = not in_code_block
            continue

        if in_code_block:
            lines.append((raw_line.rstrip(), CODE_FONT, CODE_FONT_SIZE))
            continue

        if not stripped:
            lines.append(("", BODY_FONT, BODY_FONT_SIZE))
            continue

        if stripped.startswith("# "):
            lines.append((stripped[2:].strip(), "Helvetica-Bold", 20))
            continue

        if stripped.startswith("## "):
            lines.append((stripped[3:].strip(), "Helvetica-Bold", 16))
            continue

        if stripped.startswith("### "):
            lines.append((stripped[4:].strip(), "Helvetica-Bold", 14))
            continue

        if stripped.startswith("#### "):
            lines.append((stripped[5:].strip(), "Helvetica-Bold", 12))
            continue

        if stripped.startswith(("- ", "* ")):
            lines.append((f"• {stripped[2:].strip()}", BODY_FONT, BODY_FONT_SIZE))
            continue

        lines.append((raw_line.rstrip(), BODY_FONT, BODY_FONT_SIZE))

    return lines


def render_markdown_to_pdf(markdown_text: str, output_path: Path) -> None:
    pdf = canvas.Canvas(str(output_path), pagesize=PAGE_SIZE)
    page_width, page_height = PAGE_SIZE
    max_width = page_width - LEFT_MARGIN - RIGHT_MARGIN
    y_position = page_height - TOP_MARGIN

    def next_line(font_size: int) -> None:
        nonlocal y_position
        y_position -= font_size + LINE_GAP
        if y_position <= BOTTOM_MARGIN:
            pdf.showPage()
            y_position = page_height - TOP_MARGIN

    for text, font_name, font_size in iter_markdown_lines(markdown_text):
        pdf.setFont(font_name, font_size)

        wrapped_lines = (
            [text]
            if font_name == CODE_FONT
            else wrap_text(text, font_name, font_size, max_width)
        )

        for wrapped_line in wrapped_lines:
            pdf.drawString(LEFT_MARGIN, y_position, wrapped_line)
            next_line(font_size)

        if text == "":
            next_line(font_size)

    pdf.save()


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    input_path = Path(args.markdown_file)
    output_path = Path(args.output) if args.output else input_path.with_suffix(".pdf")

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
