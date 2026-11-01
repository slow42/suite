#!/usr/bin/env bash
# Print the markdown "/context all" report for a fresh, non-interactive Claude
# Code session in the given (or current) directory. This is a local
# computation — no model call, no cost, no API latency — so it's safe to run
# as often as you like for before/after context-trimming comparisons.
#
# A freshly-started session can have a different connected-server set than a
# user's *live* interactive session (it may pick up MCP servers that weren't
# connected when their session started, or vice versa). Use this to compare a
# "before" snapshot against an "after" snapshot of the *same* change, not
# necessarily against a live session's own /context reading.
#
# Usage:
#   bash context_snapshot.sh [directory]
#
# Requires the `claude` CLI on PATH and python3.
set -euo pipefail

DIR="${1:-$(pwd)}"

(cd "$DIR" && claude -p "/context all" --verbose --output-format json) | python3 -c '
import json, sys

data = json.load(sys.stdin)
result = next((d for d in data if d.get("type") == "result"), None)
if result is None:
    print("No result entry in claude -p output — check the claude CLI ran successfully.", file=sys.stderr)
    sys.exit(1)
print(result["result"])
'
