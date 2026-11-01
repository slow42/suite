#!/usr/bin/env python3
"""List auto-memory files with type + age, flagging likely-stale candidates
for a human (or the model) to challenge before trusting or keeping them.

This does NOT delete or judge truth automatically — it only surfaces
candidates worth re-checking against the user, the codebase, or past
session transcripts. `project` memories decay fastest (they describe
in-flight work); `reference` memories decay next (paths/tools/URLs
change); `feedback`/`user` memories are durable and rarely need revisiting.

Usage:
    memory_staleness.py [--dir DIR] [--project-days N] [--reference-days N]

If --dir is omitted, defaults to this project's auto-memory directory,
computed the same way Claude Code does: ~/.claude/projects/<sanitized-cwd>/memory/
where sanitized-cwd replaces "/" with "-". Pass --dir explicitly if your
project overrides autoMemoryDirectory in settings.
"""
import argparse
import re
import time
from pathlib import Path


def default_memory_dir() -> Path:
    sanitized = str(Path.cwd()).replace("/", "-")
    return Path.home() / ".claude" / "projects" / sanitized / "memory"


FRONTMATTER = re.compile(r"^---\n(.*?)\n---", re.DOTALL)


def parse_frontmatter(text: str):
    m = FRONTMATTER.match(text)
    if not m:
        return {}
    block = m.group(1)
    fields = {}
    # description/name at top level; type is nested under metadata: — grab
    # whichever line contains "type:" that isn't "node_type:".
    for line in block.splitlines():
        line = line.strip()
        if line.startswith("name:"):
            fields["name"] = line.split(":", 1)[1].strip()
        elif line.startswith("description:"):
            fields["description"] = line.split(":", 1)[1].strip().strip('"')
        elif line.startswith("type:") and "node_type" not in line:
            fields["type"] = line.split(":", 1)[1].strip()
    return fields


PRIORITY = {"project": 0, "reference": 1, "user": 2, "feedback": 2}
DEFAULT_THRESHOLD_DAYS = {"project": 14, "reference": 60}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dir", default=None, help="Auto-memory directory. Defaults to this project's, computed from cwd.")
    ap.add_argument("--project-days", type=int, default=DEFAULT_THRESHOLD_DAYS["project"])
    ap.add_argument("--reference-days", type=int, default=DEFAULT_THRESHOLD_DAYS["reference"])
    args = ap.parse_args()

    root = Path(args.dir) if args.dir else default_memory_dir()
    if not root.is_dir():
        print(f"No such memory directory: {root}")
        print("Pass --dir explicitly, or confirm autoMemoryEnabled is on for this project.")
        return

    thresholds = {"project": args.project_days, "reference": args.reference_days}
    now = time.time()
    rows = []
    for path in root.glob("*.md"):
        if path.name == "MEMORY.md":
            continue
        fields = parse_frontmatter(path.read_text(errors="ignore"))
        mtype = fields.get("type", "unknown")
        age_days = (now - path.stat().st_mtime) / 86400
        rows.append((mtype, age_days, fields.get("name", path.stem), fields.get("description", ""), path))

    rows.sort(key=lambda r: (PRIORITY.get(r[0], 3), -r[1]))

    print(f"{'TYPE':<10}{'AGE':<8}{'NAME':<45}FLAG")
    for mtype, age_days, name, _desc, _path in rows:
        threshold = thresholds.get(mtype)
        flag = "REVISIT" if threshold and age_days >= threshold else ""
        print(f"{mtype:<10}{int(age_days):>3}d    {name:<45}{flag}")

    revisit = [r for r in rows if thresholds.get(r[0]) and r[1] >= thresholds[r[0]]]
    if revisit:
        print(f"\n{len(revisit)} candidate(s) to revisit — check against the user, current codebase/tracker state, or past session transcripts before trusting or removing.")
    else:
        print("\nNo candidates past the age thresholds — doesn't mean all memories are accurate, just that none are old enough to auto-flag.")


if __name__ == "__main__":
    main()
