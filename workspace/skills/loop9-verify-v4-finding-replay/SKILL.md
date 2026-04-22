---
name: loop9-verify-v4-finding-replay
description: AI-native V4 child skill for the current active finding's canonical replay, bounded contrast, and receipt capture. Use only after the V4 parent has already chosen the active finding and prepared a thin replay handoff.
---

# Loop9 Verify V4 Finding Replay

This is a **bounded finding-level child skill**.

It does not own repo-level control.

## Current status

Current maturity is now **shell initialized + live-consumed under the parent more than once**:
- replay boundary frozen,
- shell initialized,
- explicitly live-consumed on `buildadmin` (`H3`),
- live-consumed again inside the first full repo round on `buildadmin` (`H4`),
- current Tencent CVM lane already has a usable thin bridge implementation,
- but the child is still defined as `handoff + verdict + receipt` first rather than `script-first`.

## Use when

Use this skill only when the parent layer has already decided:
- the active repo,
- the active finding,
- that `finding-replay` is the correct next stage,
- and the parent has prepared a thin `stage-handoff.finding-replay.md`.

## AI-native operating posture

This child should be read through [`ai-native-development`](../ai-native-development/SKILL.md):
- the main control surface is `stage-handoff -> attempt-receipt + stage-verdict`
- AI owns the bounded semantic judgment:
  - what the next smallest replay action set should be
  - whether a fresh receipt is still obtainable
  - whether the current lane is `receipt-confirmed / blocked-confirmed / fixed-point / handoff-required`
- code/scripts may exist, but only as **thin bridges**
  - SSH / rsync
  - curl / PoC execution
  - host-side helper commands
  - tiny deterministic receipt capture

Hard reading:
- a request JSON is not the child
- a runner is not the child
- a bridge script may help execute, but it must not become the semantic owner of replay truth

## Default runtime binding

Current V4.2 production reading is:
- `finding-replay` is now read as `must-isolated`
- isolated is now the current production default for this child
- inline is no longer a current production default for this child
- if a future round ever uses inline at all, it must be treated as an explicit manual high-threshold exception rather than a silent decisive-receipt shortcut
- the parent may wait / poll / block on this child inside the same repo flow, but same-repo continuation may not depend on a fresh user turn
- regardless of runtime mode, this child must keep the same thin handoff/verdict contract

## Accepted input

- `stage-handoff.finding-replay.md`
- compiled hot/warm/cold refs for the frozen active finding
- current round root / expected `objects/` + `artifacts/` targets
- canonical PoC refs
- explicit runtime target when replay must stay on a remote env host
- bounded replay goal
- optional thin-bridge hints when the child wants reusable mechanical help

Read order:
- handoff body first,
- hot refs first,
- warm refs only if needed,
- cold refs only by explicit necessity.

## Required output

Return inside the current round root:
- `stage-verdict.finding-replay.md` (with thin `parent_consume.writeback_*` fields)
- `attempt-receipt.<repo>.<finding>.md`
- evidence/artifact refs

When the replay lane proves or depends on a manually reusable test/demo account, the child should also record the manual verification handoff directly inside `attempt-receipt`:
- target URL
- usable username/password
- any small note needed so later human reviewers can log in without rediscovering defaults

Hard reading:
- if the env is explicitly test/demo and the credentials are intentionally reset for replay, do not make later reviewers reverse-engineer them again from source or guesses
- if the credential is dynamic, secret, or not safe to re-expose, record the truthful boundary instead of fabricating a convenience credential

Canonical completion reading:
- `stage-verdict.finding-replay.md` is the child completion object
- `attempt-receipt` is the receipt-side truth object
- raw command output / request JSON / bridge metadata do not count as completion by themselves

Allowed result classes:
- `receipt-confirmed`
- `blocked-confirmed`
- `fixed-point`
- `handoff-required`

Timeout note:
- timeout is **not** a child result class
- if the caller cuts this run before a usable `stage-verdict.finding-replay.md` is written, record that as caller-side `timeout-budget failure`
- rerun with materially larger timeout before drawing semantic conclusions about this child/prompt

## Tencent CVM runtime target

When the handoff freezes `runtime_target=tencent-cvm`:
- replay should continue on that same Tencent CVM by default instead of bouncing back to the Mac
- PoC helper scripts, host-side curl/python probes, Docker CLI, and container-shell commands should run on the Tencent CVM itself
- this first-version target is intentionally server-local operation through SSH, not an external-debug-first model
- remote `127.0.0.1` / `localhost` values in receipts belong to the Tencent CVM env
- the child may choose a very small bridge set such as:
  - direct SSH command batches
  - one-off `curl`
  - one canonical PoC replay
  - one tiny inline Python snippet
  - one optional rsync of a missing PoC/helper asset
- but the replay lane should still stay markdown-first and AI-led:
  - handoff freezes the question
  - child decides the smallest bridge actions
  - verdict/receipt remain the canonical outputs
- if manual browser verification on Tencent CVM is part of the live value, record the public URL and any safe test credentials in the receipt so teammates can reproduce the same session entry path

## Must not do

- re-rank the whole repo findings board
- switch to a different finding on its own
- declare `repo-closed`
- emit `round_status`, `repo_status`, or `coverage_snapshot`
- directly call `distillation`
- grow into a thick replay churn machine
- redefine itself as a runner product whose success criterion is merely “the script ran”

## Reference

- `references/contract.md`
- `references/ai-native-minimal-lane.md`
- `../loop9-verify-v4/references/runtime-target.tencent-cvm.md`
- `../ai-native-development/SKILL.md`
