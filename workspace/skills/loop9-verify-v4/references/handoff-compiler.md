# Handoff compiler discipline (production first cut)

## Purpose

This ref freezes how the parent should compile `stage-handoff.<stage>.md` into a **minimal workset**, instead of copying a larger parent context into the child.

One-line freeze:

> `stage-handoff.<stage>.md` is a compiled minimal-workset packet,
> not a second parent summary,
> not a board dump,
> and not a disguised bigger context.

## Required handoff layers

Every compiled handoff should keep the same thin order:

1. **stage identity**
   - stage
   - repo
   - parent owner
   - current round root
2. **bounded question**
   - the single stage-local question the child is allowed to answer
3. **current queue scope**
   - why this queue move is active now
   - current queue posture / current queue item only if the stage really needs them
   - current next gate / stop line
4. **hot refs**
   - must-read-now refs only
   - default target: roughly `2~5` refs, ideally closer to `3`
   - when the stage still depends on repo posture, the current round `repo-task-brief.*.md` should usually be the first hot ref
5. **warm refs**
   - read only if hot refs are not enough
   - default target: `0~3` extra refs
6. **cold refs / index pointers**
   - path pointers only
   - no large body paste
   - used only when the bounded question still cannot be answered from hot+warm refs
7. **success vs blocked signals**
   - the smallest truthful receipt / blocked criteria for this stage
8. **required outputs**
   - exact verdict / receipt / artifact refs the child should return
   - expected round-local write targets (`objects/` vs `artifacts/`)

## Default exclusions

Do not compile these into the handoff body by default:
- full repo-findings-board prose
- thick historical retrospectives
- large log bodies
- unrelated findings or sibling-stage details
- whole report sections when a ref path is enough
- more than one competing stage worth of context

## Special stricter case: `repo-start-pack`

`repo-start-pack` is not a child-stage handoff, but its compiled input should now be treated as **even stricter** than an ordinary stage handoff.

Current production reading:
- it gets only start-side minimal workset,
- not a softened repo-wide context,
- and closure-side objects are not allowed even as cold pointers.

So if a future compiler packet for `repo-start-pack` starts asking for:
- `repo-closure-review`,
- `external-readout`,
- `repo-round-verdict`,
- old closure prose,
- or thick historical replay/distillation bodies,

that should be read as `compiler drift / invalid start input`, not as permission to widen the packet.

## Stage-specific default posture

### `env-bootstrap`
Prefer compiling:
- current round `repo-task-brief` ref
- current env-side bounded question
- current queue item only if env truth is specific to that row
- env root / base URL / current env truth
- strongest env refs only
- artifact paths for thick logs rather than pasted log bodies

### `finding-replay`
Prefer compiling:
- current round `repo-task-brief` ref
- frozen current queue item
- canonical PoC ref
- current env verdict ref
- one strongest historical receipt ref if needed
- fresh success / blocked signals

Do not dump unrelated board detail into replay handoff.

### `distillation`
Prefer compiling:
- current round `repo-task-brief` ref
- exact distillation question
- current round closure refs
- only the few older card refs that truly matter
- explicit `no-new-delta` / `observed-delta` / upgrade judgment boundary

Do not dump full historical case archives into the distillation handoff.

## Child read order

The child should read in this order:
1. handoff body
2. hot refs
3. warm refs only if still needed
4. cold refs only by explicit necessity

If the child ends up reading much more than this, treat it as:
- either parent compiler drift,
- or a sign the stage should stay isolated and/or be recompiled more thinly next round.

## Hard boundary

- handoff compilation stays parent-owned
- isolation does **not** mean bigger context
- isolation does **not** replace the repo-level start anchor; if repo posture still matters, expose the current `repo-task-brief` rather than pasting more board prose
- child may not use isolation as permission to absorb the whole repo history
- handoff should expose one current round root, not invent a second output tree
- if a path pointer is enough, do not paste the body
- if the bounded question is still unclear after hot+warm refs, prefer a truthful blocked/handoff outcome over silent context expansion
