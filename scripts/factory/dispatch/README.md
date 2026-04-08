# Dispatch scripts

Deterministic local dispatcher MVP lives here.

## Current executable surface
`factory.py` supports:
- `proj-init`
- `lane-new`
- `omx-deep-interview`
- `omx-ralplan`
- `lane-status`
- `lane-pause`
- `lane-resume`
- `lane-change`
- `lane-done`
- `lane-reply`
- `lane-stop`
- `lane-tail`

## Purpose
This is the executable layer between chat commands and the local runtime.
It mutates factory state files, instantiates task docs, and can launch real OmX runs in tmux-owned lanes.

## Examples
```bash
python3 scripts/factory/dispatch/factory.py proj-init trend-spotter ~/openclaw/projects/trend-spotter
python3 scripts/factory/dispatch/factory.py lane-new trend-spotter feature trend-spotter-mvp --thread-id DISCORD_THREAD_ID
python3 scripts/factory/dispatch/factory.py omx-deep-interview trend-spotter-mvp "Build a trend spotter app from YouTube transcripts for dropshippers"
python3 scripts/factory/dispatch/factory.py omx-ralplan trend-spotter-mvp "Approve architecture and validation plan" --deliberate
python3 scripts/factory/dispatch/factory.py lane-pause trend-spotter-mvp "Waiting on product clarification"
python3 scripts/factory/dispatch/factory.py lane-change trend-spotter-mvp "Add evidence ranking, keep transcript ingestion unchanged"
python3 scripts/factory/dispatch/factory.py lane-done trend-spotter-mvp "Require visual verification too" --force-replanning
python3 scripts/factory/dispatch/factory.py lane-reply trend-spotter-mvp "Focus on MVP only" --to-state planning
python3 scripts/factory/dispatch/factory.py lane-status trend-spotter-mvp
python3 scripts/factory/dispatch/factory.py lane-tail trend-spotter-mvp --lines 60
python3 scripts/factory/dispatch/factory.py lane-stop trend-spotter-mvp
```

## Important constraints
- Exactly one continuation owner per lane.
- `done` is invalid conceptually unless DoD, verification, review, docs, issue/PR linkage, and clarification closure all hold.
- `refactor` lanes currently instantiate the `design-change.md` task template.
- `--dangerous` is opt-in for OmX launchers; it is no longer the default.

## Current limitations
- no real Discord ingress yet
- no automatic clawhip watch registration yet
- no OpenAgent launcher yet
- no real reviewer lane launcher yet
