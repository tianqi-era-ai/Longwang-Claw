# REPO-STRUCTURE.md

This workspace lives **inside** a larger Git repository rooted at:

- `~/.openclaw`

So when working from `workspace/`, do **not** assume the repo only contains workspace notes. The real repository also includes runtime config, agent state, browser state, cron data, device state, and other operational files.

This file describes that **live local** mental model.
The public `Longwang-Claw` repo only carries a selected open-source-safe subset of those assets, not the whole live tree.

## Mental model

Think of the repo as having two layers:

### 1. Human-edited / durable knowledge
These are usually the files you most want to read, edit, and intentionally commit.

- `workspace/` — docs, helper files, selected hooks/plugins, and other durable workflow assets
- `openclaw.json` — main OpenClaw config
- selected files under `agents/`, `cron/`, `devices/`, `identity/` when they represent meaningful durable state

### 2. Runtime / noisy / regenerable state
These often change during normal use and can make `git status` noisy.

Examples:
- `browser/` — browser profile data, caches, downloads, session state
- `agents/main/sessions/` — conversation transcripts and session metadata
- `logs/` — logs
- `memory/main.sqlite` — memory database internals
- `cron/runs/` — run outputs
- various `*.bak`, caches, lock files, and temporary state

Some of these are ignored by the repo's `.gitignore`, some are still tracked, and some may need case-by-case decisions.

## Before making repo-wide judgments
When talking about Git status, backup completeness, or whether something "was uploaded", check from the repo root:

1. Confirm repo root with `git rev-parse --show-toplevel`
2. Read root `.gitignore`
3. Read `.git/info/exclude`
4. Inspect tracked/untracked state from repo root
5. Only then conclude whether something is intentionally excluded, accidentally omitted, or just not yet committed

## Important reminder
A commit made from `workspace/` may still need files outside `workspace/` (like `openclaw.json`) if the change affected real system behavior.

## Current known important files
- In the **live local repo**, `openclaw.json` is the main config source of truth, but it is intentionally not part of this public repo.
- In the **public Longwang-Claw repo**, start with:
  - `docs/给AI的装配说明.md`
  - `workspace/REPO-STRUCTURE.md`
  - `workspace/hooks/handlers/inject-runtime-default-model.js`
  - `workspace/plugins/star-office-sync/`
  - `extensions/openclaw-lark/`

## User habit to remember
The human may run `git add .` directly from `~/.openclaw`. That means `.gitignore` coverage matters a lot, and audit conclusions should be tested against that workflow rather than a workspace-only workflow.
