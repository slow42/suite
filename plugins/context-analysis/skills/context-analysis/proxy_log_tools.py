#!/usr/bin/env python3
"""Break down a captured Claude Code API request (system prompt + tool
schemas) by size, so you can see exactly what's eating context — not just
which category (/context already tells you that) but which specific tool
definitions to target.

Requires a raw request log: a JSON file with the same shape as the
Anthropic Messages API request body (keys: system, tools, messages, ...).
Claude Code doesn't write these by default — this script assumes you're
running a logging proxy in front of the API (e.g. the one described in
https://www.aihero.dev/how-to-kill-the-bloat-in-claude-codes-system-prompt)
that dumps each request body to disk. If you don't have one, use
`/context` instead for the coarse per-category breakdown; this script is
for going one level deeper once you know which category to attack.

Usage:
    proxy_log_tools.py <path-to-request.json-or-.txt> [--top N]
    proxy_log_tools.py --latest <logs-dir> [--top N]
"""
import argparse
import json
import sys
from pathlib import Path


def find_latest(logs_dir: Path) -> Path:
    candidates = sorted(logs_dir.glob("*.request.txt"), key=lambda p: p.stat().st_mtime, reverse=True)
    if not candidates:
        candidates = sorted(logs_dir.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
    if not candidates:
        raise SystemExit(f"No *.request.txt or *.json files found in {logs_dir}")
    return candidates[0]


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("path", nargs="?", help="Path to a captured request body (JSON)")
    ap.add_argument("--latest", metavar="LOGS_DIR", help="Instead of a path, use the most recent request log in this directory")
    ap.add_argument("--top", type=int, default=40, help="How many largest tools to show (default 40)")
    args = ap.parse_args()

    if args.latest:
        path = find_latest(Path(args.latest))
    elif args.path:
        path = Path(args.path)
    else:
        ap.error("provide a path or --latest LOGS_DIR")

    data = json.loads(path.read_text())
    print(f"Using: {path}\n")

    system = data.get("system")
    if isinstance(system, list):
        total = sum(len(json.dumps(b)) for b in system)
        print(f"System blocks: {len(system)}, total {total} bytes (~{total // 4} tokens)")
        for b in system:
            text = b.get("text", "") if isinstance(b, dict) else str(b)
            size = len(json.dumps(b))
            preview = text[:80].replace("\n", " ")
            print(f"  {size:>7} bytes  {preview}")
    elif isinstance(system, str):
        print(f"System prompt: {len(system)} chars (~{len(system) // 4} tokens), single string block")

    tools = data.get("tools", [])
    if not tools:
        print("\nNo 'tools' array in this request.")
        return

    sizes = sorted(((len(json.dumps(t)), t.get("name")) for t in tools), reverse=True)
    total_tool_bytes = sum(s for s, _ in sizes)
    print(f"\n{len(tools)} tools, {total_tool_bytes} bytes total (~{total_tool_bytes // 4} tokens)")
    print(f"\nTop {args.top} by size:")
    for size, name in sizes[: args.top]:
        mcp_tag = " [MCP]" if name and name.startswith("mcp__") else ""
        print(f"{size:>7} bytes (~{size // 4:>5} tok)  {name}{mcp_tag}")


if __name__ == "__main__":
    main()
