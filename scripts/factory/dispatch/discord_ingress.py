#!/usr/bin/env python3
from __future__ import annotations

import asyncio
import os
import re
import shlex
import subprocess
from pathlib import Path

import discord

ROOT = Path(__file__).resolve().parents[3]
DISPATCHER = ROOT / "scripts" / "factory" / "dispatch" / "factory.py"
ALLOWED_CHANNEL_ID = int(os.environ["SKELETON_DISCORD_CHANNEL_ID"])
BOT_TOKEN = os.environ["DISCORD_BOT_TOKEN"]
PYTHON = str(ROOT / ".venv" / "bin" / "python")

HELP = """Factory Skeleton Bot — commands

Project/lane:
- !proj init <name> <repo-path>
- !lane new <type> <slug>
- !lane status <lane>
- !pause <lane> <reason>
- !resume <lane>
- !stop <lane>
- !change <lane> <delta>
- !done <lane> <rule>
- !reply <lane> <answer>

OmX:
- !omx deep-interview <lane> | <prompt>
- !omx ralplan <lane> | <prompt>
- !omx ralph <lane> | <prompt>
- !omx team <lane> | <team-shape> | <prompt>
"""


def run_dispatch(args: list[str]) -> tuple[int, str]:
    proc = subprocess.run([PYTHON, str(DISPATCHER), *args], cwd=str(ROOT), capture_output=True, text=True)
    out = (proc.stdout + ("\n" + proc.stderr if proc.stderr else "")).strip()
    return proc.returncode, out[:3500]


def parse_command(text: str) -> list[str] | None:
    t = text.strip()
    if t == "!help":
        return ["__help__"]
    if m := re.match(r"^!lane status\s+(\S+)$", t):
        return ["lane-status", m.group(1)]
    if m := re.match(r"^!pause\s+(\S+)\s+(.+)$", t, re.S):
        return ["lane-pause", m.group(1), m.group(2)]
    if m := re.match(r"^!resume\s+(\S+)$", t):
        return ["lane-resume", m.group(1)]
    if m := re.match(r"^!stop\s+(\S+)$", t):
        return ["lane-stop", m.group(1)]
    if m := re.match(r"^!change\s+(\S+)\s+(.+)$", t, re.S):
        return ["lane-change", m.group(1), m.group(2)]
    if m := re.match(r"^!done\s+(\S+)\s+(.+)$", t, re.S):
        return ["lane-done", m.group(1), m.group(2), "--force-replanning"]
    if m := re.match(r"^!reply\s+(\S+)\s+(.+)$", t, re.S):
        return ["lane-reply", m.group(1), m.group(2)]
    if m := re.match(r"^!lane new\s+(\S+)\s+(\S+)$", t):
        lane_type, slug = m.groups()
        return ["lane-new", "agent-coordination-skeleton", lane_type, slug, "--thread-id", str(ALLOWED_CHANNEL_ID)]
    if m := re.match(r"^!omx deep-interview\s+(\S+)\s*\|\s*(.+)$", t, re.S):
        return ["omx-deep-interview", m.group(1), m.group(2), "--dangerous"]
    if m := re.match(r"^!omx ralplan\s+(\S+)\s*\|\s*(.+)$", t, re.S):
        return ["omx-ralplan", m.group(1), m.group(2), "--dangerous"]
    if m := re.match(r"^!omx ralph\s+(\S+)\s*\|\s*(.+)$", t, re.S):
        return ["omx-ralph", m.group(1), m.group(2), "--prd"]
    if m := re.match(r"^!omx team\s+(\S+)\s*\|\s*(\S+)\s*\|\s*(.+)$", t, re.S):
        return ["omx-team", m.group(1), m.group(2), m.group(3)]
    return None


intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
client = discord.Client(intents=intents)


@client.event
async def on_ready():
    print(f"logged in as {client.user}")


@client.event
async def on_message(message: discord.Message):
    if message.author == client.user:
        return
    if message.channel.id != ALLOWED_CHANNEL_ID:
        return
    cmd = parse_command(message.content)
    if not cmd:
        if message.content.strip().startswith("!"):
            await message.reply("Unknown command. Send `!help`.")
        return
    if cmd == ["__help__"]:
        await message.reply(HELP)
        return
    await message.add_reaction("👀")
    code, out = await asyncio.to_thread(run_dispatch, cmd)
    prefix = "✅" if code == 0 else "❌"
    body = out if out else "(no output)"
    if len(body) > 1800:
        body = body[:1800] + "\n...truncated"
    await message.reply(f"{prefix}\n```\n{body}\n```")


if __name__ == "__main__":
    client.run(BOT_TOKEN)
