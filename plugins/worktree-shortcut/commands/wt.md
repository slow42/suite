---
description: Create a worktree+branch scoped to a task and switch this session into it
argument-hint: [task description]
allowed-tools: Bash, EnterWorktree, mcp__linear, mcp__claude_ai_Linear
---

Create a git worktree on a new branch scoped to a task, then switch this session into it with `EnterWorktree`. The worktree lands under `.claude/worktrees/<branch>` and the session's working directory follows — no shell wrapper, no clipboard.

## 1. Establish the task

`$ARGUMENTS` is the task this worktree is for. If it's empty, ask the user "What's this worktree for?" and wait — the task is what names the branch. One line is enough; don't interrogate.

## 2. Link a Linear issue (only when it earns a place in the branch name)

Some repos encode a Linear issue id in the branch (e.g. `air-1307-<slug>`); most of this repo's branches don't. Decide from the convention detected in step 3, then:

- **Task text already names an issue** (`AIR-1234`, `air-1234`) → use that id.
- **Convention wants an id and none is known** → ask whether an issue exists. If not and the user wants one, create it through the Linear connector (`mcp__linear` / `mcp__claude_ai_Linear`; authenticate first if it isn't ready), then use the returned identifier. If they decline, fall back to a conforming id-less name.
- **Convention doesn't need an id** → skip Linear entirely; don't ask.

## 3. Resolve the branch name

Derive a branch name from the task (plus the issue id when in play) and make it conform to whatever the repo enforces. Conventions are enforced by hooks but rarely declared machine-readably, and branch-name hooks fire on push/commit — never on branch creation — so you can't probe them; read them. Detect best-effort, stopping at the first informative signal:

- **Git hooks** — `git config --get core.hooksPath`, then `pre-push`/`pre-commit` (follow symlinks; real logic often lives in `scripts/hooks/` or `.githooks/`). Grep for a branch-name regex and exempt prefixes (`scratch/*`, `wip/*`, `dependabot/*`).
- **Hook frameworks** — `.pre-commit-config.yaml`, `.husky/`, `lefthook.yml`/`.lefthook.yml`.
- **Docs** — `CONTRIBUTING*`, `CLAUDE.md`, `README*`.
- **Fallback** — infer the prevailing pattern from existing branches: `git branch -a --format='%(refname:short)'`.

If the derived name would violate the convention, quote the rule and its source and propose a conforming one before proceeding. Each `/`-separated segment of the final name may contain only letters, digits, dots, underscores, and dashes, and the whole name must be ≤ 64 chars (`EnterWorktree` requirement).

## 4. Create and enter the worktree

Call `EnterWorktree` with `name` set to the resolved branch. It creates the worktree under `.claude/worktrees/<branch>`, cuts the branch off your current HEAD (the repo sets `worktree.baseRef: head`), and switches this session into it. So run `/wt` from the base you want — usually an up-to-date `main`. Confirm the new path and branch, then carry on with the task there.
