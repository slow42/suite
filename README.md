# suite

Personal Claude Code plugin marketplace.

```
/plugin marketplace add slow42/suite
/plugin install <name>@suite
```

| Plugin | Source | What it does |
|---|---|---|
| context-analysis | local | Diagnose and cut context/token bloat (MCP tools, memory files) |
| stale-session-guard | local | Block resuming a cache-expired session over 100k tokens (`EATMYTOKENS` overrides) |
| git-protect | local | Block direct commits to main/master |
| worktree-shortcut | local | `/wt [task]` creates a task-scoped worktree+branch and switches into it |
| code-review | anthropics/claude-plugins-official | PR code review |
| claude-md-management | anthropics/claude-plugins-official | Audit and update CLAUDE.md |
| mattpocock-skills | mattpocock/skills (pinned) | Matt Pocock's skill collection |
