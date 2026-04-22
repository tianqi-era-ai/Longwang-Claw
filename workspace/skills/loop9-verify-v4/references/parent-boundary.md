# Parent boundary (high-visibility)

This is the **one-eye parent boundary surface** for the current production `loop9-verify-v4` family.

Read this before drilling into the more detailed refs.

Its job is not to become a second protocol.
Its job is to keep the current parent-owned meaning and first-version non-goals impossible to miss.

## First split to remember

Before drilling into stage detail, freeze this first:
- `semantic owner` = who owns meaning, accept/reject, final freeze, and repo-level truth
- `runtime placement` = where the object or stage is produced / executed

These are no longer allowed to collapse into one field.

Immediate corollary:
- `parent-owned` may still be `isolated-produced`
- `isolated-produced` does **not** imply `child-owned`
- final freeze of repo-level truth remains parent-only

See also:
- `references/owner-placement-matrix.md`

## What the parent always owns

The parent layer always owns:
- repo intake framing
- compile / invoke `repo-selection-pack`
- accept / reject `repo-selection-proposal`
- final repo choice freeze
- explicit disclosure of child-runtime posture when `must-isolated` / `isolated-produced` work is expected
- repo truth relocation
- accept / reject of `repo-start-pack / parent-draft-pack` drafts returned from isolated runtime
- current round root fix
- current-round `repo-task-brief` refresh / freeze
- `repo-findings-board` maintenance / freeze
- queue posture freeze after `repo-start-pack` return
- next queue item choice
- next gate choice
- child runtime binding
- `stage-handoff.<stage>.md` compilation
- round-local output target fixing
- same-repo continuation ownership while isolated child work is running
- repo-level closure review
- freeze of the closure-side `coverage_snapshot` before any outward projection
- external readout ownership
- repo-round verdict
- `delivery-report-bridge` handoff compilation / verdict consumption
- `final-local-review` completion freeze
- explicit post-tail `experience-sedimentation` check
- final `repo-mainline-done` / truthful blocked-tail freeze

If one of these is drifting into a child, pull it back.

Important:
- ownership here is **semantic owner**
- not automatic parent-inline execution

## What the parent may not do silently

The parent may not silently:
- reinterpret explicit skill invocation as if no bounded child-work authorization had been given
- ignore clear equivalent authorization phrases such as `subagent`, `delegation`, `parallel agent work`, `子代理`, `委派`, `隔离执行`, or `后台任务`
- inline a `must-isolated` stage without first saying whether child execution is confirmed, still blocked on authorization, or forced into an explicit inline exception
- normalize a platform/runtime restriction into “parent-inline by default”
- narrate `repo-round-verdict` as if the repo mainline were already done while the delivery tail is still pending

If a stricter platform/runtime policy still blocks child execution,
the parent must either:
- obtain the required extra authorization / confirmation, or
- declare a visible `inline-exception`

What it may not do is drift inline without telling the operator.

## What children may never steal

Children may not:
- conclude repo closure
- emit repo-level `round_status`, `repo_status`, or frozen `coverage_snapshot`
- directly chain to another child
- use isolation as permission for a bigger hidden context
- write outside the same frozen current round root
- reinterpret `historical accepted` as current-round handling
- reinterpret `historical-kept` as a terminal disposition for this round
- replace the parent start surface with the loudest receipt or the loudest finding
- relabel a parent-owned + isolated-produced draft as child-owned repo truth
- let `repo-start-pack` proposals silently become frozen queue truth
- freeze next queue item / next gate
- let `external-readout` silently become a second closure-review
- force the same repo mainline to depend on a fresh user turn / manual conversation continuation before the parent has consumed the child verdict
- treat `repo-round-verdict` as equivalent to `repo-mainline-done` before the delivery tail and explicit sedimentation check have been consumed

Child outputs stay bounded to:
- stage-local truth
- thin writeback
- receipt / blocked / fixed-point / handoff information

## What does not count as real progress

These do **not** count as real progress by themselves:
- started
- planning
- shell-created
- isolated session launched
- more objects / fields / documents
- louder logs
- better wording
- one child receipt that never changes current-round queue truth

Current real progress still requires:
- one finding entering a current-round terminal disposition
- blocked/manual-needed truth becoming explicit at the board layer
- or a true parent-owned board / closure movement caused by those truths

## First-version non-goals that remain frozen

Current first-version still does **not** admit:
- thick orchestrator / thick job system / thick queue runtime
- publish / cron / multi-repo batch orchestration inside this family
- proof-sample / control-sample selection as active default behavior
- second-wave child skill expansion
- thick sample registry / thick repo scoreboard / thick ranking table
- generalized maturity claims
- automatic promotion of V4-native learning deltas beyond `observed`

## One-sentence operating posture

> Parent owns repo-level meaning, repo selection, queue progression, control surface, and closure.
> `repo-selection-pack` may run must-isolated, but final repo choice freeze stays parent-owned.
> Some parent-owned objects may still be isolated-produced.
> Child does only bounded stage-local work and returns thin verdict / receipt.
> Real progress is truth-backed and must become visible again as current-round queue movement at the parent board / closure layer.

## Use with

Read this together with:
- `references/current-status.md`
- `references/owner-placement-matrix.md`
- `references/repo-selection.md`
- `references/repo-selection-pack.md`
- `references/parent-io-contract.md`
- `references/parent-closure-chain.md`
- `references/stage-chain.md`
- `references/runtime-isolation.md`
- `references/handoff-compiler.md`
