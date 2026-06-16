# IronClaw Skill Submission

---

## Task 1 — Skill Name & Problem It Solves

**Skill Name:** `meeting-notes-parser`

**Problem it solves:**

After every meeting, someone has to manually read through messy,
unstructured notes and figure out:
- Who is doing what?
- By when?
- What was decided?
- What were the key points discussed?

This is tedious and error-prone. The `meeting-notes-parser` skill
automates this entirely. You paste in raw meeting notes in any
free-form style and the skill outputs structured, actionable data
with owners, deadlines, and priority levels auto-detected from
natural language.

**Use cases:**
- Automatically post action items to Slack after a meeting
- Sync tasks to Jira / Asana / Trello via the JSON export
- Drop the CSV straight into Excel or Google Sheets for tracking
- Never lose a decision or action item again

---

## Task 2 — Working Interaction / Output

### INPUT (raw unstructured meeting notes):

```
Sprint Planning Meeting - June 16, 2025
Attendees: Arjun, Priya, Dev, Sneha

Action Items:
- Arjun will fix the login bug ASAP
- Priya: update API docs by Friday
- Dev will review PRs by next week
- Sneha: deploy staging build when possible

Decisions:
- We agreed to freeze the feature branch on June 20
- QA sign-off required before any production deploy

Key Points:
- Auth service latency is above threshold at 900ms
- Mobile team needs backend endpoints ready by June 18
```

---

### OUTPUT 1 — Plain Text

```
Meeting  : Sprint Planning Meeting - June 16, 2025
Date     : June 16, 2025
Attendees: Arjun, Priya, Dev, Sneha

Action Items (4):
  1. [HIGH] fix the login bug ASAP
       Owner   : Arjun

  2. [MED]  update API docs
       Owner   : Priya
       Deadline: 2026-06-19

  3. [MED]  review PRs
       Owner   : Dev
       Deadline: 2026-06-23

  4. [LOW]  deploy staging build when possible
       Owner   : Sneha

Decisions (2):
  * We agreed to freeze the feature branch on June 20
  * QA sign-off required before any production deploy

Key Points (2):
  * Auth service latency is above threshold at 900ms
  * Mobile team needs backend endpoints ready by June 18
```

---

### OUTPUT 2 — JSON (for API / integrations)

```json
{
  "meeting_info": {
    "title": "Sprint Planning Meeting - June 16, 2025",
    "date": "June 16, 2025",
    "attendees": ["Arjun", "Priya", "Dev", "Sneha"]
  },
  "action_items": [
    {
      "task": "fix the login bug ASAP",
      "owner": "Arjun",
      "deadline": null,
      "priority": "high",
      "confidence": 0.85
    },
    {
      "task": "update API docs",
      "owner": "Priya",
      "deadline": "2026-06-19",
      "priority": "medium",
      "confidence": 0.85
    },
    {
      "task": "review PRs",
      "owner": "Dev",
      "deadline": "2026-06-23",
      "priority": "medium",
      "confidence": 0.85
    },
    {
      "task": "deploy staging build when possible",
      "owner": "Sneha",
      "deadline": null,
      "priority": "low",
      "confidence": 0.85
    }
  ],
  "decisions": [
    "We agreed to freeze the feature branch on June 20",
    "QA sign-off required before any production deploy"
  ],
  "key_points": [
    "Auth service latency is above threshold at 900ms",
    "Mobile team needs backend endpoints ready by June 18"
  ]
}
```

---

### OUTPUT 3 — Slack Message (paste directly into Slack)

```
*Meeting Notes Summary*
*Title:* Sprint Planning Meeting - June 16, 2025
*Date:* June 16, 2025
*Attendees:* Arjun, Priya, Dev, Sneha

*Action Items (4):*
1. 🔴 fix the login bug ASAP (@Arjun)
2. 🟡 update API docs (@Priya) — due 2026-06-19
3. 🟡 review PRs (@Dev) — due 2026-06-23
4. 🟢 deploy staging build when possible (@Sneha)

*Decisions (2):*
1. ✅ We agreed to freeze the feature branch on June 20
2. ✅ QA sign-off required before any production deploy

*Key Points (2):*
1. 📌 Auth service latency is above threshold at 900ms
2. 📌 Mobile team needs backend endpoints ready by June 18
```

---

### OUTPUT 4 — CSV (Excel / Google Sheets ready)

```csv
task,owner,deadline,priority,confidence
fix the login bug ASAP,Arjun,,high,0.85
update API docs,Priya,2026-06-19,medium,0.85
review PRs,Dev,2026-06-23,medium,0.85
deploy staging build when possible,Sneha,,low,0.85
```

---

### How to reproduce:

```bash
pip install python-dateutil
python src/cli.py examples/sample_notes.txt                        # text
python src/cli.py examples/sample_notes.txt --format json          # JSON
python src/cli.py examples/sample_notes.txt --format slack         # Slack
python src/cli.py examples/sample_notes.txt --format csv           # CSV
python src/cli.py examples/sample_notes.txt --priority high        # filter
python src/cli.py examples/sample_notes.txt --owner Priya          # by owner
```

---

## Task 3 — GitHub PR Link

### Step 1 — Create repo on GitHub
```
1. Go to https://github.com/new
2. Name: meeting-notes-parser
3. Visibility: Public
4. Do NOT check "Add README"
5. Click "Create repository"
```

### Step 2 — Push code
```bash
cd meeting-notes-parser
git init
git add .
git commit -m "feat: add meeting-notes-parser IronClaw skill"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/meeting-notes-parser.git
git push -u origin main
```

### Step 3 — Create PR branch
```bash
git checkout -b feature/ironclaw-skill-submission
git push origin feature/ironclaw-skill-submission
```

### Step 4 — Open PR on GitHub
```
1. Go to your repo on GitHub
2. Click "Compare & pull request"
3. Title: feat: meeting-notes-parser — IronClaw skill submission
4. Click "Create pull request"
5. Copy the PR URL → submit that as Task 3
```

**PR URL format:**
```
https://github.com/YOUR_USERNAME/meeting-notes-parser/pull/1
```

---

## Project Structure

```
meeting-notes-parser/
├── src/
│   ├── __init__.py          ← package exports
│   ├── parser.py            ← core skill logic
│   └── cli.py               ← command-line interface
├── tests/
│   └── test_parser.py       ← 35 unit tests
├── examples/
│   ├── sample_notes.txt     ← example input
│   ├── basic_usage.py       ← 6 usage demos
│   └── advanced_usage.py    ← batch, filters, custom exports
├── .github/workflows/ci.yml ← GitHub Actions CI
├── SKILL.md                 ← this file (all 3 tasks)
├── pyproject.toml
├── requirements.txt
├── .gitignore
├── LICENSE
└── README.md
```
