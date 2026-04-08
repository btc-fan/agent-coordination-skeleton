# Factory State and Templates

This directory is reserved for the deterministic dispatcher layer.

## Structure
- `state/projects/` — project identity records
- `state/lanes/` — lane runtime state records
- `state/threads/` — thread to lane mappings
- `logs/dispatcher.jsonl` — append-only audit log
- `templates/` — canonical JSON templates for new records
- `schemas/` — human-readable field definitions and rules
- `examples/` — worked sample records for a real project

## Purpose
Make the control plane auditable and deterministic.
The gateway should mutate these records, not rely on chat memory.
