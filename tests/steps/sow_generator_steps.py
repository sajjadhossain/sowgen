from pathlib import Path
import subprocess
import sys
import tempfile

from behave import given, then, when


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "sow_generator.py"
PDF_SCRIPT = ROOT / "markdown_to_pdf.py"


@given("the sample configuration file")
def step_sample_configuration(context):
    context.config_path = ROOT / "sample.yaml"
    context.output_path = Path(tempfile.gettempdir()) / "sow-generator-sample.md"
    if context.output_path.exists():
        context.output_path.unlink()


@given("an invalid configuration file")
def step_invalid_configuration(context):
    temp_dir = Path(tempfile.mkdtemp(prefix="sow-generator-invalid-"))
    context.config_path = temp_dir / "invalid.yaml"
    context.config_path.write_text("project:\n  name: Missing Required Sections\n", encoding="utf-8")
    context.output_path = temp_dir / "invalid.md"


@given("a markdown file for PDF conversion")
def step_markdown_file_for_pdf_conversion(context):
    temp_dir = Path(tempfile.mkdtemp(prefix="sow-generator-pdf-"))
    context.markdown_path = temp_dir / "source.md"
    context.pdf_output_path = temp_dir / "source.pdf"
    context.markdown_path.write_text(
        "# Sample PDF\n\n- first bullet\n- second bullet\n\nPlain text paragraph.\n",
        encoding="utf-8",
    )


@given("a missing markdown file for PDF conversion")
def step_missing_markdown_file_for_pdf_conversion(context):
    temp_dir = Path(tempfile.mkdtemp(prefix="sow-generator-pdf-missing-"))
    context.markdown_path = temp_dir / "missing.md"
    context.pdf_output_path = temp_dir / "missing.pdf"


@when("I generate the scope of work")
def step_generate_scope_of_work(context):
    context.result = subprocess.run(
        [sys.executable, str(SCRIPT), str(context.config_path), "--output", str(context.output_path)],
        capture_output=True,
        text=True,
        cwd=ROOT,
    )


@when("I generate the scope of work with the invalid configuration")
def step_generate_invalid_scope_of_work(context):
    step_generate_scope_of_work(context)


@when("I generate the PDF document")
def step_generate_pdf_document(context):
    context.result = subprocess.run(
        [sys.executable, str(PDF_SCRIPT), str(context.markdown_path), "--output", str(context.pdf_output_path)],
        capture_output=True,
        text=True,
        cwd=ROOT,
    )


@then("the command succeeds")
def step_command_succeeds(context):
    assert context.result.returncode == 0, context.result.stderr
    assert context.output_path.exists(), "Expected the output file to be created."
    context.output_text = context.output_path.read_text(encoding="utf-8")


@then("the output file contains the project title")
def step_output_contains_title(context):
    assert "# Scope of Work: Sample Software Development Project" in context.output_text


@then("the output file contains a table of contents")
def step_output_contains_toc(context):
    assert "## Table of Contents" in context.output_text
    assert "- [Deliverables](#deliverables)" in context.output_text


@then("the output file contains YAML-driven methodology content")
def step_output_contains_yaml_driven_methodology(context):
    assert "### Kanban Board Columns" in context.output_text
    assert "| Backlog | All approved work items waiting to be prioritized for delivery. |" in context.output_text
    assert "| Visualize workflow | Make the current state of work visible so blockers and handoffs are easy to spot. |" in context.output_text


@then("the output file contains a Gherkin scenario")
def step_output_contains_gherkin(context):
    assert "```gherkin" in context.output_text
    assert "Feature: User Authentication" in context.output_text
    assert "Scenario: User can enter username and password" in context.output_text


@then("the output file contains the total estimated cost")
def step_output_contains_total_cost(context):
    assert "| Total Estimated Cost | $23,400.00 |" in context.output_text


@then("the command fails")
def step_command_fails(context):
    assert context.result.returncode != 0, "Expected the command to fail for invalid input."


@then("the error mentions the invalid configuration")
def step_error_mentions_invalid_configuration(context):
    assert "Configuration error:" in context.result.stderr


@then("the PDF command succeeds")
def step_pdf_command_succeeds(context):
    assert context.result.returncode == 0, context.result.stderr
    assert context.pdf_output_path.exists(), "Expected the PDF output file to be created."


@then("the generated file is a PDF")
def step_generated_file_is_a_pdf(context):
    pdf_header = context.pdf_output_path.read_bytes()[:4]
    assert pdf_header == b"%PDF", "Expected the generated file to start with the PDF header."


@then("the PDF command fails")
def step_pdf_command_fails(context):
    assert context.result.returncode != 0, "Expected the PDF command to fail."


@then("the PDF error mentions the missing input file")
def step_pdf_error_mentions_missing_input_file(context):
    assert "Markdown file" in context.result.stderr
    assert "not found" in context.result.stderr
