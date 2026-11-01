#!/usr/bin/env python3
"""PreToolUse hook: blocks direct git commits to main or master."""

# PEP 604 unions (`str | None`) are evaluated eagerly without this future
# import, so the module fails to load on Python 3.9 — the version macOS ships
# at /usr/bin/python3, which is what bare `python3` resolves to in many
# Claude Code shells. The future import keeps annotations lazy and works on
# every Python from 3.7 onward.
from __future__ import annotations

import json
import os
import re
import shlex
import subprocess
import sys

# Narrow on purpose: `git.*commit` would also block `git log --grep commit`.
_COMMIT_RE = re.compile(r"git\s+(?:-C\s+(\S+)\s+)?commit\b")

_OPERATORS = {"&&", "||", ";", "|"}
_LEADING_SHELL_SYNTAX = {"if", "then", "elif", "else", "fi", "do", "done", "while", "until", "!", "(", ")", "{", "}"}


def _normalize_newlines(command: str) -> str:
    # A newline inside a quoted commit message must stay literal.
    out = []
    quote = None
    for ch in command:
        if quote:
            out.append(ch)
            if ch == quote:
                quote = None
        elif ch in ("'", '"'):
            quote = ch
            out.append(ch)
        elif ch == "\n":
            out.append(" ; ")  # spaced so it can't fuse with adjacent punctuation like `(`
        else:
            out.append(ch)
    return "".join(out)


def _tokenize(command: str) -> list[str] | None:
    lexer = shlex.shlex(_normalize_newlines(command), posix=True, punctuation_chars=True)
    lexer.whitespace_split = True
    try:
        return list(lexer)
    except ValueError:
        return None


def _segments(tokens: list[str]) -> list[list[str]]:
    segments: list[list[str]] = [[]]
    for token in tokens:
        if token in _OPERATORS:
            segments.append([])
        else:
            segments[-1].append(token)
    return segments


def _strip_leading_shell_syntax(tokens: list[str]) -> list[str]:
    i = 0
    while i < len(tokens) and tokens[i] in _LEADING_SHELL_SYNTAX:
        i += 1
    return tokens[i:]


def _commit_targets(command: str) -> list[str | None]:
    """Directory each `git commit` in the command would run in; fails open (empty list) if unparseable."""
    tokens = _tokenize(command)
    if tokens is None:
        return []

    targets: list[str | None] = []
    target: str | None = None
    for raw_segment in _segments(tokens):
        segment = _strip_leading_shell_syntax(raw_segment)
        if len(segment) >= 2 and segment[0] == "cd":
            target = os.path.expanduser(segment[1])
            continue
        if "git" not in segment:
            continue
        rest = segment[segment.index("git") + 1:]
        if rest[:1] == ["-C"] and rest[2:3] == ["commit"]:
            targets.append(os.path.expanduser(rest[1]))
        elif rest[:1] == ["commit"]:
            targets.append(target)
    return targets


def _branch_of(target_dir: str | None, session_cwd: str | None) -> str | None:
    git_cmd = ["git", "rev-parse", "--abbrev-ref", "HEAD"]
    if target_dir:
        git_cmd = ["git", "-C", target_dir, "rev-parse", "--abbrev-ref", "HEAD"]
    try:
        return subprocess.check_output(git_cmd, cwd=session_cwd, stderr=subprocess.DEVNULL).decode().strip()
    except Exception:
        return None


def main():
    try:
        input_data = json.load(sys.stdin)
    except Exception:
        sys.exit(0)

    tool_name = input_data.get("tool_name", "")
    if tool_name != "Bash":
        sys.exit(0)

    command = input_data.get("tool_input", {}).get("command", "")
    if not _COMMIT_RE.search(command):
        sys.exit(0)

    # Claude Code runs hooks from the project root, not the session's worktree;
    # the session's directory arrives only as `cwd` in the input.
    session_cwd = input_data.get("cwd") or None
    for target_dir in _commit_targets(command):
        branch = _branch_of(target_dir, session_cwd)
        if branch in ("main", "master"):
            print(
                f"Blocked: direct commits to '{branch}' are not allowed.\n"
                "Create a branch first: git checkout -b <branch-name>",
                file=sys.stdout,
            )
            sys.exit(2)

    sys.exit(0)


if __name__ == "__main__":
    main()
