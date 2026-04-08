# Project Record Schema

One file per project under `factory/state/projects/`.

## Required fields
- `project_id` — stable slug
- `name` — human-readable name
- `repo_path` — absolute repo path
- `default_branch` — default branch name
- `discord.server_id`
- `discord.control_channel_id`
- `discord.decisions_channel_id`
- `discord.ops_channel_id`
- `openagent_enabled` — boolean
- `created_at`
- `updated_at`

## Purpose
This record answers:
- what project the thread belongs to
- where the repo lives
- which Discord channels belong to the project
- whether OpenAgent escalation is allowed by default
