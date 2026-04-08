# Worked Example — Trend Spotter Lane

This is the canonical example of how one real lane should map across Discord, dispatcher state, OmX, and clawhip.

## Step 1 — Create project record
Use `factory/examples/trend-spotter-project.json` as the model.

## Step 2 — Create lane record
Use `factory/examples/trend-spotter-lane-feature.json`.
Initial state:
- `state = planning`
- `continuation_owner = ""`
- `clarification_status = open`

## Step 3 — Create thread mapping
Use `factory/examples/trend-spotter-thread.json`.
This links the Discord thread to the lane.

## Step 4 — Start OmX deep-interview
Command:
`!omx deep-interview "Build a trend spotter app from YouTube transcripts for dropshippers"`

Dispatcher action:
- parse typed command
- locate thread → lane → project
- start OmX leader session
- append an audit line to `factory/logs/dispatcher.jsonl`

## Step 5 — Handle blocked question
If OmX emits `session.blocked`:
- clawhip routes the event to control thread
- lane state becomes `blocked_waiting_user`
- user answers with `!reply <session_id> "..."`

## Step 6 — Plan and execute
Once spec is ready:
- `!omx ralplan --deliberate "..."`
- then either:
  - `!omx team 3:executor "..."` for parallel build
  - or `!omx ralph "..."` for single persistent owner

## Step 7 — Done criteria
Lane can move to `done` only when:
- task-specific DoD satisfied
- verification evidence exists
- reviewer rejection cleared
- docs updated
- issue/PR linkage complete
- clarification state clear
