# Canonical objects (Markdown-first)

V4/V4.1/V4.2/V4.3/V4.4 canonical objects stay Markdown-first.

## Storage note

- stable rule/type docs stay in top-level refs/contracts
- pre-start selection request / proposal / acceptance may live in a bounded intake surface before a round root exists
- live round instance objects belong under the current round root `.../rounds/<repo>/<round>/objects/`
- raw evidence belongs under the same round root `artifacts/`

## Owner / placement rule

Every major object is now expected to be read with two separate fields:
- `semantic owner`
- `runtime placement`

Use:
- `references/owner-placement-matrix.md`

Hard meaning:
- parent-owned objects may still be isolated-produced
- child-produced objects do not gain repo closure authority
- queue-scope final freeze remains parent-only

## Pre-start selection objects

### `repo-selection-proposal.md`
This is the thin pre-start selection proposal returned from `repo-selection-pack`.

Current owner / placement:
- semantic owner: `parent`
- runtime placement: `must-isolated-produced`

Current instance location:
- bounded pre-start intake surface chosen by the parent

It should carry only:
- `selection_mode`
- `requested_repo_ref` when present
- `proposed_repo_ref`
- `continuation_anchor_status`
- `selection_basis`
- `suppressed_candidates`
- `next_action`

Hard meaning:
- proposal only,
- no final repo choice freeze,
- no current round root creation,
- no queue truth,
- no closure truth.

### `parent-selection-acceptance.md`
This is the thin parent decision that consumes `repo-selection-proposal`.

Current owner / placement:
- semantic owner: `parent`
- runtime placement: `parent-executed`

Current instance location:
- bounded pre-start intake surface until repo choice is frozen

It should carry:
- `selection_mode`
- accepted / rejected / overridden repo choice
- explicit override note when the parent keeps an explicit repo against high-risk reject advice
- accepted thin selection basis

Hard meaning:
- this is the last pre-start freeze point before `current round root fix`
- later `repo-task-brief` should cite this accepted basis instead of replaying the whole selection narration

## Parent-layer objects

### `repo-task-brief.md`
This is the parent-owned **repo-level start anchor**.

Current owner / placement:
- semantic owner: `parent`
- runtime placement: `isolated-produced`

It must answer, in a thin form:
- which repo is active,
- why it is active now,
- what the current repo truth currently is,
- what this round is trying to achieve,
- what this round is explicitly not trying to do,
- what the current active stage guess is,
- which few refs the next cycle most needs,
- and when the brief should be refreshed again.

Runtime expectation:
- refresh it after `repo-state-relocation + current round root fix`,
- before board refresh / child choice,
- and let the next parent cycle start from it rather than from the loudest queue item or latest receipt.

Boundary:
- it is **not** the full board,
- **not** the stage handoff,
- **not** the closure review,
- and **not** a thick repo summary.

See also:
- `references/repo-task-brief.md`

### `repo-findings-board.md`
This is the repo-wide **current-round truth board**.

Current owner / placement:
- semantic owner: `parent`
- runtime placement: `isolated-produced`

It must track:
- all in-scope findings, not only the loudest one,
- one visible row per finding,
- one explicit `current_round_disposition` per row,
- queue posture / next queue item,
- unfinished count,
- closure gates remaining,
- and the next truthful move.

Compatibility note:
- older active-bucket / active-finding cursor fields may survive only as migration background,
- older `historical-kept` / old-evidence posture may still survive as background,
- but those are no longer allowed to stand in for a row's current-round disposition.

It must be good enough that the parent can answer:
- which findings are still `unfinished`,
- which findings are already terminal this round,
- and whether repo closure is still blocked only because queue truth is incomplete.

See also:
- `references/board-closure-verdict.md`
- `references/repo-queue-workflow.md`

### `parent-draft-pack.md`
This is the thin parent consume packet returned from `repo-start-pack`.

Current owner / placement:
- semantic owner: `parent`
- runtime placement: `isolated-produced`

It should carry only:
- refs to the current relocation / brief / board drafts,
- `proposed_queue_posture`,
- `proposed_next_queue_item`,
- `proposed_next_gate`,
- minimal rationale,
- explicit note that these proposals are not yet frozen.

Hard meaning:
- it exists to help the parent freeze queue scope with less start-side context load,
- it may not silently convert proposals into accepted repo truth.

### `repo-closure-review.md`
Summarizes repo-level closure truth.

Current owner / placement:
- semantic owner: `parent`
- runtime placement: `parent-executed`

It is a **post-queue-completion freeze**, not a soft partial-progress summary.

It should say:
- whether the current round is now truthfully `round-closed`,
- whether the repo may now truthfully become `repo-closed`,
- what closure gates remain if not,
- how the current-round terminal dispositions ended up distributed,
- and which frozen `coverage_snapshot` later outward objects must consume rather than reinterpret.

If any in-scope finding is still `unfinished`,
then there is not yet a truthful `repo-closure-review` to emit.

See also:
- `references/board-closure-verdict.md`

### `external-readout.md`
Thin outward-facing coverage summary.

Current owner / placement:
- semantic owner: `parent`
- runtime placement: `isolated-produced`

Hard meaning:
- it is projection-only,
- it may not invent closure truth,
- it must project already-frozen parent closure truth,
- and its allowed truth source is only frozen `repo-closure-review + coverage_snapshot` plus accepted artifact refs.

It may not:
- rejudge `round_status`,
- rejudge `repo_status`,
- invent a new `coverage_snapshot`,
- silently promote old evidence into current-round handling,
- or let one glamorous replay story stand in for the full queue truth.

It must explicitly surface at least:
- `repo_status`
- `in_scope_findings_total`
- `terminal_disposition_count`
- `fresh_confirmed_count`
- `fresh_blocked_count`
- `fresh_manual_needed_count`
- `fresh_skip_by_policy_count`
- `remaining_unfinished_count`

This object exists to prevent one beautiful replay from pretending to be repo-level fulfillment.

### `repo-round-verdict.md`
Thin parent-owned round conclusion.

Current owner / placement:
- semantic owner: `parent`
- runtime placement: `parent-executed`

It should compress the current round into:
- `round_status`
- `repo_status`
- coverage snapshot
- key artifact refs
- next recommended truthful follow-on
- closure note

Hard meaning:
- it remains the final parent-only round verdict,
- it may cite `external-readout`,
- but its truth source stays the frozen `repo-closure-review + coverage_snapshot` rather than outward wording,
- it must still make the per-disposition queue truth legible rather than hiding it behind one headline receipt,
- it is a closure-side freeze point, not `repo-mainline-done`,
- and it should still point the parent toward the required truthful follow-on:
  - `delivery-report-bridge -> final-local-review`
  - then one explicit `experience-sedimentation` check

See also:
- `references/board-closure-verdict.md`

## Stage-layer objects

### `stage-handoff.<stage>.md`
Thin parent-to-child handoff.

Current owner / placement:
- semantic owner: `parent`
- runtime placement: `parent-executed`

It must be a **compiled minimal workset**, not a copied parent context.

Default instance location:
- current round `objects/`

At minimum it should carry:
- stage identity,
- current round root / output targets,
- one bounded stage-local question,
- current queue scope,
- hot refs,
- optional warm refs,
- cold path/index pointers,
- success vs blocked signals,
- required outputs.

### `stage-verdict.<stage>.md`
Thin child-to-parent verdict.

Current owner / placement:
- semantic owner: `child-stage`
- runtime placement: `must-isolated-produced`

Default instance location:
- current round `objects/`

Should only return:
- owner
- **stage-local** `result_class`
- artifact_refs
- `parent_consume.writeback_kind`
- minimum row patch fields when `writeback_kind = queue-item-writeback`
- smallest truthful next-stage recommendation

### `parent_consume.writeback_*`
This is the minimal seam the parent may consume back into the board.
Allowed forms are only:
- `queue-item-writeback`
- `no-coverage-delta`

If it is `queue-item-writeback`, it should carry only the minimum row patch:
- `finding_label`
- `coverage_state`
- `evidence_posture`
- `last_truth`
- `last_evidence_ref`
- `next_gate`

If it is `no-coverage-delta`, the child is explicitly saying:
- stage-local truth changed,
- but repo coverage counters / board rows should not be reclassified from the child side.

Important:
- child recommendation is not repo closure judgment
- child verdict must not emit `round_status`, `repo_status`, `coverage_snapshot`, or `repo-closed`
- the parent must first consume `parent_consume.writeback_*`, then re-enter board + queue continuation + closure review

### `attempt-receipt.<repo>.<finding>.md`
Finding-level truth receipt.
Used mainly by finding replay.

Current owner / placement:
- semantic owner: `child-stage`
- runtime placement: `must-isolated-produced`

Default instance location:
- current round `objects/`

## JSON rule

JSON is allowed only as a thin bridge:
- index
- shadow fields
- executor parameter bridge

It must not become the main semantic control surface.
