> Vendored from [anthropics/claude-plugins-official](https://github.com/anthropics/claude-plugins-official/tree/a7ba5b93db0c7c8d17f3f1d25853adca79598a1a/plugins/claude-md-management) at `a7ba5b9` (Apache-2.0). Only change: renamed from `claude-md-management`, because Claude Code reserves `claude-*` names for third-party marketplaces and Codex requires the marketplace and manifest names to match.

# CLAUDE.md Management Plugin

Tools to maintain and improve CLAUDE.md files - audit quality, capture session learnings, and keep project memory current.

## What It Does

Two complementary tools for different purposes:

| | claude-md-improver (skill) | /revise-claude-md (command) |
|---|---|---|
| **Purpose** | Keep CLAUDE.md aligned with codebase | Capture session learnings |
| **Triggered by** | Codebase changes | End of session |
| **Use when** | Periodic maintenance | Session revealed missing context |

## Usage

### Skill: claude-md-improver

Audits CLAUDE.md files against current codebase state:

```
"audit my CLAUDE.md files"
"check if my CLAUDE.md is up to date"
```

<img src="claude-md-improver-example.png" alt="CLAUDE.md improver showing quality scores and recommended updates" width="600">

### Command: /revise-claude-md

Captures learnings from the current session:

```
/revise-claude-md
```

<img src="revise-claude-md-example.png" alt="Revise command capturing session learnings into CLAUDE.md" width="600">

## Author

Isabella He (isabella@anthropic.com)
