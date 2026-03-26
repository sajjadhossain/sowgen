import unittest

from reportlab.platypus import Paragraph, Table

from src.sow_generator.pdf import (
    PAGE_CONTENT_WIDTH,
    build_markdown_flowables,
    compute_table_col_widths,
    convert_inline_markdown,
    slugify_heading,
)


class MarkdownToPdfTests(unittest.TestCase):
    def test_internal_markdown_links_become_pdf_links(self):
        converted = convert_inline_markdown("[Project Overview](#project-overview)")
        self.assertIn("<link href='#project-overview' color='blue'>Project Overview</link>", converted)

    def test_heading_anchor_slug_matches_generator_style(self):
        self.assertEqual(
            slugify_heading("Feature US-001: User Authentication"),
            "feature-us-001-user-authentication",
        )

    def test_table_widths_fit_available_space(self):
        rows = [
            ["Key", "Description"],
            ["Project Period", "A long description that should wrap within the table cell rather than overflow the page width."],
            ["Another Column", "Another long piece of content that needs to be constrained to the PDF layout."],
        ]
        widths = compute_table_col_widths(rows, PAGE_CONTENT_WIDTH - 16)
        self.assertLessEqual(sum(widths), PAGE_CONTENT_WIDTH - 16 + 0.5)
        self.assertEqual(len(widths), 2)

    def test_flowables_indent_subsections_and_build_tables(self):
        markdown = "\n".join(
            [
                "# Title",
                "## Parent",
                "### Child",
                "This paragraph should be indented under the child heading so the hierarchy reads clearly.",
                "| Key | Description |",
                "| --- | --- |",
                "| Alpha | A long row value that should wrap inside the table cell rather than running off the page. |",
            ]
        )

        flowables = build_markdown_flowables(markdown)
        paragraphs = [item for item in flowables if isinstance(item, Paragraph)]
        tables = [item for item in flowables if isinstance(item, Table)]

        self.assertGreaterEqual(len(paragraphs), 4)
        self.assertEqual(paragraphs[2].style.leftIndent, 16)
        self.assertEqual(len(tables), 1)


if __name__ == "__main__":
    unittest.main()
