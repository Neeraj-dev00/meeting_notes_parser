"""
Meeting Notes Parser - Core Implementation

Extracts action items, decisions, and key points from unstructured meeting notes.
"""

import json
import csv
import io
import re
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict, field

try:
    from dateutil import parser as date_parser
    from dateutil.relativedelta import relativedelta
    HAS_DATEUTIL = True
except ImportError:
    HAS_DATEUTIL = False


@dataclass
class ActionItem:
    """Represents a single action item extracted from meeting notes."""
    task: str
    owner: Optional[str] = None
    deadline: Optional[str] = None
    priority: str = "medium"
    confidence: float = 0.85

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class MeetingNotesResult:
    """Container for all parsed meeting notes data."""
    meeting_info: Dict[str, Any] = field(default_factory=dict)
    action_items: List[ActionItem] = field(default_factory=list)
    decisions: List[str] = field(default_factory=list)
    key_points: List[str] = field(default_factory=list)

    def export_json(self, indent: int = 2) -> str:
        """Export results to JSON format."""
        data = {
            "meeting_info": self.meeting_info,
            "action_items": [item.to_dict() for item in self.action_items],
            "decisions": self.decisions,
            "key_points": self.key_points,
        }
        return json.dumps(data, indent=indent, default=str)

    def export_csv(self) -> str:
        """Export action items to CSV format."""
        output = io.StringIO()
        fieldnames = ["task", "owner", "deadline", "priority", "confidence"]
        writer = csv.DictWriter(output, fieldnames=fieldnames)
        writer.writeheader()
        for item in self.action_items:
            writer.writerow(item.to_dict())
        return output.getvalue()

    def to_slack_message(self) -> str:
        """Format results as a Slack-compatible message."""
        blocks = ["*Meeting Notes Summary*"]

        if self.meeting_info.get("title"):
            blocks.append(f"*Title:* {self.meeting_info['title']}")
        if self.meeting_info.get("date"):
            blocks.append(f"*Date:* {self.meeting_info['date']}")
        if self.meeting_info.get("attendees"):
            blocks.append(f"*Attendees:* {', '.join(self.meeting_info['attendees'])}")

        blocks.append(f"\n*Action Items ({len(self.action_items)}):*")
        for i, item in enumerate(self.action_items, 1):
            owner_part = f" (@{item.owner})" if item.owner else ""
            deadline_part = f" — due {item.deadline}" if item.deadline else ""
            priority_emoji = {"high": "🔴", "medium": "🟡", "low": "🟢"}.get(item.priority, "⚪")
            blocks.append(f"{i}. {priority_emoji} {item.task}{owner_part}{deadline_part}")

        if self.decisions:
            blocks.append(f"\n*Decisions ({len(self.decisions)}):*")
            for i, decision in enumerate(self.decisions, 1):
                blocks.append(f"{i}. ✅ {decision}")

        if self.key_points:
            blocks.append(f"\n*Key Points ({len(self.key_points)}):*")
            for i, point in enumerate(self.key_points, 1):
                blocks.append(f"{i}. 📌 {point}")

        return "\n".join(blocks)

    def summary(self) -> str:
        """Return a short human-readable summary."""
        parts = [
            f"{len(self.action_items)} action item(s)",
            f"{len(self.decisions)} decision(s)",
            f"{len(self.key_points)} key point(s)",
        ]
        title = self.meeting_info.get("title", "Meeting")
        return f"{title}: " + ", ".join(parts)


class MeetingNotesParser:
    """
    Parser for extracting structured data from unstructured meeting notes.

    Features:
    - Extract action items with owners, deadlines, and priorities
    - Parse natural language dates (requires python-dateutil)
    - Auto-calculate priority from urgency keywords
    - Export to JSON, CSV, or Slack-formatted text
    - Parse from string or file

    Example::

        parser = MeetingNotesParser()
        result = parser.parse(notes_text)
        print(result.export_json())
    """

    PRIORITY_KEYWORDS: Dict[str, List[str]] = {
        "high": ["urgent", "asap", "critical", "important", "priority", "immediately", "right away", "right now", "blocker"],
        "medium": ["soon", "this week", "next week", "shortly"],
        "low": ["eventually", "later", "when possible", "no rush", "backlog", "someday"],
    }

    # Patterns ordered from most-specific to least-specific
    ACTION_PATTERNS = [
        # "Sarah will finish the report by Friday"
        r"(?P<owner>[A-Z][a-z]+(?:\s[A-Z][a-z]+)?)\s+(?:will|'ll|should|needs? to|must)\s+(?P<task>.+?)(?:\s+by\s+(?P<deadline>[^.\n]+))?[.\n]?$",
        # "Sarah: Please finish the report by Friday"
        r"(?P<owner>[A-Z][a-z]+(?:\s[A-Z][a-z]+)?):\s*(?:please\s+)?(?P<task>.+?)(?:\s+by\s+(?P<deadline>[^.\n]+))?[.\n]?$",
        # "- [ ] Finish report (Sarah) by Friday"
        r"[-*]\s*(?:\[[ x]\]\s*)?(?P<task>[^(]+?)\s*(?:\((?P<owner>[^)]+)\))?\s*(?:by\s+(?P<deadline>[^.\n]+))?[.\n]?$",
    ]

    def __init__(self):
        self.priority_keywords = {k: list(v) for k, v in self.PRIORITY_KEYWORDS.items()}
        self.default_priority = "medium"

    # ------------------------------------------------------------------ #
    #  Public API                                                          #
    # ------------------------------------------------------------------ #

    def parse(self, text: str) -> MeetingNotesResult:
        """Parse meeting notes text and return a MeetingNotesResult."""
        text = self._normalise(text)
        return MeetingNotesResult(
            meeting_info=self._extract_meeting_info(text),
            action_items=self._extract_action_items(text),
            decisions=self._extract_decisions(text),
            key_points=self._extract_key_points(text),
        )

    def parse_file(self, filepath: str) -> MeetingNotesResult:
        """Parse meeting notes from a plain-text file."""
        with open(filepath, "r", encoding="utf-8") as fh:
            return self.parse(fh.read())

    # ------------------------------------------------------------------ #
    #  Internal helpers                                                    #
    # ------------------------------------------------------------------ #

    @staticmethod
    def _normalise(text: str) -> str:
        """Normalise line endings and strip trailing whitespace."""
        return "\n".join(line.rstrip() for line in text.replace("\r\n", "\n").splitlines())

    def _extract_meeting_info(self, text: str) -> Dict[str, Any]:
        """Extract meeting metadata: title, date, attendees."""
        info: Dict[str, Any] = {"title": None, "date": None, "attendees": []}

        # Title: first non-empty, non-bullet line
        for line in text.splitlines()[:5]:
            stripped = line.strip()
            if stripped and not stripped.startswith(("-", "*", "#")):
                info["title"] = stripped
                break

        # Date
        date_match = re.search(
            r"\b(\w+\s+\d{1,2},?\s+\d{4}|\d{1,2}[/-]\d{1,2}[/-]\d{2,4})\b",
            text, re.IGNORECASE,
        )
        if date_match:
            info["date"] = date_match.group(1)

        # Attendees
        attendees_match = re.search(
            r"(?:attendees?|participants?|present|with)[:\s]+(.+?)(?:\n\n|\n(?=\w)|\Z)",
            text, re.IGNORECASE | re.DOTALL,
        )
        if attendees_match:
            raw = attendees_match.group(1)
            info["attendees"] = [
                a.strip().lstrip("-* ")
                for a in re.split(r"[,\n]", raw)
                if a.strip()
            ]

        return info

    def _extract_action_items(self, text: str) -> List[ActionItem]:
        """Extract action items, de-duplicating by task text."""
        items: List[ActionItem] = []
        seen: set = set()

        # Focus on the action-items section when present
        section = self._get_section(text, r"action\s+items?|todos?|tasks?")
        lines = (section or text).splitlines()

        for line in lines:
            stripped = line.strip()
            if not stripped:
                continue

            for pattern in self.ACTION_PATTERNS:
                m = re.search(pattern, stripped, re.IGNORECASE)
                if not m:
                    continue

                groups = m.groupdict()
                task = re.sub(r"\s+", " ", (groups.get("task") or "").strip())
                owner = (groups.get("owner") or "").strip() or None
                deadline_raw = (groups.get("deadline") or "").strip() or None

                if not task or len(task) < 4:
                    continue

                key = task.lower()
                if key in seen:
                    break
                seen.add(key)

                items.append(ActionItem(
                    task=task,
                    owner=owner,
                    deadline=self._parse_deadline(deadline_raw) if deadline_raw else None,
                    priority=self._calculate_priority(task, deadline_raw),
                    confidence=0.85,
                ))
                break  # first matching pattern wins

        return items

    def _calculate_priority(self, task: str, deadline: Optional[str]) -> str:
        """Derive priority from keyword signals in task and deadline text."""
        combined = f"{task} {deadline or ''}".lower()
        for level in ("high", "medium", "low"):
            if any(kw in combined for kw in self.priority_keywords[level]):
                return level
        return self.default_priority

    def _parse_deadline(self, deadline_text: str) -> Optional[str]:
        """Convert natural-language deadline to ISO-8601 date string."""
        if not deadline_text:
            return None

        text = deadline_text.strip().lower()
        today = datetime.now()

        # Simple relative patterns (no dateutil needed)
        simple: Dict[str, datetime] = {
            "today": today,
            "tomorrow": today + timedelta(days=1),
            "next week": today + timedelta(weeks=1),
            "next month": today + timedelta(days=30),
            "end of week": today + timedelta(days=(4 - today.weekday()) % 7 or 7),
            "eow": today + timedelta(days=(4 - today.weekday()) % 7 or 7),
            "eod": today,
        }
        for label, dt in simple.items():
            if label in text:
                return dt.strftime("%Y-%m-%d")

        # Named weekdays
        weekdays = {"monday": 0, "tuesday": 1, "wednesday": 2, "thursday": 3,
                    "friday": 4, "saturday": 5, "sunday": 6}
        for name, idx in weekdays.items():
            if name in text:
                days_ahead = (idx - today.weekday()) % 7 or 7
                return (today + timedelta(days=days_ahead)).strftime("%Y-%m-%d")

        # Fall back to dateutil if available
        if HAS_DATEUTIL:
            try:
                return date_parser.parse(deadline_text, dayfirst=False).strftime("%Y-%m-%d")
            except (ValueError, OverflowError):
                pass

        return deadline_text  # return as-is when unparseable

    def _get_section(self, text: str, heading_pattern: str) -> Optional[str]:
        """Extract a named section from the notes (returns None if not found)."""
        m = re.search(
            rf"(?:^|\n)(?:#+\s*)?(?:{heading_pattern})[:\s]*\n(.+?)(?=\n(?:#+\s*)?\w|$)",
            text, re.IGNORECASE | re.DOTALL,
        )
        return m.group(1) if m else None

    def _extract_decisions(self, text: str) -> List[str]:
        """Extract decisions made during the meeting."""
        section = self._get_section(text, r"decisions?|agreed?|resolved?")
        if not section:
            return []
        return self._parse_bullet_list(section)

    def _extract_key_points(self, text: str) -> List[str]:
        """Extract key discussion points."""
        section = self._get_section(text, r"key\s+points?|discussion\s+points?|highlights?|notes?")
        if not section:
            return []
        return self._parse_bullet_list(section)

    @staticmethod
    def _parse_bullet_list(text: str) -> List[str]:
        """Turn a block of bullet lines into a clean list of strings."""
        results = []
        for line in text.splitlines():
            item = line.strip().lstrip("-*•·").strip()
            if item and len(item) > 2:
                results.append(item)
        return results
  
