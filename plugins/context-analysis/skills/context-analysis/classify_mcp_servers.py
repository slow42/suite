#!/usr/bin/env python3
"""Classify every MCP server seen in past transcripts into its control tier,
so you know which lever actually removes it — editing config does nothing
if you're editing the wrong tier's file.

Three tiers, discovered the hard way (each requires a different fix AND a
different reload mechanism):

  local       Registered directly in ~/.claude.json under "mcpServers".
              Fix: edit/remove the entry there. Needs a full restart —
              NOT picked up by /reload-plugins.

  plugin      Provided by a plugin (visible in settings.json enabledPlugins).
              Fix: set "<plugin>@<marketplace>": false in enabledPlugins,
              or use per-server filtering if the plugin's MCP supports it
              (e.g. Datadog's toolset env var). /reload-plugins DOES pick
              this up.

  claude_ai   A claude.ai account cloud connector (tool names literally
              prefixed mcp__claude_ai_*). Not in any local file at all —
              auto-fetched at session start from your claude.ai account.
              Fix: disconnect it in claude.ai's own connector settings, or
              nuke ALL of them at once with settings.json
              `"disableClaudeAiConnectors": true`. Needs a full restart —
              NOT picked up by /reload-plugins, and there is no per-server
              on/off switch for this tier from local config.

Usage:
    classify_mcp_servers.py [--claude-json PATH] [--settings PATH] [--projects-dir DIR]
"""
import argparse
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

SERVER_TOOL_PATTERN = re.compile(r'"name"\s*:\s*"(mcp__[^"]+)"')


def extract_server_name(tool_name: str) -> str:
    # mcp__github__pull_request_read -> github
    # mcp__claude_ai_ProductName__some-tool -> claude_ai_ProductName
    # mcp__plugin_vendor_server__some_tool -> plugin_vendor_server
    parts = tool_name.split("__")
    if len(parts) < 3:
        return tool_name
    return parts[1]


def scan_transcripts(projects_dir: Path):
    server_calls = Counter()
    tool_calls = defaultdict(Counter)
    files_scanned = 0
    for path in projects_dir.glob("*/*.jsonl"):
        files_scanned += 1
        try:
            with path.open("r", errors="ignore") as f:
                for line in f:
                    for m in SERVER_TOOL_PATTERN.finditer(line):
                        tool = m.group(1)
                        server = extract_server_name(tool)
                        server_calls[server] += 1
                        tool_calls[server][tool] += 1
        except OSError:
            continue
    return server_calls, tool_calls, files_scanned


def load_json(path: Path):
    if not path.is_file():
        return {}
    try:
        return json.loads(path.read_text())
    except (OSError, json.JSONDecodeError):
        return {}


def classify(server: str, local_servers: set) -> str:
    if server in local_servers:
        return "local"
    if server.startswith("claude_ai_"):
        return "claude_ai"
    # Anything else seen in mcp__X__ namespace that isn't in ~/.claude.json
    # and isn't claude_ai_-prefixed is almost certainly plugin-hosted.
    return "plugin (probable)"


FIX = {
    "local": "edit ~/.claude.json mcpServers, then FULL RESTART",
    "claude_ai": "disableClaudeAiConnectors:true (all-or-nothing) or claude.ai connector settings, then FULL RESTART",
    "plugin (probable)": "toggle in settings.json enabledPlugins, then /reload-plugins is enough",
}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--claude-json", default=str(Path.home() / ".claude.json"))
    ap.add_argument("--settings", default=str(Path.home() / ".claude" / "settings.json"))
    ap.add_argument("--projects-dir", default=str(Path.home() / ".claude" / "projects"))
    args = ap.parse_args()

    claude_json = load_json(Path(args.claude_json))
    local_servers = set(claude_json.get("mcpServers", {}).keys())

    root = Path(args.projects_dir)
    if not root.is_dir():
        print(f"No such directory: {root}", file=sys.stderr)
        sys.exit(1)

    server_calls, tool_calls, files_scanned = scan_transcripts(root)

    if not server_calls:
        print(f"No mcp__ tool calls found across {files_scanned} transcript files.")
        return

    print(f"{'SERVER':<28}{'TIER':<18}{'CALLS':>7}  {'TOOLS USED':>10}  FIX")
    for server, calls in server_calls.most_common():
        tier = classify(server, local_servers)
        n_tools = len(tool_calls[server])
        print(f"{server:<28}{tier:<18}{calls:>7}  {n_tools:>10}  {FIX[tier]}")

    unused_local = local_servers - set(server_calls)
    if unused_local:
        print(f"\nRegistered in ~/.claude.json but ZERO calls ever: {', '.join(sorted(unused_local))}")
        print("These cost nothing if not connecting, but confirm before deleting — some fail silently without auth.")

    print(f"\n{files_scanned} transcript files scanned. Cross-reference call counts with tool_usage.py per-server for tool-level detail.")


if __name__ == "__main__":
    main()
