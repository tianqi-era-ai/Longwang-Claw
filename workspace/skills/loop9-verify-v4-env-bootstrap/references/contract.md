# Env-bootstrap child contract

## Scope

This child handles only:
- repo-scoped env establish / revive / repair
- truthful env-side bounded work
- env-side receipts / blocked truth

## Input expectation

Input should already be narrowed by the parent into:
- current repo identity
- current env route hypothesis
- minimal env refs
- runtime target / execution host when env work should stay on a remote machine
- bounded success/block signals
- current round root / output targets

## Output expectation

Return only, and write back into the current round root:
- `stage-verdict.env-bootstrap.md`
- artifact refs
- the smallest truthful next-stage recommendation

## Underlying deterministic bridge boundary

This child may consume bounded deterministic bridge help, but that bridge never replaces the child contract.

Canonical reading:
- script outputs such as `env_result.json` may support the child
- deterministic transport / runtime materialization may be delegated downward
- child completion still requires `stage-verdict.env-bootstrap.md`
- stage meaning and parent writeback remain owned by this child contract

Current active execution reading lives at:
- `references/minimal-bridge-lane.md`

The previously external `loop9-env-bootstrap` prototype is retired and should not be treated as a second active stage owner.

Inside `stage-verdict.env-bootstrap.md`, the child must also carry the thin parent-consume seam:
- `parent_consume.writeback_kind`
- and, when needed, only the minimum active-finding row patch:
  - `finding_label`
  - `coverage_state`
  - `evidence_posture`
  - `last_truth`
  - `last_evidence_ref`
  - `next_gate`

If env work changed only env-side truth but did not reclassify coverage,
use `writeback_kind = no-coverage-delta`.

When `runtime_target=tencent-cvm` is active:
- env truth should be produced on the Tencent CVM itself
- remote `localhost` / `127.0.0.1` values belong to that host, not the parent Mac
- the child should preserve this runtime target unless the parent explicitly re-freezes placement
- before materializing a new remote round on a shared CVM, inspect current Docker/memory pressure; stopping stale historical rounds is part of honest env setup rather than optional cleanup
- historical useful rounds may remain as restartable evidence, but they should normally be preserved as **stopped** snapshots instead of hot services
- when converting an old round into a cold snapshot, prefer a non-sticky restart posture such as `restart=no` over shared-host `unless-stopped`
- if the live repair path still needs a proxy and the frozen Tencent CVM loopback proxy is intentionally a backhaul to the operator's Mac-local Clash, the child should prefer a reverse `SSH -R` tunnel as the canonical carrier after smaller source/mirror adjustments fail
- ad-hoc proxy emulation on the Tencent CVM should be treated as a different carrier and should not silently replace that reverse-tunnel reading
- if manual cleanup changes the hot/cold runtime boundary, leave a short operator-visible retention note near the remote workspace root

Timeout note:
- timeout without a written `stage-verdict.env-bootstrap.md` is not child output truth
- parent should record caller-side `timeout-budget failure` and rerun with a larger timeout
- parent may blame prompt/worker only after inspecting concrete process-pathology evidence

## Forbidden actions

This child may not:
- take repo-level owner
- pick a different repo
- pick a different finding
- announce repo closure
- emit `round_status`, `repo_status`, `coverage_snapshot`, or `repo-closed`
- directly jump into another child skill
