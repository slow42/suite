# worktree-shortcut

Adds the `/wt [task]` slash command.

## What it does

Given a task, `/wt`:

1. Derives a branch name from the task, conforming to any branch-naming convention the repo enforces (git hooks, pre-commit/husky/lefthook, or a documented pattern). Pulls in a Linear issue id when the convention expects one — using an id you mention, or offering to open an issue via the Linear connector.
2. Creates a git worktree under `.claude/worktrees/<branch>` on that branch (forked from your current HEAD) via the native `EnterWorktree` tool.
3. Switches this session's working directory into the worktree — same session, full context, no shell wrapper or clipboard hop.

If no task is given, it asks what the worktree is for.

## Usage

```
/wt fix the login redirect loop
/wt            # prompts for the task
```

Run it from the branch you want as the base (usually an up-to-date `main`); the new branch forks off your current HEAD.

## Requirements

- Run inside a git repository.
- Native `EnterWorktree` worktree support (Claude Code).
- Linear connector optional — only used when a branch convention wants an issue id and you choose to create one.
