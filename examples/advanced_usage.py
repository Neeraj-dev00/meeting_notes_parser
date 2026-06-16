"""
examples/advanced_usage.py
--------------------------
Advanced patterns: batch processing, file I/O, integration hooks.
Run from the repo root:
    python examples/advanced_usage.py
"""

import sys
import os
import json
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from parser import MeetingNotesParser, MeetingNotesResult  # noqa: E402

NOTES_A = """\
Sprint Review — January 8, 2025
Attendees: Alice, Bob, Carol

Action Items:
- Alice will deploy the new auth service by Wednesday
- Bob: write migration guide ASAP
- Carol will update the runbook by end of week

Decisions:
- Rollback plan approved for v2.3
- On-call rotation updated
"""

NOTES_B = """\
Design Sync — January 9, 2025
Attendees: Dana, Eve

Action Items:
- Dana will share updated mockups by Thursday
- Eve: review accessibility audit when possible

Key Points:
- New component library reduces bundle size by 30 %
- Dark-mode support scheduled for Q2
"""


def example_batch_processing():
    """Parse multiple sets of notes and aggregate action items."""
    print("=" * 50)
    print("ADVANCED 1 — Batch processing")
    print("=" * 50)

    parser = MeetingNotesParser()
    all_notes = [NOTES_A, NOTES_B]
    all_action_items = []

    for notes in all_notes:
        result = parser.parse(notes)
        all_action_items.extend(result.action_items)

    print(f"Total action items across {len(all_notes)} meetings: {len(all_action_items)}")
    high = [i for i in all_action_items if i.priority == "high"]
    print(f"High-priority items: {len(high)}")
    for item in high:
        print(f"  🔴 {item.task} ({item.owner or 'unassigned'})")
    print()


def example_file_roundtrip():
    """Write notes to a temp file then parse it back."""
    print("=" * 50)
    print("ADVANCED 2 — File round-trip")
    print("=" * 50)

    parser = MeetingNotesParser()

    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False, encoding="utf-8") as fh:
        fh.write(NOTES_A)
        tmp_path = fh.name

    result = parser.parse_file(tmp_path)
    os.unlink(tmp_path)

    print(f"Parsed from file: {tmp_path}")
    print(f"Action items found: {len(result.action_items)}")
    for item in result.action_items:
        print(f"  • {item.task}")
    print()


def example_json_to_dict():
    """Demonstrate round-trip through JSON."""
    print("=" * 50)
    print("ADVANCED 3 — JSON round-trip")
    print("=" * 50)

    parser = MeetingNotesParser()
    result = parser.parse(NOTES_B)

    raw_json = result.export_json()
    data = json.loads(raw_json)

    print(f"Meeting: {data['meeting_info']['title']}")
    print(f"Action items serialised: {len(data['action_items'])}")
    for item in data["action_items"]:
        print(f"  [{item['priority']}] {item['task']} — owner: {item['owner'] or 'N/A'}")
    print()


def example_owner_filter():
    """Filter and report per owner."""
    print("=" * 50)
    print("ADVANCED 4 — Per-owner action items")
    print("=" * 50)

    parser = MeetingNotesParser()
    results = [parser.parse(NOTES_A), parser.parse(NOTES_B)]

    owner_map: dict[str, list] = {}
    for result in results:
        for item in result.action_items:
            key = item.owner or "Unassigned"
            owner_map.setdefault(key, []).append(item)

    for owner, items in sorted(owner_map.items()):
        print(f"{owner} ({len(items)} task(s)):")
        for item in items:
            print(f"  • [{item.priority}] {item.task}")
    print()


def example_custom_export():
    """Build a custom markdown export."""
    print("=" * 50)
    print("ADVANCED 5 — Custom markdown export")
    print("=" * 50)

    parser = MeetingNotesParser()
    result = parser.parse(NOTES_A)

    lines = [f"# {result.meeting_info.get('title', 'Meeting Notes')}", ""]
    if result.meeting_info.get("date"):
        lines.append(f"**Date:** {result.meeting_info['date']}  ")
    if result.meeting_info.get("attendees"):
        lines.append(f"**Attendees:** {', '.join(result.meeting_info['attendees'])}  ")
    lines.append("")

    if result.action_items:
        lines.append("## Action Items")
        for item in result.action_items:
            deadline = f" *(due {item.deadline})*" if item.deadline else ""
            owner = f" — **{item.owner}**" if item.owner else ""
            lines.append(f"- [ ] {item.task}{owner}{deadline}")
        lines.append("")

    if result.decisions:
        lines.append("## Decisions")
        for d in result.decisions:
            lines.append(f"- {d}")
        lines.append("")

    print("\n".join(lines))


if __name__ == "__main__":
    example_batch_processing()
    example_file_roundtrip()
    example_json_to_dict()
    example_owner_filter()
    example_custom_export()
