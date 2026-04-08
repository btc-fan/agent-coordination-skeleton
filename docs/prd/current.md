# PRD — Agent Coordination Skeleton — Current

## Problem statement
We need a reusable local software-factory skeleton that reproduces the article’s Discord-driven coordination pattern without hardwiring it to one product.

## Target users
- Mike operating future projects like Trend Spotter
- Agent lanes running OmX as the primary workflow engine
- Optional OpenAgent specialist lanes

## Goals
- Provide a reusable project skeleton for Discord-driven control and local execution.
- Make OmX the workflow system-of-record.
- Centralize operational routing through clawhip.
- Keep source-of-truth docs separate from runtime state.

## Non-goals
- This repo is not the actual app.
- This repo does not implement the full factory gateway yet.
- This repo does not hardcode one project’s credentials or Discord IDs.

## Constraints
- Discord is the intended human control plane.
- OmX is primary; OpenAgent is escalation-only.
- clawhip is the single routing/formatting layer for ops events.
- Runtime state must remain gitignored.

## Success metrics
- New projects can be bootstrapped from this skeleton quickly.
- Docs, memory, and runtime boundaries stay clean.
- Future work follows explicit workflow and verification gates.

## Scope
### In scope
- Folder structure
- Core operating docs
- Memory layout
- OmX/OpenAgent skeleton config
- GitHub template/checklist scaffolding

### Out of scope
- Full dispatcher implementation
- Full Discord bot integration
- Full production clawhip route secrets

## User stories
- US-001 As an operator, I want a reusable skeleton so new projects start with the same workflow discipline.
- US-002 As an agent, I want stable docs and memory boundaries so I can execute without drift.

## Acceptance criteria (testable)
- AC-001 Required folders and files exist.
- AC-002 AGENTS.md defines workflow authority and verification rules.
- AC-003 docs/, memory/, .codex/, and .opencode/ are scaffolded.
- AC-004 Runtime state paths are gitignored.

## Verification plan
- Unit: n/a for initial skeleton
- Integration: verify OmX/OpenAgent/clawhip files are present and coherent
- E2E: bootstrap a future project from this skeleton
- Observability: clawhip config template exists for later wiring

## Rollout plan
Use this repo as the template/base for Trend Spotter and future projects.

## Open questions (must be resolved before execution declare-done)
- Exact factory gateway implementation language/runtime
- Final Discord command grammar
- Final lane naming and thread mapping rules
