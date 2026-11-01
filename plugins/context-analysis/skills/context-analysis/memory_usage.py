#!/usr/bin/env python3
"""Count how often each auto-memory file was actually re-opened (via the
Read tool) in past sessions, as a second vector alongside
memory_staleness.py's age-only signal.

Age (mtime) only tells you a memory hasn't been *edited* recently. It does
NOT tell you whether the memory is still being *recalled*: MEMORY.md's
index is always loaded, but an individual memory file only enters context
when the model decides it's relevant and Reads it. A memory can be old but
still get pulled in often (still load-bearing), or recently written but
never Read again (its description isn't matching real queries, or the
fact stopped being relevant faster than its age suggests).

Cross-reference the two: old + never re-read is a much stronger prune
signal than old + still frequently read.

Usage:
    memory_usage.py [--dir DIR] [--projects-dir DIR]

If --dir/--projects-dir are omitted, both default to this project's
auto-memory location and its sibling transcript files, computed the same
way Claude Code does: ~/.claude/projects/<sanitized-cwd>/
"""
import argparse
import json
from collections import Counter
from pathlib import Path


def default_project_dir() -> Path:
    sanitized = str(Path.cwd()).replace("/", "-")
    return Path.home() / ".claude" / "projects" / sanitized


def scan_reads(projects_dir: Path, memory_paths: set):
    counts = Counter()
    files_scanned = 0
    for path in projects_dir.glob("*.jsonl"):
        files_scanned += 1
        try:
            with path.open("r", errors="ignore") as f:
                for line in f:
                    if '"name":"Read"' not in line and '"name": "Read"' not in line:
                        continue
                    try:
                        obj = json.loads(line)
                    except json.JSONDecodeError:
                        continue
                    content = obj.get("message", {}).get("content")
                    if not isinstance(content, list):
                        continue
                    for block in content:
                        if not isinstance(block, dict):
                            continue
                        if block.get("type") == "tool_use" and block.get("name") == "Read":
                            fp = block.get("input", {}).get("file_path")
                            if fp in memory_paths:
                                counts[fp] += 1
        except OSError:
            continue
    return counts, files_scanned


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dir", default=None, help="Auto-memory directory. Defaults to this project's, computed from cwd.")
    ap.add_argument("--projects-dir", default=None, help="Directory containing this project's *.jsonl transcripts. Defaults alongside --dir.")
    args = ap.parse_args()

    project_dir = Path(args.projects_dir) if args.projects_dir else default_project_dir()
    memory_dir = Path(args.dir) if args.dir else project_dir / "memory"

    if not memory_dir.is_dir():
        print(f"No such memory directory: {memory_dir}")
        print("Pass --dir explicitly, or confirm autoMemoryEnabled is on for this project.")
        return
    if not project_dir.is_dir():
        print(f"No such transcripts directory: {project_dir}")
        return

    memory_files = sorted(p for p in memory_dir.glob("*.md") if p.name != "MEMORY.md")
    if not memory_files:
        print(f"No memory files found in {memory_dir}")
        return

    memory_paths = {str(p) for p in memory_files}
    counts, files_scanned = scan_reads(project_dir, memory_paths)

    ranked = sorted(memory_files, key=lambda p: -counts.get(str(p), 0))
    print(f"{'READS':>6}  MEMORY FILE")
    for p in ranked:
        n = counts.get(str(p), 0)
        flag = "NEVER RE-READ" if n == 0 else ""
        print(f"{n:>6}  {p.name:<50}{flag}")

    never = [p.name for p in memory_files if counts.get(str(p), 0) == 0]
    print(f"\n{files_scanned} transcript file(s) scanned in {project_dir}.")
    if never:
        print(f"{len(never)} memor{'y' if len(never) == 1 else 'ies'} never re-read after creation — cross-check against memory_staleness.py's age flag before pruning; a memory can be genuinely durable (feedback/user type) without ever needing re-recall.")


if __name__ == "__main__":
    main()
