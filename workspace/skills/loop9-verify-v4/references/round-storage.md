# Round storage discipline (production first cut)

## Purpose

This ref freezes where a live `loop9-verify-v4` round should write:
- round-local objects,
- stage-local outputs,
- and raw artifacts.

One-line freeze:

> one bounded live repo round = one current round root,
> and both parent + child runtime outputs must land back into that same root.

## Current round root

Before repo-mainline child work begins, the parent should already have one active round root.

Special pre-start exception:
- `repo-selection-pack` may run before current round root exists
- its request / proposal / acceptance should therefore live in one bounded pre-start intake surface chosen by the parent
- once selection is accepted, normal current-round root discipline begins

Default shape:
- `reports/.../rounds/<repo>/<round>/`

Inside it, keep exactly three first-cut locations:
- `round-summary.md`
- `objects/`
- `artifacts/`

## Stable layer vs runtime layer

### Stable layer
These stay as rule/type/reference surfaces only:
- `skills/loop9-verify-v4/references/*.md`
- report-level contract objects such as `objects/*.contract.md`
- other long-lived canonical type definitions

Do **not** dump live round instances there.

### Runtime layer
Live round instances belong under the current round root.

That means the current round should own:
- parent-generated instance objects,
- child-generated verdict/receipt objects,
- and raw evidence or artifact pointers.

Pre-start selection note:
- `repo-selection-proposal.*.md` and `parent-selection-acceptance.*.md` may exist briefly before round-root creation
- they are the one bounded pre-start exception rather than proof that live round objects should move back out of round roots

### Report-level experience layer
There is one additional post-closure layer that may exist outside the round root:
- report-root experience cards under `reports/.../<report-root>/experience/cards/`

This layer is allowed because it is:
- post-closure
- explanatory
- non-gating for repo completion

It is **not** a second live round root.
It does not replace:
- current round `objects/`
- current round `artifacts/`
- or the family-facing `learning-delta` object

## What belongs in `objects/`

### Parent-owned round instances
Keep these in the current round `objects/`:
- `repo-task-brief.*.md`
- `repo-state-relocation.*.md`
- `repo-findings-board.*.md`
- `repo-closure-review.*.md`
- `external-readout.*.md`
- `repo-round-verdict.*.md`

### Child-owned round instances
Also keep these in the same current round `objects/`:
- `stage-handoff.<stage>.*.md`
- `stage-verdict.<stage>.*.md`
- `attempt-receipt.*.md`
- `learning-delta.*.md`
- other bounded round-local writebacks that are still semantic objects rather than raw evidence

Repo-local experience cards are the exception that stay at report-root level rather than round-root level, because they are case-memory artifacts rather than live round-control objects.

## What belongs in `artifacts/`

Keep raw evidence in the current round `artifacts/`:
- HTTP headers / bodies
- stdout / stderr
- screenshots
- probe captures
- exported raw files

If the current round mainly reuses older evidence, prefer:
- a small `artifacts/README.md`, or
- explicit `artifact_refs`

instead of copying large raw bodies again.

## Parent read / child write default

The default production read/write posture is now:
1. parent compiles / runs `repo-selection-pack` in one bounded pre-start intake surface,
2. parent accepts selection and fixes the current round root,
3. parent refreshes the round-local `repo-task-brief` before board / stage work,
4. parent writes round-local objects there,
5. handoff exposes the same round root + expected output targets,
6. child writes verdict / receipt / artifacts back into that same round root,
7. parent consumes current-round objects first,
8. then follows explicit artifact refs if more evidence is needed.

## Hard boundary

- isolation changes runtime mode, **not** canonical storage root
- child work may not invent a second ad-hoc output tree as the canonical result location
- do not start dumping live instances into top-level contract/ref directories
- report-root experience cards are allowed only as post-closure explanatory memory; they may not impersonate round-root canonical control objects
- this rule is execution-facing, not a retroactive demand to relayout all historical rounds
- curated repo bundles such as `dax-pay-full-round/` may keep their own report shape as stage outputs, but they do **not** replace the current round-root discipline for active production-skill execution
