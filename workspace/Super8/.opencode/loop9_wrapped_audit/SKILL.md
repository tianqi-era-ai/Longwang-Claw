---
name: loop9_wrapped_audit
description: Run the Super8 Loop9 wrapper for a local target path, with the wrapper as the single blessed entrypoint.
user-invocable: true
disable-model-invocation: true
metadata: {"openclaw":{"emoji":"🦞","os":["darwin"],"requires":{"bins":["python3","bash"]}}}
---

# loop9_wrapped_audit

Use the Super8 wrapper as the single blessed entrypoint for Loop9-style local audits.

## Usage

Slash command form:

`/loop9_wrapped_audit <local-target-path>`

Example:

`/loop9_wrapped_audit /absolute/path/to/local/repo`

## Intended use

This skill is intended as an **OpenClaw / Telegram-facing entrypoint** only.
It is **not** meant to be reused by local Loop9 commands, controllers, or any `skill(name="loop9")`-style internal recursion path.

## Single blessed entrypoint

When invoked by the user, the execution policy should be:

- call only the local wrapper script
- do not bypass the wrapper
- do not repackage this skill as another loop9 skill
- do not let controller/command internals route back into this skill

Wrapper path:

`~/.openclaw/workspace/Super8/.opencode/_scripts/loop9_authorized_review.py`

The wrapper is the primary stable入口 because it centralizes:

- prompt-file generation
- target-path filling
- mode selection (`command` default, `agent` experimental)
- local path conventions
- future fixes/workarounds

## Important notes / pitfalls

- Prefer the wrapper over hand-built `opencode ...` commands.
- Current default mode is `command`, because `command` mode's 【higher contamination risk under oh-my-opencode】 has been fixed.
- Current known issue: `loop9-controller` may bounce through `skill(name="loop9")` instead of directly orchestrating run_dir + solver/validator/refiner.
- `command` mode must use `loop9` (no leading slash) when using `opencode run --command ...`.
- Keep the actual large task instructions inside the generated task file when possible; avoid exposing large prompt bodies in the entry message.
- If the wrapper behavior changes, update the wrapper script first, then this skill.
- This skill should remain **isolated from local loop9 recursion**. If it is later wired into Telegram/OpenClaw, keep it as an outer entrypoint only.
