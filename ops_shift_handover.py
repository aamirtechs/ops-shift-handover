#!/usr/bin/env python3
"""Assemble a shift handover note for support and ops teams.

Input is a JSON file describing one shift. Output is a readable
Markdown handover note, or plain text with --format txt. Run
--template to print a blank input file you can fill in.

Example input (see examples/handover.json):

    {
      "date": "2026-10-28",
      "shift": "Night",
      "team": "Support",
      "outgoing": "Ayesha",
      "incoming": "Bilal",
      "summary": ["Queue cleared to zero at handover."],
      "open_incidents": [
        {"id": "INC-1001", "severity": "high",
         "title": "Billing page timeout", "status": "investigating",
         "next_step": "Check payment gateway logs at 09:00."}
      ],
      "pending_tasks": ["Reply to ticket 4521 about refund timing."],
      "watch_items": ["Traffic spike expected at 10:00 during the sale."]
    }

Severity order in the rendered note is critical, high, medium, low,
then anything else, so the incoming shift sees the worst first.
"""

import argparse
import json
import sys

VERSION = "1.0.0"

REQUIRED = ["date", "shift", "team", "outgoing", "incoming"]
SEVERITY_ORDER = {"critical": 0, "high": 1, "medium": 2, "low": 3}

TEMPLATE = {
    "date": "2026-10-28",
    "shift": "Night",
    "team": "Support",
    "outgoing": "Outgoing lead name",
    "incoming": "Incoming lead name",
    "summary": ["One line per key event of the shift."],
    "open_incidents": [
        {"id": "INC-1001", "severity": "high", "title": "Short title",
         "status": "investigating",
         "next_step": "What the next shift should do first."}
    ],
    "pending_tasks": ["Task the next shift must pick up."],
    "watch_items": ["Something to keep an eye on."],
}


def validate(data):
    """Return a list of validation problems, empty when the input is fine."""
    problems = []
    if not isinstance(data, dict):
        return ["input must be a JSON object"]
    for field in REQUIRED:
        if not data.get(field):
            problems.append(f"missing required field: {field}")
    for field in ("summary", "pending_tasks", "watch_items"):
        if field in data and not isinstance(data[field], list):
            problems.append(f"{field} must be a list of strings")
        elif isinstance(data.get(field), list):
            for item in data[field]:
                if not isinstance(item, str):
                    problems.append(f"{field} must contain only strings")
    incidents = data.get("open_incidents", [])
    if not isinstance(incidents, list):
        problems.append("open_incidents must be a list")
    elif incidents:
        for incident in incidents:
            if not isinstance(incident, dict):
                problems.append("each open incident must be an object")
                continue
            for field in ("id", "title", "status"):
                if not incident.get(field):
                    problems.append(
                        f"open incident missing required field: {field}")
    return problems


def sort_incidents(incidents):
    return sorted(
        incidents,
        key=lambda i: (SEVERITY_ORDER.get(str(i.get("severity", "")).lower(), 4),
                       str(i.get("id", ""))))


def render_md(data):
    lines = []
    lines.append(f"# Shift handover: {data['team']}, {data['shift']} shift, "
                 f"{data['date']}")
    lines.append("")
    lines.append(f"Outgoing: {data['outgoing']}  |  "
                 f"Incoming: {data['incoming']}")
    lines.append("")
    if data.get("summary"):
        lines.append("## Summary")
        for item in data["summary"]:
            lines.append(f"- {item}")
        lines.append("")
    incidents = sort_incidents(data.get("open_incidents", []))
    if incidents:
        lines.append("## Open incidents")
        for incident in incidents:
            severity = incident.get("severity", "unspecified")
            lines.append(f"- **{incident['id']}** [{severity}] "
                         f"{incident['title']} ({incident['status']})")
            if incident.get("next_step"):
                lines.append(f"  - Next step: {incident['next_step']}")
        lines.append("")
    if data.get("pending_tasks"):
        lines.append("## Pending tasks")
        for item in data["pending_tasks"]:
            lines.append(f"- [ ] {item}")
        lines.append("")
    if data.get("watch_items"):
        lines.append("## Watch items")
        for item in data["watch_items"]:
            lines.append(f"- {item}")
        lines.append("")
    if not any([data.get("summary"), incidents,
                data.get("pending_tasks"), data.get("watch_items")]):
        lines.append("Nothing to hand over. All clear.")
        lines.append("")
    return "\n".join(lines)


def render_txt(data):
    """Plain text version: same content, no Markdown markers."""
    text = render_md(data)
    text = text.replace("# ", "").replace("## ", "")
    text = text.replace("**", "")
    text = text.replace("- [ ] ", "- ")
    return text


def load(path):
    try:
        with open(path, encoding="utf-8") as handle:
            return json.load(handle), None
    except OSError as exc:
        return None, f"cannot read {path}: {exc}"
    except json.JSONDecodeError as exc:
        return None, f"invalid JSON in {path}: {exc}"


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Assemble a shift handover note from a JSON file.")
    parser.add_argument("file", nargs="?",
                        help="handover JSON file (see --template)")
    parser.add_argument("--format", choices=["md", "txt"], default="md",
                        help="output format (default: md)")
    parser.add_argument("--out", help="write output to this file")
    parser.add_argument("--template", action="store_true",
                        help="print a blank handover JSON template")
    parser.add_argument("--check", action="store_true",
                        help="validate the input, print nothing else")
    parser.add_argument("--version", action="version", version=VERSION)
    args = parser.parse_args(argv)
    if args.template:
        print(json.dumps(TEMPLATE, indent=2))
        return 0
    if not args.file:
        parser.error("a file is required unless --template is given")
    data, error = load(args.file)
    if error:
        print(f"error: {error}", file=sys.stderr)
        return 2
    problems = validate(data)
    if args.check:
        if problems:
            for problem in problems:
                print(f"error: {problem}", file=sys.stderr)
            return 1
        print("ok: handover input is valid")
        return 0
    if problems:
        for problem in problems:
            print(f"error: {problem}", file=sys.stderr)
        return 1
    text = render_md(data) if args.format == "md" else render_txt(data)
    if args.out:
        try:
            with open(args.out, "w", encoding="utf-8") as handle:
                handle.write(text)
        except OSError as exc:
            print(f"error: cannot write {args.out}: {exc}", file=sys.stderr)
            return 2
    else:
        print(text, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
