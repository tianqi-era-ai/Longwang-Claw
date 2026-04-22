# Recurring recovery

## Purpose

This ref freezes the thin recurring/auto-run recovery answer for `loop9-verify-v4`:

> if an hourly/recurring `loop9-verify-v4-auto` attempt is interrupted before truthful repo closure,
> the next slot should continue the **same unfinished task** first,
> not spend the slot on a fresh repo selection.

This is a thin continuation surface, not a thick scheduler.

## Control model

AI should still own:
- current frontier reading
- same-task continuation judgment
- workspace truth relocation
- whether a repo mainline is truthfully finished, blocked, or still unfinished

The bridge layer should own only deterministic hard edges:
- record the last run dir
- record the last session id when one exists
- classify terminal transport/provider failure signatures
- expose a thin current-task pointer for the next slot
- choose between `exec resume` and cold recovery based on deterministic availability

## Canonical recurring artifacts

The recurring auto-run surface should stay thin:
- `runs/loop9-verify-v4-auto/00-current-task.md`
  - one global pointer for the currently active unfinished task
- `runs/loop9-verify-v4-auto/<stamp>/run-state.md`
  - one attempt-local receipt for launch mode / session id / exit class / next mode
- `runs/loop9-verify-v4-auto/<stamp>/01-recovery-note.md`
  - one human-readable recovery note explaining what the next slot must do

Hard meaning:
- these files are **pointer/receipt surfaces**
- they are not a second repo brain
- they do not replace round root / board / objects / artifacts inside the repo workspace

## Default recurring rule

If `00-current-task.md` says the current task is still `active`,
the next recurring slot must:
1. recover that same unfinished task first
2. continue from the existing workspace frontier
3. suppress fresh auto-select unless the prior task is truthfully closed or truthfully unrecoverable as the same mainline

This rule exists because provider/network failure is not repo-semantic completion.

## Preferred hot recovery path

When the last unfinished attempt still has a usable Codex session id and the session record exists, prefer:
- `codex exec resume <session_id> <recovery prompt>`

Why:
- same-session tool/event history is preserved
- the parent can continue the same unfinished reasoning path
- the slot is not wasted on re-selecting a repo that was already in progress

## Cold recovery path

If no usable session id exists, or the session record is unavailable, use cold recovery:
- start a fresh `codex exec`
- explicitly tell it this is the **same unfinished task**
- require it to inspect the current workspace frontier first:
  - current task pointer
  - prior run receipt/note
  - accepted round root / board / objects / artifacts / delivery-tail material
- forbid fresh repo selection unless the prior task is first proven closed or no longer recoverable as the same mainline

Cold recovery is therefore:
- a new transport carrier
- for the same semantic task
- not permission to spend the slot on a new repo

## Completion and fail-closed meaning

The bridge layer should read recurring completion conservatively:
- exit `0` from the Codex run closes the current recurring task pointer
- non-zero exit does **not** close the task
- missing `final-message.txt` does **not** authorize fresh auto-select
- `429 / reconnect / stream disconnected / provider-side interruption` are caller/provider-side failures first

Hard meaning:
- transport failure may interrupt the carrier
- it may not silently consume the repo slot as if repo closure happened
- it may not silently release the slot to a new repo either

## Relation to same-repo continuity

This ref does **not** weaken the active same-repo continuity rule.

It only says:
- if the transport carrier died during the same repo mainline,
- the recurring caller may reopen that same unfinished task in the next slot,
- while preserving the current workspace frontier as source of truth.

It does **not** mean:
- manual later chat continuation becomes the normal path
- detached old artifacts can silently reopen a delivered repo
- recurring auto-run may keep re-probing a completed repo instead of advancing the unfinished queue

## Hard prohibitions

Do not:
- add a thick Python orchestrator to carry semantic workflow state
- treat `00-current-task.md` as a substitute for repo-level canonical objects
- let a fresh hourly slot bypass an active unfinished task and auto-select a new repo
- mistake transport/provider failure for repo-level semantic closure
- use cold recovery as cover for redoing already-finished stages from scratch
- keep a delivered repo active in recurring verify just because its runtime still exists

## One-sentence operating posture

> recurring/auto-run recovery should preserve the same unfinished repo-complete task first, with workspace truth as the source of truth and only a thin bridge deciding whether to use hot resume or cold recovery.
