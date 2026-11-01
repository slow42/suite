#!/usr/bin/env python3
"""SessionStart hook: make the suite marketplace the source of truth for user-scope plugins.

Ensures the marketplace is declared with autoUpdate in user settings and installs, at user scope, every plugin it lists
that the user hasn't decided on yet. An explicit `"<name>@suite": false` in enabledPlugins is an opt-out and is kept.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

MARKETPLACE = "suite"
MARKETPLACE_SOURCE = {"source": "github", "repo": "slow42/suite"}
INSTALL_TIMEOUT_SECONDS = 60


def config_dir() -> Path:
    return Path(os.environ.get("CLAUDE_CONFIG_DIR") or Path.home() / ".claude")


def marketplace_manifest() -> Path | None:
    """The plugin runs either in place inside the repo or from the plugin cache; check both."""
    root = Path(os.environ.get("CLAUDE_PLUGIN_ROOT", __file__)).resolve()
    for parent in [root, *root.parents]:
        candidate = parent / ".claude-plugin" / "marketplace.json"
        if candidate.is_file() and json.loads(candidate.read_text()).get("name") == MARKETPLACE:
            return candidate
    known = config_dir() / "plugins" / "known_marketplaces.json"
    if known.is_file():
        location = json.loads(known.read_text()).get(MARKETPLACE, {}).get("installLocation")
        if location and (Path(location) / ".claude-plugin" / "marketplace.json").is_file():
            return Path(location) / ".claude-plugin" / "marketplace.json"
    return None


def ensure_auto_update(settings_path: Path) -> bool:
    """Declare the marketplace with autoUpdate on; returns True if settings changed."""
    settings = json.loads(settings_path.read_text()) if settings_path.is_file() else {}
    entry = settings.setdefault("extraKnownMarketplaces", {}).setdefault(MARKETPLACE, {"source": MARKETPLACE_SOURCE})
    if entry.get("autoUpdate") is True:
        return False
    entry["autoUpdate"] = True
    settings_path.write_text(json.dumps(settings, indent=2) + "\n")
    return True


def install(key: str) -> str | None:
    """Install at user scope via the CLI, which also writes enabledPlugins; returns an error or None."""
    claude = shutil.which("claude")
    if not claude:
        return "claude CLI not on PATH"
    try:
        result = subprocess.run([claude, "plugin", "install", key, "--scope", "user"], capture_output=True, text=True, timeout=INSTALL_TIMEOUT_SECONDS)
    except subprocess.TimeoutExpired:
        return "timed out"
    if result.returncode == 0:
        return None
    output = (result.stderr or result.stdout).strip().splitlines()
    return output[-1] if output else f"exit {result.returncode}"


def main() -> int:
    manifest = marketplace_manifest()
    if manifest is None:
        return 0
    settings_path = config_dir() / "settings.json"
    changed_marketplace = ensure_auto_update(settings_path)
    enabled = json.loads(settings_path.read_text()).get("enabledPlugins", {})
    missing = [f"{p['name']}@{MARKETPLACE}" for p in json.loads(manifest.read_text())["plugins"] if f"{p['name']}@{MARKETPLACE}" not in enabled]
    installed, failed = [], []
    for key in missing:
        error = install(key)
        if error:
            failed.append(f"{key} ({error})")
        else:
            installed.append(key)
    notes = []
    if changed_marketplace:
        notes.append("suite marketplace set to autoUpdate")
    if installed:
        notes.append(f"enabled {', '.join(installed)}; run /reload-plugins to load them now")
    if failed:
        notes.append(f"could not install {', '.join(failed)}")
    if notes:
        print(json.dumps({"systemMessage": "suite-sync: " + "; ".join(notes)}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
