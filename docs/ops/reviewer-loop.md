# Reviewer Loop

The software factory is not just execution. It must support convergence through review.

## Core loop
- Architect / planner defines direction
- Executor builds
- Reviewer inspects output
- If serious problems exist, reviewer rejects and forces replanning
- If acceptable, reviewer approves and verification can close the lane

## Required reviewer statuses
- `pending`
- `requested`
- `rejected`
- `approved`

## Required transitions
- `requested` -> reviewer lane invoked
- `rejected` -> lane state becomes `review_rejected`, then `replanning`
- `approved` -> lane may proceed to final verification/closure

## Hard rules
- Reviewer rejection is not the same as a minor note.
- If implementation direction is wrong, lane must replan instead of blindly continuing.
- A lane is not done while reviewer rejection remains unresolved.

## What counts as reviewer rejection
- wrong architecture
- wrong scope
- missing verification
- hidden regressions
- mismatch with PRD/ADR/design constraints

## What reviewer approval means
- output is aligned with requirements
- no major unresolved direction errors remain
- verification can be considered authoritative
