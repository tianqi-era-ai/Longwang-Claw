# Historical proof/sample selection background (inactive by default)

## Status

This file used to describe how the parent chose the **next proof/sample repo**.

That reading is **no longer the active default** for `loop9-verify-v4`.

Current active contract is now:
- `repo-complete only`
- one repo in -> finish that repo's current-round in-scope finding queue -> then repo closure

So this file is now kept only as **historical repair background**.
It may help explain why older bounded rounds were chosen,
but it must not drive current default execution.

Active replacement now lives at:
- `references/repo-selection.md`

## Active replacement rule (after P2 landed)

When `repo_ref` is not explicit, the parent should now answer:

> which repo most needs a truthful repo-complete current-round finish?

Not:

> which repo best answers the current proof gap?

Current active bridge rules are:
- explicit `repo_ref` always wins
- prefer repos that still need repo-complete finish / report / delivery
- do not auto-select old proof samples or repos that already look fully verified / ready-for-delivery by default
- do not use `env-proof / replay-proof / full-round-proof / control-sample` as the main driver for auto-selection

## What remains historical-only

The old proof/sample classes remain useful only as background labels when reading older repair artifacts:
- `env-proof`
- `replay-proof`
- `full-round-proof`
- `control-sample`

They may still help explain:
- why an older bounded round chose one repo over another
- what kind of uncertainty an older repair lane was trying to reduce
- how a historical sample should be interpreted

But they no longer justify:
- active default repo selection
- partial-current-round repo closure
- keeping an already-finished sample repo in the default verify mainline

## Hard boundary

- do not let this file silently pull the parent back into `proof-gap-first`
- do not let historical sample tags override a repo that still needs repo-complete finish
- do not use this file to reintroduce `control-sample` as a default mainline
- if research/proof mode is ever needed again, it should come from a separate explicit entry rather than from the current active skill default
