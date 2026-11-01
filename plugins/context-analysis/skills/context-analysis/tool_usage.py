#!/usr/bin/env python3
"""Count how often a tool (or every tool on an MCP server) was actually
called, across all past Claude Code session transcripts. Works for both
MCP tools (mcp__server__tool) and built-in tools (Bash, Workflow, Artifact,
DesignSync, ...) — the transcript JSON shape is identical for both.

Usage:
    tool_usage.py <substring> [--projects-dir DIR]

Examples:
    tool_usage.py mcp__github__            # every tool on the github server
    tool_usage.py plugin_vendor_server     # every tool on a plugin-hosted server
    tool_usage.py Workflow                 # a single built-in tool, exact name
    tool_usage.py DesignSync
"""
import argparse
import re
import sys
from collections import Counter
from pathlib import Path

NAME_PATTERN = re.compile(r'"name"\s*:\s*"([^"]+)"')


def iter_tool_names(path: Path):
    # Tolerate partially-written or malformed lines; transcripts are JSONL,
    # one JSON object per line, and old/rotated files sometimes have both.
    try:
        with path.open("r", errors="ignore") as f:
            for line in f:
                for m in NAME_PATTERN.finditer(line):
                    yield m.group(1)
    except OSError:
        return


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("substring", help="Tool name or substring to match, e.g. 'mcp__github__' or 'Workflow'")
    ap.add_argument("--projects-dir", default=str(Path.home() / ".claude" / "projects"))
    args = ap.parse_args()

    root = Path(args.projects_dir)
    if not root.is_dir():
        print(f"No such directory: {root}", file=sys.stderr)
        sys.exit(1)

    counts = Counter()
    files_scanned = 0
    for path in root.glob("*/*.jsonl"):
        files_scanned += 1
        for name in iter_tool_names(path):
            if args.substring in name:
                counts[name] += 1

    if not counts:
        print(f"No calls found matching '{args.substring}' across {files_scanned} transcript files.")
        print("Either the substring is wrong, or this tool/server is unused (a real trim signal — verify before cutting).")
        return

    width = max(len(n) for n in counts)
    for name, n in counts.most_common():
        print(f"{n:>5}  {name:<{width}}")

    print(f"\n{len(counts)} distinct tool name(s) matched, across {files_scanned} transcript files.", file=sys.stderr)


if __name__ == "__main__":
    main()
