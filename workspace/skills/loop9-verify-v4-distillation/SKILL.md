---
name: loop9-verify-v4-distillation
description: Thin V4 child skill for repo-level distillation, old-card upgrade vs new sub-family judgment, and bounded learning-delta writeback. Use only after the V4 parent has prepared a thin distillation handoff.
---

# Loop9 Verify V4 Distillation

This is a **bounded distillation child skill**.

It does not own repo-level control.

## Current status

Current maturity is now **shell initialized + live-consumed more than once**:
- distillation boundary frozen,
- shell initialized,
- live-consumed once on `mcms` (`P6`),
- live-consumed again inside the first full repo round on `buildadmin` (`H4`),
- still no extra thick script layer.

## Use when

Use this skill only when the parent layer has already decided:
- repo-level closure/context is mature enough for distillation,
- `distillation` is the correct next stage,
- and the parent has prepared a thin `stage-handoff.distillation.md`.

## Default runtime binding

Current V4.2 production reading is:
- `distillation` is now read as `must-isolated`
- isolated is now the current production default for this child
- inline is no longer a current production default for this child
- if a future round ever uses inline at all, it must be treated as an explicit manual high-threshold exception rather than a silent thin-delta fallback
- the parent may wait / poll / block on this child inside the same repo flow, but same-repo continuation may not depend on a fresh user turn
- regardless of runtime mode, this child must keep the same thin handoff/verdict contract

## Accepted input

- `stage-handoff.distillation.md`
- compiled hot/warm/cold refs for the bounded distillation question
- current round root / expected `objects/` + `artifacts/` targets
- repo closure refs
- related older card refs

Read order:
- handoff body first,
- hot refs first,
- warm refs only if needed,
- cold refs only by explicit necessity.

## Required output

Return inside the current round root:
- `stage-verdict.distillation.md` (normally with `parent_consume.writeback_kind = no-coverage-delta`)
- card refs / learning-delta refs

Allowed result classes:
- `receipt-confirmed`
- `fixed-point`
- `handoff-required`

Timeout note:
- timeout is **not** a child result class
- if the caller cuts this run before a usable `stage-verdict.distillation.md` is written, record that as caller-side `timeout-budget failure`
- rerun with materially larger timeout before drawing semantic conclusions about this child/prompt

Here `receipt-confirmed` means only: bounded distillation writeback / learning-delta materialized.
It never means repo closure.

## Must not do

- restart replay on its own
- choose a new repo
- emit `round_status`, `repo_status`, `coverage_snapshot`, or `repo-closed`
- declare live progress from writeback alone
- promote a learning artifact without truth-backed and later live-consumed justification

## Reference

- `references/contract.md`
