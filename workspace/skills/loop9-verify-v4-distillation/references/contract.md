# Distillation child contract

## Scope

This child handles only:
- repo-level experience distillation
- old-card upgrade vs new sub-family judgment
- bounded learning-delta outputs

## Input expectation

Input should already be narrowed by the parent into:
- repo closure review refs
- key receipts / evidence refs
- older related card refs
- explicit distillation question
- current round root / output targets

## Output expectation

Return only, and write back into the current round root:
- `stage-verdict.distillation.md`
- new/updated card refs
- learning-delta refs

Inside `stage-verdict.distillation.md`, the default parent-consume seam should be:
- `parent_consume.writeback_kind = no-coverage-delta`

If a bounded learning delta or card writeback happened,
that may still be `receipt-confirmed` at the stage level,
but it must never be emitted as repo closure.

Timeout note:
- timeout without a written `stage-verdict.distillation.md` is not child output truth
- parent should record caller-side `timeout-budget failure` and rerun with a larger timeout
- parent may blame prompt/worker only after inspecting concrete process-pathology evidence

## Forbidden actions

This child may not:
- reopen replay on its own
- choose repo-level owner
- emit `round_status`, `repo_status`, `coverage_snapshot`, or `repo-closed`
- auto-publish
- treat “new card written” as live progress by itself
