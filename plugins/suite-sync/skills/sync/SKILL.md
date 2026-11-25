---
name: sync
description: Run suite-sync now instead of waiting for the next session start - pull the latest suite marketplace and install every listed plugin not yet decided on at user scope. Use when the user says "/sync", "run suite-sync", "sync suite", or just merged a plugin into suite and wants it without restarting. Claude Code only.
allowed-tools: Bash
---

1. Pull the latest marketplace: run `claude plugin marketplace update suite`. Without this the script reads a stale plugin list.
2. Run the SessionStart hook script from this plugin's copy, two levels above this skill's base directory: `python3 "<skill base dir>/../../hooks/enable_all.py"`. Don't run the copy in a suite repo checkout; it would read unmerged entries.
3. Report the result. The script prints a JSON `systemMessage` only when it changed something; no output means every listed plugin is already installed or opted out (`"<name>@suite": false`).
4. If it installed anything, tell the user to run `/reload-plugins` to load them in this session; you can't run slash commands yourself.
