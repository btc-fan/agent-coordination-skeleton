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

## Canonical states
- `planning`
- `executing`
- `blocked_waiting_user`
- `verifying`
- `done`
- `stopped`

## Rules
- `session.blocked` must move lane state to `blocked_waiting_user`.
- `!reply` resumes the mapped session and clears the blocked state.
- `!stop <lane>` kills tmux/session continuation and marks lane `stopped`.
- `done` is valid only after verification evidence exists.
