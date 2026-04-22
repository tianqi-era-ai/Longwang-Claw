# Parent closure chain (active V4.3 cut)

## Purpose

This ref freezes the last parent-owned chain after child work returns.

It exists to make one thing impossible to miss:

> `external-readout` may be isolated-produced,
> but closure truth still freezes only at the parent,
> and closure-side objects do not exist at all until the repo queue is truthfully complete.

This is not a second protocol.
It is the thin high-visibility compression of the active closure-side control surface.

## One-line freeze

> child returns stage-local truth + thin writeback;
> parent refreshes board;
> if any row is still unfinished, the parent keeps working the queue;
> only after every in-scope finding is terminal may the parent run `repo-closure-review`, freeze `coverage_snapshot`, project `external-readout`, emit `repo-round-verdict`, then continue with `delivery-report-bridge -> final-local-review -> explicit experience-sedimentation check`.
> Repo mainline is not `done` before that tail has been consumed.

## Frozen owner / placement chain

### `repo-closure-review`
- semantic owner: `parent`
- runtime placement: `parent-executed`
- role: parent-only closure judgment after queue completion

It freezes:
- `round_status`
- `repo_status`
- `coverage_snapshot`
- `closure_gates_remaining`
- `closure_note`

Hard gate:
- it may not be emitted while any in-scope finding is still `unfinished`

### `external-readout`
- semantic owner: `parent`
- runtime placement: `isolated-produced`
- role: projection-only outward summary

It may consume only:
- frozen `repo-closure-review`
- frozen `coverage_snapshot`
- accepted artifact / evidence refs

It may not:
- rejudge `round_status`
- rejudge `repo_status`
- invent a new `coverage_snapshot`
- silently promote historical evidence into current-round handling
- restate partial queue progress as repo completion
- reopen closure gates

### `repo-round-verdict`
- semantic owner: `parent`
- runtime placement: `parent-executed`
- role: final parent-owned round conclusion

Its truth source stays:
- frozen `repo-closure-review`
- frozen `coverage_snapshot`
- accepted next-step / artifact refs

It may cite `external-readout`,
but may not let outward wording become a new truth source.

## Frozen consume order

After any child stage returns, the parent closure-side order is now:
1. consume `stage-verdict.<stage>.md`
2. apply thin `parent_consume.writeback_*`
3. refresh `repo-findings-board`
4. check whether **every** in-scope finding now has a current-round terminal disposition
5. if not, keep queue progression in the parent layer and do **not** emit closure-side objects yet
6. if yes, run `repo-closure-review`
7. freeze `coverage_snapshot`
8. produce `external-readout` as projection-only
9. emit parent-only `repo-round-verdict`
10. compile `stage-handoff.delivery-reports.*`
11. consume `stage-verdict.delivery-reports.*`
12. run `final-local-review`
13. run one explicit experience-sedimentation check (`no-new-delta` or one thin `learning-delta`)
14. only then freeze `repo-mainline-done` or a truthful blocked-tail boundary

## Hard prohibitions

Do not allow any of these drifts:
- `external-readout -> repo-closure-review`
- child verdict -> `repo-round-verdict` directly
- `repo-round-verdict` replacing closure review
- `external-readout` silently rewriting repo closure truth
- closure-side objects appearing before queue completion
- coverage numbers changing first in outward wording and only later in parent closure objects
- `repo-round-verdict` being narrated as repo-mainline completion before the delivery tail is consumed
- skipping the explicit experience-sedimentation check just because the likely outcome is `no-new-delta`

## One-sentence operating posture

> Board first.
> Queue truth first.
> Parent closes repo truth only after the full queue is terminal.
> Outward wording comes after that.
> Repo mainline then finishes on local delivery bundle review plus an explicit sedimentation check, not on publish.
