# Dispatcher Audit Log

File: `factory/logs/dispatcher.jsonl`

Append-only JSONL log of:
- raw command received
- parsed command type
- target project/lane/thread
- state mutation performed
- process/session action taken
- outcome (`ok`, `blocked`, `failed`)
- timestamp

## Why it exists
Without this log, debugging control-plane errors and state drift becomes painful.
The gateway must be auditable.
