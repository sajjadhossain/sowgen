# Scope of Work Generator

This repository contains a Python-based tool to generate a Scope of Work (SOW) document from a YAML configuration file. The generated SOW uses Gherkin user story language, includes a table of contents, and incorporates a technical Kanban approach suitable for small development teams. The primary outcome is an estimate of the workload price.

## Features

- Reads project details from a YAML file
- Generates a comprehensive SOW in Markdown format
- Generates a PDF from an existing Markdown document
- Keeps document content in YAML and uses Python as a renderer
- Adds a generated table of contents at the top of the SOW
- Uses Gherkin syntax for user stories
- Applies Kanban methodology for task management
- Estimates workload and pricing based on provided rates
- Validates configuration structure before generating output

## Installation

Run the installation script:

```bash
./install.sh
```

This will install the required Python dependencies.

## Usage

1. Create a YAML configuration file (see `sample.yaml` for an example).
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

```bash
python3 sow_generator.py <path_to_yaml>
```

3. The `sow.md` file will be generated in the current directory.
4. Optionally provide a custom output path:

```bash
python3 sow_generator.py <path_to_yaml> --output custom-sow.md
```

5. Convert a Markdown file to PDF:

```bash
python3 markdown_to_pdf.py <path_to_markdown>
```

6. Optionally provide a custom PDF output path:

```bash
python3 markdown_to_pdf.py <path_to_markdown> --output custom-sow.pdf
```

## Project Structure

- `sow_generator.py`: Main script to generate the SOW
- `markdown_to_pdf.py`: Converts Markdown documents into PDFs
- `sample.yaml`: Example YAML configuration
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
- `assumptions_and_constraints`
- `risk_management`

The script no longer fills in document copy from Python defaults. If a required content block is missing, generation fails with a configuration error.

## Testing

Run tests with:

```bash
python3 -m behave tests/
```

Tests are written in Gherkin format and verify the YAML-driven Markdown output, PDF generation, pricing summary, and invalid-input handling.
