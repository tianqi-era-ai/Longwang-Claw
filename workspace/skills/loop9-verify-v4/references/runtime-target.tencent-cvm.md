# Tencent CVM runtime target

This ref freezes the first-version reading for a remote runtime target:
- `runtime_target.kind = tencent-cvm`

## Purpose

Use this target when:
- the parent still lives on the Mac/OpenClaw side
- but `env-bootstrap` and/or `finding-replay` should actually execute on a Tencent CVM through SSH
- and the intent is to keep the remote host itself as the place where Docker, container shell commands, and host-side PoC helpers run

This is intentionally **not**:
- remote Docker API first
- external debugger first
- a requirement to expose the remote env directly back to the Mac as if it were local

## First-version execution rule

The first-version preferred transport is:
1. parent compiles thin stage handoff locally
2. child stage keeps the same thin handoff/verdict contract
3. before materializing a new runtime, child stage inspects the shared Tencent CVM for existing Docker/memory pressure
4. if old Loop9 rounds are still running and the handoff does not explicitly require parallel live comparison, convert non-essential historical runtime to cold snapshots first rather than layering a new hot stack on top; delivered repos from previous rounds should normally be stopped unless they are the repo's declared `published-final` public runtime or an explicit reopen/compare need keeps them hot
5. child stage uses `SSH + rsync` to materialize its working set on the Tencent CVM
6. Docker commands, `docker exec`, container-local checks, and host-side PoC helper scripts all run **on the Tencent CVM itself**
7. child writes its stage verdict / artifacts under the same round root semantics
8. child syncs the needed outputs back to the parent-visible round root
9. if remote Docker/APT traffic must use a Tencent CVM loopback proxy and that loopback is intentionally the operator Mac's local Clash path, prefer a reverse `SSH -R` tunnel from the Mac to the Tencent CVM while keeping the remote endpoint unchanged

## Important interpretation

When this target is active:
- remote `127.0.0.1` / `localhost` values belong to the Tencent CVM, not the Mac
- the parent must not silently collapse a `tencent-cvm` stage back into Mac-local execution
- `finding-replay` should normally continue on the same remote target used by the current env unless the parent explicitly re-freezes runtime placement
- before interpreting shared-host Docker clutter, first read `/root/openclaw-runtime/docker-resource-registry.json` through `/usr/local/bin/openclaw-docker-inventory --json`; treat that registry as the operator-visible authority for `published-final`, `historical-cold-snapshot`, `stopped-intermediate`, and `operator-keep`
- on a shared Tencent CVM, keep only the current decisive round runtime hot by default, but allow one declared `published-final` public runtime per delivered repo to remain hot when operators still need direct access; prior useful rounds should normally be preserved as stopped snapshots rather than always-running stacks
- once a repo has already reached `repo-mainline-done`, do not keep extra historical stacks hot just because a later hourly verify turn might revisit them; if the product contract still needs a public entry, retain only the repo's declared `published-final` runtime and use lighter status/heartbeat checks for everything else
- when a repo keeps a `published-final` runtime hot, record it in an operator-visible registry near the remote workspace root with repo slug, public URL, runtime root, and restart/startup carrier so later cleanup does not misread it as disposable history
- reclaim/deletion on the shared CVM should only target containers / images / volumes older than `12h` and not marked or recorded as `published-final` / current decisive runtime
- for containers, the `12h` minimum age should be judged by latest lifecycle activity with `State.StartedAt` preferred, then `State.FinishedAt`, and only then `Created`; do not reclaim a container just because it was created long ago if it was restarted within the last `12h`
- future Docker-based runtimes on that CVM should carry stable retention labels whenever their carrier allows it:
  - `io.openclaw.repo_slug=<repo-slug>`
  - `io.openclaw.runtime_unit=<unit-key>`
  - `io.openclaw.retention.class=published-final|historical-cold-snapshot|intermediate`
  - `io.openclaw.visibility=show|hidden`
  - `io.openclaw.retention.keep=true` for `published-final`
- if a proxy escalation is required after smaller mirror/source fixes fail and the frozen loopback proxy semantically belongs to the Mac-local Clash, keep the Tencent CVM-facing endpoint stable and backhaul it with reverse `SSH -R` rather than inventing a fake local proxy on the Tencent CVM

## Scope boundary

First-version expectation is deliberately narrow:
- make the existing Mac-local env/bootstrap + replay flow **move intact** onto the Tencent CVM
- do not front-load panel software, remote-debug infrastructure, or a thicker remote control plane
- snapshot/backup freezing for successful PoC states is allowed, but on a shared host those preserved states should usually stay cold rather than continuing to auto-revive; the exception is the explicit `published-final` runtime that still serves the public access contract
