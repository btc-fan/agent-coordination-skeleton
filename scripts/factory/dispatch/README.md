# Dispatch scripts

Deterministic local dispatcher MVP lives here.

## Current MVP
`factory.py` supports:
- `proj-init`
- `lane-new`
- `omx-deep-interview`
- `lane-status`
- `lane-stop`

## Purpose
This is the first executable layer between chat commands and the local runtime.
It mutates factory state files and can launch a real OmX deep-interview in a tmux-owned lane.

## Examples
```bash
python3 scripts/factory/dispatch/factory.py proj-init trend-spotter ~/openclaw/projects/trend-spotter
python3 scripts/factory/dispatch/factory.py lane-new trend-spotter feature trend-spotter-mvp --thread-id DISCORD_THREAD_ID
python3 scripts/factory/dispatch/factory.py omx-deep-interview trend-spotter-mvp "Build a trend spotter app from YouTube transcripts for dropshippers"
python3 scripts/factory/dispatch/factory.py lane-status trend-spotter-mvp
python3 scripts/factory/dispatch/factory.py lane-stop trend-spotter-mvp
```

## Current limitations
- no real Discord ingress yet
- no `pause/resume/change/done` handlers yet
- no OpenAgent launcher yet
- no automatic clawhip watch registration yet
