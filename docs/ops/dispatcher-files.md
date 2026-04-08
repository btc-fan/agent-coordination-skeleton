# Dispatcher Files

The factory gateway must persist deterministic state instead of relying on chat memory.

## Directory layout
- `factory/state/projects/` — project identity records
- `factory/state/lanes/` — lane runtime state records
- `factory/state/threads/` — Discord thread to lane mappings
- `factory/logs/dispatcher.jsonl` — append-only audit log of parsed commands and state changes
- `factory/templates/` — canonical JSON templates for new records

## Why split the state
The dispatcher must answer three different questions cleanly:
1. Which project does this thread belong to?
2. Which lane is active for this thread?
3. Which repo/worktree/session belongs to that lane?

## Hard rules
- The dispatcher parses typed commands only.
- The dispatcher never decides architecture or writes product code.
- The dispatcher owns mapping and process lifecycle only.
- All mutations should be auditable in `dispatcher.jsonl`.
