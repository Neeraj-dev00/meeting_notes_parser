"""
meeting-notes-parser
~~~~~~~~~~~~~~~~~~~~
Extract action items, decisions, and key points from unstructured meeting notes.

Basic usage::

    from meeting_notes_parser import MeetingNotesParser

    parser = MeetingNotesParser()
    result = parser.parse(open("notes.txt").read())
    print(result.export_json())
"""

from .parser import MeetingNotesParser, MeetingNotesResult, ActionItem

__version__ = "1.0.0"
__author__ = "Your Name"
__license__ = "MIT"

__all__ = [
    "MeetingNotesParser",
    "MeetingNotesResult",
    "ActionItem",
]
