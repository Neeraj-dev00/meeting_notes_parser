"""
Command-Line Interface for Meeting Notes Parser

Usage:
    python -m meeting_notes_parser.cli notes.txt
    python -m meeting_notes_parser.cli notes.txt --format json
    cat notes.txt | python -m meeting_notes_parser.cli --format slack
"""

import argparse
import sys
from pathlib import Path

# Support both installed-package and direct-run contexts
try:
    from meeting_notes_parser import MeetingNotesParser, MeetingNotesResult
except ImportError:
    from parser import MeetingNotesParser, MeetingNotesResult  # type: ignore


# ------------------------------------------------------------------ #
#  Formatters                                                          #
# ------------------------------------------------------------------ #

def format_text(result: MeetingNotesResult) -> str:
    lines: list[str] = []

    # Header
    if result.meeting_info.get("title"):
        lines.append(f"📋  {result.meeting_info['title']}")
    if result.meeting_info.get("date"):
        lines.append(f"📅  {result.meeting_info['date']}")
    if result.meeting_info.get("attendees"):
        lines.append(f"👥  {', '.join(result.meeting_info['attendees'])}")
    if lines:
        lines.append("")

    # Action items
    lines.append(f"ACTION ITEMS  ({len(result.action_items)})")
    lines.append("─" * 42)
    if result.action_items:
        priority_emoji = {"high": "🔴", "medium": "🟡", "low": "🟢"}
        for i, item in enumerate(result.action_items, 1):
            em = priority_emoji.get(item.priority, "⚪")
            lines.append(f"{i:>2}. {em} {item.task}")
            if item.owner:
                lines.append(f"      Owner    : {item.owner}")
            if item.deadline:
                lines.append(f"      Deadline : {item.deadline}")
            if item.priority != "medium":
                lines.append(f"      Priority : {item.priority}")
    else:
        lines.append("    (none found)")
    lines.append("")

    # Decisions
    if result.decisions:
        lines.append(f"DECISIONS  ({len(result.decisions)})")
        lines.append("─" * 42)
        for i, d in enumerate(result.decisions, 1):
            lines.append(f"{i:>2}. ✅ {d}")
        lines.append("")

    # Key points
    if result.key_points:
        lines.append(f"KEY POINTS  ({len(result.key_points)})")
        lines.append("─" * 42)
        for i, p in enumerate(result.key_points, 1):
            lines.append(f"{i:>2}. 📌 {p}")
        lines.append("")

    return "\n".join(lines)


FORMATTERS = {
    "text":  format_text,
    "json":  lambda r: r.export_json(),
    "csv":   lambda r: r.export_csv(),
    "slack": lambda r: r.to_slack_message(),
}


# ------------------------------------------------------------------ #
#  CLI                                                                 #
# ------------------------------------------------------------------ #

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        prog="meeting-notes-parser",
        description="Extract action items and decisions from meeting notes.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  Parse a file and print to stdout (default text format):
    %(prog)s notes.txt

  Export as JSON:
    %(prog)s notes.txt --format json

  Export high-priority items as CSV:
    %(prog)s notes.txt --format csv --priority high

  Pipe from stdin:
    cat notes.txt | %(prog)s --format slack

  Write output to a file:
    %(prog)s notes.txt --format json --output summary.json
""",
    )
    ap.add_argument(
        "input", nargs="?",
        help="Path to a plain-text file with meeting notes (omit to read from stdin).",
    )
    ap.add_argument(
        "-f", "--format",
        choices=list(FORMATTERS), default="text",
        help="Output format (default: text).",
    )
    ap.add_argument(
        "-o", "--output",
        help="Write output to this file instead of stdout.",
    )
    ap.add_argument(
        "--priority",
        choices=["high", "medium", "low"],
        help="Filter action items by priority level.",
    )
    ap.add_argument(
        "--owner",
        help="Filter action items by owner name (case-insensitive substring).",
    )
    ap.add_argument(
        "-v", "--version",
        action="version", version="meeting-notes-parser 1.0.0",
    )
    return ap


def main(argv: list[str] | None = None) -> int:
    ap = build_parser()
    args = ap.parse_args(argv)

    # Read input
    if args.input:
        path = Path(args.input)
        if not path.exists():
            print(f"Error: file not found: {args.input}", file=sys.stderr)
            return 1
        text = path.read_text(encoding="utf-8")
    else:
        if sys.stdin.isatty():
            print("Paste meeting notes below, then press Ctrl-D (Ctrl-Z on Windows):",
                  file=sys.stderr)
        text = sys.stdin.read()

    if not text.strip():
        print("Error: no input provided.", file=sys.stderr)
        return 1

    # Parse
    parser = MeetingNotesParser()
    result = parser.parse(text)

    # Apply filters
    items = result.action_items
    if args.priority:
        items = [it for it in items if it.priority == args.priority]
    if args.owner:
        needle = args.owner.lower()
        items = [it for it in items if it.owner and needle in it.owner.lower()]
    result.action_items = items

    # Format
    formatter = FORMATTERS[args.format]
    output = formatter(result)

    # Write
    if args.output:
        Path(args.output).write_text(output, encoding="utf-8")
        print(f"Output written to: {args.output}", file=sys.stderr)
    else:
        print(output)

    return 0


if __name__ == "__main__":
    sys.exit(main())
