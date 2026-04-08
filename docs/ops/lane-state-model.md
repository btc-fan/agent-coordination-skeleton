# Lane State Model

A Discord thread maps to one lane.

## Required state fields
- repo_path
- worktree_path
- branch
- session_id
- session_name
- lane_type
- lane_slug
- state
- continuation_owner
- issue_id
- issue_url
- pr_id
- pr_url
- review_status
- clarification_status
- dod_status
- verification_status
- docs_status

## Canonical states
- `planning`
- `executing`
- `blocked_waiting_user`
- `paused`
- `replanning`
- `verifying`
- `review_rejected`
- `handoff_needed`
- `done`
- `stopped`
- `failed`

## Rules
- `session.blocked` must move lane state to `blocked_waiting_user`.
- `!reply` resumes the mapped session and clears the blocked state.
- `!pause <lane>` preserves artifacts and halts autonomous forward execution.
- `!stop <lane>` kills tmux/session continuation, preserves artifacts, and marks lane `stopped`.
- `!change <lane> ...` must move the lane to `replanning` after docs are updated.
- `!done <lane> ...` updates task-specific DoD and may require replanning before resume.
- `done` is valid only after task-specific DoD, verification, reviewer closure, docs updates, issue/PR linkage, and clarification closure all hold.
