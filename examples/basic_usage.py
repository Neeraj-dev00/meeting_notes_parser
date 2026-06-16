"""
examples/basic_usage.py
-----------------------
Demonstrates the most common ways to use MeetingNotesParser.
Run from the repo root:
    python examples/basic_usage.py
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from parser import MeetingNotesParser  # noqa: E402


# ------------------------------------------------------------------ #
#  Sample notes                                                        #
# ------------------------------------------------------------------ #

SAMPLE_NOTES = """\
Q3 Planning Meeting — October 15, 2024
Attendees: Sarah, John, Mike

Action Items:
- Sarah will finish the API documentation by Friday
- John: please migrate the database ASAP
- Mike will write unit tests by next week

Decisions:
- We agreed to adopt trunk-based development
- Launch date moved to November 1

Key Points:
- The current CI pipeline is too slow
- We need better test coverage before the launch
"""


def example_basic():
    """Parse notes and print a plain-text summary."""
    print("=" * 50)
    print("EXAMPLE 1 — Plain text output")
    print("=" * 50)

    parser = MeetingNotesParser()
    result = parser.parse(SAMPLE_NOTES)

    print(f"Meeting : {result.meeting_info.get('title')}")
    print(f"Date    : {result.meeting_info.get('date')}")
    print(f"Attendees: {', '.join(result.meeting_info.get('attendees', []))}")
    print()

    print(f"Action Items ({len(result.action_items)}):")
    for i, item in enumerate(result.action_items, 1):
        print(f"  {i}. [{item.priority.upper()}] {item.task}")
        if item.owner:
            print(f"       Owner   : {item.owner}")
        if item.deadline:
            print(f"       Deadline: {item.deadline}")
    print()

    print(f"Decisions ({len(result.decisions)}):")
    for d in result.decisions:
        print(f"  • {d}")
    print()

    print(f"Key Points ({len(result.key_points)}):")
    for p in result.key_points:
        print(f"  • {p}")
    print()


def example_json_export():
    """Export parsed results to JSON."""
    print("=" * 50)
    print("EXAMPLE 2 — JSON export")
    print("=" * 50)

    parser = MeetingNotesParser()
    result = parser.parse(SAMPLE_NOTES)
    print(result.export_json())
    print()


def example_csv_export():
    """Export action items as CSV."""
    print("=" * 50)
    print("EXAMPLE 3 — CSV export (action items only)")
    print("=" * 50)

    parser = MeetingNotesParser()
    result = parser.parse(SAMPLE_NOTES)
    print(result.export_csv())


def example_slack_message():
    """Format results as a Slack message."""
    print("=" * 50)
    print("EXAMPLE 4 — Slack message")
    print("=" * 50)

    parser = MeetingNotesParser()
    result = parser.parse(SAMPLE_NOTES)
    print(result.to_slack_message())
    print()


def example_filter_by_priority():
    """Filter action items by priority level."""
    print("=" * 50)
    print("EXAMPLE 5 — Filter by priority (high only)")
    print("=" * 50)

    parser = MeetingNotesParser()
    result = parser.parse(SAMPLE_NOTES)

    high_priority = [item for item in result.action_items if item.priority == "high"]
    print(f"High-priority items: {len(high_priority)}")
    for item in high_priority:
        print(f"  🔴 {item.task} (owner: {item.owner or 'unassigned'})")
    print()


def example_custom_priorities():
    """Add custom priority keywords."""
    print("=" * 50)
    print("EXAMPLE 6 — Custom priority keywords")
    print("=" * 50)

    parser = MeetingNotesParser()
    parser.priority_keywords["high"].extend(["p0", "showstopper", "hotfix"])
    parser.priority_keywords["low"].extend(["nice-to-have", "stretch goal"])

    notes = "Alice will deploy the hotfix by EOD\nBob: add dark-mode toggle — nice-to-have"
    result = parser.parse(notes)
    for item in result.action_items:
        print(f"  [{item.priority}] {item.task}")
    print()


if __name__ == "__main__":
    example_basic()
    example_json_export()
    example_csv_export()
    example_slack_message()
    example_filter_by_priority()
    example_custom_priorities()
