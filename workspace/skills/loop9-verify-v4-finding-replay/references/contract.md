# Finding-replay child contract

## Scope

This child handles only:
- the current active finding
- canonical replay
- bounded contrast when it can still change truth
- receipt / blocked / fixed-point capture

## Control surface

Canonical control surface:
- `stage-handoff.finding-replay.md`
- `attempt-receipt.<repo>.<finding>.md`
- `stage-verdict.finding-replay.md`

Canonical reading:
- the child is markdown-first and AI-native
- handoff/verdict/receipt are the primary semantic objects
- any script / JSON / helper command is only a thin bridge

Hard meaning:
- a request JSON does not replace the handoff
- a runner does not replace the verdict
- raw logs do not count as child completion

## Input expectation

Input should already be narrowed by the parent into:
- current repo identity
- current active finding identity
- env refs
- runtime target / execution host when replay must stay on a remote machine
- canonical PoC refs
- bounded replay goal
- current round root / output targets

## Output expectation

Return only, and write back into the current round root:
- `stage-verdict.finding-replay.md`
- `attempt-receipt.<repo>.<finding>.md`
- evidence refs

When a replay depends on a manually reusable account and that account is intentionally safe to disclose for a test/demo env, `attempt-receipt` should carry a small manual verification handoff:
- entry URL
- username
- password
- any tiny note needed for a later human checker

Do not force later reviewers to recover those credentials from repo defaults, seed scripts, or guesswork when the child already has truthful access to them.

The child should prefer:
- markdown-first bounded reasoning
- the minimum artifact set that supports the verdict
- optional thin bridge artifacts only when they materially help receipt capture or truthful blocked diagnosis

Inside `stage-verdict.finding-replay.md`, the child must also carry the thin parent-consume seam:
- `parent_consume.writeback_kind = active-finding-writeback`
- and only the minimum active-finding row patch:
  - `finding_label`
  - `coverage_state`
  - `evidence_posture`
  - `last_truth`
  - `last_evidence_ref`
  - `next_gate`

When `runtime_target=tencent-cvm` is active:
- replay truth should be produced on the Tencent CVM itself
- remote `localhost` / `127.0.0.1` values belong to that host, not the parent Mac
- the child should keep replay on the same remote env unless the parent explicitly changes runtime placement
- the child may choose a tiny bridge set on that host:
  - SSH command batches
  - `curl`
  - host-side Python
  - Docker CLI / `docker exec`
  - one canonical PoC replay
- but these remain subordinate to the handoff/verdict contract
- if the replay result is meant to support later teammate browser verification, the receipt should preserve the safe manual entry hints rather than assuming the next reviewer will rediscover them

The child may not jump from replay receipt straight to repo closure.

## AI-native boundary

This child should follow [`ai-native-development`](../../ai-native-development/SKILL.md):
- AI owns bounded replay judgment
- code owns only hard edges
- retry/replay policy belongs to the parent/dispatcher, not hidden bridge defaults
- object growth is not progress unless it changes live truth or live consumption

Timeout note:
- timeout without a written `stage-verdict.finding-replay.md` is not child output truth
- parent should record caller-side `timeout-budget failure` and rerun with a larger timeout
- parent may blame prompt/worker only after inspecting concrete process-pathology evidence

## Forbidden actions

This child may not:
- pick a new repo
- pick a new active finding
- declare repo closure
- emit `round_status`, `repo_status`, `coverage_snapshot`, or `repo-closed`
- directly jump to distillation or env-bootstrap
- redefine the lane into a script-first runner protocol
