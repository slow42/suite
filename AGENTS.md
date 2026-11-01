# suite

Plugin marketplace served to Claude Code, Codex, and Cursor. Read README.md "How it works" before editing.

- Hand-edit only `.claude-plugin/marketplace.json` and `plugins/*/.claude-plugin/plugin.json`; run `python3 scripts/suite.py sync` after, never edit the generated `plugins/*/plugin.json` or `.cursor-plugin/marketplace.json`.
- `python3 scripts/suite.py check` and `claude plugin validate .` must pass before committing.
- New capabilities are skills (`skills/<name>/SKILL.md`, frontmatter `name` = directory) written as agent-neutral actions; hooks and commands are Claude-only and must be marked so in the README table.
- To verify in Codex without touching real config, set `CODEX_HOME` to a scratch dir, `codex plugin marketplace add <repo path>`, `codex plugin add <name>@suite`.
- The `suite-dev:add-to-suite` skill has the full authoring workflow.
