# Production-grade local AI software factory for macOS driven by Discord

## Phase 1 study findings: what each component ships today

**oh-my-codex (OmX) — real capabilities and defaults**

OmX is explicitly a workflow/runtime layer that sits on top of OpenAI’s Codex CLI rather than a replacement for it: Codex performs the actual agent work, while OmX provides a standardised workflow surface and durable runtime state under `.omx/` for plans, logs, memory, and mode tracking. citeturn7search0turn23search0

OmX’s “canonical pipeline” is documented as **deep-interview → ralplan → team/ralph**, and the public CLI surface includes `omx deep-interview`, `omx team`, and `omx setup` as first-class commands. citeturn6view6turn7search0

OmX installation and maintenance are centred around `omx setup` (installs prompts/skills, writes Codex config artefacts, scaffolds `AGENTS.md`, configures HUD/notifications) and `omx doctor` (verification). citeturn7search3turn8search3

OmX now treats Codex-native hooks as the canonical lifecycle surface for non-team sessions. `omx setup` owns `.codex/config.toml` (enabling `[features].codex_hooks = true`) and `.codex/hooks.json` (registering the OmX-managed native hook command). Internally, OmX separates (a) native Codex hook registration (`.codex/hooks.json`), (b) OmX plugin hooks (`.omx/hooks/*.mjs`), and (c) tmux/runtime fallback paths (`omx tmux-hook`, notify-hook, derived watcher, idle/session-end reporters). citeturn21view4turn8search3

OmX’s supported workflows are designed to be triggered deterministically via keywords and explicit `$skill` invocations, with documented resolution rules (case-insensitive keyword matching; explicit `$name` invocations override non-explicit routing; left-to-right execution for explicit invocations; “most specific” match wins). citeturn7search9

### Deep Interview (requirements clarification as a first-class mode)

The `deep-interview` skill is an **intent-first Socratic clarification loop** that explicitly forbids implementing inside the session; it exists to produce execution-ready requirement artefacts and a structured handoff into `$ralplan`, `$autopilot`, `$ralph`, or `$team`. citeturn24view0

It implements **quantitative ambiguity gating** with three depth profiles (Quick/Standard/Deep), explicit thresholds/max rounds, a mandatory “Non-goals” and “Decision Boundaries” readiness gate, and a requirement for at least one “pressure pass” revisiting earlier answers before crystallisation. citeturn24view0

Its persistence semantics are explicit:
- Context snapshots: `.omx/context/{slug}-{timestamp}.md`
- Interview transcript summary: `.omx/interviews/{slug}-{timestamp}.md`
- Execution-ready spec: `.omx/specs/deep-interview-{slug}.md`
- Mode state is persisted via `state_write/state_read` for resumability. citeturn24view0

Deep Interview also has a specialised `--autoresearch` intake that emits a launch-ready artefact bundle under `.omx/specs/autoresearch-{slug}/` and enforces a “refine further vs launch” confirmation boundary before detached execution. citeturn24view0

### Plan and RALPLAN-DR consensus planning

The `plan` skill supports (a) interview vs direct planning auto-detection, (b) consensus planning mode (Planner → Architect → Critic loop), and (c) plan review mode via Critic evaluation. It also imposes quality standards (evidence density and testability expectations) and “one question per round” interview discipline. citeturn21view0

`ralplan` is a documented shorthand alias for `$plan --consensus`, adding explicit consensus workflow structure and deliberate-mode escalation for high-risk work; it includes an iterative re-review loop with a maximum of five iterations and optional `--interactive` user approval gates at defined steps. citeturn21view1turn6view3

### Team mode

`$team` is a tmux-based parallel execution mode that starts *real* worker CLI sessions in split panes and coordinates through `.omx/state/team/...` plus CLI team interop (`omx team api ...`). It explicitly distinguishes itself from Codex native subagents by emphasising durability, shared task state, mailbox/dispatch coordination, and worktree isolation. citeturn21view3turn7search13

Team mode’s guidance is operationally strict: it must invoke the real `omx team` runtime (not simulate fanout), must surface concrete startup/state evidence, and reserves verification ownership as a dedicated lane. citeturn21view3

### Ralph persistence mode

`$ralph` is designed as a persistent execution/verification loop, with an explicit **PRD mode** (`--prd`) that:
- Runs `$deep-interview --quick` before PRD artefacts.
- Persists interview output to `.omx/interviews/{slug}-{timestamp}.md`.
- Creates PRD at `.omx/plans/prd-{slug}.md`.
- Tracks progress in `.omx/state/{scope}/ralph-progress.json`. citeturn21view2

Ralph further codifies background-vs-foreground execution rules (tests/builds/installs in background; quick checks and file edits in foreground). citeturn21view2

### Stop/continuation behaviour and tool hook scope

OmX’s Codex-native hook mapping documents which behaviours are truly native vs runtime-only. Critically:
- Native `PreToolUse/PostToolUse` scope is currently **Bash-only**.
- The native `Stop` hook path implements continuation logic for active Ralph/autopilot/ultrawork/ultraqa/team phases, with explicit “block decision + reason” semantics and a `stop_hook_active` guard to avoid re-block loops. citeturn21view4

OmX also documents that `ask-user-question` is runtime-only (no distinct Codex native hook for it today), and `session-idle/session-end` remain runtime-fallback emissions rather than native. citeturn21view4

### Notifications and question routing hooks

OmX’s notification/event inventory includes lifecycle events such as `session-start`, `session-stop`, `session-end`, `session-idle`, and `ask-user-question`, plus verbosity tiers that can include tmux tail snippets. It supports notification delivery via custom webhook commands and custom CLI commands. citeturn6view5


**clawhip — real capabilities and defaults**

clawhip is explicitly a **daemon-first Discord notification router** with a typed event pipeline, extracted event sources (Git/GitHub/tmux), and a clean router→renderer→sink split. citeturn10search0turn9view0

Its runtime architecture is a queue-driven pipeline:
`[sources] → [Tokio mpsc queue] → [dispatcher] → [router -> renderer -> sink] → Discord/Slack delivery`, with best-effort multi-delivery (one route failure does not stop others) and no built-in retry queue in the referenced architecture description. citeturn9view0turn10search0

clawhip’s shipped event families include Git commit/branch-change events, GitHub issue/PR events, tmux keyword/stale events, and agent lifecycle events, aligned to its typed event model. citeturn9view0

clawhip explicitly recommends a **dedicated Discord bot token** for high-volume operational notifications (commits, PRs, tmux keyword alerts, stale warnings), to keep those cleanly separated from an AI chat bot. citeturn10search0turn9view4

Configuration is TOML-based with preferred provider config under `[providers.discord]` (token, default_channel), dispatch batching windows, and `[[routes]]` entries that match event patterns and optional structured filters. citeturn10search0turn9view0

Routes can opt into dynamic template tokens (including `{tmux_tail:...}` and `{file_tail:...}`) when `allow_dynamic_tokens = true`. citeturn10search3

### Native OMC/OMX event contract and OmX bridge

clawhip’s **native OMC/OMX event contract** states the goal unambiguously: clawhip should be the single routing/formatting layer, while OMC/OmX should emit machine-readable native events rather than sending direct Slack/Discord notifications. citeturn10search4

It defines the canonical routing surface as `session.*` events (`session.started`, `session.blocked`, `session.finished`, `session.failed`, `session.retry-needed`, `session.pr-created`, `session.test-*`, `session.handoff-needed`), and provides mapping rules for legacy `agent.*` events for backward compatibility. citeturn10search4turn11search7

It also explicitly rejects treating raw OmX tool events (such as `pre-tool-use/post-tool-use`) as canonical new event families; instead, tool-level detail should be carried as metadata on existing frozen `session.*` events (e.g., `session.test-failed`) when the semantics warrant it. citeturn10search4

The recommended OmX integration path is the “native hook bridge” under `integrations/omx/`, which ships a small SDK and sample OmX hook plugin that forwards the frozen v1 envelope to `clawhip omx hook` (CLI) or `/api/omx/hook` (HTTP). The SDK has a documented discovery/transport order and explicit transport override via environment variables. citeturn11search0turn10search4

### Memory offload scaffolding

clawhip ships an explicit “filesystem-offloaded memory” pattern with a bootstrapping CLI (`clawhip memory init`) that scaffolds:
`MEMORY.md`, `memory/README.md`, `memory/daily/YYYY-MM-DD.md`, `memory/projects/<project>.md`, durable topic shards, and optional lane shards (channel/agent), leaving existing files untouched unless `--force` is set. citeturn9view1turn9view2

The operating rule is explicit: `MEMORY.md` is the fast pointer layer and should not accumulate all detail; detail belongs in leaf shard files, and `MEMORY.md` changes only when the pointer map or current beliefs change. citeturn9view1turn9view3


**oh-my-openagent — real capabilities and defaults**

Oh My OpenAgent is a **multi-model agent orchestration harness for OpenCode**, designed to transform a single agent into a coordinated team with explicit delegation and background parallelism. citeturn12view0turn12view2

Its architecture is anchored around an “Intent Gate” and core orchestrator agent (“Sisyphus”), with specialist agents such as Prometheus (planner), Atlas (todo execution), Oracle (architecture/review), Librarian (docs/search), and Explore (fast grep), plus category-based agent selection. citeturn12view0turn12view2

Configuration is explicitly file-based, with strong rename-compatibility notes:
- Project config: `.opencode/oh-my-openagent.json[c]` or `.opencode/oh-my-opencode.json[c]`
- User config (macOS/Linux): `~/.config/opencode/oh-my-openagent.json[c]` or legacy `~/.config/opencode/oh-my-opencode.json[c]`
- Detection currently checks legacy `oh-my-opencode.*` before `oh-my-openagent.*` if both exist in the same directory. citeturn22view0turn22view1

It supports determinism in UI agent tab cycling via an injected runtime ordering for core agents (Sisyphus=1, Hephaestus=2, Prometheus=3, Atlas=4). citeturn12view1turn12view2

### Background tasks, stale control, and task persistence

OpenAgent supports background agent execution with explicit concurrency controls, including `staleTimeoutMs` (interrupt tasks with no activity; minimum 60s) and per-provider/per-model concurrency overrides, with clear priority rules. citeturn15view1turn14view0

Its task system can be enabled with `experimental.task_system: true`, and it defines a Claude-Code-aligned task schema (subject/blockedBy/blocks/etc.), dependency semantics, and storage as JSON files in `.sisyphus/tasks/`. citeturn16view2turn15view1

### Continuation loops and stop controls

OpenAgent ships slash-command workflows including:
- `/ralph-loop` (self-referential development loop) with completion detection via `<promise>DONE</promise>`, auto-continue behaviour, and explicit stop conditions (max iterations or `/cancel-ralph`). citeturn16view0turn13view3
- `/stop-continuation` (stops ralph loop, todo continuation, and boulder state for the session). citeturn16view1turn13view3
- `/handoff` (generates a structured handoff document for continuing work in a new session). citeturn16view1turn13view3
- `/init-deep` (generates hierarchical `AGENTS.md` files throughout a project). citeturn16view0turn13view3

### Hashline edit and context pruning

OpenAgent can replace the built-in edit tool with “Hashline Edit”, which uses hash-anchored `LINE#ID` references to prevent stale-line edits; it enables two companion hooks for read annotation and diff enhancement. citeturn15view3turn13view2

It also provides optional “dynamic_context_pruning” strategies (deduplication, supersede-writes, purge-errors) with turn protection and tool protection lists. citeturn15view3turn13view2

### Hook inventory and safeguards

OpenAgent documents a large hook inventory, including:
- AGENTS/rules injection hooks
- continuation hooks (todo continuation enforcer, ralph-loop)
- safety hooks (write-existing-file guard, hashline enhancers, recovery hooks)
- runtime fallback switching among models/providers on retryable errors. citeturn16view3turn15view2turn14view5

It can also run Claude Code-style hook scripts via a “Claude Code hooks integration” mechanism that reads `.claude/settings.json` and executes configured hook commands. citeturn16view4turn14view7


**claw-code orchestration concept — architectural intent vs illustration**

The core architectural intent described by Claw Code’s own “PHILOSOPHY.md” is:
- The human interface is a Discord channel.
- The system is a three-part composition: OmX (workflow layer), clawhip (event/router layer), and OmO (multi-agent coordination layer).
- Notification routing must be pushed out of the agent context window to keep agents focused on implementation rather than formatting/routing operational noise. citeturn20view0

A secondary explanation of the same concept describes the operational loop explicitly as Architect → Executor → Reviewer cycles, with Discord as the human interface and clawhip filing updates/mentions when blocked, and continuing otherwise. citeturn20view1

Architectural (non-illustrative) parts to treat as constraints:
- Discord as the control surface (chat-first control plane). citeturn20view0turn20view1
- Event delivery and monitoring out of active coding context (context hygiene). citeturn20view0turn10search4
- Structured planning/execution/review/retry loops; convergence under disagreement. citeturn20view0turn20view1turn12view2

Illustrative parts to treat as non-binding:
- Exact agent naming conventions for “Architect/Executor/Reviewer” (implement as lanes/roles mapped onto each tool’s real primitives rather than inventing a new agent framework). citeturn21view1turn21view3turn12view0turn12view2


## Boundary reconciliation and authority

**2. Phase 2 — reconcile overlaps and boundaries (implementation constraints + authority rules)**

**OmX vs Oh My OpenAgent (planning, execution, loops)**  
Both stacks ship planning and continuation mechanics, but they are anchored to different harnesses and persistence models:

- OmX’s planning and execution workflows are expressed as Codex skills/modes (`$deep-interview`, `$plan`, `$ralplan`, `$team`, `$ralph`) and persist state/artefacts under `.omx/`, with Codex-native hook participation for some lifecycle events and Bash-only tool hooks. citeturn24view0turn21view0turn21view4  
- OpenAgent’s orchestration is expressed as an OpenCode plugin with its own agent inventory, background task concurrency, slash-command workflows (`/ralph-loop`, `/handoff`, `/stop-continuation`), a task system stored in `.sisyphus/tasks/`, and optional hashline editing to prevent stale-line edits. citeturn12view2turn16view1turn16view2turn15view3  

**Authority rule (recommended):**
- OmX is the system-of-record for **project workflow state** (requirements → plan → implementation → verification → delivery) and for ensuring the output is a validated, clean-room codebase (because its workflows explicitly orchestrate requirements artefacts, consensus planning, tmux team worktrees, and persistence loops tied to repo state). citeturn24view0turn21view1turn21view3turn21view2  
- OpenAgent is an **escalation engine** for (a) parallel specialist lanes, (b) reviewer lanes, and (c) high-risk refactors where hashline edit + dynamic pruning + background tasks materially reduce stale edits and context overload. citeturn16view3turn15view3turn15view1  

**One-loop-at-a-time rule (hard constraint):**  
Never run OmX Ralph persistence and OpenAgent `/ralph-loop` continuation in the same lane simultaneously. Use one continuation mechanism per lane and enforce explicit “stop continuation” semantics at lane boundaries (OpenAgent provides `/stop-continuation`; OmX documents stop-hook continuation guards). citeturn13view3turn21view4  

**clawhip vs OmX hooks (routing, monitoring, notifications)**  
clawhip’s contract positions it as the single routing and formatting layer; OmX should emit machine-readable session events, not do direct Discord notifications, for clawhip-integrated operator workflows. citeturn10search4turn11search0turn11search7

**Authority rule (recommended):**
- OmX owns event *emission* (structured session lifecycle facts, embedded metadata) but cedes routing/format/mention policy to clawhip. citeturn10search4turn11search0turn21view4  
- clawhip owns delivery policy (channels, batching, formats, mentions) and must be the only component that floods high-volume operational noise into Discord. citeturn10search0turn9view0turn20view0  

**clawhip vs “general notifications”**  
clawhip is not “notifications” in the generic sense; it is an event pipeline with multiple sources (git/GitHub/tmux/custom ingress), route resolution that can fan out to multiple deliveries per event, and renderer/sink separation. Treat it as the harness-level observability and event router. citeturn9view0turn10search0turn10search3  

**OmX Ralph vs OpenAgent resumption/task persistence**  
OmX Ralph persists progress and PRD artefacts in `.omx/state/.../ralph-progress.json` for its loop. OpenAgent persists task state in `.sisyphus/tasks/` and can create session handoff artefacts via `/handoff`. Treat these as separate persistence planes:
- `.omx/` is OmX runtime truth for Codex-based execution.
- `.sisyphus/` is OpenAgent runtime truth for OpenCode-based execution. citeturn21view2turn16view2turn15view1  


## Executive architecture and component interactions

**1. Executive architecture — final recommended architecture (plain English)**

A reusable “local software factory” on macOS is best implemented as a **four-layer system**:

1) **Discord control plane** (human interface): low-noise command messages go to a control channel/thread. This is the only place the human “drives”. citeturn20view0turn20view1  

2) **Factory gateway** (deterministic dispatcher on the Mac): a small local daemon that:
- parses Discord commands into an explicit workflow intent (no fuzzy agent routing in the gateway),
- maps a Discord thread to a repo + worktree + lane/session IDs,
- starts/stops OmX sessions and (optionally) OpenAgent sessions,
- never emits operational noise into active agent contexts (only injects user answers/explicit control commands).  
This layer is new glue, but it is not an agent framework; it is a deterministic process launcher and state mapper built around the existing mechanisms of OmX/clawhip/OpenAgent. citeturn10search4turn21view3turn22view1turn20view0  

3) **OmX execution plane** (primary orchestration and repo workflow): OmX runs Codex sessions (leader or tmux team workers) to execute the canonical development loop: Analysis → Planning → Coding/Tools → Review → Verification → Coding/Tools. Use `$deep-interview` and `$ralplan` as explicit gates before long-running execution modes; use `$team` for coordinated parallel work and `$ralph` for persistence + verification when a single-owner loop is required. citeturn24view0turn21view1turn21view3turn21view2turn20view1  

4) **clawhip harness plane** (event router, session coordination signals, memory scaffolding): clawhip runs as a background daemon and owns all routing, formatting, batching, and mentions for operational events, especially session lifecycle and tmux monitoring signals. OmX emits contract-compliant session events; clawhip ingests, normalises, and routes. citeturn9view0turn10search4turn11search0turn20view0  

OpenAgent fits as a **specialist expansion plane**: it is invoked by the gateway (or by an OmX-approved step) to run parallel reviewer/specialist lanes in OpenCode when its mechanics are advantageous (hashline edit to prevent stale edits; dynamic pruning; background tasks; slash-command loops). It remains subordinate to OmX’s workflow authority, and its outputs converge back through Git artefacts (PRs/branches) and clawhip-delivered status summaries. citeturn15view3turn16view3turn22view1turn20view0  

**Why this architecture is correct (tied to claw-code intent and real plugin behaviour)**  
This architecture matches Claw Code’s stated philosophy: Discord is the human interface; OmX turns directives into structured execution; clawhip keeps monitoring/delivery outside the coding agent’s context window; OmO/OpenAgent provides multi-agent coordination and convergence when roles disagree. citeturn20view0turn20view1turn12view2turn10search4

It also aligns with clawhip’s explicit contract requirement that the notification/router layer should be centralised in clawhip (not duplicated in each agent toolchain), avoiding double-notification, inconsistent mention policy, and context pollution. citeturn10search4turn11search7

Finally, it respects OmX’s real runtime boundaries: Codex-native hook scope is limited (Bash-only tool hooks), some events are runtime-only, and persistence/continuation behaviour is hook-guarded; therefore, the gateway and clawhip should not rely on fragile parsing of agent text, but on explicit session event emission + structured state artefacts and worktree/workflow discipline. citeturn21view4turn21view3turn10search4

**Sequence diagram (Discord-driven, OmX primary, clawhip routing, OpenAgent optional escalation)**

```text
Human (Discord)          Factory Gateway (macOS)          OmX (Codex)                clawhip daemon               OpenAgent (OpenCode)
     |                           |                           |                           |                             |
     | !new project X            |                           |                           |                             |
     |-------------------------->| create repo/worktrees      |                           |                             |
     |                           | start clawhip watches      |                           |                             |
     |                           |--------------------------->| (optional) start omx      |                             |
     |                           |                           |--------------------------->|                             |
     |                           |                           | emits session.started      |                             |
     |                           |                           |--------------------------->| ingest+route to Discord      |
     |                           |                           |                           |----------------------------->|
     |                           |                           |                           | status msg in #ops            |
     | !omx deep-interview ...   |                           |                           |                             |
     |-------------------------->| inject prompt/start leader |                           |                             |
     |                           |--------------------------->| $deep-interview runs       |                             |
     |                           |                           | asks a question            |                             |
     |                           |                           | emits session.blocked      |                             |
     |                           |                           |--------------------------->| route @mention in #control    |
     | !reply <sid> <answer>     |                           |                           |                             |
     |-------------------------->| inject answer into session |                           |                             |
     |                           |--------------------------->| continues; writes .omx/specs|                            |
     |                           |                           | emits session.finished     |                             |
     |                           |                           |--------------------------->| route finished                |
     | !omx ralplan ...          |                           |                           |                             |
     |-------------------------->| inject/start consensus     | Planner/Architect/Critic   |                             |
     |                           |                           | writes plan artefacts       |                             |
     | !omx team 3:executor ...  |                           |                           |                             |
     |-------------------------->| start tmux workers/worktrees| tmux sessions spawn        |                             |
     |                           |                           | emits session.* updates     |                             |
     |                           |                           |--------------------------->| route + tmux keyword alerts   |
     | (optional) !oa review ... |                           |                           |                             |
     |-------------------------->| start OpenAgent lane       |                           |                             |
     |                           |--------------------------------------------------------->| tmux watch + route summaries  |
     |                           |                                                     start OpenAgent session      |
     |                           |----------------------------------------------------------------------------->
```

**Component interaction diagram (ownership boundaries)**

```text
                 Discord (control surface)
                          |
                          v
                 Factory Gateway (deterministic)
                  |                |
      (launch/inject)              | (status only; never inject noise)
                  v                v
       OmX / Codex sessions     clawhip daemon (router)
        (leader/team/ralph)      - typed events
          |   |                 - route policy
          |   +--- emits v1      - discord delivery
          |       hook envelopes
          v
   .omx/ runtime state + artefacts
   - .omx/specs, .omx/plans, .omx/state
   - optional .omx/hooks forwarding to clawhip

Optional escalation lane:
   Factory Gateway -> OpenCode + Oh My OpenAgent
   - .opencode/oh-my-openagent.jsonc
   - .sisyphus/tasks/
   - hashline edit, dynamic pruning, background tasks
   - results return via git artefacts + clawhip-routed status
```

**Control ownership map (hard rules)**  
- **Discord** owns human intent and approvals only. citeturn20view0turn24view0  
- **Factory gateway** owns deterministic parsing, mapping, and process lifecycle; it does not “decide” architecture or write production code. citeturn10search4turn21view3turn22view1  
- **OmX** owns workflow state and the authoritative dev loop (requirements → plan → coordinated execution → verification → delivery). citeturn24view0turn21view1turn21view3turn21view2  
- **clawhip** owns routing, formatting, batching, and mention policy for operational events (single routing layer doctrine). citeturn10search4turn10search0turn9view0  
- **OpenAgent** owns specialist/parallel orchestration inside OpenCode when invoked, including background tasks, task persistence, and stale-edit prevention mechanisms (hashline edit). citeturn15view1turn16view2turn15view3  


## Full local macOS project structure: reusable factory layout and file ownership

**3. Full local project architecture — macOS layout (reusable across projects)**

The architecture below uses three distinct persistence planes:
- **Git-tracked “source of truth”**: product and engineering documents, templates, ADRs, PRD, UI rules, checklists.
- **Repo-local durable memory** (Git-tracked) using clawhip’s filesystem-offloaded memory layout (`MEMORY.md` + `memory/` shards). citeturn9view1turn9view2  
- **Runtime state** (gitignored): `.omx/` (OmX), `.sisyphus/` (OpenAgent), `.port_sessions/` (Claw Code port, if ever used), plus local logs.

### Reusable folder tree (single repo)

```text
<repo-root>/
  AGENTS.md                         # OmX top-level operating contract (Git-tracked)
  README.md                          # Human-facing overview (Git-tracked)

  docs/
    prd/
      current.md                     # current PRD (source of truth)
      backlog.md                     # optional: PRD-aligned backlog
    adr/
      0001-template.md               # ADR template
      0002-<decision>.md             # ADR instances (source of truth)
    product/
      vision.md                      # product vision
      roadmap.md                     # roadmap & sequencing
    design/
      ui-rules.md                    # UI/UX invariants & constraints
      accessibility.md               # optional
    ceo/
      strategy.md                    # strategy/positioning/monetisation notes
    qa/
      validation-checklist.md        # required verification gates
      test-strategy.md               # unit/integration/e2e strategy
    ops/
      deployment-checklist.md        # deploy gates & rollback steps
      incident-runbook.md            # post-release operations

  memory/
    MEMORY.md                        # pointer/index/current beliefs (fast layer)
    README.md                        # subtree guide
    projects/
      <project>.md                   # project-specific state
    daily/
      YYYY-MM-DD.md                  # chronological execution log
    topics/
      rules.md                       # durable operating rules
      lessons.md                     # reusable lessons
    handoffs/
      YYYY-MM-DD-<slug>.md           # bounded handoffs
    archive/
      YYYY-MM/                       # cold history

  scripts/
    factory/
      dispatch/                      # Discord gateway scripts (safe wrappers)
      verify/                        # CI parity scripts used locally
      pr/                            # PR creation helpers

  .github/
    workflows/
      ci.yml
    ISSUE_TEMPLATE/
      bug_report.md
      feature_request.md
    pull_request_template.md

  .codex/
    config.toml                      # Codex hook enablement (managed by omx setup)
    hooks.json                       # Codex native hook registration (generated; gitignored)
    rules/
      default.rules                  # deterministic coding rules (Git-tracked; read by agents)

  .opencode/
    oh-my-openagent.jsonc            # OpenAgent config (project override)
    skills/                          # optional custom skills (OpenCode)
    command/                         # optional custom commands (OpenCode)

  .gitignore                         # must ignore .omx/, .sisyphus/, worktrees, etc.

  worktrees/                         # optional repo-local worktree directory (gitignored)
    <branch-or-issue>/               # git worktrees created by OmX team mode or gateway
```

Why this matches shipped behaviour:
- clawhip’s `memory init` scaffolds `MEMORY.md` + `memory/daily`, `memory/projects`, and related shards exactly in this shape. citeturn9view1turn9view2  
- OmX explicitly uses `.omx/` for runtime state/memory/plans/logs and manages `.codex/config.toml` + `.codex/hooks.json` for native hook ownership. citeturn7search0turn21view4  
- OpenAgent explicitly supports project config at `.opencode/oh-my-openagent.json[c]` and task storage at `.sisyphus/tasks/`. citeturn22view1turn15view1turn16view2  

### Ownership map per directory/file class

Source-of-truth (Git-tracked):
- `docs/**` — owned by the human + Architect lane; consumed by OmX planning and Reviewer lanes as hard constraints. citeturn24view0turn21view1turn20view0  
- `memory/**` — owned by the harness discipline: detail in shards, pointers in `MEMORY.md`. clawhip provides the scaffolds and the operating rule. citeturn9view1turn9view3  
- `.codex/rules/**` — owned by the determinism policy; consumed by agent rule injectors (tool-specific). citeturn16view3turn21view4  

Runtime/derived (Git-ignored):
- `.omx/**` — owned by OmX modes (`deep-interview`, `ralplan`, `team`, `ralph`) for state and artefacts. citeturn24view0turn21view2turn21view3  
- `.sisyphus/**` — owned by OpenAgent task system and cross-session tracking. citeturn15view1turn16view2  
- `.codex/hooks.json` — generated and explicitly expected to be gitignored in project scope. citeturn21view4  


## Exact file definitions: templates and line-by-line intent

**4. Exact file definitions — production-ready templates with rationale**

### AGENTS.md (OmX operating contract; project root)

Template:

```md
# AGENTS.md — Operating Contract

## Role & intent
This repository is operated through OmX-led workflows to produce a validated, clean-room codebase.
Primary goals: correctness, auditability, deterministic workflows, and verifiable delivery.

## Operating principles
- Prefer explicit workflow invocations ($deep-interview, $ralplan, $team, $ralph) over implicit keyword guessing.
- Keep operational noise out of coding context; clawhip owns notification routing.
- Treat docs/prd/current.md and docs/adr/* as source of truth; do not invent requirements.
- Never claim “done” without verification evidence (tests, lint, typecheck, reproducible commands).

## Execution protocols
### Standard development loop (authoritative)
Analysis → Planning → Coding/Tools → Review → Verification → Coding/Tools

### Workflow gates (required)
- If requirements are ambiguous: run $deep-interview until spec artefacts exist.
- For high-risk or irreversible work: run $ralplan --deliberate.
- For parallelisation: use $team (tmux workers + worktrees).
- For persistent single-owner verification: use $ralph.

### Artefact obligations
- Requirements: docs/prd/current.md (update when scope changes).
- Decisions: docs/adr/NNNN-*.md (one decision per ADR).
- Memory pointers: memory/MEMORY.md; details in memory/** leaf shards.

## Verification
- Minimum gate: unit tests + lint + typecheck + deterministic reproduction steps.
- If CI exists: match CI locally before declaring complete.
- If verification fails: loop back to Coding/Tools with explicit failure evidence.

## Recovery & lifecycle overlays
- If blocked on user input: emit a session.blocked event and write a clarification record in memory/daily/YYYY-MM-DD.md.
- If sessions drift: stop continuation, restate requirements from docs/prd/current.md, and re-plan.
```

Why each block exists:
- “Operating principles” enforces the claw-code intent that monitoring stays out of the agent’s context window and routing belongs to clawhip. citeturn20view0turn10search4  
- “Workflow gates” maps directly onto OmX’s real skill contracts: deep-interview is requirements-only and explicitly bridges into ralplan/autopilot/ralph/team; ralplan supports deliberate mode; team is tmux/worktree coordination; ralph is a persistent loop with PRD mode. citeturn24view0turn21view1turn21view3turn21view2  
- “Artefact obligations” binds to clawhip’s filesystem-offloaded memory doctrine (`MEMORY.md` pointer layer) and prevents monolithic memory rot. citeturn9view1turn9view3  

### docs/prd/current.md (source of truth requirements)

Template:

```md
# PRD — <Project> — Current

## Problem statement
## Target users
## Goals
## Non-goals
## Constraints
## Success metrics

## Scope
### In scope
### Out of scope

## User stories
- US-001 ...
- US-002 ...

## Acceptance criteria (testable)
- AC-001 ...
- AC-002 ...

## Verification plan
- Unit:
- Integration:
- E2E:
- Observability:

## Rollout plan
## Open questions (must be resolved before execution declare-done)
```

Rationale:
- OmX deep-interview explicitly requires Non-goals and Decision Boundaries as readiness gates before handoff; this PRD template makes Non-goals first-class and testable acceptance criteria explicit. citeturn24view0turn21view0  
- OmX Ralph PRD mode constructs user stories with acceptance criteria and tracks pass/fail state; this PRD structure keeps those artefacts compatible with a ralph-style verification ledger when desired. citeturn21view2  

### docs/adr/0001-template.md (decision record)

Template:

```md
# ADR — <Title>

## Context
## Decision
## Alternatives considered
## Consequences
## Verification and rollout notes
## Links
- PR:
- Relevant docs:
```

Rationale:
- Consensus planning (`ralplan`) explicitly requires viable options and invalidation rationale; ADRs are the durable place to preserve those option trade-offs beyond a single planning session. citeturn21view1turn21view0  

### docs/product/vision.md and docs/ceo/strategy.md (leadership intent constraints)

Keep these deliberately short and stable; they function as “intent anchors” that the Architect lane must treat as non-negotiable constraints, preventing drift during long-running execution loops. This matches deep-interview’s intent-first design and claw-code’s emphasis that the scarce resource is architectural clarity and direction. citeturn24view0turn20view0  

### docs/design/ui-rules.md (design invariants)

Use a rule-style document (constraints, tokens, layout invariants, accessibility requirements). This enables the Reviewer lane to enforce UI consistency without reloading large design conversations into the active coding context. citeturn20view0turn13view7  

### memory/MEMORY.md and shard files (filesystem-offloaded memory)

Root pointer file template (aligned to clawhip example):

```md
# MEMORY.md — pointer/index layer

## Current beliefs
- Current priority:
- Current risks:
- Current decision boundaries:

## Quick file map
- Project status: memory/projects/<project>.md
- Today’s execution log: memory/daily/YYYY-MM-DD.md
- Durable rules: memory/topics/rules.md
- Durable lessons: memory/topics/lessons.md

## Read this when…
- You need current repo status -> memory/projects/<project>.md
- You need latest execution context -> memory/daily/YYYY-MM-DD.md
- You are changing workflow policy -> memory/topics/rules.md

## Write obligations
- Detail goes in leaf shards; MEMORY.md changes only when pointers/beliefs change.
```

This is the exact policy clawhip documents: `MEMORY.md` is a fast pointer layer and detail belongs in leaf shards. citeturn9view1turn9view3  

### .codex/config.toml and .codex/hooks.json (managed by OmX)

Operational rule:
- Treat `.codex/config.toml` and `.codex/hooks.json` as **OmX-managed** artefacts for native hook enablement and registration; do not hand-edit them in normal operation. citeturn21view4turn8search3  

Minimum expectations:
- `.codex/config.toml` must enable `[features].codex_hooks = true`. citeturn21view4  
- `.codex/hooks.json` must register the OmX-managed native hook command; for project scope, `.gitignore` should keep it out of source control. citeturn21view4  

### .codex/rules/default.rules (determinism rule layer)

Use this as a small “hard constraints” file that enforces:
- do not claim done without verification evidence,
- do not write outside allowed directories,
- do not run destructive shell commands without explicit approval,
- prefer worktrees and atomic PRs.

This fits the overall harness approach: keep rules small, stable, and enforceable by hook-level injection rather than repeated chat reminders. citeturn21view4turn16view3turn20view0  

### .opencode/oh-my-openagent.jsonc (project override)

Template (minimal, anchored to documented keys):

```jsonc
{
  // Enable schema autocomplete (officially documented in config reference)
  "$schema": "https://raw.githubusercontent.com/code-yeongyu/oh-my-openagent/dev/assets/oh-my-opencode.schema.json",

  // Keep rename-transition behaviour explicit:
  // (If legacy oh-my-opencode.jsonc exists in the same directory, legacy wins.)
  "agents": {
    "sisyphus": { "model": "anthropic/claude-opus-4-6", "variant": "max" },
    "oracle": { "model": "openai/gpt-5.4", "variant": "high" }
  },

  "background_task": {
    "defaultConcurrency": 5,
    "staleTimeoutMs": 180000,
    "providerConcurrency": { "anthropic": 2, "openai": 2, "google": 4 }
  },

  "experimental": {
    "task_system": true,
    "dynamic_context_pruning": {
      "enabled": true,
      "notification": "minimal",
      "turn_protection": { "enabled": true, "turns": 3 }
    }
  },

  "hashline_edit": true,

  "tmux": { "enabled": true, "layout": "main-vertical" },

  "disabled_hooks": [
    // Example: if you prefer external review tools
    // "comment-checker"
  ]
}
```

Every key above is explicitly documented, including file locations and rename compatibility, background task concurrency/stale timeout, dynamic pruning, hashline edit, and tmux integration. citeturn22view1turn15view1turn15view3turn14view4turn14view7  

### clawhip routing config (single source of truth for Discord delivery)

Minimal structure (TOML):

```toml
[providers.discord]
token = "DISCORD_BOT_TOKEN_FOR_CLAWHIP"
default_channel = "123456789012345678"

[dispatch]
routine_batch_window_secs = 5
ci_batch_window_secs = 300

[[routes]]
event = "session.*"
filter = { tool = "omx", repo_name = "<repo>" }
channel = "123456789012345678"
format = "compact"

[[routes]]
event = "tmux.*"
channel = "123456789012345678"
format = "alert"
```

This is aligned to clawhip’s preferred provider config surface and the native contract’s guidance to route on `session.*` first for OmX traffic. citeturn10search0turn10search4turn11search7  

### PR template, issue template, release checklist, validation checklist

These files enforce “validated codebase” delivery by design:
- PR template must require reproduction steps and verification evidence.
- Validation checklist becomes the definition of done enforced by Reviewer lanes.
This aligns with OmX planning quality requirements (testable criteria) and with the claw-code philosophy that the coordination system is the product lesson, not plausible output. citeturn21view0turn21view1turn20view0turn20view1  


## Discord-driven operating model and workflow selection

**5. Discord-driven operating model — information architecture, routing, and auditability**

### Channel and thread model (recommended)

Use **one server for all projects** with strict channel separation by function:
- `#factory-control` (low-noise): human commands only; each workstream uses a thread.
- `#factory-decisions` (low-volume): ADR approvals, PRD sign-offs, scope updates.
- `#factory-ops` (high-volume): clawhip-routed status/events, CI summaries, tmux keyword alerts, stale warnings.
- Optional trust-boundary split: separate servers when projects differ in credential sensitivity or when Discord membership differs materially.

This directly implements claw-code’s “Discord as interface” intent while preserving clawhip’s requirement to keep high-volume operational noise separate (and to use a dedicated bot token to avoid mixing bot roles). citeturn20view0turn10search0turn9view4  

### Command grammar (deterministic, short, auditable)

Gateway commands must be explicit (no fuzzy routing in the gateway). Example grammar:

- `!proj init <name> <repo-url-or-template>`
- `!lane new <type> <slug>` where `<type>` ∈ `{feature, bug, refactor, experiment, seo, strategy}`
- `!omx deep-interview "<prompt>"`
- `!omx ralplan "<prompt>" [--interactive] [--deliberate]`
- `!omx team <N:role> "<prompt>"`
- `!omx ralph "<prompt>" [--prd]`
- `!oa start "<prompt>"` (OpenAgent escalation lane)
- `!reply <session_id> "<answer>"` (inject into OmX session when blocked)
- `!stop <lane>` (kills tmux session + stops continuation mechanisms; clawhip watch removed)

This approach supports determinism and auditability because every action is a typed intent rather than implied by natural language. It complements OmX’s own deterministic skill routing (explicit `$skill` invocations) without competing with it. citeturn7search9turn21view3turn10search4  

### Project identity mapping (Discord → repo/worktree/session)

The gateway must persist a mapping record per Discord thread that includes:
- repo path
- worktree path
- branch name
- OmX session ID / tmux session name
- current lane state (`planning`, `executing`, `blocked`, `verifying`, `done`)
These map directly onto clawhip’s normalised metadata fields (`repo_name`, `repo_path`, `worktree_path`, `branch`, `session_id`, `session_name`) as the canonical event payload fields to route on. citeturn10search4turn11search7  

### How clawhip routes map into Discord

For OmX lanes, route `session.*` events into `#factory-ops`, filtered by `tool="omx"` + `repo_name` + optional `session_name`/`issue_number`/`branch`. This is the contract-recommended stable routing approach. citeturn10search4turn11search7

For tmux monitoring (both OmX team sessions and OpenAgent tmux panes), route `tmux.keyword` and `tmux.stale` into `#factory-ops` with `format="alert"` and an explicit mention only on blocked/failure keywords. clawhip explicitly supports tmux monitoring sources and tmux watch/new registration paths. citeturn9view0turn11search1turn10search3  

**6. Invocation rules — decision matrix (exact workflow selection)**

The matrix below treats OmX as primary and OpenAgent as escalation, consistent with claw-code’s three-part system framing and with each tool’s shipped strengths. citeturn20view0turn24view0turn15view3turn10search4

| Condition (deterministic) | Preferred workflow | Why (tied to shipped behaviour) | Expected artefacts | Stop condition |
|---|---|---|---|---|
| Idea is vague / acceptance criteria missing / scope unclear | OmX `$deep-interview` (Standard) | Deep Interview is explicitly requirements-only, ambiguity-gated, produces `.omx/specs/*` and forbids direct implementation. citeturn24view0 | `.omx/context/*`, `.omx/interviews/*`, `.omx/specs/deep-interview-*` citeturn24view0 | ambiguity ≤ threshold AND Non-goals + Decision Boundaries resolved citeturn24view0 |
| High-risk change (auth/security/migrations/destructive/public API break) | OmX `$ralplan --deliberate` | RALPLAN deliberate mode adds pre-mortem + expanded test planning and enforces consensus loop structure. citeturn21view1 | `.omx/plans/*` (plan/test-spec), ADR candidate entries | Critic returns `APPROVE` OR max 5 iterations reached citeturn21view1 |
| Clear task, single-owner fix, needs persistence until verified | OmX `$ralph` | Ralph is the persistent execution loop; PRD mode creates structured artefacts and tracked progress ledger. citeturn21view2 | `.omx/state/.../ralph-progress.json`, PR branch, verification evidence | verification gates pass OR explicit blocker/handoff-needed |
| Large task with parallelisable components | OmX `$team` | tmux workers + worktrees + shared state are the designed mechanism; avoids weak in-session fanout. citeturn21view3turn7search13 | per-worker worktrees, `.omx/state/team/...`, merged commits/PR | team phase terminal + verification lane complete citeturn21view3 |
| Existing plan exists; need critique/review only | OmX `$plan --review` or OpenAgent Oracle lane | OmX plan supports Critic review mode; OpenAgent Oracle is read-only consultation with strong analysis capacity. citeturn21view0turn12view2 | annotated plan feedback, ADR suggestions | reviewer verdict delivered + decision recorded |
| Stale edits / line drift risk is high (big refactor, file churn) | OpenAgent lane with `hashline_edit: true` | Hashline edit is explicitly designed to prevent stale-line edits via hash-anchored `LINE#ID`. citeturn15view3 | clean diffs; structured edits; PR | diff applies cleanly + tests pass |
| Need parallel research + implementation + verification while keeping main lane moving | OpenAgent background tasks (task system enabled) OR OmX team workers | OpenAgent supports background agents with concurrency + stale kill; OmX team supports durable tmux workers. citeturn15view1turn13view7turn21view3 | background outputs + main lane commits | task completion events delivered; results incorporated |
| Need to stop runaway loops | OpenAgent `/stop-continuation` (OpenAgent lanes) + OmX stop hook guard and explicit `!stop lane` | OpenAgent ships an explicit stop-all-continuation command; OmX stop behaviour is hook-guarded and can be controlled by operator lifecycle. citeturn13view3turn21view4 | lane state updated; tmux sessions killed; clawhip route emits “stopped” | no active continuation mechanisms; lane marked halted |


## Full lifecycle simulation and human-in-the-loop design

**7. Full lifecycle simulation — eight scenarios (Discord prompt → validated output)**

All scenarios assume:
- a Discord thread represents a lane,
- the gateway maps thread → repo/worktree/session,
- clawhip routes session/tmux events into `#factory-ops`,
- OmX remains primary unless escalation rules trigger OpenAgent. citeturn20view0turn10search4turn21view3turn22view1

### New product build: “Trend Spotter app from YouTube transcripts for dropshippers”

Control prompt (Discord thread):
- `!lane new feature trend-spotter`
- `!omx deep-interview --standard "Build a Trend Spotter app from YouTube transcripts for dropshippers"`

Dispatcher interpretation:
- Requirements are ambiguous; must invoke deep-interview as the first gate. citeturn24view0

OmX invocation:
- `$deep-interview` runs, creates `.omx/context/*` and `.omx/specs/deep-interview-trend-spotter.md`. citeturn24view0

Clarification needed:
- OmX emits `session.blocked`/question events; clawhip routes an @mention into control thread; user replies via `!reply <session_id> "..."`. OmX resumes via persisted mode state. citeturn6view5turn10search4turn24view0

Planning:
- `!omx ralplan --deliberate "<path-to-spec>"` (or direct spec reference in prompt) to force multi-perspective architecture and verification planning. citeturn21view1turn24view0

Execution:
- `!omx team 3:executor "<approved plan summary>"` to parallelise ingestion pipeline, UI skeleton, and test harness in isolated worktrees. citeturn21view3turn7search13

Verification gates:
- Verification lane runs tests/builds; failures emit `session.test-failed` or `session.failed` events; clawhip routes to ops. citeturn10search4turn11search7turn21view4

If review fails:
- The Reviewer lane posts explicit failure evidence; OmX loops back to Coding/Tools and re-runs verification. (This is explicitly the ralph/team verification ethos: do not claim done without evidence.) citeturn21view3turn21view2turn21view0

Final validated result:
- PR created + CI clean + local reproduction steps recorded in PR template; docs/prd/current.md updated to match shipped scope. citeturn21view0turn20view0

### UI refactor: “Redesign pricing/onboarding mobile-first without breaking analytics”

Prompt:
- `!lane new refactor pricing-onboarding`
- `!omx ralplan --deliberate "Mobile-first redesign of pricing + onboarding; preserve analytics invariants in docs/design/ui-rules.md"`

Reasoning:
- High risk (product surface + analytics regressions) → deliberate consensus planning. citeturn21view1turn21view0

Execution:
- OmX team lanes: one executor for UI refactor, one for analytics snapshot/regression tests, one for e2e flows. citeturn21view3  
- Escalate to OpenAgent `visual-engineering` lane only if the UI work is heavily visual and benefits from category+skill combos and agent-browser/playwright usage (OpenAgent supports skills and browser automation integration). citeturn15view2turn16view0turn12view2

Failure handling:
- If tests fail, loop to Coding/Tools; if plan assumptions break, loop to Architect lane and update ADR/PRD. citeturn21view1turn24view0

### Bug fixing: “Fix flaky auth callback and failing CI”

Prompt:
- `!lane new bug auth-callback-flake`
- `!omx team "fix flaky auth callback + failing CI"`

Dispatcher:
- This is likely parallelisable (repro + fix + CI triage) and benefits from durable workers. citeturn21view3turn7search13

Workflow:
- Team lane A: reproduce locally + isolate failure.
- Team lane B: CI logs analysis + minimal patch candidate.
- Team lane C: add regression test + run targeted suite.  

Stop conditions:
- CI green + local reproduction proves fix; emit `session.finished` and record lesson in memory/topics/lessons.md. citeturn10search4turn9view1turn20view0

### Requirement extension mid-flight: “Add AI-assisted evidence ranking after build started”

Prompt:
- `!omx deep-interview --quick "Add AI-assisted evidence ranking to existing Trend Spotter MVP"`

Policy:
- Mid-flight scope change triggers deep-interview quick mode to capture intent, non-goals, and decision boundaries, then re-plan. citeturn24view0turn21view2

Artefacts:
- Update docs/prd/current.md + ADR if architecture changes; update `.omx/specs/*` for new requirement. citeturn24view0turn21view1

### Product experimentation: onboarding A/B flow prototype

Prompt:
- `!lane new experiment onboarding-ab-01`
- `!omx ralplan "Define experiment hypothesis + instrumentation + rollback; scope limited to prototype"`

Rule:
- Experiments require explicit rollback and instrumentation in plan (embed in PRD/ADR). This is aligned with consensus planning’s emphasis on testable criteria and verification steps. citeturn21view0turn21view1

### CEO/strategy input: monetisation pivot

Prompt:
- `!lane new strategy monetisation-pivot`
- `!omx deep-interview --standard "Given docs/ceo/strategy.md, propose monetisation pivot and translate into PRD changes"`

Flow:
- deep-interview first to lock decision boundaries and success criteria; then ralplan to generate an approved roadmap and implementation phases. citeturn24view0turn21view1turn20view0

### Article/content/SEO work: landing page from positioning request

Prompt:
- `!lane new seo landing-v1`
- `!omx plan --direct "Create landing page; constraints in docs/ceo/strategy.md and docs/design/ui-rules.md"`

Escalation:
- If heavy copywriting + layout iteration is needed, OpenAgent “writing” category lane can run in parallel while OmX owns repo integration and verification. citeturn13view7turn22view1turn21view3

### Design system change: major colour/layout responsiveness redesign

Prompt:
- `!lane new refactor design-system-v2`
- `!omx ralplan --deliberate "Design system v2; update docs/design/ui-rules.md; enforce accessibility"`

Execution:
- OmX team for parallel component migration; OpenAgent lane with tmux + background agents for wide codebase audits using LSP/AST-grep hooks, if used via OpenCode. citeturn21view3turn16view3turn14view4

**8. Human-in-the-loop design — question emission, persistence, and resumption**

OmX is already designed to ask one question per round during interviews/planning, and it defines `ask-user-question` as a discrete lifecycle event. The correct architecture is therefore:
- questions are emitted as **blocked** session events (not as ongoing chatter),
- delivered to Discord via clawhip routing,
- answered via explicit `!reply <session_id> "<answer>"`,
- persisted in memory/daily and, when scope-affecting, in PRD/ADR. citeturn6view5turn10search4turn24view0turn9view1

Use OmX deep-interview’s documented readiness gates as the structured clarification schema: Non-goals and Decision Boundaries must be explicit before execution handoff. Capture those fields in PRD and in the deep-interview spec artefact under `.omx/specs/`. citeturn24view0turn21view0

Blocked-waiting-on-user status pattern:
- `session.blocked` emitted with `summary` describing the question.
- clawhip routes to `#factory-control` thread with an @mention.
- gateway marks lane state = `blocked_waiting_user` and writes an entry to `memory/daily/YYYY-MM-DD.md`. citeturn10search4turn9view1turn20view0


## Determinism, drift prevention, lifecycle support, reusable blueprint, risks, golden path

**9. Memory architecture — consolidated model across all three plugins**

Memory must be split explicitly by function:

1) **Git-tracked durable knowledge**: PRD, ADR, design rules, strategy, validation checklists.
- Purpose: stable constraints and decisions.
- Update policy: only via explicit human/Architect approval.
- Retrieval constraint: always read PRD + relevant ADRs before major changes. citeturn21view1turn20view0  

2) **Filesystem-offloaded operational memory (repo-tracked)**: `MEMORY.md` pointer + `memory/**` shards.
- Purpose: cheap retrieval of the right shard; avoid monolithic memory.
- Update policy: leaf shards append detail; `MEMORY.md` changes only when beliefs/pointers change.
- Tooling: scaffold via `clawhip memory init/status`. citeturn9view1turn9view2turn9view3  

3) **OmX runtime memory/state (gitignored)**: `.omx/` (plans, interviews/specs, logs, mode state).
- Purpose: resumability and workflow artefact generation (`.omx/specs`, `.omx/interviews`, `.omx/state/...` for Ralph/team).
- Update policy: generated by OmX workflows; treated as derived execution artefacts.
- Retrieval constraint: load only the spec/plan artefacts relevant to the lane; do not dump `.omx/` wholesale into active contexts. citeturn24view0turn21view2turn21view3turn7search0  

4) **OpenAgent runtime state (gitignored)**: `.sisyphus/tasks` and session artefacts.
- Purpose: cross-session task tracking and background work coordination.
- Update policy: generated by OpenAgent; only summaries get promoted to Git-tracked docs/memory shards. citeturn15view1turn16view2  

Conflict resolution rules:
- PRD/ADR override memory shards.
- `MEMORY.md` pointers override “chat recollection”.
- `.omx/specs/deep-interview-*` override ad-hoc interpretations once created (deep-interview explicitly defines itself as requirements source of truth for handoffs). citeturn24view0turn9view1turn20view0  

**10. Determinism and hallucination control — hook strategy, stop conditions, verification gates**

Deterministic routing:
- Gateway routing is explicit command-based and must not rely on LLM classification.
- OmX internal routing is explicit `$skill`-based; do not rely on keyword detection when determinism matters (use explicit invocations). citeturn7search9turn21view3  

Deterministic stop conditions:
- OmX: use stop-hook continuation guard semantics and mode state to prevent re-block loops. citeturn21view4  
- OpenAgent: `/stop-continuation` halts ralph/todo/boulder mechanisms for the session. citeturn13view3turn16view1  

Stale edit prevention:
- Prefer OpenAgent hashline edit on large refactors; it is explicitly designed to prevent stale-line edits. citeturn15view3turn16view1  
- In OmX, treat non-Bash tool hook interception as runtime-only; enforce “read-before-write” and “verify-before-done” through workflow discipline rather than assuming hook enforcement exists for all tools. citeturn21view4turn21view0  

Verification gates:
- `ralplan` requires testable acceptance and explicit verification steps; deliberate mode enforces expanded testing and pre-mortem. citeturn21view1turn21view0  
- Team mode must keep a verification lane active until workers are terminal and evidence exists. citeturn21view3  
- Ralph PRD mode tracks story acceptance criteria and progress ledger; do not exit without passing criteria or emitting `handoff-needed`. citeturn21view2turn10search4  

Anti-drift design:
- Use deep-interview gating whenever Non-goals/Decision Boundaries are unclear; deep-interview explicitly disallows execution without those gates. citeturn24view0  
- Keep ops noise out of agent context by centralising routing in clawhip (contract doctrine). citeturn10search4turn20view0  
- Enable OpenAgent dynamic context pruning only with protected-tool lists and turn protection to avoid losing critical workflow context. citeturn15view3turn13view2  

**11. Product lifecycle support — stage mapping**

A minimal lifecycle mapping (primary plugin + primary artefact):
- Ideation/discovery: OmX deep-interview → `.omx/specs/*` + `docs/product/vision.md`. citeturn24view0turn20view0  
- Requirement shaping: OmX deep-interview + ralplan → `docs/prd/current.md` + `docs/adr/*`. citeturn24view0turn21view1  
- Build/refactor: OmX team/ralph → PR + verification evidence. citeturn21view3turn21view2  
- QA/verification: OmX verification lanes; OpenAgent task/background lanes optional for parallel diagnostics. citeturn21view3turn15view1turn16view2  
- Release/post-release: clawhip routes CI summaries and operational events; memory/daily captures incidents and lessons. citeturn10search0turn9view1turn20view0  

**12. Reusable project factory blueprint — bootstrap sequence**

Bootstrap (deterministic):
1) Create repo from template (docs/, memory/, .github/, .codex/rules/, .opencode/).
2) Run `clawhip memory init` to scaffold memory layout.
3) Run `omx setup` to install OmX-managed artefacts (`AGENTS.md` bootstrap if absent, `.codex/config.toml`, `.codex/hooks.json`).
4) Install clawhip OmX native hook bridge into `.omx/hooks/` and validate (`omx hooks validate/test`).
5) Start clawhip daemon; confirm routing on `session.*` events.
6) Add `.opencode/oh-my-openagent.jsonc` for projects that will use OpenAgent escalation lanes. citeturn9view1turn21view4turn11search0turn10search0turn22view1  

This sequence is fully aligned to shipped tooling: clawhip provides the memory scaffolder; OmX owns Codex hook enablement and hook registration; clawhip ships the OmX bridge assets; OpenAgent supports `.opencode/oh-my-openagent.jsonc` project overrides. citeturn9view1turn21view4turn11search0turn22view1  

**13. Risks and failure modes — symptoms and mitigations**

| Risk | Symptom | Root cause | Mitigation | Monitoring signal | Recovery action |
|---|---|---|---|---|---|
| Ownership confusion (OmX vs clawhip) | duplicate/misaligned Discord notifications | OmX sends direct notifications in parallel with clawhip routing | enforce clawhip single-router doctrine; only emit session events from OmX | duplicate messages; wrong channels | disable direct OmX notification hooks; route only via clawhip citeturn10search4turn11search7 |
| Context pollution | agents regress or hallucinate due to noise | operational chatter injected into agent context | keep ops in `#factory-ops`; inject only user answers | long prompts; repeated restatements | stop continuation; re-anchor on PRD + spec; re-plan citeturn20view0turn24view0 |
| Runaway loops | never-ending continuation | multiple continuation mechanisms active | one-loop-at-a-time; `/stop-continuation` + OmX stop hook guard | repeated session.started without progress | kill lane tmux; persist handoff; restart with explicit plan citeturn13view3turn21view4 |
| Stale edits | patches apply incorrectly or to wrong lines | file churn + naive edit mechanism | use hashline edit in OpenAgent lanes | repeated edit failures; broken diffs | revert and re-run with hashline edit; smaller patch granularity citeturn15view3turn16view1 |
| Weak auditability | “done” claims without proof | missing verification gates | PR template + validation checklist gates | CI failures after “done” | enforce evidence-only completion; rerun verification lanes citeturn21view1turn21view3turn20view0 |
| Stale memory | MEMORY.md becomes unreadable | monolithic memory accumulation | filesystem-offloaded memory rule; shard + archive | large MEMORY.md; slow retrieval | split shards; rewrite pointer layer; archive cold history citeturn9view1turn9view2 |

**14. Final recommended golden path — minimal viable, production-grade**

Golden path architecture:
- Discord control threads for each lane.
- Deterministic gateway commands.
- OmX as the default workflow engine (deep-interview → ralplan → team/ralph).
- clawhip as the only router for operational events (`session.*`, `tmux.*`), using a dedicated bot and separate ops channel.
- OpenAgent invoked only for specialist reviewer lanes and high-risk refactors requiring hashline edit or heavy background parallelism. citeturn20view0turn21view3turn10search4turn15view3turn10search0  

Golden path folder tree (compressed):
- `docs/` as source-of-truth.
- `memory/` as offloaded memory (pointer + shards).
- `.codex/` managed by OmX + rules.
- `.opencode/` for OpenAgent when used.
- `.omx/` and `.sisyphus/` gitignored runtime state. citeturn9view1turn21view4turn22view1turn15view1  

Golden path workflow selection:
- Ambiguous → deep-interview (never code inside it). citeturn24view0  
- High-risk → ralplan deliberate. citeturn21view1  
- Parallel build → team. citeturn21view3  
- Persistent single-owner verification → ralph. citeturn21view2  
- Stale-edit risk/high churn → OpenAgent hashline lane, then merge back through PR. citeturn15view3turn16view1  

Golden path memory model:
- `docs/**` overrides everything.
- `MEMORY.md` is pointer-only; detail in shards.
- `.omx/specs/*` is the requirements handoff truth after deep-interview.
- `.sisyphus/tasks` remains runtime-only unless summarised into durable docs. citeturn9view1turn24view0turn16view2  

Golden path success checklist:
- Requirements artefact exists (`docs/prd/current.md` + `.omx/specs/deep-interview-*` when applicable). citeturn24view0  
- Plan approved (Critic `APPROVE` or explicit user approval). citeturn21view1  
- Work isolated in worktrees/branches (team/worktree discipline). citeturn21view3  
- Verification evidence exists (tests/build/typecheck and reproducible commands). citeturn21view0turn21view3  
- Routing centralised through clawhip (no direct notification duplication). citeturn10search4turn11search7  
- Memory updated correctly (leaf shard updated; pointer updated only when beliefs/pointers changed). citeturn9view1turn9view3