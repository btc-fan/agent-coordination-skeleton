# Discord Channel Policy

## Purpose
Separate human control from operational noise.

## Recommended channels
- `#factory-control` — human commands, blocked questions, replies, approvals
- `#factory-decisions` — ADR approvals, PRD sign-offs, scope changes, DoD changes
- `#factory-ops` — clawhip-routed high-volume status, tmux keyword alerts, stale alerts, CI summaries, lifecycle events

## Rules
- Human intent and approvals belong in `#factory-control`.
- Scope/decision changes belong in `#factory-decisions`.
- High-volume operational chatter belongs in `#factory-ops`.
- Do not inject ops-channel noise into active coding contexts.
- Use a dedicated Discord bot token for clawhip operational delivery.

## Routing guidance
- `session.*` → `#factory-ops`
- `tmux.*` → `#factory-ops`
- blocked questions should be routed back to the relevant control thread with mention policy applied by clawhip
- default channel should be fallback only, not primary route policy
