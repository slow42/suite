# stale-session-guard

Blocks continuing a session once its Anthropic prompt cache has almost
certainly expired, instead of silently paying full price to re-read the
whole transcript on the next turn.

## Hooks

### block_stale_session

`UserPromptSubmit` hook. Reads the timestamp and token usage of the last
assistant reply in the session transcript. Blocks the prompt only when
*both* are true:

- idle time since that reply exceeds 1hr (the standard ephemeral cache TTL)
- that reply's context was over 100k tokens

A small session stays cheap to re-read regardless of staleness, so it's
never blocked. Say `EATMYTOKENS` anywhere in the prompt to force it
through anyway.

Blocking has no other override: a blocked prompt is discarded, and
resubmitting the same text hits the same wall again (the idle window it's
measuring hasn't moved). Start a fresh session, or use the override token.

## Installation

Opt-in — not installed by default. Install via the ai-primitives marketplace:
```
/plugin install stale-session-guard@ai-primitives
```
