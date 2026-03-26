from __future__ import annotations

import argparse
import sys
from pathlib import Path

from src.sow_generator.markdown import generate_sow, load_yaml
from src.sow_generator.pdf import render_markdown_to_pdf


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
    parser.add_argument(
        "--clean",
        action="store_true",
        help="Delete existing Markdown and PDF outputs before rebuilding",
    )
    return parser.parse_args(argv)


def iter_yaml_files(yaml_dir: Path, demo_name: str | None) -> list[Path]:
    if demo_name:
        return [yaml_dir / f"{demo_name}.yaml"]
    return sorted(yaml_dir.glob("*.yaml"))


def build_output_name(yaml_file: Path) -> str:
    return f"{yaml_file.stem}-sow"


def clean_output_dir(directory: Path, pattern: str) -> list[Path]:
    removed_files: list[Path] = []
    if not directory.exists():
        return removed_files

    for file_path in sorted(directory.glob(pattern)):
        if file_path.is_file():
            file_path.unlink()
            removed_files.append(file_path)

    return removed_files


def build_demo_documents(yaml_files: list[Path], md_dir: Path, pdf_dir: Path) -> list[tuple[Path, Path]]:
    generated_files: list[tuple[Path, Path]] = []

    for yaml_file in yaml_files:
        data = load_yaml(yaml_file)
        markdown_text = generate_sow(data)

        output_name = build_output_name(yaml_file)
        markdown_path = md_dir / f"{output_name}.md"
        pdf_path = pdf_dir / f"{output_name}.pdf"

        markdown_path.write_text(markdown_text, encoding="utf-8")
        render_markdown_to_pdf(markdown_text, pdf_path)
        generated_files.append((markdown_path, pdf_path))

    return generated_files


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

        if args.clean:
            removed_markdown = clean_output_dir(md_dir, "*.md")
            removed_pdfs = clean_output_dir(pdf_dir, "*.pdf")
            print(
                f"Cleaned {len(removed_markdown)} Markdown file(s) and {len(removed_pdfs)} PDF file(s)."
            )

        generated_files = build_demo_documents(yaml_files, md_dir, pdf_dir)
        for markdown_path, pdf_path in generated_files:
            print(f"Generated {markdown_path} and {pdf_path}")

        return 0
    except FileNotFoundError as error:
        print(f"Error: {error}", file=sys.stderr)
    except Exception as error:  # pragma: no cover
        print(f"Error: {error}", file=sys.stderr)

    return 1
