# AGENTS.md — Operating Contract

## Role & intent
This repository is operated through OmX-led workflows to produce a validated, clean-room codebase.
Primary goals: correctness, auditability, deterministic workflows, and verifiable delivery.

## Operating principles
- Prefer explicit workflow invocations ($deep-interview, $ralplan, $team, $ralph) over implicit keyword guessing.
- Keep operational noise out of coding context; clawhip owns notification routing.
- Treat docs/prd/current.md and docs/adr/* as source of truth; do not invent requirements.
- Never claim done without verification evidence (tests, lint, typecheck, reproducible commands).

## Execution protocols
### Standard development loop (authoritative)
Analysis → Planning → Coding/Tools → Review → Verification → Coding/Tools

### Workflow gates (required)
- If requirements are ambiguous: run $deep-interview until spec artefacts exist.
- For high-risk or irreversible work: run $ralplan --deliberate.
- For parallelisation: use $team (tmux workers + worktrees).
- For persistent single-owner verification: use $ralph.

### Artefact obligations
- Requirements: docs/prd/current.md (update when scope changes).
- Decisions: docs/adr/NNNN-*.md (one decision per ADR).
- Memory pointers: memory/MEMORY.md; details in memory/** leaf shards.

## Verification
- Minimum gate: unit tests + lint + typecheck + deterministic reproduction steps.
- If CI exists: match CI locally before declaring complete.
- If verification fails: loop back to Coding/Tools with explicit failure evidence.

## Recovery & lifecycle overlays
- If blocked on user input: emit a session.blocked event and write a clarification record in memory/daily/YYYY-MM-DD.md.
- If sessions drift: stop continuation, restate requirements from docs/prd/current.md, and re-plan.
