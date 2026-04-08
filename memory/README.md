# Memory layout

This repo follows filesystem-offloaded memory rules:
- MEMORY.md = pointer/index layer
- memory/projects/* = project state
- memory/daily/* = chronological execution log
- memory/topics/* = durable rules and lessons
- memory/handoffs/* = bounded transfer summaries
- memory/archive/* = cold history
