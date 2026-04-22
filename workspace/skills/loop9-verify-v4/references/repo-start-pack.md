# Repo-start-pack / parent-draft-pack (production current cut)

## Purpose

This ref freezes the current production start-side default for `loop9-verify-v4`.

One-line freeze:

> repo start side should no longer begin as three scattered parent-inline drafting acts.
> The current production default is now:
> `repo-selection-pack -> parent selection accept/reject -> current round root fix -> repo-start-pack -> parent accept/reject -> queue-scope freeze`.

## What `repo-start-pack` is

`repo-start-pack` is a **parent-owned start worker**.

Current owner / placement:
- semantic owner: `parent`
- runtime placement: `isolated-produced`

It is not:
- a second parent,
- a child stage,
- a closure object,
- or a hidden orchestrator.

Its job is only to prepare the current repo start side in one bounded cut.

## Current required outputs

A valid `repo-start-pack` should return exactly four things into the current round root:
1. `repo-state-relocation.*.md`
2. `repo-task-brief.*.md`
3. `repo-findings-board.*.md`
4. `parent-draft-pack.*.md`

The first three remain parent-owned canonical start-side objects.

The fourth is the thin parent consume surface.

## Output discipline / round-root boundary

Current production reading is now stricter than the first cut:
- those four outputs are the **entire valid return set**,
- they must all land under the **current round root**,
- and the packet must remain purely **start-side + proposal-only**.

Hard meaning:
- `repo-start-pack` may not return closure objects,
- may not return repo verdict objects,
- may not point back to old closure-side refs as if they were part of the start pack,
- and may not mix valid start-side drafts with stale closure material in one packet.

## What `parent-draft-pack` is

`parent-draft-pack` is the thin accept/reject packet returned from `repo-start-pack`.

Current owner / placement:
- semantic owner: `parent`
- runtime placement: `isolated-produced`

At minimum it should carry:
- refs to the three start-side drafts,
- `proposed_queue_posture`,
- `proposed_next_queue_item`,
- `proposed_next_gate`,
- minimal rationale,
- explicit note that these are proposals only, not frozen truth.

It may **not** carry or imply:
- accepted `round_status` / `repo_status`,
- `coverage_snapshot` freeze,
- `repo-closure-review` truth,
- `repo-round-verdict` wording,
- child-stage verdicts as if they were already consumed,
- or any wording that silently upgrades proposal into accepted truth.

## Start-only minimal input discipline

`repo-start-pack` should now be compiled as an explicit **start-only minimal workset**.

## Relation to selection stage

`repo-start-pack` now starts only **after** selection has already been accepted.

Current hard meaning:
- the allowed selection-side input is the accepted thin basis
- not the raw multi-repo narration
- and not the full selection request/proposal history unless a thin ref is truly necessary

Preferred selection-side inputs:
- `parent-selection-acceptance.*.md`
- optionally one thin `repo-selection-proposal.*.md` ref if the brief really needs it

Do **not** reopen:
- full candidate ranking prose
- thick why-not-this-other-repo narration
- thick selection comparison dumps

### Start-only allowlist
By default it may read only:
- repo intake / `repo_ref` / repo identity,
- accepted selection basis / `parent-selection-acceptance`,
- current round root and round-local output targets,
- thin current constraints / explicit non-goals / stop line,
- only the hot refs needed to draft:
  - `repo-state-relocation`
  - `repo-task-brief`
  - `repo-findings-board`
  - `parent-draft-pack`

Current hot-ref posture:
- prefer roughly `2~5` refs, ideally closer to `3`,
- path/ref first,
- excerpts over thick pasted bodies,
- and only repo-start-side material, not closure-side interpretation.

### Hard denylist
These may **not** enter the default `repo-start-pack` input, not even as warm refs or cold pointers:
- `repo-closure-review`,
- `external-readout`,
- `repo-round-verdict`,
- frozen `coverage_snapshot` material,
- old round closure prose,
- old `V4.1` closure material,
- full replay receipts dump / raw child log bodies,
- thick multi-repo comparison narration,
- raw selection request/proposal dumps beyond thin accepted basis,
- thick historical round retrospectives unrelated to current start-side drafting.

### Compiler boundary
If the parent notices that `repo-start-pack` seems to "need" closure-side material to proceed,
the correct reading is now:
- `compiler drift / invalid start input`,
- not silent context widening.

So the parent should recompile a thinner start-only packet rather than feeding the worker older closure truth.

Hard meaning:
- it is a start worker, not a whole-round brain,
- and it is no longer allowed to be a soft reader of older closure material.

## Hard reject / stale-drift gate

Treat the whole return packet as `invalid-start-draft / stale-drift` and reject it if any of these appear:
- any closure-side object or closure-side prose,
- any `repo-closure-review`, `external-readout`, or `repo-round-verdict` ref,
- any old-round / old-closure / old `V4.1` ref presented as current start material,
- any proposal wording that pretends queue scope or repo closure is already frozen truth,
- any packet that mixes valid start-side drafts with stale closure material,
- or any packet that fails to return the full start-side set (`repo-state-relocation / repo-task-brief / repo-findings-board / parent-draft-pack`).

Default fail-closed meaning:
- do **not** half-accept the mixed packet,
- do **not** cherry-pick one pretty draft out of a stale packet,
- write a thin parent reject decision,
- then recompile thinner or rewrite the start-side drafts cleanly before parent freeze.

## Parent consume / freeze rule

After `repo-start-pack` returns, the parent must still do all of these itself:
1. accept or reject the returned drafts,
2. freeze `current queue posture`,
3. freeze `next queue item`,
4. freeze `next gate`.

The worker may:
- draft,
- compress,
- propose,
- pre-structure.

The worker may **not**:
- silently freeze queue scope,
- silently choose the next child stage as accepted truth,
- silently conclude repo closure,
- bypass parent consume.

## Queue-scope freeze point

Current queue scope is only:
- `current queue posture`
- `next queue item`
- `next gate`

The final freeze point for all three is still:
- `parent-only`

This rule remains true even though the start-side drafts are isolated-produced.

## Current relation to parent minimal core

`repo-start-pack` exists to make the parent smaller, not empty.

After this cut, the parent minimal core should read as:
- selection acceptance / repo choice freeze,
- current round root fix,
- draft accept/reject,
- queue-scope freeze,
- handoff compilation,
- child runtime binding,
- child verdict consume,
- repo closure review,
- external readout ownership,
- repo-round verdict.

If the parent starts reabsorbing the whole start-side drafting body,
this cut has drifted.

## Hard rules

- `repo-start-pack` is now the current production default repo-start path
- it may return only the current-round start-side draft set plus proposal-only `parent-draft-pack`
- any closure-side drift or accepted-truth wording makes the whole packet `invalid-start-draft / stale-drift`
- it does not replace the parent
- it does not freeze queue scope
- it does not choose closure truth
- it does not start child work on its own
- it must stay thinner than the parent it is helping
- if a path/ref is enough, do not expand it into thick prose

## Naming discipline

Current production naming should stay on:
- `repo-state-relocation`

Do not drift back to mixed `repo-state-relocator / repo-state-relocation` wording inside current refs.
