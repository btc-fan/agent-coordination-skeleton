# Lane Event Schema

Append-only event log for lane lifecycle and convergence.

File:
- `factory/logs/lane-events.jsonl`

## Required fields
- `timestamp`
- `event_type`
- `project_id`
- `lane_id`
- `thread_id`
- `state`
- `actor` (`dispatcher`, `omx`, `reviewer`, `human`, `clawhip`, `openagent`)
- `summary`

## Optional fields
- `session_name`
- `session_id`
- `issue_id`
- `pr_id`
- `review_status`
- `verification_status`
- `details`

## Core event vocabulary
- `lane.created`
- `lane.started`
- `lane.blocked`
- `lane.reply-injected`
- `lane.paused`
- `lane.resumed`
- `lane.changed`
- `lane.replanning`
- `lane.review-requested`
- `lane.review-rejected`
- `lane.review-approved`
- `lane.verification-started`
- `lane.verification-failed`
- `lane.verification-passed`
- `lane.pr-created`
- `lane.pr-reviewed`
- `lane.merged`
- `lane.done-denied`
- `lane.done-approved`
- `lane.stopped`
- `lane.failed`
- `lane.handoff-needed`

## Purpose
Lane state is the current snapshot.
Lane events are the history of how the machine moved and why.
