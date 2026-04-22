# Current status

## Active contract snapshot

Current active `loop9-verify-v4` contract is now frozen as:
- `repo-complete only`
- daily-work / delivery-oriented by default
- one repo in -> all current-round in-scope findings processed -> then repo closure / readout / verdict
- repo intake now begins with a **must-isolated pre-start selection stage**
- old `proof-gap / control-sample / bounded hardening / 1 fresh + N historical-kept` language is historical background only

Immediate hard meaning:
- `historical-kept` is now only history / resume seed / old-evidence pointer
- `historical-kept` may not support repo closure, external readout, or repo verdict
- one fresh replay receipt does **not** imply repo completion
- `repo-coverage-incomplete` is not an acceptable default completion posture for active user-facing behavior
- active refs should no longer drive repo selection by `proof-gap / sample-slot / control-sample`
- explicit `repo_ref` keeps semantic priority, but it no longer bypasses selection checking

## Current V4.4 follow-on position

The V4.3 repo-complete repair base remains closed.

The current active follow-on cut is now:
- repo selection split into:
  - `references/repo-selection.md` = semantic surface
  - `references/repo-selection-pack.md` = pre-start runtime carrier
- `repo-selection-pack` is now `must-isolated`
- it remains a built-in **stage**, not an independent child skill
- both auto-select and explicit repo intake now pass through that same stage
- parent still owns final repo choice freeze
- only after parent selection acceptance does current round root fix begin

Recent live-validation outcome now also freezes:
- explicit high-risk reject advice may be kept only through a **visible parent override**
- selection child timeout / interrupted run without usable proposal is first a **caller-side timeout-budget failure**
- repo choice freeze must wait until a usable `repo-selection-proposal` actually exists
- anchor-first auto-select is already validated

## Active execution-core answer

The active stable repo-complete entry is still explicitly:
- `loop9-verify-v4` itself

Important current reading:
- the queue-first parent loop is still the active execution core
- the deleted historical verifier v1 under `skills/loop9-poc-verification/` is lineage/background only
- helper scripts may still exist as deterministic bridges, but they are no longer the hidden repo-complete brain
- `repo-selection-pack` is a pre-start carrier inside this execution core, not a second canonical runner

Companion entry-binding ref now lives at:
- `references/repo-execution-core.md`

## Active queue-first reading

The active parent reading is now:
1. intake one repo request
2. run `repo-selection-pack`
3. accept / reject `repo-selection-proposal`
4. fix the current round root
5. accept / reject start-side drafts from `repo-start-pack`
6. freeze `current queue posture / next queue item / next gate`
7. iterate one truthful queue move at a time
8. after each child return, write back to the board and re-evaluate the queue
9. only after **every** in-scope finding is terminal, produce:
   - `repo-closure-review`
   - `external-readout`
   - `repo-round-verdict`

High-visibility workflow ref now lives at:
- `references/repo-queue-workflow.md`

## Historical repair context (background only)

Earlier V4 / V4.1 / V4.2 / V4.3 work still matters as repair background, for example:
- owner / placement split
- `repo-start-pack + parent accept/reject`
- must-isolated first-wave children
- start-worker boundary tightening
- timeout / stochastic-wobble attribution correction
- selection grounded in real repo state sources rather than proof/sample convenience

But those rounds now mean only:
- repair evidence exists,
- not that proof/sample selection remains the active product posture.

None of that background may by itself:
- drive default repo auto-selection
- justify repo closure from partial current-round handling
- reintroduce `1 fresh + N historical-kept` as an acceptable end state

## What the active skill should currently do

When the user asks to run `loop9-verify-v4` on a repo, the natural reading must now be:
1. intake one repo request
2. run the pre-start selection stage truthfully
3. freeze repo choice truthfully at the parent
4. refresh the repo start side truthfully
5. freeze the current-round in-scope finding queue
6. keep iterating until **every** in-scope finding has a current-round terminal disposition
7. only then produce:
   - `repo-closure-review`
   - `external-readout`
   - `repo-round-verdict`

## Current non-goals

This active cut is still **not** about:
- turning `repo-selection-pack` into a standalone child skill
- publish / Feishu sync
- cron fan-out / multi-repo orchestration
- thick runtime queue / thick job system
- thick outer resume scheduler semantics / program-first retry controller

## Current recurring recovery answer

The active recurring/auto-run answer is now:
- thin recurring recovery surface lives at `references/recurring-recovery.md`
- `runs/loop9-verify-v4-auto/00-current-task.md` is allowed as a thin pointer only
- if that pointer says the task is still `active`, the next slot should recover the same unfinished task before fresh auto-select
- hot recovery should prefer `codex exec resume` when a usable session id still exists
- cold recovery may use a fresh `codex exec`, but it must reconstruct the frontier from current workspace canonical artifacts before any repo re-selection
- non-zero transport/provider failure does not count as repo closure and does not release the slot to a new repo

## Current follow-on validation risk

The older V4.3 validation matrix remains useful historical baseline for:
- explicit repo precedence
- auto-select suppression
- unfinished repo continuation
- re-entry without `historical-kept` completion drift

But the new V4.4 selection-stage seam still has one primary remaining proof gap:
- fresh unfinished-repo auto-select when `repo_ref` is missing **and** no continuation anchors already exist

Current reading after the latest validation lane:
- explicit repo override wording is now covered
- selection child timeout / wobble attribution discipline is now covered at the runtime-carrier level
- pre-start storage discipline is already frozen enough for request / proposal / acceptance intake surfaces
- for the remaining fresh auto-select gap, prefer historical snapshot replay before synthetic unfinished-pool construction
- current contract also now freezes the tail completion gate more explicitly:
  - `repo-round-verdict` is not `repo-mainline-done`
  - the same repo mainline must continue through `delivery-report-bridge -> final-local-review`
  - one explicit experience-sedimentation check must still exist after that tail
- current selector contract also now freezes suppressor precedence more explicitly:
  - only accepted in-flight anchors count as continuation authority
  - detached env/replay assets are support only
  - `auto-select` may not silently supersede canonical delivery suppressors
- one finished repo should consume at most one verify slot by default; later recurring turns should advance the unfinished repo queue rather than revisit the delivered repo for liveness/status sync
- later liveness/status checks belong to monitor/heartbeat/status surfaces, not to repo-complete auto-select

P6 residue-sweep outcome remains frozen as:
- `references/proof-gap-sample-selection.md` stays historical-only and is no longer part of the default repo-complete read path
- `references/experience-index.md` stays as a visibility layer only and should be consulted on-demand after explicit delta relevance, not during normal intake / selection / closure
- experience sedimentation remains allowed, but only as a post-closure non-gating follow-on

## Active surfaces

The active selection surfaces are now:
- `references/repo-selection.md`
- `references/repo-selection-pack.md`

The active closure semantics surface is now:
- `references/board-closure-verdict.md`

The active queue workflow surface is now:
- `references/repo-queue-workflow.md`

The active execution-core binding surface is now:
- `references/repo-execution-core.md`

The active recurring recovery surface is now:
- `references/recurring-recovery.md`

Current selector truth is:
- every repo intake first enters `repo-selection-pack`
- missing `repo_ref` = answer repo-complete need, not proof-gap convenience
- explicit `repo_ref` = semantic priority + isolated check, not silent bypass
- high-risk reject advice may still be explicitly overridden, but only by a visible parent decision
- no usable `repo-selection-proposal` = runtime failure first, not semantic repo truth
- only accepted in-flight continuation anchors + `repo_verify_summary.json` + canonical delivery manifest presence are the thin state sources
- detached old env/bootstrap/replay assets are support-only and may not silently reopen a delivered repo in `auto-select`
- finished historical sample repos should now be suppressed by default rather than silently reabsorbed into verify auto-selection
- a delivered repo with `repo-mainline-done` + canonical `98/99` markers + explicit sedimentation result is suppressed from future recurring verify slots even if its old runtime is still live
- post-closure live verification is allowed only as one lightweight same-run acceptance note by default; repeated hourly revisits are invalid as repo-complete work
- an active recurring current-task pointer must be resumed before fresh auto-select; if resume transport is unavailable, cold recovery must still continue the same unfinished task from workspace truth rather than re-selecting a repo
