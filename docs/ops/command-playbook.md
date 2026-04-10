# Command Playbook

## Review commands
### `lane-review-request <lane>`
Use when:
- executor output is ready for review
- you want explicit review state in the machine

### `lane-review-reject <lane> <reason>`
Use when:
- implementation direction is wrong
- scope/architecture diverged materially
- reviewer rejection should force replanning

Consequence:
- lane state becomes `review_rejected`
- lane event log records rejection
- task doc records rejection reason
- lane should replan before continuing

### `lane-review-approve <lane>`
Use when:
- reviewer agrees output is directionally valid
- lane can move toward final verification/closure

Consequence:
- review status becomes `approved`
- lane can proceed to verification closure
