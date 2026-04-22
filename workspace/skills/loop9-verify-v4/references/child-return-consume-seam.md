# Child-return / parent-consume seam (active V4.3 queue form)

## Purpose

This seam only solves one thing:

> how a child verdict feeds back into the parent-owned
> `repo-findings-board -> repo queue continuation -> repo-closure-review -> external-readout`
> chain without letting the child steal repo closure.

It is intentionally thin.

## Frozen rule

Child returns only:
- stage-local truth
- thin writeback for the current queue item row
- smallest truthful next-stage recommendation

Parent alone owns:
- queue continuation judgment
- `round_status`
- `repo_status`
- `coverage_snapshot`
- repo closure judgment
- projection-only external readout
- final repo-round verdict

## Required addition inside every `stage-verdict.<stage>.md`

Every child verdict must include:

- `parent_consume.writeback_kind`

Allowed values:
- `queue-item-writeback`
- `no-coverage-delta`

### If `writeback_kind = queue-item-writeback`
The child may return only the minimum row patch:
- `finding_label`
- `coverage_state`
- `evidence_posture`
- `last_truth`
- `last_evidence_ref`
- `next_gate`

This is enough for the parent to update the current queue item row,
then rebuild board / queue continuation / closure truth on top of that board.

### If `writeback_kind = no-coverage-delta`
The child is explicitly saying:
- stage-local truth changed,
- but repo coverage rows / counters should not be reclassified from the child side.

This is the normal default for distillation,
and may also appear in other stages when no finding-row truth actually changed.

## Hard prohibitions

Child verdicts must not emit:
- `round_status`
- `repo_status`
- `coverage_snapshot`
- `repo-closed`

Those belong only to parent-owned:
- `repo-closure-review.md`
- `external-readout.md`
- `repo-round-verdict.md`

## Parent consume order

After any child returns, the parent must consume it in this order:
1. read `stage-verdict.<stage>.md`
2. apply `parent_consume.writeback_*` to the current board posture
3. refresh `repo-findings-board`
4. check whether every in-scope row is now terminal
5. if the queue is still unfinished:
   - freeze refreshed `current queue posture`
   - freeze refreshed `next queue item`
   - freeze refreshed `next gate`
   - continue the queue
6. only if the queue is fully terminal:
   - run `repo-closure-review`
   - freeze `coverage_snapshot`
   - regenerate `external-readout` as projection-only
   - emit parent-owned `repo-round-verdict`

The parent must not jump from child `result_class` straight to repo closure,
and `external-readout` must not become a second closure-review.

## Stage-specific notes

### env-bootstrap
Normal pattern:
- keep the current queue item row non-terminal if replay is still missing
- write back env-side truth such as replay-openable / env-blocked
- push `next_gate` toward `finding-replay` or explicit env follow-up

### finding-replay
Normal pattern:
- write back the current queue item row into a truthful terminal or bounded non-terminal state
- for example: `fresh-confirmed`, `fresh-blocked`, `fresh-manual-needed`, or other frozen board vocabulary already allowed by the board contract

### distillation
Normal pattern:
- `writeback_kind = no-coverage-delta`
- card refs / learning-delta refs come back,
- but repo closure still belongs to the parent.

## One-line freeze

> Child returns only stage-local truth + thin queue-item writeback.
> Parent rebuilds repo truth and queue continuation after that.
