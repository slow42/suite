---
name: add-to-suite
description: Add a plugin or skill to the suite marketplace repo (github.com/slow42/suite) so it loads in Claude Code, Codex, and Cursor. Use when the user says "add this to my suite", "make this a plugin", "turn this into a skill in suite", or wants to package a workflow, prompt, hook, or MCP server for their agents.
---

# Add to suite

`.claude-plugin/marketplace.json` is the one index; Claude Code and Codex both read it. `python3 scripts/suite.py sync` derives everything else (each plugin's Agent Plugins `plugin.json`, Cursor's marketplace). Never hand-edit generated files.

## Pick the component type, most portable first

| Type | Lives in | Loads in |
|---|---|---|
| Skill | `skills/<name>/SKILL.md` | Claude Code, Codex, Cursor, any Agent Skills client |
| MCP server | `.mcp.json` | Claude Code, Codex, Cursor |
| Hook | `hooks/hooks.json` | Claude Code; Codex after the user trusts it once in interactive `codex` |
| Slash command | — | Write a skill instead: Claude Code runs skills as `/name` too |

## New plugin

1. From the suite repo root run `python3 scripts/suite.py new <kebab-name> --description "<one sentence>" [--skill <skill-name>]`.
2. Write the generated `SKILL.md` (see "Writing a skill").
3. Run `python3 scripts/suite.py check` and fix what it reports.

## New skill in an existing plugin

1. Create `plugins/<plugin>/skills/<skill>/SKILL.md`; frontmatter `name` must equal the directory name.
2. Bump `version` in `plugins/<plugin>/.claude-plugin/plugin.json` if it has one.
3. Run `python3 scripts/suite.py sync` then `check`.

## External plugin

Add an entry whose `source` is `{"source": "git-subdir", "url": ..., "path": ..., "ref"|"sha": ...}` or `{"source": "url", "url": "https://github.com/<owner>/<repo>.git", "sha": ...}`. Do not use `"source": "github"` — Codex ignores it.

## Writing a skill

- `description` decides when agents load it: what it does, then "Use when …" with the user's likely phrasings.
- Name actions ("read the file", "run the tests", "ask the user"). When a step needs one agent's tool, give a fallback for the rest.
- Invoke bundled scripts through their interpreter (`python3 x.py`, `bash x.sh`); some installers drop the executable bit.

## Ship

Run `claude plugin validate .`, commit on a branch, and open a PR. After merge, refresh with `/plugin marketplace update suite` (Claude Code) or `codex plugin marketplace upgrade suite` (Codex).
