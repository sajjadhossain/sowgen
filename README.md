# Scope of Work Generator

This repository contains a Python-based tool to generate a Scope of Work (SOW) document from a YAML configuration file. The generated SOW uses Gherkin user story language, includes a table of contents, and incorporates a technical Kanban approach suitable for small development teams. The primary outcome is an estimate of the workload price.

## Features

- Reads project details from a YAML file
- Generates a comprehensive SOW in Markdown format
- Generates a PDF from an existing Markdown document
- Supports a clean one-command demo pipeline using `demos/yaml`, `demos/md`, and `demos/pdf`
- Includes a GitHub Actions workflow that can be triggered from `gh`
- Keeps document content in YAML and uses Python as a renderer
- Adds a generated table of contents at the top of the SOW
- Uses Gherkin syntax for user stories
- Applies Kanban methodology for task management
- Estimates workload and pricing based on provided rates
- Validates configuration structure before generating output

## Installation

### Windows

Run the installation script:

```bat
install.bat
```

### Mac/Linux

Run the installation script:

```bash
./install.sh
```

This will install the required Python dependencies.

## Usage

1. Create a YAML configuration file (see `demos/yaml/sample.yaml` for an example).
   The YAML now owns all document content that appears in the final SOW, including:
   - project metadata
   - team members
   - Kanban description, columns, and principles
   - user stories and acceptance criteria
   - deliverables
   - milestones
   - pricing inputs
   - assumptions and constraints
   - risk management entries
2. Run the generator:

Windows:

```bat
py -m src.sow_generator.cli.generate_sow <path_to_yaml>
```

Mac/Linux:

```bash
python3 -m src.sow_generator.cli.generate_sow <path_to_yaml>
```

3. The `sow.md` file will be generated in the current directory.
4. Optionally provide a custom output path:

Windows:

```bat
py -m src.sow_generator.cli.generate_sow <path_to_yaml> --output custom-sow.md
```

Mac/Linux:

```bash
python3 -m src.sow_generator.cli.generate_sow <path_to_yaml> --output custom-sow.md
```

5. Convert a Markdown file to PDF:

Windows:

```bat
py -m src.sow_generator.cli.markdown_to_pdf <path_to_markdown>
```

Mac/Linux:

```bash
python3 -m src.sow_generator.cli.markdown_to_pdf <path_to_markdown>
```

6. Optionally provide a custom PDF output path:

Windows:

```bat
py -m src.sow_generator.cli.markdown_to_pdf <path_to_markdown> --output custom-sow.pdf
```

Mac/Linux:

```bash
python3 -m src.sow_generator.cli.markdown_to_pdf <path_to_markdown> --output custom-sow.pdf
```

7. Build all demo files and clean old outputs first:

Windows:

```bat
py -m src.sow_generator.cli.generate_demo_documents --clean
```

Mac/Linux:

```bash
python3 -m src.sow_generator.cli.generate_demo_documents --clean
```

This maps:

- `demos/yaml/*.yaml` to `demos/md/*-sow.md`
- `demos/yaml/*.yaml` to `demos/pdf/*-sow.pdf`

It also deletes existing `*.md` files in `demos/md` and `*.pdf` files in `demos/pdf` before rebuilding.

8. Trigger the GitHub Actions version from GitHub CLI:

```bash
gh workflow run build-demo-documents.yml
```

After the run finishes, you can download the generated artifacts with:

```bash
gh run download --name demo-documents
```

## Project Structure

- `src/sow_generator/markdown.py`: Core Markdown SOW generation logic
- `src/sow_generator/pdf.py`: Markdown-to-PDF rendering logic
- `src/sow_generator/demo.py`: Demo build orchestration for `demos/`
- `src/sow_generator/cli/`: CLI entrypoints for generating SOWs, PDFs, and demo outputs
- `.github/workflows/build-demo-documents.yml`: GitHub Actions workflow for `gh workflow run`
- `demos/yaml/sample.yaml`: Example YAML configuration
- `requirements.txt`: Python dependencies
- `install.sh`: Installation script
- `docs/`: Supplemental documentation and future GitHub Wiki content
- `tests/`: Gherkin acceptance tests for the generator

## YAML Requirements

The generator expects these top-level YAML sections:

- `project`
- `team`
- `kanban`
- `user_stories`
- `deliverables`
- `milestones`
- `pricing`

Optional sections:

- `assumptions_and_constraints`
- `risk_management`

The script no longer fills in document copy from Python defaults. If a required content block is missing, generation fails with a configuration error. The optional sections above are only rendered when they are present in the YAML.

## Testing

Run tests with:

```bash
python3 -m behave tests/
```

Tests are written in Gherkin format and verify the YAML-driven Markdown output, PDF generation, pricing summary, and invalid-input handling.
