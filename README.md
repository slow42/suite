# suite

Personal plugin marketplace for AI coding agents: one repo, installable in Claude Code, Codex, and Cursor.

## Install

**Claude Code** (one-time bootstrap; afterwards everything in suite is on at user scope and tracks `main`)
```
claude plugin marketplace add slow42/suite
claude plugin install suite-sync@suite --scope user
```
On each session start `suite-sync` sets the marketplace to `autoUpdate` and installs every listed plugin you haven't decided on. Opt out of one with `"<name>@suite": false` in `~/.claude/settings.json` `enabledPlugins`; it stays off.

**Codex** (0.164+ reads `.claude-plugin/marketplace.json` natively)
```
codex plugin marketplace add slow42/suite
codex plugin add <name>@suite
```

**Cursor** (Teams/Enterprise): Dashboard → Plugins & MCPs → Team Marketplaces → Import from Repo → `https://github.com/slow42/suite`. Reads `.cursor-plugin/marketplace.json`; untested.

## Plugins

| Plugin | Source | What it does | Claude Code | Codex | Cursor |
|---|---|---|---|---|---|
| suite-sync | local | Enable every suite plugin at user scope; keep the marketplace on autoUpdate | ✓ | — | — |
| context-analysis | local | Diagnose and cut context/token bloat (MCP tools, memory files) | ✓ | ✓ | ✓ |
| stale-session-guard | local | Block resuming a cache-expired session over 100k tokens (`EATMYTOKENS` overrides) | ✓ | no-op¹ | — |
| git-protect | local | Block direct commits to main/master | ✓ | trust once² | — |
| worktree-shortcut | local | `/wt [task]` creates a task-scoped worktree+branch and switches into it | ✓ | ✓ | ✓ |
| suite-dev | local | Add plugins and skills to this marketplace | ✓ | ✓ | ✓ |
| project-memory | vendored from anthropics/claude-plugins-official | Audit and update CLAUDE.md | ✓ | ✓ | — |
| code-review | anthropics/claude-plugins-official | PR code review | ✓ | —³ | — |
| mattpocock-skills | mattpocock/skills (pinned) | Matt Pocock's skill collection | ✓ | ✓ | — |

1. Reads Claude Code's transcript format; in Codex it installs but never blocks.
2. Codex runs plugin hooks only after you approve each one in interactive `codex` (requires `[features] hooks = true`).
3. Command-only plugin; Codex converts commands to skills only when a plugin also has a `skills/` folder.

Cursor lists only local plugins built purely from skills and MCP servers, which is what [Agent Plugins](https://agent-plugins.org) can carry.

## How it works

| File | Role | Edited by |
|---|---|---|
| `.claude-plugin/marketplace.json` | The index. Claude Code and Codex both read it. | hand |
| `plugins/<name>/.claude-plugin/plugin.json` | Plugin manifest for Claude Code and Codex | hand |
| `plugins/<name>/plugin.json` | Agent Plugins 1.0.0 manifest (Cursor and other agent-plugins.org clients) | `scripts/suite.py sync` |
| `.cursor-plugin/marketplace.json` | Cursor's index | `scripts/suite.py sync` |

```
python3 scripts/suite.py new <name> --description "..."   # scaffold a plugin with one skill
python3 scripts/suite.py sync                             # regenerate derived manifests
python3 scripts/suite.py check                            # CI: stale manifests, malformed skills, Codex-invisible sources
```

Own plugins are never pinned (no `version`), so every push reaches every machine; `check` enforces this. External plugins track upstream unless pinned with `sha` to a reviewed commit: mattpocock-skills is pinned (bump the sha after reviewing upstream), Anthropic's code-review tracks `main`. Prefer skills over commands: Claude Code runs a skill as `/name`, and every other agent can load it. External plugins must use `git-subdir` or `url` sources; Codex ignores `github`. Names can't start with `claude-` (Claude Code reserves them), and an external plugin's marketplace name must match its own `plugin.json` name (Codex enforces this), so plugins named `claude-*` upstream get vendored and renamed.
