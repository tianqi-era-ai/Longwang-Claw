# Parent minimal core (active V4.4 selection/start cut)

## Purpose

This ref freezes what the parent still must keep after
`repo-selection-pack` and `repo-start-pack` have entered the production path.

One-line freeze:

> The parent should get smaller after `repo-selection-pack` and `repo-start-pack`,
> but not hollow.
> It still keeps the only freeze point for repo choice, queue scope, child binding,
> closure truth, and final repo verdict.

## What the parent still must keep

Current parent minimal core is only:
1. compile / invoke `repo-selection-pack` when a repo flow starts or re-entry needs selection checking
2. accept / reject `repo-selection-proposal`
3. freeze final repo choice, including explicit parent override when needed
4. current round root fix
5. accept / reject of `repo-start-pack` drafts
6. freeze `current queue posture`
7. freeze `next queue item`
8. freeze `next gate`
9. compile `stage-handoff.<stage>.md`
10. freeze child runtime placement
11. consume `stage-verdict.<stage>.md`
12. own blocker diagnosis / bounded self-repair choice when first-pass friction is still ambiguous
13. refresh `repo-findings-board`
14. decide whether the queue continues or closure is now allowed
15. run `repo-closure-review`
16. freeze the closure-side `coverage_snapshot`
17. own `external-readout`
18. run `repo-round-verdict`

## What the parent no longer needs to do by default

The parent no longer needs to default to inline drafting of:
- cross-repo selection comparison
- `repo-state-relocation`
- `repo-task-brief`
- `repo-findings-board`

Those may now be isolated-produced first,
then accepted/frozen by the parent.

Selection-specific reading:
- explicit repo still stays semantically parent-owned
- but the parent no longer needs to inline the whole selection check by default

## Queue-scope freeze rule

Even after `repo-start-pack` has returned,
only the parent may freeze:
- `current queue posture`
- `next queue item`
- `next gate`

This is the current smallest hard owner surface that may not be pushed outward.

## Closure-chain rule

The parent still owns the last closure chain in this order:
- verdict consume / writeback
- board refresh
- queue continuation judgment
- `repo-closure-review`
- closure-side `coverage_snapshot` freeze
- `external-readout` ownership
- `repo-round-verdict`

`external-readout` may be isolated-produced,
but only as projection of already-frozen parent closure truth.
It may not rejudge `round_status`, `repo_status`, or `coverage_snapshot`.

## Current hard boundary

The parent may become thinner.
It may not become:
- a passive mailbox,
- a shell that only forwards child outputs,
- or a reviewer that signs whatever drafts returned.

If it stops owning queue-scope freeze or closure truth,
this cut has drifted.

## One-sentence operating posture

> `repo-start-pack` prepares the repo start side.
> `repo-selection-pack` and `repo-start-pack` make the parent smaller, not empty.
> The parent still owns selection acceptance, queue-scope freeze, child binding, closure review, and final verdict.
