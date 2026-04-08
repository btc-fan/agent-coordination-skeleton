#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
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
    branch = f"{args.lane_type}/{lane_id}"
    repo_path = Path(project["repo_path"])
    worktree_path = repo_path / "worktrees" / branch.replace("/", "-")
    thread_id = args.thread_id or f"local-{lane_id}"

    if args.create_worktree:
        worktree_path.parent.mkdir(parents=True, exist_ok=True)
        subprocess.run(["git", "-C", str(repo_path), "worktree", "add", str(worktree_path), "-b", branch], check=True)

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
        "created_at": now_iso(),
        "updated_at": now_iso(),
    })
    save_json(lane_file(lane_id), data)

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
    append_log({"timestamp": now_iso(), "command_type": "lane.new", "project_id": args.project_id, "lane_id": lane_id, "thread_id": thread_id, "action": "lane_created", "outcome": "ok"})
    print(lane_file(lane_id))
    return 0


def tmux_has_session(name: str) -> bool:
    return subprocess.run(["tmux", "has-session", "-t", name], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL).returncode == 0


def cmd_omx_deep_interview(args: argparse.Namespace) -> int:
    lane = require_lane(args.lane_id)
    lane_path = lane_file(args.lane_id)
    session_name = lane["session_name"] or lane["lane_id"]
    workdir = Path(lane["worktree_path"])
    workdir.mkdir(parents=True, exist_ok=True)
    log_dir = ROOT / ".omx" / "dispatcher-runs"
    log_dir.mkdir(parents=True, exist_ok=True)
    run_log = log_dir / f"{session_name}.log"

    prompt = f'$deep-interview {shlex.quote(args.prompt)}'
    cmd = f'cd {shlex.quote(str(workdir))} && omx exec --dangerously-bypass-approvals-and-sandbox {shlex.quote(prompt)} >> {shlex.quote(str(run_log))} 2>&1'

    if tmux_has_session(session_name):
        raise SystemExit(f"tmux session already exists: {session_name}")

    subprocess.run(["tmux", "new-session", "-d", "-s", session_name, cmd], check=True)

    lane["state"] = "planning"
    lane["continuation_owner"] = "omx-exec"
    lane["updated_at"] = now_iso()
    save_json(lane_path, lane)
    append_log({
        "timestamp": now_iso(),
        "raw_command": f'!omx deep-interview "{args.prompt}"',
        "command_type": "omx.deep-interview",
        "project_id": lane["project_id"],
        "lane_id": lane["lane_id"],
        "thread_id": lane["thread_id"],
        "state_before": "planning",
        "state_after": lane["state"],
        "action": "start_omx_deep_interview",
        "tmux_session": session_name,
        "log_path": str(run_log),
        "outcome": "ok",
    })
    print(json.dumps({"session_name": session_name, "log_path": str(run_log)}, indent=2))
    return 0


def cmd_lane_status(args: argparse.Namespace) -> int:
    lane = require_lane(args.lane_id)
    lane["tmux_alive"] = tmux_has_session(lane["session_name"])
    print(json.dumps(lane, indent=2))
    return 0


def cmd_lane_stop(args: argparse.Namespace) -> int:
    lane = require_lane(args.lane_id)
    session_name = lane["session_name"]
    if tmux_has_session(session_name):
        subprocess.run(["tmux", "kill-session", "-t", session_name], check=True)
    lane["state"] = "stopped"
    lane["continuation_owner"] = ""
    lane["updated_at"] = now_iso()
    save_json(lane_file(args.lane_id), lane)
    append_log({"timestamp": now_iso(), "command_type": "lane.stop", "project_id": lane["project_id"], "lane_id": lane["lane_id"], "thread_id": lane["thread_id"], "action": "stop_lane", "outcome": "ok"})
    print(f"stopped {args.lane_id}")
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
    s.add_argument("lane_type", choices=["feature", "bug", "refactor", "experiment", "seo", "strategy"])
    s.add_argument("slug")
    s.add_argument("--thread-id")
    s.add_argument("--tool", default="omx")
    s.add_argument("--create-worktree", action="store_true")
    s.set_defaults(func=cmd_lane_new)

    s = sub.add_parser("omx-deep-interview")
    s.add_argument("lane_id")
    s.add_argument("prompt")
    s.set_defaults(func=cmd_omx_deep_interview)

    s = sub.add_parser("lane-status")
    s.add_argument("lane_id")
    s.set_defaults(func=cmd_lane_status)

    s = sub.add_parser("lane-stop")
    s.add_argument("lane_id")
    s.set_defaults(func=cmd_lane_stop)

    return p


if __name__ == "__main__":
    parser = build_parser()
    args = parser.parse_args()
    sys.exit(args.func(args))
