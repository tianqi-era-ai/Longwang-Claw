# Board / closure / verdict semantics (active V4.3 cut)

## Purpose

This ref freezes one active reading:

> `repo-findings-board` must expose the current-round disposition of **every** in-scope finding;
> `repo-closure-review` may exist only after **all** in-scope findings have entered a current-round terminal disposition;
> `external-readout` and `repo-round-verdict` may only project that already-frozen closure truth.

This is not a new protocol layer.
It is the thin active compression for the P3 repair cut.

## `repo-findings-board`

The board is the repo-wide current-round truth surface.

Minimum active requirement:
- one row per in-scope finding
- one explicit `current_round_disposition` field per row
- one visible repo-level unfinished counter
- one visible next queue move / next queue item

Allowed row posture:
- `unfinished`
- or an explicit current-round terminal disposition such as:
  - `fresh-confirmed`
  - `fresh-blocked`
  - `fresh-manual-needed`
  - `fresh-skip-by-policy`
  - or another equally explicit terminal label

Compatibility note:
- `historical-kept`
- older verification refs
- old evidence posture
may still appear as background fields or pointers,
but they may not count as this round's disposition and may not support repo closure.

Execution note:
- focus row / next queue item may still exist as an execution cursor,
- but it is no longer the semantic center of repo truth.

## `repo-closure-review`

`repo-closure-review` is no longer a soft partial-progress summary.
It is a **post-queue completion freeze**.

It may exist only when:
- every in-scope finding has a current-round terminal disposition
- `terminal_disposition_count == in_scope_findings_total`
- no row is closure-supported only by `historical-kept` or old verification

If any finding is still `unfinished`,
then the truthful state is:
- keep working the queue
- refresh the board
- do **not** emit `repo-closure-review`
- do **not** emit `external-readout`
- do **not** emit `repo-round-verdict`

## Frozen `coverage_snapshot`

Once closure is allowed, the frozen `coverage_snapshot` should at minimum expose:
- `in_scope_findings_total`
- `terminal_disposition_count`
- `fresh_confirmed_count`
- `fresh_blocked_count`
- `fresh_manual_needed_count`
- `fresh_skip_by_policy_count`
- `remaining_unfinished_count`

Older compatibility counters like:
- `historical_kept_count`
- `not_yet_replayed_count`
may survive only as migration/debug background,
not as closure support.

## `external-readout`

`external-readout` stays projection-only.
It may consume only:
- frozen `repo-closure-review`
- frozen `coverage_snapshot`
- accepted artifact refs

It may not:
- invent a new closure truth
- restate partial queue progress as repo completion
- silently promote old evidence into current-round handling
- replace per-disposition truth with one glamorous fresh replay story

## `repo-round-verdict`

`repo-round-verdict` stays the final parent-owned round conclusion.

Its truth source is only:
- frozen `repo-closure-review`
- frozen `coverage_snapshot`
- accepted artifact refs

It must be able to answer:
- how many findings were in scope this round
- how many reached each current-round terminal disposition
- whether anything remained unfinished when closure was attempted
- what the next truthful follow-on is, if any

If it cannot answer that,
it is not yet a truthful repo-level verdict.

## Hard prohibitions

Do not allow any of these drifts:
- `historical-kept` acting as a current-round terminal disposition
- one fresh replay carrying repo closure for untouched rows
- `repo-closure-review` emitted while unfinished rows still exist
- `external-readout` becoming the first place where closure truth appears
- `repo-round-verdict` hiding the per-row current-round disposition matrix

## One-sentence operating posture

> Board first.
> Queue truth first.
> Closure only after every row is terminal.
> Readout and verdict only after closure is already frozen.
