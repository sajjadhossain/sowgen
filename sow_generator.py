#!/usr/bin/env python3

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

import yaml


REQUIRED_TOP_LEVEL_KEYS = {
    "project",
    "team",
    "kanban",
    "user_stories",
    "deliverables",
    "milestones",
    "pricing",
    "assumptions_and_constraints",
    "risk_management",
}


def load_yaml(file_path: str | Path) -> dict[str, Any]:
    """Load a YAML configuration file into a dictionary."""
    with Path(file_path).open("r", encoding="utf-8") as file:
        data = yaml.safe_load(file)

    if not isinstance(data, dict):
        raise ValueError("YAML root must be a mapping of configuration sections.")

    return data


def validate_data(data: dict[str, Any]) -> None:
    """Validate the minimum structure required to generate a SOW."""
    missing_keys = sorted(REQUIRED_TOP_LEVEL_KEYS - data.keys())
    if missing_keys:
        raise ValueError(
            f"Missing required top-level sections: {', '.join(missing_keys)}"
        )

    project = data["project"]
    team = data["team"]
    kanban = data["kanban"]
    pricing = data["pricing"]
    assumptions = data["assumptions_and_constraints"]
    risks = data["risk_management"]

    required_project_keys = ["name", "client", "start_date", "end_date", "description"]
    required_pricing_keys = ["hourly_rate", "overhead", "profit_margin"]

    _require_keys(project, required_project_keys, "project")
    _require_keys(team, ["members"], "team")
    _require_keys(kanban, ["description", "columns", "principles"], "kanban")
    _require_keys(pricing, required_pricing_keys, "pricing")

    if not isinstance(team["members"], list) or not team["members"]:
        raise ValueError("`team.members` must contain at least one team member.")

    for index, member in enumerate(team["members"], start=1):
        _require_keys(member, ["role", "name", "email", "phone"], f"team.members[{index}]")

    if not isinstance(data["user_stories"], list) or not data["user_stories"]:
        raise ValueError("`user_stories` must contain at least one story.")

    if not isinstance(data["deliverables"], list) or not data["deliverables"]:
        raise ValueError("`deliverables` must contain at least one deliverable.")

    if not isinstance(data["milestones"], list) or not data["milestones"]:
        raise ValueError("`milestones` must contain at least one milestone.")

    if not isinstance(kanban["columns"], list) or not kanban["columns"]:
        raise ValueError("`kanban.columns` must contain at least one item.")

    if not isinstance(kanban["principles"], list) or not kanban["principles"]:
        raise ValueError("`kanban.principles` must contain at least one item.")

    if not isinstance(assumptions, list) or not assumptions:
        raise ValueError("`assumptions_and_constraints` must contain at least one item.")

    if not isinstance(risks, list) or not risks:
        raise ValueError("`risk_management` must contain at least one item.")

    for index, story in enumerate(data["user_stories"], start=1):
        _require_keys(
            story,
            ["id", "title", "as_a", "i_want", "so_that", "acceptance_criteria", "estimate", "priority"],
            f"user_stories[{index}]",
        )
        if not isinstance(story["acceptance_criteria"], list) or not story["acceptance_criteria"]:
            raise ValueError(
                f"`user_stories[{index}].acceptance_criteria` must contain at least one item."
            )

    for index, milestone in enumerate(data["milestones"], start=1):
        _require_keys(milestone, ["name", "due_date", "deliverables"], f"milestones[{index}]")

    for index, deliverable in enumerate(data["deliverables"], start=1):
        _require_keys(
            deliverable,
            ["id", "name", "description", "access_details"],
            f"deliverables[{index}]",
        )

    for index, column in enumerate(kanban["columns"], start=1):
        _require_keys(column, ["key", "description"], f"kanban.columns[{index}]")

    for index, principle in enumerate(kanban["principles"], start=1):
        _require_keys(principle, ["key", "description"], f"kanban.principles[{index}]")

    for index, assumption in enumerate(assumptions, start=1):
        _require_keys(
            assumption,
            ["id", "summary", "mitigation"],
            f"assumptions_and_constraints[{index}]",
        )

    for index, risk in enumerate(risks, start=1):
        _require_keys(risk, ["id", "summary", "mitigation"], f"risk_management[{index}]")


def _require_keys(section: dict[str, Any], keys: list[str], label: str) -> None:
    missing = [key for key in keys if key not in section]
    if missing:
        raise ValueError(f"Missing keys in `{label}`: {', '.join(missing)}")


def format_currency(value: float) -> str:
    return f"${value:,.2f}"


def format_story_outcome(outcome: str) -> str:
    cleaned = outcome.strip()
    lowered = cleaned.lower()
    if lowered.startswith("i can "):
        return cleaned[6:]
    if lowered.startswith("can "):
        return cleaned[4:]
    return cleaned


def slugify_heading(heading: str) -> str:
    slug = heading.strip().lower()
    allowed = []
    for char in slug:
        if char.isalnum() or char in {" ", "-"}:
            allowed.append(char)
    return "".join(allowed).replace(" ", "-")


def build_table(headers: list[str], rows: list[list[str]]) -> list[str]:
    header_row = "| " + " | ".join(headers) + " |"
    separator_row = "| " + " | ".join(["---"] * len(headers)) + " |"
    table_rows = ["| " + " | ".join(row) + " |" for row in rows]
    return [header_row, separator_row, *table_rows]


def build_story_config(user_stories: list[dict[str, Any]]) -> list[dict[str, Any]]:
    story_config: list[dict[str, Any]] = []
    for story in user_stories:
        story_config.append(
            {
                "epic": {
                    "id": story["id"],
                    "title": story["title"],
                    "estimate": story["estimate"],
                    "priority": story["priority"],
                },
                "feature": {
                    "id": story["id"],
                    "name": story["title"],
                    "as_a": story["as_a"],
                    "i_want": story["i_want"],
                    "so_that": story["so_that"],
                    "scenarios": story["acceptance_criteria"],
                },
                "ac": story["acceptance_criteria"],
            }
        )
    return story_config


def normalize_deliverables(deliverables: list[dict[str, Any]]) -> list[dict[str, str]]:
    normalized: list[dict[str, str]] = []
    for deliverable in deliverables:
        normalized.append(
            {
                "id": str(deliverable["id"]),
                "name": str(deliverable["name"]),
                "description": str(deliverable["description"]),
                "access_details": str(deliverable["access_details"]),
            }
        )
    return normalized


def build_toc(story_config: list[dict[str, Any]]) -> list[str]:
    toc_lines = [
        "## Table of Contents",
        "",
        "- [Project Overview](#project-overview)",
        "- [Team Structure](#team-structure)",
        "- [Methodology: Technical Kanban](#methodology-technical-kanban)",
        "  - [Kanban Board Columns](#kanban-board-columns)",
        "  - [Key Principles](#key-principles)",
        "- [User Stories](#user-stories)",
    ]
    for story in story_config:
        epic = story["epic"]
        feature = story["feature"]
        epic_heading = f"{epic['id']}: {epic['title']}"
        feature_heading = f"Feature {feature['id']}: {feature['name']}"
        toc_lines.append(
            f"  - [{epic_heading}](#{slugify_heading(epic_heading)})"
        )
        toc_lines.append(
            f"    - [{feature_heading}](#{slugify_heading(feature_heading)})"
        )
    toc_lines.extend(
        [
            "- [Deliverables](#deliverables)",
            "  - [Delivery Estimate Summary](#delivery-estimate-summary)",
            "- [Milestones](#milestones)",
            "- [Pricing Estimate](#pricing-estimate)",
            "- [Assumptions and Constraints](#assumptions-and-constraints)",
            "- [Risk Management](#risk-management)",
            "",
        ]
    )
    return toc_lines


def generate_sow(data: dict[str, Any]) -> str:
    """Generate the Scope of Work document."""
    validate_data(data)

    project = data["project"]
    team = data["team"]
    kanban = data["kanban"]
    user_stories = data["user_stories"]
    story_config = build_story_config(user_stories)
    deliverables = normalize_deliverables(data["deliverables"])
    milestones = data["milestones"]
    pricing = data["pricing"]
    assumptions = data["assumptions_and_constraints"]
    risks = data["risk_management"]

    total_estimate = sum(story["epic"]["estimate"] for story in story_config)
    total_hours = total_estimate * 8
    base_cost = total_hours * pricing["hourly_rate"]
    overhead_cost = base_cost * pricing["overhead"]
    profit = (base_cost + overhead_cost) * pricing["profit_margin"]
    total_cost = base_cost + overhead_cost + profit

    lines: list[str] = [
        f"# Scope of Work: {project['name']}",
        "",
    ]
    lines.extend(build_toc(story_config))
    lines.extend(
        build_table(
            ["Key", "Description"],
            [
                ["Client", str(project["client"])],
                ["Project Period", f"{project['start_date']} to {project['end_date']}"],
            ],
        )
    )
    lines.extend(
        [
        "",
        "## Project Overview",
        "",
        project["description"],
        "",
        "## Team Structure",
        "",
        ]
    )
    lines.extend(
        build_table(
            ["Role", "Name", "Email", "Phone"],
            [
                [
                    str(member["role"]),
                    str(member["name"]),
                    str(member["email"]),
                    str(member["phone"]),
                ]
                for member in team["members"]
            ],
        )
    )

    lines.extend(
        [
            "",
            "## Methodology: Technical Kanban",
            "",
            str(kanban["description"]),
            "",
            "### Kanban Board Columns",
        ]
    )
    lines.extend(
        build_table(
            ["Key", "Description"],
            [
                [str(column["key"]), str(column["description"])]
                for column in kanban["columns"]
            ],
        )
    )
    lines.extend(
        [
            "",
            "### Key Principles",
        ]
    )
    lines.extend(
        build_table(
            ["Key", "Description"],
            [
                [str(principle["key"]), str(principle["description"])]
                for principle in kanban["principles"]
            ],
        )
    )
    lines.extend(
        [
            "",
            "## User Stories",
            "",
        ]
    )

    for story in story_config:
        epic = story["epic"]
        feature = story["feature"]
        story_outcome = format_story_outcome(feature["so_that"])
        lines.extend(
            [
                f"### {epic['id']}: {epic['title']}",
                "",
                "**User Story:**",
                f"- As a {feature['as_a']}",
                f"- I want {feature['i_want']}",
                f"- So that {feature['so_that']}",
                "",
                f"#### Feature {feature['id']}: {feature['name']}",
                "",
            ]
        )
        lines.extend(
            build_table(
                ["AC ID", "US ID", "Acceptance Criteria"],
                [
                    [f"AC-{index:02d}", epic["id"], str(criterion)]
                    for index, criterion in enumerate(story["ac"], start=1)
                ],
            )
        )
        lines.extend([""])
        for criterion in feature["scenarios"]:
            lines.extend(
                [
                    f"```gherkin",
                    f"Feature: {feature['name']}",
                    f"  Scenario: {criterion}",
                    f"    Given a {feature['as_a']}",
                    f"    When they need {feature['i_want']}",
                    f"    Then they can {story_outcome}",
                    "```",
                    "",
                ]
            )
        lines.extend(
            build_table(
                ["Key", "Description"],
                [
                    ["Estimate", f"{epic['estimate']} story points"],
                    ["Estimated Hours", f"{epic['estimate'] * 8} hours"],
                    ["Priority", str(epic["priority"])],
                ],
            )
        )
        lines.extend(
            [
                "",
            ]
        )

    lines.extend(["## Deliverables", ""])
    lines.extend(
        build_table(
            ["Deliverable ID", "Deliverable", "Description", "Access Details"],
            [
                [
                    deliverable["id"],
                    deliverable["name"],
                    deliverable["description"],
                    deliverable["access_details"],
                ]
                for deliverable in deliverables
            ],
        )
    )
    lines.extend(
        [
            "",
            "### Delivery Estimate Summary",
        ]
    )
    lines.extend(
        build_table(
            ["Epic ID", "Epic", "Feature", "Story Points", "Estimated Hours", "Priority"],
            [
                [
                    str(story["epic"]["id"]),
                    str(story["epic"]["title"]),
                    str(story["feature"]["name"]),
                    str(story["epic"]["estimate"]),
                    str(story["epic"]["estimate"] * 8),
                    str(story["epic"]["priority"]),
                ]
                for story in story_config
            ]
            + [["Total", "-", "-", str(total_estimate), str(total_hours), "-"]],
        )
    )

    lines.extend(["", "## Milestones", ""])
    lines.extend(
        build_table(
            ["Milestone", "Due Date", "Deliverables"],
            [
                [
                    str(milestone["name"]),
                    str(milestone["due_date"]),
                    "<br>".join(str(deliverable) for deliverable in milestone["deliverables"]),
                ]
                for milestone in milestones
            ],
        )
    )

    lines.extend(
        [
            "",
            "## Pricing Estimate",
            "",
        ]
    )
    lines.extend(
        build_table(
            ["Key", "Description"],
            [
                ["Total Story Points", str(total_estimate)],
                ["Estimated Hours", f"{total_hours} (assuming 8 hours per story point)"],
                ["Hourly Rate", format_currency(pricing["hourly_rate"])],
                ["Base Cost", format_currency(base_cost)],
                [f"Overhead ({pricing['overhead'] * 100:.1f}%)", format_currency(overhead_cost)],
                [f"Profit Margin ({pricing['profit_margin'] * 100:.1f}%)", format_currency(profit)],
                ["Total Estimated Cost", format_currency(total_cost)],
            ],
        )
    )
    lines.extend(
        [
            "",
            "## Assumptions and Constraints",
            "",
        ]
    )
    lines.extend(
        build_table(
            ["ID", "Summary", "Mitigation"],
            [
                [
                    str(item["id"]),
                    str(item["summary"]),
                    str(item["mitigation"]),
                ]
                for item in assumptions
            ],
        )
    )
    lines.extend(
        [
            "",
            "## Risk Management",
            "",
        ]
    )
    lines.extend(
        build_table(
            ["ID", "Summary", "Mitigation"],
            [
                [
                    str(item["id"]),
                    str(item["summary"]),
                    str(item["mitigation"]),
                ]
                for item in risks
            ],
        )
    )
    lines.extend([""])

    return "\n".join(lines)


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate a Markdown scope of work from a YAML configuration file."
    )
    parser.add_argument("yaml_file", help="Path to the YAML configuration file")
    parser.add_argument(
        "-o",
        "--output",
        default="sow.md",
        help="Output Markdown file path (default: sow.md)",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])

    try:
        data = load_yaml(args.yaml_file)
        sow_content = generate_sow(data)

        output_path = Path(args.output)
        output_path.write_text(sow_content, encoding="utf-8")
        print(f"SOW generated successfully: {output_path}")
        return 0

    except FileNotFoundError:
        print(f"Error: File '{args.yaml_file}' not found.", file=sys.stderr)
    except yaml.YAMLError as error:
        print(f"Error parsing YAML: {error}", file=sys.stderr)
    except ValueError as error:
        print(f"Configuration error: {error}", file=sys.stderr)
    except Exception as error:  # pragma: no cover - last-resort CLI safeguard
        print(f"Error: {error}", file=sys.stderr)

    return 1


if __name__ == "__main__":
    raise SystemExit(main())
