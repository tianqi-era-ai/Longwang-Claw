# AI-Native Minimal Env-Bootstrap Bridge Lane

This note defines the **current active thin execution reading** for `loop9-verify-v4-env-bootstrap`.

It exists so the child can keep an AI-native control model while still allowing bounded deterministic help at hard edges.

## Canonical owner split

The child skill owns:
- the bounded env question
- the current smallest honest action set
- success vs blocked judgment
- `stage-verdict.env-bootstrap.md`

Thin deterministic bridges may own only:
- local file/state writeback
- one-off runtime planning/materialization steps
- direct Docker / process / HTTP checks
- remote `SSH + rsync`
- minimal installer submission / seed import / snapshot mechanics

Hard reading:
- bridge execution is subordinate
- `env_result.json` is supporting evidence, not child completion
- `stage-verdict.env-bootstrap.md` remains the child completion object

## Tencent CVM first-version lane

When `runtime_target=tencent-cvm` is frozen, prefer this thin flow:

1. parent freezes the stage handoff locally
2. child chooses the smallest truthful bridge set
3. inspect the live Tencent CVM for existing Docker/memory pressure before adding a new runtime
4. if old Loop9 rounds are still running and are not the current decisive hot path, convert them to cold snapshots first:
   - stop the containers
   - keep named images / volumes / artifact roots when they still matter as restartable evidence
   - prefer `restart=no` rather than sticky `unless-stopped` on a shared CVM
5. if needed, `rsync` only the working set to the Tencent CVM
6. run Docker commands, host-side Python, container-shell checks, and install/seed actions on the Tencent CVM itself
7. sync back only the needed artifacts
8. write `stage-verdict.env-bootstrap.md` in the round root

Interpretation:
- remote `127.0.0.1` / `localhost` belong to the Tencent CVM
- the child must not silently collapse this lane back into Mac-local execution
- by default, keep only the current decisive runtime hot on a shared CVM; important historical rounds may stay preserved, but they do not need to remain started

Operational note for proxy-bound Tencent CVM runs:
- if remote Docker/APT tooling already expects a Tencent CVM loopback proxy whose intended upstream is the operator's Mac-local Clash, prefer a reverse `SSH -R` backhaul from the Mac to the Tencent CVM as the thin bridge
- keep the remote consumer pointed at `127.0.0.1:<remote_port>` and map that port back to the Mac Clash `mixed-port` or HTTP port
- do not normalize that situation into a separate fake proxy service on the Tencent CVM unless the parent explicitly asks for a different carrier
- if the current runtime was created from a compose file with `restart: unless-stopped`, do not let that historical snapshot keep auto-revive behavior by accident once it ceases to be the active hot path

## Useful supporting artifacts

These may support the child when they exist:
- `env_result.json`
- `artifacts/runtime_decision.json`
- `artifacts/post_install_remediation_report.json`
- `artifacts/healthcheck.json`
- `snapshots/initial/manifest.json`

But they do not replace:
- handoff
- verdict
- parent-consume seam

## Current thin defaults

Unless live truth pushes otherwise, keep these as the current thin defaults:
- prefer official runtime/service images first
- prefer a slim app + selected DB lane before kitchen-sink repo compose
- default to no source patch
- treat route probes and canonical actions separately
- for config-dependent findings, prove seed/config truth before calling the env `ready_for_poc`
- on shared Tencent CVM hosts, front-load snapshot cooling before new materialization and prefer one hot runtime per repo line unless the handoff explicitly requires parallel live comparison

## Anti-drift rule

Do not let a deterministic bridge quietly grow into:
- repo-level owner
- semantic stage contract
- giant hidden policy engine
- the new mainline identity of env-bootstrap

If bounded deterministic help is needed again, keep it visibly subordinate to this child skill.
