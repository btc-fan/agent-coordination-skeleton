# Agent Coordination Skeleton

Reusable local software-factory skeleton for Discord-driven development.

Primary architecture:
- Discord = control plane
- Factory gateway = deterministic dispatcher
- OmX = primary workflow/execution plane
- clawhip = event router and observability layer
- OpenAgent = optional specialist escalation plane

This repository is intentionally a template/skeleton, not an app.
It exists to be copied and adapted into future projects like Trend Spotter.

## Current scope
This skeleton now includes:
- source-of-truth docs
- memory/offload structure
- project-local OmX bootstrap
- OpenAgent project config
- clawhip routing template
- Discord command grammar
- control policy
- task templates by lane type
- dispatcher state/template scaffolding

It does **not** yet implement the actual gateway daemon.
