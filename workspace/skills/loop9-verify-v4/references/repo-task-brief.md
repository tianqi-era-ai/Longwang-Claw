# Repo-task-brief as repo-level start anchor (production first cut)

## Purpose

This ref freezes how `repo-task-brief.*.md` should behave inside an active `loop9-verify-v4` round.

One-line freeze:

> `repo-task-brief` is the parent-owned **repo-level start anchor**.
> It should be refreshed after `repo-state-relocation + current round root fix`,
> before board refresh / child choice,
> and the next cycle should start from it rather than from whichever queue item or receipt was loudest last turn.

## Required minimum fields

A production-strength `repo-task-brief` should carry exactly the repo-level truths that help the parent start correctly again.

### 1. `repo identity`
At minimum:
- `repo_ref`
- `selection_mode`
- `parent-selection-acceptance` ref when it exists
- repo root / evidence root when they matter
- current parent owner

### 2. `why this repo now`
At minimum:
- why this repo is active in this round
- the accepted thin selection basis
- not the full multi-repo comparison narration
- what repo-complete need currently justifies it

### 3. `current repo truth`
At minimum:
- the current repo-level posture
- whether this is fresh / continuation / reposition / delivery-finish
- the dominant repo-level blocker family or progress family

### 4. `this-round repo goal`
At minimum:
- the repo-level truth this round is actually trying to move
- the current bounded target for the round

### 5. `explicit non-goals`
At minimum:
- what this round must not drift into
- what old surfaces / tempting side paths must not retake control

### 6. `current active stage guess`
At minimum:
- the parent's current best stage guess
- why that stage is more correct than the most obvious alternatives

### 7. `minimum refs`
At minimum:
- only the few refs the next parent cycle or child handoff truly needs
- prefer roughly `3~7` refs
- prefer anchors / indices / decisive receipts, not large pasted bodies

### 8. `round exit condition`
At minimum:
- when this brief has done its job for the current round
- when it must be refreshed again because repo truth / stage guess changed materially

## Runtime use order

The parent should treat `repo-task-brief` as part of the default repo start sequence:

1. repo select / repo re-entry
2. run `repo-selection-pack`
3. accept or reject `repo-selection-proposal`
4. current round root fix
5. run `repo-start-pack`
6. accept or reject the returned start-side drafts
7. freeze `current queue posture / next queue item / next gate`
8. compile `stage-handoff.<stage>.md` if child work is needed

Inside `repo-start-pack`, the brief is still refreshed together with:
- `repo-state-relocation`
- `repo-findings-board`
- `parent-draft-pack`

After child return:
- parent still does writeback -> board refresh -> queue continuation judgment first,
- then decides whether the repo brief must be refreshed because repo truth / stage guess changed enough,
- and the next cycle should start from that refreshed brief instead of from leftover child-local noise.

## Boundary with other objects

### It is not `repo-findings-board`
It may say which queue move currently matters most,
but it must not absorb the full repo-wide coverage board.

### It is not `stage-handoff`
It may hold the current stage guess,
but it must not turn into a stage-local work packet.

### It is not `repo-closure-review`
It explains why this repo should start this way now,
not the final repo closure judgment.

### It is not a thick summary page
If the brief starts getting thick,
cut body size and keep refs thinner instead of expanding prose.

## Default interaction with the handoff compiler

When child work still depends on repo posture,
the parent should usually expose the current `repo-task-brief` as the **first hot ref**,
before heavier board / receipt / artifact refs.

This helps keep the child anchored to:
- why this repo is active now,
- current repo truth,
- current round goal,
- and what not to drift into.

## Hard rules

- do **not** let the last queue item or last child receipt become the default repo start surface
- do **not** let `repo-task-brief` swallow board / handoff / closure-review duties
- if repo truth or active stage guess changes materially, refresh the brief instead of pretending the old one is still good enough
- if a path/ref is enough, do not paste larger bodies
- the brief exists to stabilize the parent's next start, not to become a repo-level万能总表
