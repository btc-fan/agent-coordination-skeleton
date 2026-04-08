#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import shlex
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[3]
FACTORY = ROOT / "factory"
STATE = FACTORY / "state"
PROJECTS = STATE / "projects"
LANES = STATE / "lanes"
THREADS = STATE / "threads"
TEMPLATES = FACTORY / "templates"
LOG_FILE = FACTORY / "logs" / "dispatcher.jsonl"
TASK_TEMPLATE_DIR = ROOT / "docs" / "tasks" / "templates"
TASKS_DIR = ROOT / "docs" / "tasks" / "active"
RUN_LOG_DIR = ROOT / ".omx" / "dispatcher-runs"

LANE_TYPES = ["feature", "bug", "refactor", "experiment", "seo", "strategy"]
VALID_STATES = {
    "planning",
    "executing",
    "blocked_waiting_user",
    "paused",
    "replanning",
    "verifying",
    "review_rejected",
    "handoff_needed",
    "done",
    "stopped",
    "failed",
}


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text())


def save_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2) + "\n")


def append_log(entry: dict[str, Any]) -> None:
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    with LOG_FILE.open("a") as f:
        f.write(json.dumps(entry) + "\n")


def slugify(value: str) -> str:
    value = value.strip().lower()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    value = re.sub(r"-+", "-", value).strip("-")
    if not value:
        raise SystemExit("empty slug")
    return value


def project_file(project_id: str) -> Path:
    return PROJECTS / f"{project_id}.json"


def lane_file(lane_id: str) -> Path:
    return LANES / f"{lane_id}.json"


def thread_file(thread_id: str) -> Path:
    return THREADS / f"{thread_id}.json"


def require_project(project_id: str) -> dict[str, Any]:
    path = project_file(project_id)
    if not path.exists():
        raise SystemExit(f"project not found: {project_id}")
    return load_json(path)


def require_lane(lane_id: str) -> dict[str, Any]:
    path = lane_file(lane_id)
    if not path.exists():
        raise SystemExit(f"lane not found: {lane_id}")
    return load_json(path)


def require_thread(thread_id: str) -> dict[str, Any]:
    path = thread_file(thread_id)
    if not path.exists():
        raise SystemExit(f"thread not found: {thread_id}")
    return load_json(path)


def tmux_has_session(name: str) -> bool:
    return subprocess.run(["tmux", "has-session", "-t", name], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL).returncode == 0


def tmux_pane_output(session_name: str, lines: int = 80) -> str:
    if not tmux_has_session(session_name):
        return ""
    pane_id = subprocess.check_output(["tmux", "list-panes", "-t", session_name, "-F", "#{pane_id}"]).decode().splitlines()[0]
    out = subprocess.check_output(["tmux", "capture-pane", "-p", "-t", pane_id]).decode()
    return "\n".join(out.splitlines()[-lines:])


def task_doc_path(lane_type: str, lane_id: str) -> Path:
    return TASKS_DIR / lane_type / f"{lane_id}.md"


def instantiate_task_doc(lane_type: str, lane_id: str) -> Path:
    template_name = "design-change.md" if lane_type == "refactor" else f"{lane_type}.md"
    template = TASK_TEMPLATE_DIR / template_name
    if not template.exists():
        raise SystemExit(f"task template missing: {template_name}")
    target = task_doc_path(lane_type, lane_id)
    target.parent.mkdir(parents=True, exist_ok=True)
    if not target.exists():
        content = template.read_text()
        content = content.replace("- Lane:\n", f"- Lane: {lane_id}\n")
        target.write_text(content)
    return target


def update_task_doc_section(path: Path, heading: str, text: str) -> None:
    if not path.exists():
        return
    content = path.read_text()
    marker = f"\n## {heading}\n"
    if marker in content:
        head, tail = content.split(marker, 1)
        next_heading = tail.find("\n## ")
        rest = "" if next_heading == -1 else tail[next_heading:]
        new = head + marker + text.strip() + "\n" + rest.lstrip("\n")
        path.write_text(new)
    else:
        content = content.rstrip() + f"\n\n## {heading}\n{text.strip()}\n"
        path.write_text(content)


def lane_state_change(lane: dict[str, Any], *, new_state: str | None = None, continuation_owner: str | None = None, **fields: Any) -> dict[str, Any]:
    if new_state is not None:
        if new_state not in VALID_STATES:
            raise SystemExit(f"invalid state: {new_state}")
        lane["state"] = new_state
    if continuation_owner is not None:
        lane["continuation_owner"] = continuation_owner
    lane.update(fields)
    lane["updated_at"] = now_iso()
    return lane


def build_omx_exec_command(workdir: Path, mode_prompt: str, run_log: Path, dangerous: bool = False) -> str:
    flags = ["omx", "exec"]
    if dangerous:
        flags.append("--dangerously-bypass-approvals-and-sandbox")
    cmd = " ".join(shlex.quote(x) for x in flags)
    return f"cd {shlex.quote(str(workdir))} && {cmd} {shlex.quote(mode_prompt)} >> {shlex.quote(str(run_log))} 2>&1"


DEFAULT_TMUX_KEYWORDS = "error,failed,blocked,PR created,complete"
DEFAULT_TMUX_STALE_MINUTES = "20"


def start_tmux_command(session_name: str, cmd: str, cwd: Path) -> None:
    import time
    if tmux_has_session(session_name):
        raise SystemExit(f"tmux session already exists: {session_name}")
    subprocess.Popen([
        "clawhip", "tmux", "new",
        "--session", session_name,
        "--cwd", str(cwd),
        "--keywords", DEFAULT_TMUX_KEYWORDS,
        "--stale-minutes", DEFAULT_TMUX_STALE_MINUTES,
        "--format", "alert",
        "--",
        "bash", "-lc", cmd,
    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    for _ in range(20):
        if tmux_has_session(session_name):
            return
        time.sleep(0.25)
    raise SystemExit(f"tmux session did not appear after launch: {session_name}")


def cmd_proj_init(args: argparse.Namespace) -> int:
    tmpl = load_json(TEMPLATES / "project.json")
    project_id = slugify(args.name)
    data = tmpl
    data["project_id"] = project_id
    data["name"] = args.name
    data["repo_path"] = str(Path(args.repo_path).resolve())
    data["default_branch"] = args.default_branch
    data["discord"]["server_id"] = args.server_id or ""
    data["discord"]["control_channel_id"] = args.control_channel_id or ""
    data["discord"]["decisions_channel_id"] = args.decisions_channel_id or ""
    data["discord"]["ops_channel_id"] = args.ops_channel_id or ""
    data["openagent_enabled"] = not args.disable_openagent
    data["created_at"] = now_iso()
    data["updated_at"] = data["created_at"]
    save_json(project_file(project_id), data)
    append_log({"timestamp": now_iso(), "command_type": "proj.init", "project_id": project_id, "action": "project_created", "outcome": "ok"})
    print(project_file(project_id))
    return 0


def cmd_lane_new(args: argparse.Namespace) -> int:
    project = require_project(args.project_id)
    tmpl = load_json(TEMPLATES / "lane.json")
    lane_id = slugify(args.slug)
    lane_path = lane_file(lane_id)
    if lane_path.exists():
        raise SystemExit(f"lane already exists: {lane_id}")
    branch = f"{args.lane_type}/{lane_id}"
    repo_path = Path(project["repo_path"])
    worktree_path = repo_path / "worktrees" / branch.replace("/", "-")
    thread_id = args.thread_id or f"local-{lane_id}"

    if args.create_worktree:
        worktree_path.parent.mkdir(parents=True, exist_ok=True)
        subprocess.run(["git", "-C", str(repo_path), "worktree", "add", str(worktree_path), "-b", branch], check=True)
    else:
        worktree_path.mkdir(parents=True, exist_ok=True)

    task_doc = instantiate_task_doc(args.lane_type, lane_id)

    data = tmpl
    data.update({
        "lane_id": lane_id,
        "project_id": args.project_id,
        "lane_type": args.lane_type,
        "thread_id": thread_id,
        "repo_path": str(repo_path),
        "worktree_path": str(worktree_path),
        "branch": branch,
        "tool": args.tool,
        "session_name": lane_id,
        "session_id": "",
        "state": "planning",
        "continuation_owner": "",
        "clarification_status": "open",
        "docs_status": "initialized",
        "task_doc": str(task_doc.relative_to(ROOT)),
        "created_at": now_iso(),
        "updated_at": now_iso(),
    })
    save_json(lane_path, data)

    thread = load_json(TEMPLATES / "thread.json")
    thread.update({
        "thread_id": thread_id,
        "project_id": args.project_id,
        "lane_id": lane_id,
        "control_channel_id": project["discord"].get("control_channel_id", ""),
        "created_at": now_iso(),
        "updated_at": now_iso(),
    })
    save_json(thread_file(thread_id), thread)
    append_log({"timestamp": now_iso(), "command_type": "lane.new", "project_id": args.project_id, "lane_id": lane_id, "thread_id": thread_id, "action": "lane_created", "task_doc": str(task_doc.relative_to(ROOT)), "outcome": "ok"})
    print(lane_path)
    return 0


def cmd_omx_deep_interview(args: argparse.Namespace) -> int:
    lane = require_lane(args.lane_id)
    lane_path = lane_file(args.lane_id)
    session_name = lane["session_name"] or lane["lane_id"]
    workdir = Path(lane["worktree_path"])
    workdir.mkdir(parents=True, exist_ok=True)
    RUN_LOG_DIR.mkdir(parents=True, exist_ok=True)
    run_log = RUN_LOG_DIR / f"{session_name}.log"

    prompt = f'$deep-interview {shlex.quote(args.prompt)}'
    cmd = build_omx_exec_command(workdir, prompt, run_log, dangerous=args.dangerous)
    start_tmux_command(session_name, cmd, workdir)

    before = lane["state"]
    lane = lane_state_change(lane, new_state="planning", continuation_owner="omx-exec", clarification_status="open")
    save_json(lane_path, lane)
    append_log({
        "timestamp": now_iso(),
        "raw_command": f'!omx deep-interview "{args.prompt}"',
        "command_type": "omx.deep-interview",
        "project_id": lane["project_id"],
        "lane_id": lane["lane_id"],
        "thread_id": lane["thread_id"],
        "state_before": before,
        "state_after": lane["state"],
        "action": "start_omx_deep_interview",
        "tmux_session": session_name,
        "log_path": str(run_log),
        "dangerous": args.dangerous,
        "outcome": "ok",
    })
    print(json.dumps({"session_name": session_name, "log_path": str(run_log)}, indent=2))
    return 0


def cmd_omx_ralplan(args: argparse.Namespace) -> int:
    lane = require_lane(args.lane_id)
    lane_path = lane_file(args.lane_id)
    base_session_name = lane["lane_id"]
    session_name = f"{base_session_name}-ralplan"
    workdir = Path(lane["worktree_path"])
    workdir.mkdir(parents=True, exist_ok=True)
    RUN_LOG_DIR.mkdir(parents=True, exist_ok=True)
    run_log = RUN_LOG_DIR / f"{session_name}.log"

    suffix = " --deliberate" if args.deliberate else ""
    prompt = f'$ralplan{suffix} {shlex.quote(args.prompt)}'
    cmd = build_omx_exec_command(workdir, prompt, run_log, dangerous=args.dangerous)
    start_tmux_command(session_name, cmd, workdir)

    before = lane["state"]
    lane["session_name"] = session_name
    lane = lane_state_change(lane, new_state="planning", continuation_owner="omx-exec")
    save_json(lane_path, lane)
    append_log({
        "timestamp": now_iso(),
        "raw_command": f'!omx ralplan "{args.prompt}"',
        "command_type": "omx.ralplan",
        "project_id": lane["project_id"],
        "lane_id": lane["lane_id"],
        "thread_id": lane["thread_id"],
        "state_before": before,
        "state_after": lane["state"],
        "action": "start_omx_ralplan",
        "tmux_session": session_name,
        "log_path": str(run_log),
        "deliberate": args.deliberate,
        "dangerous": args.dangerous,
        "outcome": "ok",
    })
    print(json.dumps({"session_name": session_name, "log_path": str(run_log)}, indent=2))
    return 0


def cmd_omx_ralph(args: argparse.Namespace) -> int:
    lane = require_lane(args.lane_id)
    lane_path = lane_file(args.lane_id)
    base_session_name = lane["lane_id"]
    session_name = f"{base_session_name}-ralph"
    workdir = Path(lane["worktree_path"])
    workdir.mkdir(parents=True, exist_ok=True)
    RUN_LOG_DIR.mkdir(parents=True, exist_ok=True)
    run_log = RUN_LOG_DIR / f"{session_name}.log"

    if args.prd:
        omx_cmd = f'omx ralph --prd {shlex.quote(args.prompt)}'
    else:
        omx_cmd = f'omx ralph {shlex.quote(args.prompt)}'
    if args.no_deslop:
        omx_cmd += ' --no-deslop'
    cmd = f'cd {shlex.quote(str(workdir))} && {omx_cmd} >> {shlex.quote(str(run_log))} 2>&1'
    start_tmux_command(session_name, cmd, workdir)

    before = lane["state"]
    lane["session_name"] = session_name
    lane = lane_state_change(lane, new_state="executing", continuation_owner="omx-ralph")
    save_json(lane_path, lane)
    append_log({
        "timestamp": now_iso(),
        "raw_command": f'!omx ralph "{args.prompt}"',
        "command_type": "omx.ralph",
        "project_id": lane["project_id"],
        "lane_id": lane["lane_id"],
        "thread_id": lane["thread_id"],
        "state_before": before,
        "state_after": lane["state"],
        "action": "start_omx_ralph",
        "tmux_session": session_name,
        "log_path": str(run_log),
        "prd": args.prd,
        "no_deslop": args.no_deslop,
        "outcome": "ok",
    })
    print(json.dumps({"session_name": session_name, "log_path": str(run_log)}, indent=2))
    return 0


def cmd_omx_team(args: argparse.Namespace) -> int:
    lane = require_lane(args.lane_id)
    lane_path = lane_file(args.lane_id)
    base_session_name = lane["lane_id"]
    session_name = f"{base_session_name}-team"
    workdir = Path(lane["worktree_path"])
    workdir.mkdir(parents=True, exist_ok=True)
    RUN_LOG_DIR.mkdir(parents=True, exist_ok=True)
    run_log = RUN_LOG_DIR / f"{session_name}.log"

    omx_cmd = f'omx team {shlex.quote(args.team_shape)} {shlex.quote(args.prompt)}'
    cmd = f'cd {shlex.quote(str(workdir))} && {omx_cmd} >> {shlex.quote(str(run_log))} 2>&1'
    start_tmux_command(session_name, cmd, workdir)

    before = lane["state"]
    lane["session_name"] = session_name
    lane = lane_state_change(lane, new_state="executing", continuation_owner="omx-team")
    save_json(lane_path, lane)
    append_log({
        "timestamp": now_iso(),
        "raw_command": f'!omx team {args.team_shape} "{args.prompt}"',
        "command_type": "omx.team",
        "project_id": lane["project_id"],
        "lane_id": lane["lane_id"],
        "thread_id": lane["thread_id"],
        "state_before": before,
        "state_after": lane["state"],
        "action": "start_omx_team",
        "tmux_session": session_name,
        "log_path": str(run_log),
        "team_shape": args.team_shape,
        "outcome": "ok",
    })
    print(json.dumps({"session_name": session_name, "log_path": str(run_log)}, indent=2))
    return 0


def cmd_lane_status(args: argparse.Namespace) -> int:
    lane = require_lane(args.lane_id)
    lane["tmux_alive"] = tmux_has_session(lane["session_name"])
    print(json.dumps(lane, indent=2))
    return 0


def cmd_lane_pause(args: argparse.Namespace) -> int:
    lane = require_lane(args.lane_id)
    before = lane["state"]
    lane = lane_state_change(lane, new_state="paused")
    task_doc = ROOT / lane.get("task_doc", "") if lane.get("task_doc") else None
    if task_doc:
        update_task_doc_section(task_doc, "Paused State", f"Paused at {now_iso()}\n\nReason: {args.reason}")
    save_json(lane_file(args.lane_id), lane)
    append_log({"timestamp": now_iso(), "command_type": "lane.pause", "project_id": lane["project_id"], "lane_id": lane["lane_id"], "thread_id": lane["thread_id"], "state_before": before, "state_after": lane["state"], "reason": args.reason, "action": "pause_lane", "outcome": "ok"})
    print(f"paused {args.lane_id}")
    return 0


def cmd_lane_resume(args: argparse.Namespace) -> int:
    lane = require_lane(args.lane_id)
    before = lane["state"]
    if before not in {"paused", "blocked_waiting_user", "replanning"}:
        raise SystemExit(f"cannot resume lane from state: {before}")
    lane = lane_state_change(lane, new_state=args.to_state)
    save_json(lane_file(args.lane_id), lane)
    append_log({"timestamp": now_iso(), "command_type": "lane.resume", "project_id": lane["project_id"], "lane_id": lane["lane_id"], "thread_id": lane["thread_id"], "state_before": before, "state_after": lane["state"], "action": "resume_lane", "outcome": "ok"})
    print(f"resumed {args.lane_id} -> {lane['state']}")
    return 0


def cmd_lane_change(args: argparse.Namespace) -> int:
    lane = require_lane(args.lane_id)
    before = lane["state"]
    lane = lane_state_change(lane, new_state="replanning", clarification_status="open")
    task_doc = ROOT / lane.get("task_doc", "") if lane.get("task_doc") else None
    if task_doc:
        update_task_doc_section(task_doc, "Change Request", f"Updated at {now_iso()}\n\n{args.requirement_delta}")
    save_json(lane_file(args.lane_id), lane)
    append_log({"timestamp": now_iso(), "command_type": "lane.change", "project_id": lane["project_id"], "lane_id": lane["lane_id"], "thread_id": lane["thread_id"], "state_before": before, "state_after": lane["state"], "requirement_delta": args.requirement_delta, "action": "change_lane", "outcome": "ok"})
    print(f"changed {args.lane_id}")
    return 0


def cmd_lane_done(args: argparse.Namespace) -> int:
    lane = require_lane(args.lane_id)
    before = lane["state"]
    lane = lane_state_change(lane, dod_status="updated")
    task_doc = ROOT / lane.get("task_doc", "") if lane.get("task_doc") else None
    if task_doc:
        update_task_doc_section(task_doc, "Definition of Done Override", f"Updated at {now_iso()}\n\n{args.new_done_rule}")
    if args.force_replanning:
        lane["state"] = "replanning"
    save_json(lane_file(args.lane_id), lane)
    append_log({"timestamp": now_iso(), "command_type": "lane.done", "project_id": lane["project_id"], "lane_id": lane["lane_id"], "thread_id": lane["thread_id"], "state_before": before, "state_after": lane["state"], "new_done_rule": args.new_done_rule, "force_replanning": args.force_replanning, "action": "update_done_rule", "outcome": "ok"})
    print(f"updated done rule for {args.lane_id}")
    return 0


def cmd_lane_reply(args: argparse.Namespace) -> int:
    lane = require_lane(args.lane_id)
    session_name = lane["session_name"]
    if not tmux_has_session(session_name):
        raise SystemExit(f"tmux session not found: {session_name}")
    subprocess.run(["tmux", "send-keys", "-t", session_name, args.answer, "C-m"], check=True)
    before = lane["state"]
    lane = lane_state_change(lane, new_state=args.to_state, clarification_status="clear")
    save_json(lane_file(args.lane_id), lane)
    append_log({"timestamp": now_iso(), "command_type": "lane.reply", "project_id": lane["project_id"], "lane_id": lane["lane_id"], "thread_id": lane["thread_id"], "state_before": before, "state_after": lane["state"], "action": "inject_reply", "outcome": "ok"})
    print(f"replied to {args.lane_id}")
    return 0


def cmd_lane_stop(args: argparse.Namespace) -> int:
    lane = require_lane(args.lane_id)
    session_name = lane["session_name"]
    if tmux_has_session(session_name):
        subprocess.run(["tmux", "kill-session", "-t", session_name], check=True)
    before = lane["state"]
    lane = lane_state_change(lane, new_state="stopped", continuation_owner="")
    save_json(lane_file(args.lane_id), lane)
    append_log({"timestamp": now_iso(), "command_type": "lane.stop", "project_id": lane["project_id"], "lane_id": lane["lane_id"], "thread_id": lane["thread_id"], "state_before": before, "state_after": lane["state"], "action": "stop_lane", "outcome": "ok"})
    print(f"stopped {args.lane_id}")
    return 0


def cmd_lane_tail(args: argparse.Namespace) -> int:
    lane = require_lane(args.lane_id)
    print(tmux_pane_output(lane["session_name"], lines=args.lines))
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Deterministic local factory dispatcher MVP")
    sub = p.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("proj-init")
    s.add_argument("name")
    s.add_argument("repo_path")
    s.add_argument("--default-branch", default="main")
    s.add_argument("--server-id")
    s.add_argument("--control-channel-id")
    s.add_argument("--decisions-channel-id")
    s.add_argument("--ops-channel-id")
    s.add_argument("--disable-openagent", action="store_true")
    s.set_defaults(func=cmd_proj_init)

    s = sub.add_parser("lane-new")
    s.add_argument("project_id")
    s.add_argument("lane_type", choices=LANE_TYPES)
    s.add_argument("slug")
    s.add_argument("--thread-id")
    s.add_argument("--tool", default="omx")
    s.add_argument("--create-worktree", action="store_true")
    s.set_defaults(func=cmd_lane_new)

    s = sub.add_parser("omx-deep-interview")
    s.add_argument("lane_id")
    s.add_argument("prompt")
    s.add_argument("--dangerous", action="store_true")
    s.set_defaults(func=cmd_omx_deep_interview)

    s = sub.add_parser("omx-ralplan")
    s.add_argument("lane_id")
    s.add_argument("prompt")
    s.add_argument("--deliberate", action="store_true")
    s.add_argument("--dangerous", action="store_true")
    s.set_defaults(func=cmd_omx_ralplan)

    s = sub.add_parser("omx-ralph")
    s.add_argument("lane_id")
    s.add_argument("prompt")
    s.add_argument("--prd", action="store_true")
    s.add_argument("--no-deslop", action="store_true")
    s.set_defaults(func=cmd_omx_ralph)

    s = sub.add_parser("omx-team")
    s.add_argument("lane_id")
    s.add_argument("team_shape", help='Example: 3:executor')
    s.add_argument("prompt")
    s.set_defaults(func=cmd_omx_team)

    s = sub.add_parser("lane-status")
    s.add_argument("lane_id")
    s.set_defaults(func=cmd_lane_status)

    s = sub.add_parser("lane-pause")
    s.add_argument("lane_id")
    s.add_argument("reason")
    s.set_defaults(func=cmd_lane_pause)

    s = sub.add_parser("lane-resume")
    s.add_argument("lane_id")
    s.add_argument("--to-state", default="executing", choices=sorted(VALID_STATES))
    s.set_defaults(func=cmd_lane_resume)

    s = sub.add_parser("lane-change")
    s.add_argument("lane_id")
    s.add_argument("requirement_delta")
    s.set_defaults(func=cmd_lane_change)

    s = sub.add_parser("lane-done")
    s.add_argument("lane_id")
    s.add_argument("new_done_rule")
    s.add_argument("--force-replanning", action="store_true")
    s.set_defaults(func=cmd_lane_done)

    s = sub.add_parser("lane-reply")
    s.add_argument("lane_id")
    s.add_argument("answer")
    s.add_argument("--to-state", default="planning", choices=sorted(VALID_STATES))
    s.set_defaults(func=cmd_lane_reply)

    s = sub.add_parser("lane-stop")
    s.add_argument("lane_id")
    s.set_defaults(func=cmd_lane_stop)

    s = sub.add_parser("lane-tail")
    s.add_argument("lane_id")
    s.add_argument("--lines", type=int, default=80)
    s.set_defaults(func=cmd_lane_tail)

    return p


if __name__ == "__main__":
    parser = build_parser()
    args = parser.parse_args()
    sys.exit(args.func(args))
