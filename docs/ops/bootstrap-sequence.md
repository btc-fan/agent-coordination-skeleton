# Bootstrap Sequence

## Deterministic setup order
1. Create repo from this skeleton.
2. Run `clawhip memory init` if a derived project needs fresh memory scaffolding.
3. Run `omx setup --scope project` in the target repo.
4. Install the clawhip OMX native hook bridge into `.omx/hooks/`.
5. Run `omx hooks validate` and `omx hooks test`.
6. Start clawhip daemon and confirm routing on `session.*` events.
7. Add `.opencode/oh-my-openagent.jsonc` only for projects that will use OpenAgent escalation lanes.

## Hard rules
- OmX is primary workflow authority.
- clawhip is the single routing layer.
- OpenAgent is escalation-only by default.
- Never run OmX Ralph and OpenAgent `/ralph-loop` in the same lane at the same time.
