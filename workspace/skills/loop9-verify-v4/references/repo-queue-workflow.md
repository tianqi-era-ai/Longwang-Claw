# Repo queue workflow (active V4.4 cut)

## Purpose

This ref freezes one active reading:

> the parent workflow is now **repo queue first**,
> not a single-active-finding glamour loop.

One repo round now means:
- freeze the repo's current-round in-scope queue,
- keep moving queue truth row by row,
- and only emit closure-side objects after the whole queue is terminal.

Companion reading:
- `references/repo-execution-core.md` freezes that this queue-first parent loop is the active stable repo-complete entry, not a hidden second runner.

## Start-side freeze

The current production start-side order is:
- repo intake / repo re-entry
- `repo-selection-pack`
- parent selection accept/reject
- current round root fix
- `repo-start-pack`
- parent accept/reject
- freeze `current queue posture`
- freeze `next queue item`
- freeze `next gate`

Exact queue-posture labels may evolve,
but the frozen meaning should stay thin:
- what is the queue's current truthful posture,
- which row moves next,
- and which gate/stage the parent is opening now.

## Queue-first parent loop

After the start side is accepted, the default parent loop is:

1. read current `repo-task-brief`
2. read current `repo-findings-board`
3. confirm the next truthful queue move
4. freeze `next queue item + next gate`
5. compile `stage-handoff.<stage>.md`
6. run exactly one bounded child stage
7. consume `stage-verdict.<stage>.md`
8. apply thin board writeback
9. refresh `repo-findings-board`
10. if any row is still unfinished:
   - freeze refreshed `current queue posture`
   - freeze refreshed `next queue item`
   - freeze refreshed `next gate`
   - continue the queue
11. only if every in-scope row is terminal:
   - run `repo-closure-review`
   - freeze `coverage_snapshot`
   - project `external-readout`
   - emit `repo-round-verdict`

## What counts as queue movement

Real queue movement means one of:
- one row became terminal this round,
- one row truthfully changed into a fresh blocked/manual-needed posture,
- one shared unblock changed a row cluster from `not-openable` to `replay-openable`,
- the next queue item/gate changed because of truthful parent consume,
- the board's unfinished picture changed in a visible way.

These do **not** count as queue movement by themselves:
- one isolated child started,
- one pretty receipt appeared for only one row,
- one historical proof looked reusable,
- or one old `historical-kept` pointer was re-read.

## Relation to child stages

Child stages remain bounded.
They still answer only stage-local questions.

But the parent may no longer mistake:
- `one child finished`
for
- `repo workflow finished`.

The child owns only stage-local verdict.
The parent owns queue continuation.

## When one queue row resists the first replay

One failed first pass does **not** automatically mean the row should freeze as `fresh-blocked`.

Default parent reading:
- separate transport/budget failure from semantic finding evidence
- if the runtime is alive, inspect whether the row is actually missing seed, auth, live ids, or other cheaply materializable prerequisites
- rerun after the smallest truthful repair
- for mutation-style claims, require landing proof rather than trusting `HTTP 200`

Companion ref:
- `references/agentic-blocker-diagnosis.md`

## When several rows resist for the same reason

If multiple unfinished rows are all parked behind the same cheap blocker, the parent may:
- pause premature row-local freezing,
- run one bounded shared unblock such as install completion, seed import, or honest auth materialization,
- then reopen the affected rows one by one.

Important boundary:
- the shared unblock is queue movement,
- but it is not row-local confirmation,
- and it does not skip the need for per-row terminal dispositions.

Do not:
- duplicate the same cheap unblock work independently for every row
- freeze the old shared blocker as several fake row-local negatives

## Hard prohibitions

Do not drift back to any of these:
- `freeze one active finding -> run one child -> closure`
- closure-side objects appearing while unfinished rows still exist
- `historical-kept` acting like queue completion
- `external-readout` becoming the first place queue truth is compressed
- one loud row retaking control of repo truth

## One-sentence operating posture

> Start the repo truthfully.
> Freeze the queue truthfully.
> Move one queue item at a time.
> Close only after every row is terminal.
