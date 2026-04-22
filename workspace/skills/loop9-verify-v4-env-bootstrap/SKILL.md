---
name: loop9-verify-v4-env-bootstrap
description: Thin V4 child skill for repo-scoped truthful env establish / repair / revive. Use only after the V4 parent has already chosen env-bootstrap as the current next stage and prepared a thin stage handoff.
---

# Loop9 Verify V4 Env Bootstrap

This is a **bounded child skill**.

It does not own repo-level control.

## Current status

Current maturity is now **shell initialized + live-consumed under the parent more than once**:
- boundary frozen,
- shell initialized,
- explicitly live-consumed on `dzzoffice` (`H2`),
- live-consumed again inside the first full repo round on `buildadmin` (`H4`),
- current active evolution now lives here rather than in the retired `loop9-env-bootstrap` prototype.

## Retired prototype boundary

The old `loop9-env-bootstrap` prototype is no longer an active skill-layer owner.

Current active reading:
- this directory is the semantic owner of the env-bootstrap child stage
- any future deterministic bridge must stay visibly subordinate to this child
- active iteration should happen here, not by reviving the retired prototype as a parallel owner

If later we mine the retired prototype, the target should be:
- thin references
- bounded bridge rules
- durable learning deltas

Not:
- reactivating a second competing env-bootstrap skill surface

## Experience posture

This child should sediment experience in a thin way:
- keep the active visibility layer in `references/experience-index.md`
- keep case-backed observed lessons in small reference notes
- prefer abstract reusable truths over replaying the whole case narrative
- do not let experience sedimentation turn into a new thick planner

## Use when

Use this skill only when the parent layer has already decided:
- the active repo,
- that `env-bootstrap` is the correct next stage,
- and the parent has prepared a thin `stage-handoff.env-bootstrap.md`.

## Default runtime binding

Current V4.2 production reading is:
- `env-bootstrap` is now read as `must-isolated`
- isolated is now the current production default for this child
- inline is no longer a current production default for this child
- if a future round ever uses inline at all, it must be treated as an explicit manual high-threshold exception rather than a silent thin-case fallback
- the parent may wait / poll / block on this child inside the same repo flow, but same-repo continuation may not depend on a fresh user turn
- regardless of runtime mode, this child must keep the same thin handoff/verdict contract

## Accepted input

- `stage-handoff.env-bootstrap.md`
- compiled hot/warm/cold refs for the current env question
- current round root / expected `objects/` + `artifacts/` targets
- explicit runtime target when the env should materialize on a remote host
- bounded success vs blocked signals

Read order:
- handoff body first,
- hot refs first,
- warm refs only if needed,
- cold refs only by explicit necessity.

## Required output

Return inside the current round root:
- `stage-verdict.env-bootstrap.md` (with thin `parent_consume.writeback_*` fields)
- env-side artifact refs

Allowed result classes:
- `receipt-confirmed`
- `blocked-confirmed`
- `fixed-point`
- `handoff-required`

Timeout note:
- timeout is **not** a child result class
- if the caller cuts this run before a usable `stage-verdict.env-bootstrap.md` is written, record that as caller-side `timeout-budget failure`
- rerun with materially larger timeout before drawing semantic conclusions about this child/prompt

## Tencent CVM runtime target

When the handoff freezes `runtime_target=tencent-cvm`:
- before trusting raw `docker ps -a` / `docker compose ls --all` on the shared CVM, first read the operator registry by running `/usr/local/bin/openclaw-docker-inventory --json` (or its text form) and treat `/root/openclaw-runtime/docker-resource-registry.json` as the authority for `published-final` vs `historical-cold-snapshot` vs `stopped-intermediate`
- before materializing a new remote round, inspect the live Tencent CVM for existing Docker/memory pressure; shared-host cleanup is part of truthful env prep, not optional aftercare
- if historical Loop9 runtimes are still running and the handoff does not explicitly require parallel live comparison, convert them to **cold snapshots** first:
  - stop the old containers
  - keep named images / volumes / artifact roots when they still matter as restartable evidence
  - prefer `restart=no` for those historical containers rather than leaving them in sticky auto-revive mode on a shared CVM
- keep only the current decisive round runtime hot by default, but do not silently demote a repo's declared `published-final` public runtime when operators still need direct access; one such runtime may remain hot per delivered repo, while the rest should stay cold
- this child should prefer `SSH + rsync` into the Tencent CVM as the first-version carrier
- Docker commands, `docker exec`, container-local repairs, and host-side helper scripts should run on the Tencent CVM itself
- remote `127.0.0.1` / container-facing URLs in artifacts should be read as **Tencent CVM local truth**
- do not widen the first implementation into remote Docker API / external debugger complexity unless the parent explicitly asks for that extra layer
- when remote APT/package installation is genuinely required, do not pretend it can always be skipped:
  - prefer the smallest viable source adjustment first, such as keeping the main image lineage and switching only blocking APT fetches to a simple reachable mirror
  - if official source and simple mirror routes both fail or stall and the package install is still decisive, only then escalate to a proxy path such as ClashParty
  - if that proxy escalation is needed because the Tencent CVM runtime is already frozen to a remote loopback proxy that is intentionally meant to reach the operator's Mac-local Clash, prefer a reverse `SSH -R` backhaul from the Mac into the Tencent CVM while keeping the remote consumer pointed at `127.0.0.1:<remote_port>`
  - in that situation, treat the reverse tunnel as the canonical thin bridge and do not silently replace it with an ad-hoc fake proxy process on the Tencent CVM unless the parent explicitly freezes a different carrier
  - keep the complexity ladder explicit: simple mirror/source substitution first, proxy second, larger networking machinery last
- when env-bootstrap records a bare probe on an action endpoint whose real semantics are not `GET` (for example upload routes), read that sample as route/debug shape only; it must not by itself terminalize a later `finding-replay` row
- when the next frozen finding depends on seeded config/business truth, prefer proving that config truth exists before claiming the env is honestly `ready_for_poc`
- when manual cleanup changes which runtimes are hot vs cold, leave a short operator-visible retention note under the remote workspace root that explicitly separates `published-final` public runtimes from `cold-snapshot` history, including repo slug, public URL, runtime root, and startup carrier
- any reclaim/deletion path on that shared CVM should only target containers / images / volumes older than `12h` and must skip the current decisive runtime plus anything marked/recorded as `published-final`
- for container age on that shared CVM, do not judge the `12h` window by `CreatedAt` alone; use the latest lifecycle activity with `State.StartedAt` preferred, then `State.FinishedAt`, and only fall back to `Created` when the lifecycle fields are absent
- when this child creates or refreshes Docker-based runtime on the Tencent CVM, write retention labels into the resulting compose/service definitions whenever the carrier allows it:
  - `io.openclaw.repo_slug=<repo-slug>`
  - `io.openclaw.runtime_unit=<unit-key>`
  - `io.openclaw.retention.class=published-final|historical-cold-snapshot|intermediate`
  - `io.openclaw.visibility=show|hidden`
  - `io.openclaw.retention.keep=true` for `published-final`
- for future Portainer filtering, treat `io.openclaw.visibility=hidden` as the canonical label pair for cold history / stopped intermediate runtime; do not hide published-final or operator-keep runtime with that label

## Must not do

- choose the repo
- choose the active finding
- declare `repo-closed`
- emit `round_status`, `repo_status`, or `coverage_snapshot`
- directly call `finding-replay`
- turn itself into a thick env orchestrator

## Reference

- `references/contract.md`
- `references/minimal-bridge-lane.md`
- `references/live-knowledge-index.md`
- `references/experience-index.md`
- `../loop9-verify-v4/references/runtime-target.tencent-cvm.md`
