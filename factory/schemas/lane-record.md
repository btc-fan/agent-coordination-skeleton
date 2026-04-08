# Lane Record Schema

One file per lane under `factory/state/lanes/`.

## Required fields
- `lane_id`
- `project_id`
- `lane_type`
- `thread_id`
- `repo_path`
- `worktree_path`
- `branch`
- `tool`
- `session_name`
- `session_id`
- `state`
- `continuation_owner`
- `issue_id`
- `issue_url`
- `pr_id`
- `pr_url`
- `review_status`
- `clarification_status`
- `dod_status`
- `verification_status`
- `docs_status`
- `created_at`
- `updated_at`

## State meanings
- `planning` — deep-interview / planning active
- `executing` — main execution running
- `blocked_waiting_user` — explicit question or approval needed
- `paused` — intentionally halted with state preserved
- `replanning` — docs changed; plan must be refreshed
- `verifying` — verification lane active
- `review_rejected` — reviewer says direction is wrong or unacceptable
- `handoff_needed` — continuation requires explicit handoff
- `done` — all completion gates satisfied
- `stopped` — run intentionally killed; no auto-resume
- `failed` — non-terminal failure requiring operator decision

## Hard rules
- Exactly one continuation owner per lane.
- `done` is invalid unless DoD, verification, review, docs, issue/PR linkage, and clarification closure are all satisfied.
