# Discord Command Grammar

Deterministic gateway commands only. No fuzzy routing.

## Project and lane commands
- `!proj init <name> <repo-url-or-template>`
- `!lane new <type> <slug>` where `<type>` ∈ `{feature, bug, refactor, experiment, seo, strategy}`

## OmX commands
- `!omx deep-interview "<prompt>"`
- `!omx ralplan "<prompt>" [--interactive] [--deliberate]`
- `!omx team <N:role> "<prompt>"`
- `!omx ralph "<prompt>" [--prd]`

## OpenAgent escalation
- `!oa start "<prompt>"`

## Human-in-the-loop controls
- `!reply <session_id> "<answer>"`
- `!stop <lane>`

## Rules
- The gateway parses commands deterministically.
- Discord owns intent and approvals only.
- The gateway maps each Discord thread to repo/worktree/branch/session IDs.
- Operational noise goes to clawhip-routed ops channels, not back into agent contexts.
