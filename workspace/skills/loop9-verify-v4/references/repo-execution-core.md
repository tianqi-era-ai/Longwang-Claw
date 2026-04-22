# Repo execution core (active P5 cut)

## Purpose

This ref freezes one active answer:

> what is the **current stable repo-complete execution entry** for `loop9-verify-v4`?

The answer is now explicit:
- the stable active entry is **the parent skill itself**: `loop9-verify-v4`
- not a hidden second runner
- not a deleted historical verifier script
- and not a revived `proof/sample` shared surface

## Historical surviving lineage

A real repo-level batch verifier **did** exist historically:
- old path: `skills/loop9-poc-verification/scripts/run_loop9_repo_verification.py`
- first add commit: `5f5578f42c7fc91ee53abe86352dfdf050b71116` (`feat: add repo-level loop9 verifier entry`)
- stripped commit: `1e28b35b076d8f1fc5817223c4dc1314a774fbf5` (`chore(loop9): strip verify shared surface and seal v1 assets`)

So the truthful reading is **not**:
- “repo-level batch execution never existed”

It is:
- a historical repo verifier v1 existed,
- but the old `loop9-poc-verification` shared surface was later intentionally stripped,
- and current active `loop9-verify-v4` must therefore rebind execution truth explicitly instead of silently depending on a deleted path.

Useful historical preservation paths now include:
- `reports/2026-04-10-loop9-verify-鬼打墙复盘/artifacts/rebuild-audit/shared-base-pre-strip/`
- `reports/2026-04-10-loop9-verify-鬼打墙复盘/artifacts/rebuild-audit/verify-code-surfaces.full.tar.gz`

Those are historical evidence / fallback archaeology only.
They are **not** the active product entry.

## Active rebinding decision

Current active rebinding is:
- **semantic entry** = `loop9-verify-v4`
- **repo-complete brain** = parent queue-first loop under this skill family
- **deterministic helper layer** = optional script/report/verifier bridges only

Hard meaning:
- do not split active execution truth between this skill and one hidden repo verifier script
- do not require the deleted `loop9-poc-verification` family to exist for current active behavior to remain legible
- do not let old `repo_verify_summary.json` semantics quietly become the active closure brain

## Current execution-core chain

The active repo-complete execution core is now:

1. repo intake
2. resolve and announce child-runtime posture:
   - explicit invocation of this skill counts as semantic authorization for the bounded `must-isolated` work required by the same repo mainline
   - if the current platform/runtime still requires extra approval or blocks child execution, surface that now rather than silently inlining later
3. compile / run `repo-selection-pack`
4. parent accept/reject of `repo-selection-proposal`
5. current round root fix
6. `repo-start-pack`
7. parent accept/reject of start-side drafts
8. freeze `current queue posture / next queue item / next gate`
9. compile `stage-handoff.<stage>.md`
10. run one bounded child stage in isolated runtime when required
11. consume `stage-verdict.<stage>.md`
12. apply thin board writeback
13. refresh the board and continue the queue
14. only after every in-scope row is terminal:
    - `repo-closure-review`
    - `coverage_snapshot`
    - `external-readout`
    - `repo-round-verdict`
15. keep the same repo mainline alive and run:
    - `delivery-report-bridge`
    - `final-local-review`
16. run one explicit experience-sedimentation check:
    - `no-new-delta`
    - or one thin `learning-delta`
17. only then may the parent mark `repo-mainline-done`
    - or freeze a truthful blocked-tail boundary
18. once a repo is truthfully `repo-mainline-done`, any later recurring/auto-select turn must re-enter the core as a new repo intake for the next unfinished repo by default rather than spending a fresh slot on post-closure liveness/status sync of the delivered repo

This means:
- the current queue-first parent loop **is** the execution core
- not just a documentation shell around some other hidden runner
- `repo-round-verdict` is a closure-side freeze point, not the repo-mainline completion gate
- only accepted in-flight round anchors may extend the same repo mainline by default
- detached env/bootstrap/replay artifacts may still support judgment, but they may not silently reopen a delivered repo in `auto-select`
- post-closure runtime liveness of a delivered repo is not same-repo continuation authority for the next recurring verify slot

## Helper boundary

Deterministic helpers may still exist for things like:
- per-finding verification
- request normalization
- report generation
- archived result inspection

But they stay only:
- helper bridges
- bounded executors
- report builders
- historical evidence surfaces

They may **not** become:
- a second user-facing canonical repo-complete entry
- a second repo-level semantic owner
- a hidden closure authority

## Relation to historical repo summaries

Historical `runs/repo-verify-*/repo_verify_summary.json` outputs remain useful for:
- selector state sources
- historical evidence
- already-finished repo suppression
- legacy/fallback delivery-report generation inputs

They are **not** by themselves:
- current-round closure truth
- current queue truth
- a substitute for current `repo-findings-board`
- proof that current active skill behavior still lives in the old stripped surface

## Hard prohibitions

Do not drift into any of these:
- resurrect the whole deleted `loop9-poc-verification` shared surface as the active default brain
- create a new thick orchestrator just because the old verifier v1 was stripped
- let `repo-complete` active behavior depend on hidden archaeology knowledge
- treat old `next_action / deliver-now / review-summary-manually` state names as the active closure contract for `loop9-verify-v4`
- let `repo_verify_summary.json` stand in for current-round queue completion
- let `repo-round-verdict` stand in for repo-mainline completion
- let detached old env/replay assets outrank canonical delivery suppressors during `auto-select`
- let `auto-select` silently reopen a repo already in canonical delivery posture
- let a later hourly/recurring verify turn spend its slot on post-closure liveness/status sync of a delivered repo instead of advancing the unfinished repo queue
- keep stale delivered runtimes hot on a shared Tencent CVM when they are no longer needed for the current decisive mainline
- let the mandatory experience-sedimentation check disappear just because the likely result is `no-new-delta`

## Validation posture

This P5 cut froze the **entry binding**, not the full validation matrix by itself.

That follow-on validation has now already landed under plan `P7`, and it passed the required four checks:
- explicit repo path
- auto-select suppression of already-finished repos
- true unfinished repo continuation
- interruption / re-entry without `historical-kept` completion drift

Current reading:
- entry binding is closed
- the anti-regression matrix is also closed
- any further work should open as a new lane rather than pretending this ref still has hidden unfinished `P7` debt

## One-sentence operating posture

> The stable repo-complete entry is now the `loop9-verify-v4` parent skill itself; old repo verifier v1 is historical lineage, and helper scripts are bridges rather than the brain.
