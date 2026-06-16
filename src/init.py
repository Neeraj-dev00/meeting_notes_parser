init_content = '''"""
Meeting Notes Parser - Extract action items from meeting notes
"""

from .parser import MeetingNotesParser, MeetingNotesResult

version = "1.0.0"
author = "AI Assistant"

all = ["MeetingNotesParser", "MeetingNotesResult"]
'''

init_file = open("meeting-notes-parser/src/init.py", "w")
init_file.write(init_content)
init_file.close()
print("✓ Created src/init.py")
