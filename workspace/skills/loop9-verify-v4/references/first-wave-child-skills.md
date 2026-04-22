# First-wave child skill freeze line

## Official first-wave child skills

Only these 4 are frozen as independent child skills for V4 first wave:
1. `loop9-verify-v4-env-bootstrap`
2. `loop9-verify-v4-finding-replay`
3. `loop9-verify-v4-distillation`
4. `loop9-delivery-reports`

These child skills are execution surfaces, not one-platform-only runtime names.

Active reading:
- on any platform that supports child agents / isolated workers, these are the default isolation targets
- the skill names stay canonical, while the runtime primitive used to host them is adapter detail

## Built-in must-isolated stage that is **not** a child skill

`repo-selection-pack` is now also `must-isolated`,
but it stays:
- a built-in pre-start stage
- not an independent child skill
- and not a second-wave child-skill admission

## Kept in parent layer

These remain in the parent skill for now:
1. final repo choice freeze / selection acceptance
2. `repo-state-relocation`
3. `repo-closure-review`
4. `external-readout`
5. `repo-round-verdict`
6. `final-local-review`

## Why

Because the official first-wave skills are currently the most bounded:
- easier to feed with thin handoffs,
- easier to isolate in a smaller context window,
- less likely to steal repo-level owner.

`repo-selection-pack` is the special pre-start exception:
- bounded enough to require isolation,
- but still too close to parent repo-choice ownership to promote into a standalone child skill right now.

The remaining parent-layer items still depend too heavily on repo-level owner, active-scope freeze, tie-break, closure judgment, and outward truth projection.
