#!/usr/bin/env python3

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from markdown_to_pdf import render_markdown_to_pdf
from sow_generator import generate_sow, load_yaml


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate demo Markdown and PDF files from the demos folder structure."
    )
    parser.add_argument(
        "--yaml-dir",
        default="demos/yaml",
        help="Directory containing YAML source files (default: demos/yaml)",
    )
    parser.add_argument(
        "--md-dir",
        default="demos/md",
        help="Directory where Markdown files are written (default: demos/md)",
    )
    parser.add_argument(
        "--pdf-dir",
        default="demos/pdf",
        help="Directory where PDF files are written (default: demos/pdf)",
    )
    parser.add_argument(
        "--name",
        help="Optional demo base name to build, for example 'sample' or 'airtable-player-static'",
    )
    return parser.parse_args(argv)


def iter_yaml_files(yaml_dir: Path, demo_name: str | None) -> list[Path]:
    if demo_name:
        return [yaml_dir / f"{demo_name}.yaml"]
    return sorted(yaml_dir.glob("*.yaml"))


def build_output_name(yaml_file: Path) -> str:
    return f"{yaml_file.stem}-sow"


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    yaml_dir = Path(args.yaml_dir)
    md_dir = Path(args.md_dir)
    pdf_dir = Path(args.pdf_dir)

    try:
        yaml_files = iter_yaml_files(yaml_dir, args.name)
        if not yaml_files:
            raise FileNotFoundError(f"No YAML files found in '{yaml_dir}'.")

        md_dir.mkdir(parents=True, exist_ok=True)
        pdf_dir.mkdir(parents=True, exist_ok=True)

        for yaml_file in yaml_files:
            data = load_yaml(yaml_file)
            markdown_text = generate_sow(data)

            output_name = build_output_name(yaml_file)
            markdown_path = md_dir / f"{output_name}.md"
            pdf_path = pdf_dir / f"{output_name}.pdf"

            markdown_path.write_text(markdown_text, encoding="utf-8")
            render_markdown_to_pdf(markdown_text, pdf_path)
            print(f"Generated {markdown_path} and {pdf_path}")

        return 0
    except FileNotFoundError as error:
        print(f"Error: {error}", file=sys.stderr)
    except Exception as error:  # pragma: no cover - last-resort CLI safeguard
        print(f"Error: {error}", file=sys.stderr)

    return 1


if __name__ == "__main__":
    raise SystemExit(main())
