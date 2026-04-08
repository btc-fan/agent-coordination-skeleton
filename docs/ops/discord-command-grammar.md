# Discord Command Grammar

Deterministic gateway commands only. No fuzzy routing.

## Project and lane commands
- `!proj init <name> <repo-url-or-template>`
- `!proj status <name>`
- `!lane new <type> <slug>` where `<type>` ∈ `{feature, bug, refactor, experiment, seo, strategy}`
- `!lane status <lane>`

## OmX commands
- `!omx deep-interview "<prompt>"`
- `!omx ralplan "<prompt>" [--interactive] [--deliberate]`
- `!omx team <N:role> "<prompt>"`
- `!omx ralph "<prompt>" [--prd]`

## OpenAgent escalation
- `!oa start "<prompt>"`

## Human-in-the-loop controls
- `!reply <session_id> "<answer>"`
- `!pause <lane>`
- `!stop <lane>`
- `!resume <lane>`
- `!change <lane> "<requirement delta>"`
- `!done <lane> "<new done rule>"`

## Rules
- The gateway parses commands deterministically.
- Discord owns intent and approvals only.
- The gateway maps each Discord thread to repo/worktree/branch/session IDs.
- Operational noise goes to clawhip-routed ops channels, not back into agent contexts.
- Typed commands update structured task/lane artifacts, not just the chat log.
