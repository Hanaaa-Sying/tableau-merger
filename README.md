# tableau-merger

A Claude Code slash command (`/tableaumerger`) for merging multiple Tableau `.twbx` files into a single workbook with a dashboard.

## Background

Tableau Public does not support copying sheets between workbooks via the GUI. This skill documents a Python-based approach — treating `.twbx` files as ZIP archives and merging their XML directly — along with hard-won lessons about Tableau's strict XML content model.

## Install the skill

### User-level (available in all projects)

```powershell
# Windows
Copy-Item .claude\commands\tableaumerger.md "$env:USERPROFILE\.claude\commands\"
```

```bash
# macOS / Linux
cp .claude/commands/tableaumerger.md ~/.claude/commands/
```

### Project-level (available in one project only)

```powershell
# Windows
Copy-Item .claude\commands\tableaumerger.md "your\project\.claude\commands\"
```

Then in Claude Code, type `/tableaumerger` to invoke it.

## What's included

- `.claude/skills/tableau-merger/tableau-merger.md` — the slash command definition
- `merge_twbx.py` — a complete, working merge script (uses Python standard library only)

## Requirements

- Python 3.x (standard library only, no pip installs)
- Tableau Public desktop app
- All `.twbx` files must share the same data schema
