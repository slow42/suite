# git-protect

Blocks direct commits to `main` or `master`, enforcing that all changes go through a branch and PR.

## Hooks

### no_commit_main

Intercepts any `git commit` Bash call and exits with code 2 if the current branch is `main` or `master`.

## Installation

Install via the ai-primitives marketplace:
```
/plugin install git-protect@ai-primitives
```
