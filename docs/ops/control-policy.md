# Control Policy

This document defines the mandatory control semantics for the factory flow.

## Core rule
Do not treat pause, stop, change, redefine-done, and resume as the same action.
They have different meanings and different state transitions.

## Controls

### `pause`
Use when:
- waiting on human input
- inspecting partial output
- requirements are still alive but autonomous execution should temporarily halt

Effect:
- no more autonomous forward execution
- preserve branch, worktree, session, and artifacts
- lane state becomes `paused` or `blocked_waiting_user`
- write a summary into the task doc and `memory/daily/YYYY-MM-DD.md`

### `stop`
Use when:
- the current run should die
- drift is severe
- architecture changed enough that this run is no longer valid
- cost/time is being wasted

Effect:
- continuation is disabled
- lane state becomes `stopped`
- no auto-recovery or auto-resume
- artifacts are preserved

Hard rule:
- stopping a lane must never silently destroy branch/worktree/spec/plan artifacts

### `change`
Use when:
- task remains alive, but requirements changed materially
- scope changed
- implementation direction changed
- product/design/CEO input changed the target

Effect:
- pause active execution
- update the structured task artifact first
- if architecture changed, update PRD and ADRs
- lane state becomes `replanning`
- planning must run again before resume

### `redefine-done`
Use when:
- success criteria changed
- reviewer adds new mandatory conditions
- tests were insufficient
- business requirements changed what counts as complete

Effect:
- update task-specific DoD in the task artifact
- update AGENTS.md only if the rule is global
- if material, trigger replanning before resume

### `resume`
Resume is valid only after:
- docs reflect reality
- current plan is up to date
- blocked question is answered
- continuation owner is unambiguous

Resume must never mean “continue with stale assumptions.”

## One-loop-at-a-time rule
Never run OmX Ralph and OpenAgent `/ralph-loop` in the same lane simultaneously.
Each lane must have exactly one continuation owner.

## Force replanning when
- requirement changed materially
- architecture changed
- issue type changed
- branch/worktree became conceptually wrong
- reviewer says direction is wrong, not just imperfect
- the system is solving the wrong problem

Hard rule:
- do not continue in Ralph mode through a major scope mutation

## Done rule
A lane is not done unless all are true:
- task-specific DoD is satisfied
- verification gates pass
- no unresolved reviewer rejection remains
- required docs are updated
- issue/PR linkage is complete
- no pending clarification blocks the task
