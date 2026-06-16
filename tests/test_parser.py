"""
Unit tests for Meeting Notes Parser
Run with:  pytest tests/ -v
"""

import json
import pytest
import sys
import os

# Allow running tests from the repo root without installing the package
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from parser import MeetingNotesParser, MeetingNotesResult, ActionItem


# ------------------------------------------------------------------ #
#  Fixtures                                                            #
# ------------------------------------------------------------------ #

@pytest.fixture
def parser():
    return MeetingNotesParser()


SIMPLE_NOTES = """\
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
- We need better test coverage before launch
"""


# ------------------------------------------------------------------ #
#  ActionItem                                                          #
# ------------------------------------------------------------------ #

class TestActionItem:
    def test_default_priority(self):
        item = ActionItem(task="Do something")
        assert item.priority == "medium"
        assert item.confidence == 0.85
        assert item.owner is None
        assert item.deadline is None

    def test_to_dict_keys(self):
        item = ActionItem(task="Write docs", owner="Sarah", deadline="2024-10-18", priority="high")
        d = item.to_dict()
        assert set(d.keys()) == {"task", "owner", "deadline", "priority", "confidence"}

    def test_to_dict_values(self):
        item = ActionItem(task="Deploy service", owner="John", priority="low")
        d = item.to_dict()
        assert d["task"] == "Deploy service"
        assert d["owner"] == "John"
        assert d["priority"] == "low"


# ------------------------------------------------------------------ #
#  MeetingNotesResult                                                  #
# ------------------------------------------------------------------ #

class TestMeetingNotesResult:
    @pytest.fixture
    def result(self, parser):
        return parser.parse(SIMPLE_NOTES)

    def test_export_json_is_valid(self, result):
        raw = result.export_json()
        data = json.loads(raw)
        assert "meeting_info" in data
        assert "action_items" in data
        assert "decisions" in data
        assert "key_points" in data

    def test_export_csv_has_header(self, result):
        csv_text = result.export_csv()
        first_line = csv_text.splitlines()[0]
        assert "task" in first_line
        assert "owner" in first_line
        assert "deadline" in first_line

    def test_export_csv_rows_match_items(self, result):
        csv_text = result.export_csv()
        lines = [l for l in csv_text.splitlines() if l.strip()]
        # header + one row per action item
        assert len(lines) == len(result.action_items) + 1

    def test_to_slack_message_contains_emoji(self, result):
        msg = result.to_slack_message()
        assert "🔴" in msg or "🟡" in msg or "🟢" in msg

    def test_to_slack_message_contains_title(self, result):
        msg = result.to_slack_message()
        assert "Q3 Planning Meeting" in msg

    def test_summary_string(self, result):
        s = result.summary()
        assert "action item" in s
        assert "decision" in s


# ------------------------------------------------------------------ #
#  MeetingNotesParser — meeting info                                   #
# ------------------------------------------------------------------ #

class TestExtractMeetingInfo:
    def test_title_extracted(self, parser):
        result = parser.parse(SIMPLE_NOTES)
        assert result.meeting_info["title"] is not None
        assert "Planning" in result.meeting_info["title"]

    def test_date_extracted(self, parser):
        result = parser.parse(SIMPLE_NOTES)
        assert result.meeting_info["date"] is not None

    def test_attendees_extracted(self, parser):
        result = parser.parse(SIMPLE_NOTES)
        attendees = result.meeting_info["attendees"]
        assert len(attendees) >= 2
        names = [a.lower() for a in attendees]
        assert any("sarah" in n for n in names)
        assert any("john" in n for n in names)

    def test_no_crash_on_empty_input(self, parser):
        result = parser.parse("")
        assert result.meeting_info["title"] is None
        assert result.action_items == []


# ------------------------------------------------------------------ #
#  MeetingNotesParser — action items                                   #
# ------------------------------------------------------------------ #

class TestExtractActionItems:
    def test_finds_action_items(self, parser):
        result = parser.parse(SIMPLE_NOTES)
        assert len(result.action_items) > 0

    def test_owner_assigned(self, parser):
        result = parser.parse(SIMPLE_NOTES)
        owners = [item.owner for item in result.action_items if item.owner]
        assert len(owners) > 0

    def test_all_items_have_tasks(self, parser):
        result = parser.parse(SIMPLE_NOTES)
        for item in result.action_items:
            assert item.task and len(item.task) > 0

    def test_no_duplicate_tasks(self, parser):
        result = parser.parse(SIMPLE_NOTES)
        tasks = [item.task.lower() for item in result.action_items]
        assert len(tasks) == len(set(tasks))

    def test_colon_pattern(self, parser):
        notes = "Sarah: update the roadmap slides by Thursday"
        result = parser.parse(notes)
        assert any("roadmap" in item.task.lower() for item in result.action_items)

    def test_will_pattern(self, parser):
        notes = "John will deploy the service by Monday"
        result = parser.parse(notes)
        assert any("deploy" in item.task.lower() for item in result.action_items)

    def test_bullet_checkbox_pattern(self, parser):
        notes = "- [ ] Refactor auth module (Alice) by next Friday"
        result = parser.parse(notes)
        assert any("auth" in item.task.lower() or "refactor" in item.task.lower()
                   for item in result.action_items)


# ------------------------------------------------------------------ #
#  MeetingNotesParser — priority                                       #
# ------------------------------------------------------------------ #

class TestPriorityCalculation:
    def test_high_on_asap(self, parser):
        assert parser._calculate_priority("Fix the bug ASAP", None) == "high"

    def test_high_on_critical(self, parser):
        assert parser._calculate_priority("Critical: server is down", None) == "high"

    def test_high_on_urgent(self, parser):
        assert parser._calculate_priority("Urgent deployment needed", None) == "high"

    def test_low_on_eventually(self, parser):
        assert parser._calculate_priority("Refactor codebase eventually", None) == "low"

    def test_low_on_no_rush(self, parser):
        assert parser._calculate_priority("Update readme, no rush", None) == "low"

    def test_medium_is_default(self, parser):
        assert parser._calculate_priority("Write tests", None) == "medium"

    def test_deadline_contributes(self, parser):
        # "this week" in deadline text → medium
        assert parser._calculate_priority("Deploy staging", "this week") == "medium"


# ------------------------------------------------------------------ #
#  MeetingNotesParser — deadline parsing                               #
# ------------------------------------------------------------------ #

class TestDeadlineParsing:
    def test_tomorrow(self, parser):
        from datetime import datetime, timedelta
        expected = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
        assert parser._parse_deadline("tomorrow") == expected

    def test_today(self, parser):
        from datetime import datetime
        expected = datetime.now().strftime("%Y-%m-%d")
        assert parser._parse_deadline("today") == expected

    def test_eod(self, parser):
        from datetime import datetime
        expected = datetime.now().strftime("%Y-%m-%d")
        assert parser._parse_deadline("EOD") == expected

    def test_next_week(self, parser):
        from datetime import datetime, timedelta
        result = parser._parse_deadline("next week")
        assert result is not None
        # Should be 7 days out, give or take a day for test timing
        parsed = datetime.strptime(result, "%Y-%m-%d")
        diff = (parsed - datetime.now()).days
        assert 6 <= diff <= 8

    def test_friday(self, parser):
        result = parser._parse_deadline("Friday")
        assert result is not None
        from datetime import datetime
        parsed = datetime.strptime(result, "%Y-%m-%d")
        assert parsed.weekday() == 4  # 4 = Friday

    def test_none_input(self, parser):
        assert parser._parse_deadline(None) is None  # type: ignore

    def test_empty_string(self, parser):
        assert parser._parse_deadline("") is None

    def test_unparseable_falls_back(self, parser):
        result = parser._parse_deadline("sometime soon-ish")
        # Should not raise; returns text as-is or a best-effort value
        assert result is not None


# ------------------------------------------------------------------ #
#  MeetingNotesParser — decisions & key points                         #
# ------------------------------------------------------------------ #

class TestDecisionsAndKeyPoints:
    def test_decisions_extracted(self, parser):
        result = parser.parse(SIMPLE_NOTES)
        assert len(result.decisions) > 0

    def test_decisions_are_strings(self, parser):
        result = parser.parse(SIMPLE_NOTES)
        for d in result.decisions:
            assert isinstance(d, str) and len(d) > 0

    def test_key_points_extracted(self, parser):
        result = parser.parse(SIMPLE_NOTES)
        assert len(result.key_points) > 0

    def test_no_decisions_section(self, parser):
        result = parser.parse("Just a title\n- Do something")
        assert result.decisions == []

    def test_no_key_points_section(self, parser):
        result = parser.parse("Just a title\n- Do something")
        assert result.key_points == []


# ------------------------------------------------------------------ #
#  Edge cases                                                          #
# ------------------------------------------------------------------ #

class TestEdgeCases:
    def test_empty_string(self, parser):
        result = parser.parse("")
        assert isinstance(result, MeetingNotesResult)

    def test_whitespace_only(self, parser):
        result = parser.parse("   \n\n   ")
        assert result.action_items == []

    def test_no_action_items(self, parser):
        result = parser.parse("Just a casual chat.\n\nNothing was decided.")
        assert isinstance(result.action_items, list)

    def test_very_long_input(self, parser):
        big = SIMPLE_NOTES * 50
        result = parser.parse(big)
        assert isinstance(result, MeetingNotesResult)

    def test_unicode_names(self, parser):
        notes = "Søren will update translations by Friday"
        result = parser.parse(notes)
        assert isinstance(result, MeetingNotesResult)

    def test_parse_file(self, parser, tmp_path):
        p = tmp_path / "notes.txt"
        p.write_text(SIMPLE_NOTES, encoding="utf-8")
        result = parser.parse_file(str(p))
        assert len(result.action_items) > 0
