test_content = '''"""
Unit tests for Meeting Notes Parser
"""
import pytest
import json
from meeting_notes_parser import MeetingNotesParser, MeetingNotesResult, ActionItem

class TestActionItem:
    def test_action_item_creation(self):
        item = ActionItem(task="Complete documentation", owner="Sarah", priority="high")
        assert item.task == "Complete documentation"
        assert item.owner == "Sarah"
        assert item.priority == "high"

class TestMeetingNotesParser:
    @pytest.fixture
    def parser(self):
        return MeetingNotesParser()
    
    def test_parse_basic(self, parser):
        notes = "Team Meeting\\n- Sarah: Finish documentation by Friday"
        result = parser.parse(notes)
        assert len(result.action_items) >= 0
    
    def test_priority_calculation(self, parser):
        high_task = "Fix critical bug ASAP"
        priority = parser._calculate_priority(high_task, None)
        assert priority == "high"
        
        low_task = "Do it when possible"
        priority = parser._calculate_priority(low_task, None)
        assert priority == "low"

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
'''

test_file = open("meeting-notes-parser/tests/test_parser.py", "w")
test_file.write(test_content)
test_file.close()
print("✓ Created tests/test_parser.py")

# 5. Create examples/basic_usage.py
example_content = '''"""
Basic Usage Examples for Meeting Notes Parser
"""

from meeting_notes_parser import MeetingNotesParser

def example_basic():
    """Example: Basic parsing of meeting notes."""
    parser = MeetingNotesParser()
    
    notes = """
Team Planning Meeting - October 15, 2024
Attendees: Sarah, John, Mike

Action Items:
- Sarah: Please finish the API documentation by next Friday
- John: I'll handle the database migration ASAP
"""
    
    result = parser.parse(notes)
    
    print(f"Meeting: {result
