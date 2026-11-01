#!/usr/bin/env python3
"""UserPromptSubmit hook: refuses to continue a session whose prompt cache
has almost certainly expired (idle > 1hr since the last assistant reply)
AND whose context is large enough (> 100k tokens) that re-reading it at
full price actually costs something. Say EATMYTOKENS anywhere in the
prompt to override.
"""

import json
import sys
from datetime import datetime, timezone

IDLE_THRESHOLD_SECONDS = 3600
CONTEXT_THRESHOLD_TOKENS = 100_000
OVERRIDE_TOKEN = "EATMYTOKENS"


def last_assistant_snapshot(transcript_path):
    """Return (timestamp, context_tokens) as of the last context-resetting
    event in the transcript: an assistant turn's usage, or a /compact that
    dropped the transcript down to compactMetadata.postTokens. Whichever
    happened later in the file wins - a compact makes prior assistant usage
    moot even if its own timestamp doesn't strictly postdate it, since the
    whole point of compacting is that resuming afterward is cheap again.
    """
    last_ts = None
    last_tokens = None
    try:
        with open(transcript_path) as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    entry = json.loads(line)
                except ValueError:
                    continue
                if entry.get("subtype") == "compact_boundary" and entry.get("timestamp"):
                    post_tokens = entry.get("compactMetadata", {}).get("postTokens")
                    if post_tokens is not None:
                        last_ts = entry["timestamp"]
                        last_tokens = post_tokens
                    continue
                if entry.get("type") != "assistant" or not entry.get("timestamp"):
                    continue
                usage = entry.get("message", {}).get("usage", {})
                if not usage:
                    continue
                last_ts = entry["timestamp"]
                last_tokens = (
                    usage.get("input_tokens", 0)
                    + usage.get("cache_creation_input_tokens", 0)
                    + usage.get("cache_read_input_tokens", 0)
                )
    except OSError:
        return None, None
    return last_ts, last_tokens


def main():
    try:
        input_data = json.load(sys.stdin)
    except Exception:
        sys.exit(0)

    if OVERRIDE_TOKEN in input_data.get("prompt", ""):
        sys.exit(0)

    transcript_path = input_data.get("transcript_path", "")
    if not transcript_path:
        sys.exit(0)

    last_ts, context_tokens = last_assistant_snapshot(transcript_path)
    if last_ts is None or context_tokens is None:
        sys.exit(0)

    if context_tokens <= CONTEXT_THRESHOLD_TOKENS:
        sys.exit(0)

    last_dt = datetime.fromisoformat(last_ts.replace("Z", "+00:00"))
    idle_seconds = (datetime.now(timezone.utc) - last_dt).total_seconds()

    if idle_seconds > IDLE_THRESHOLD_SECONDS:
        hours = idle_seconds / 3600
        reason = (
            f"Session idle {hours:.1f}h with ~{context_tokens // 1000}k tokens of context - "
            "prompt cache (1hr TTL) has expired. Continuing here re-reads that whole context "
            "at full price instead of a cheap cache hit. Start a fresh session instead - or "
            f"include {OVERRIDE_TOKEN} anywhere in this prompt to force through anyway."
        )
        print(json.dumps({"decision": "block", "reason": reason}))


if __name__ == "__main__":
    main()
