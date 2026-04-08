# Thread Record Schema

One file per Discord thread under `factory/state/threads/`.

## Required fields
- `thread_id`
- `project_id`
- `lane_id`
- `control_channel_id`
- `created_at`
- `updated_at`

## Purpose
This record answers:
- which project a Discord thread belongs to
- which active lane the thread currently controls
- where blocked questions and replies should route
