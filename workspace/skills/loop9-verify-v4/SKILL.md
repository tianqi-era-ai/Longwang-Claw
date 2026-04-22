---
name: loop9-verify-v4
description: Markdown-first, AI-native parent skill for one repo-level Loop9 repo-complete loop. Use when you want the parent layer to hold repo-level owner, repo truth relocation, full finding-queue completion, repo-level closure, and final deliverable-oriented verdict while dispatching only thin handoffs to env-bootstrap / finding-replay / distillation child skills.
user-invocable: true
---

# Loop9 Verify V4

This is the active parent skill for the `loop9-verify-v4` family.

The active stable repo-complete entry / execution-core binding now lives at:
- `references/repo-execution-core.md`

## Active product contract

Current user-facing contract is now frozen as:
- **repo-complete by default**
- **daily-work / delivery-oriented by default**
- **one repo in, all in-scope findings processed in the current round before repo closure**
- **stages marked `must-isolated` / `isolated-by-default` should use a cross-platform child-agent / isolated-executor capability by default, because the point is context isolation rather than one platform's API**
- **when the user explicitly invokes this skill, that invocation itself semantically authorizes the bounded `must-isolated` / `isolated-by-default` work needed by this skill family to finish the same repo mainline**

The natural reading must now be:

> Enter one repo, process all in-scope PoCs / findings for the current round, then emit repo-level closure, repo-level readout, and repo-level verdict.

Not:
- a bounded proof sample
- a single active-finding glamour round
- a proof-gap verifier
- a shell that reuses `historical-kept` as a completion substitute

## Historical background vs active behavior

The accepted V4 / V4.1 / V4.2 repair stack, sample rounds, bounded hardening lanes, proof-gap discussions, and start-worker tightening work remain useful as **historical repair context**.

But they no longer define the active product contract.

Important reading rule:
- if an older ref still speaks in `proof-gap / control-sample / bounded hardening / 1 fresh + N historical-kept` language,
- and that wording conflicts with repo-complete execution,
- treat it as **historical background**, not active default behavior.

Until all refs are cleaned, this `SKILL.md` is the active contract source.

## Cross-platform child-isolation principle

When this skill says:
- `isolated`
- `must-isolated`
- `isolated-produced`
- `child stage`

read that as a **cross-platform context-isolation contract**, not a platform-specific keyword.

Canonical meaning:
- if the current platform supports `subagent / child agent / isolated worker / isolated session`, use that capability as the default carrier for `must-isolated` child work
- if the platform does not expose that exact primitive, use the nearest equivalent isolated execution unit rather than silently normalizing everything back inline
- keep the same thin `stage-handoff -> stage-verdict` contract and the same round root
- keep semantic owner at the parent layer; runtime isolation does not move repo truth

## Explicit Skill Invocation = Semantic Delegation Authorization

When the user explicitly invokes this skill family, for example by:
- naming `loop9-verify-v4`
- pointing at this `SKILL.md`
- or otherwise clearly asking to use this skill as the active execution surface

that invocation should be read as:

> semantic authorization for the bounded `must-isolated` / `isolated-by-default` child work required by this skill to finish the same repo mainline

Hard meaning:
- this authorization is **cross-platform semantic intent**, not one platform's API keyword
- it covers the bounded `child agent / isolated executor / background task` equivalents required by this skill family
- it does **not** widen into unrelated fan-out, optional side quests, or arbitrary extra delegation
- when a platform exposes multiple compatible child runtimes, default preference should stay on the closest supported equivalent to the parent runtime rather than inventing a different execution family without reason
- if a stricter platform/runtime policy still requires extra confirmation or blocks child execution, the parent must surface that explicitly instead of silently broadening parent-inline context

## Delegation Phrase Normalization

When this skill is explicitly invoked, the following phrases should be treated as
equivalent signals for bounded child-runtime authorization if they are attached to
the same request or immediate continuation:

### Preferred exact phrases

These phrases should be treated as especially strong positive matches because many
platform adapters already reason about them explicitly:
- `subagent`
- `sub-agent`
- `delegation`
- `delegate`
- `parallel agent work`
- `parallel agent`
- `child agent`
- `isolated executor`

### Equivalent English phrases

These should normalize to the same intent:
- `child-agent`
- `child worker`
- `isolated worker`
- `isolated run`
- `isolated task`
- `background task`
- `background worker`
- `background run`
- `spawn_agent`
- `spawn`
- `forked worker`
- `separate worker`
- `separate context`
- `bounded child run`

### Equivalent Chinese phrases

These should normalize to the same intent:
- `子代理`
- `子 Agent`
- `子Agent`
- `子任务代理`
- `委派`
- `委托执行`
- `并行代理`
- `并行 Agent`
- `并行执行`
- `隔离任务`
- `隔离执行`
- `隔离运行`
- `独立执行器`
- `独立 worker`
- `独立上下文`
- `后台任务`
- `后台执行`
- `后台代理`

### Mixed / adapter phrases

These should also normalize to the same intent:
- `must-isolated 可直接 spawn`
- `must-isolated 可直接 SubAgent`
- `must-isolated 可直接后台任务`
- `可直接 delegation`
- `可直接 parallel agent work`
- `可直接 isolated executor`

### Normalization rules

Hard meaning:
- singular / plural / case / hyphen variants count equivalently
- English / Chinese / mixed-language wording counts equivalently when the meaning is clear
- `spawn_agent` and similar platform-specific names should be read as adapter hints, not as the only valid form
- these phrases authorize only the bounded child work needed by the same skill mainline; they do **not** authorize unrelated fan-out
- if the user also says `same model`, `same runtime`, `与主Agent一样的模型`, `与父Agent一致`, or equivalent wording, treat that as a runtime preference for child work; if the exact model is unsupported, use the nearest supported equivalent and say so explicitly

## Startup Disclosure / Fail-Closed Rule

Before substantial repo work begins, if the expected path includes any `must-isolated` or `isolated-produced` work, the parent must explicitly state one of the following postures:
- `isolated-run confirmed`
- `extra authorization still required`
- `inline-exception required`

Hard meaning:
- silent inline fallback is forbidden
- if extra authorization is still required by the current platform/runtime, the parent should say so before that stage begins rather than discovering it only after drifting inline
- if an `inline-exception` is unavoidable, the parent must say why, keep inputs as thin as the intended handoff, and record the exception as a runtime-placement exception rather than pretending inline was the normal reading
- this rule exists to protect expected workflow shape, not to create extra ceremony

## When to use

Use this skill when the task is:
- one repo-level Loop9 verify run,
- repo is the main unit,
- the goal is to finish the repo’s current-round in-scope finding queue,
- the parent layer must keep owner over repo truth relocation / repo-findings-board / queue progression / closure,
- and the expected output is repo-level completion + repo-level readout, not merely one decisive replay receipt.

## Do not use for

- publish / Feishu sync
- cron fan-out / multi-repo batch orchestration
- thick queue systems across many repos
- replacing AI-native repo judgment with a big program state machine
- claiming repo completion from one decisive finding receipt alone
- using old proof/sample lanes as the default product posture

## Parent responsibilities

The parent layer keeps semantic ownership of:
- repo intake / repo selection
- repo truth relocation
- accept / reject of `repo-start-pack / parent-draft-pack`
- repo manifest / in-scope finding queue freeze
- repo-findings-board maintenance
- per-finding current-round disposition tracking
- next queue item choice
- stage routing for each queue item
- repo-level closure review
- external readout / repo-round verdict
- delivery-report-bridge handoff compilation / verdict consumption
- final-local-review completion boundary

Important:
- ownership here means **semantic owner**, not automatic parent-inline execution,
- and some parent-owned objects may still be `isolated-produced` while returning to the parent for accept/freeze.

## Canonical workflow

1. Read `references/current-status.md`
2. Read:
   - `references/repo-execution-core.md`
   - `references/parent-boundary.md`
   - `references/owner-placement-matrix.md`
   - `references/repo-selection.md`
   - `references/repo-selection-pack.md`
   - `references/parent-io-contract.md`
   - `references/canonical-objects.md`
   - `references/repo-start-pack.md`
   - `references/parent-minimal-core.md`
   - `references/parent-closure-chain.md`
   - `references/board-closure-verdict.md`
   - `references/repo-queue-workflow.md`
   - `references/agentic-blocker-diagnosis.md`
   - `references/repo-task-brief.md`
   - `references/stage-chain.md`
   - `references/child-return-consume-seam.md`
   - `references/first-wave-child-skills.md`
   - `references/runtime-isolation.md`
   - `references/handoff-compiler.md`
   - `references/round-storage.md`
   - `references/recurring-recovery.md`
   - `references/experience-sedimentation.md`
3. Historical-only background ref (consult only when decoding older repair artifacts, never as default repo-complete intake):
   - `references/proof-gap-sample-selection.md`
4. On-demand visibility ref (consult only when an explicit delta/experience question exists, not as default intake/selection/closure input):
   - `references/experience-index.md`
5. Intake an explicit `repo_ref` when provided, but treat it as `requested_repo_ref`, not as permission to bypass selection checking.
6. Compile and run `repo-selection-pack` as one bounded `child agent / isolated executor` pre-start stage.
7. Accept or reject the returned `repo-selection-proposal`; explicit repo still wins semantically, but any high-risk reject advice should require explicit parent override rather than silent bypass.
8. If selection child runtime exits before a usable `repo-selection-proposal` exists, record caller-side `timeout-budget failure`, do **not** freeze repo choice yet, and rerun before semantic judgment.
9. Only after accepted selection, fix or refresh the current round root (`round-summary.md / objects / artifacts`).
10. Run `repo-start-pack / parent-draft-pack` as the repo-start worker.
11. Accept or reject the returned relocation / brief / board draft set.
12. Freeze the repo’s current-round **in-scope finding queue**.
13. For each queue item, choose the needed stage path (`env-bootstrap` when needed, `finding-replay` when needed, thin parent writeback always).
14. Compile `stage-handoff.<stage>.md` as a minimal workset packet for the active queue item.
15. Freeze runtime placement using `references/owner-placement-matrix.md` + `references/runtime-isolation.md`; if `runtime_target=tencent-cvm` is active, keep that target explicit in the handoff and do not silently collapse the child back to Mac-local execution.
16. Invoke exactly one bounded child stage for the current queue item.
17. Wait / poll / block as needed inside the same repo flow; same-repo completion must not depend on a fresh user turn.
18. Consume `stage-verdict.<stage>.md` back at the parent layer as **stage-local truth + thin parent-consume writeback**.
19. Mark the queue item with a **current-round terminal disposition**.
20. Repeat until **every in-scope finding** has a current-round terminal disposition.
21. Only then run `repo-closure-review -> coverage snapshot freeze -> external-readout -> repo-round-verdict`.
22. After repo-level verify truth is frozen, run `delivery-report-bridge -> final-local-review` as the required local-bundle completion tail of the same repo mainline.
23. Run one explicit experience-sedimentation check for the finished repo mainline:
   - either `no-new-delta`
   - or at most one thin `learning-delta`
24. Only after that tail has either completed or truthfully blocked, and after the explicit experience-sedimentation check has been performed, may the parent treat the repo mainline as `done`.
25. Once a repo has truthfully reached `repo-mainline-done` and already holds canonical delivery markers (`98-delivery-bundle.manifest.json` + `99-最终本地复盘.*`), later recurring/auto-select turns must suppress it by default and spend the next verify slot on another unfinished repo rather than on post-closure live verification or status sync of the finished repo.

## Recurring auto-run continuation rule

When the invocation comes from `loop9-verify-v4-auto` or another recurring carrier, and
`~/.openclaw/workspace/runs/loop9-verify-v4-auto/00-current-task.md`
shows an `active` unfinished task, read that pointer as:

> accepted same-task continuation authority for the next recurring slot

Hard meaning:
- continue that same unfinished task before any fresh auto-select
- read current workspace round roots / boards / objects / artifacts first
- do not re-run `repo-selection-pack` as a fresh repo intake unless the prior task is first proven truthfully closed or truthfully unrecoverable as the same mainline
- transport/provider interruption does not consume the slot as repo closure
- transport/provider interruption does not release the slot to a different repo either
26. If a final liveness/acceptance note is still useful, keep it lightweight and inside the same repo mainline run when possible; later periodic checks belong to a separate monitor/heartbeat/status lane rather than to the next `repo-complete` turn.
27. When the runtime target is a shared Tencent CVM, release non-essential hot runtime from already-delivered repos by default, but do not silently demote a repo's declared external-facing final runtime when the product contract still requires public access; one `published-final` runtime per delivered repo may stay hot, while older useful states stay as stopped snapshots.

## Repo-complete execution rules

### Queue completion rule
A repo round is not complete until **all in-scope findings** have entered a current-round terminal disposition.

### Allowed terminal-disposition shape
Exact labels may evolve, but the disposition must be current-round and explicit, for example:
- `fresh-confirmed`
- `fresh-blocked`
- `fresh-manual-needed`
- `fresh-skip-by-policy`
- or another equally explicit current-round terminal state

### Forbidden completion shortcuts
The following do **not** count as repo completion:
- `historical-kept`
- old verification results with no current-round handling
- “relevant but not processed this round”
- one replayed finding plus several untouched findings
- `round-closed` claimed before queue completion

## Adaptive blocker-solving discipline

Default posture:
- the first failed replay attempt is a **diagnosis input**, not automatic closure truth
- the parent should distinguish:
  - transport / timeout / caller-budget failure
  - env not yet materialized
  - seed / auth / target-id / live-material mismatch
  - one cheap shared blocker spanning several unfinished rows
  - success-response shell without state change
  - true manual/policy boundary
- when a bounded truthful repair is available inside the same repo round, do that repair and rerun before freezing a negative disposition
- when several unfinished rows visibly share the same cheap runtime/auth/bootstrap blocker, repair that blocker once, capture the resulting live material, and then reopen the affected rows one by one before freezing row-local negative truth
- for state-changing claims, `HTTP 200` alone is not enough; require landing proof from before/after state or another equally direct control

Read:
- `references/agentic-blocker-diagnosis.md`

## Isolated-child uncertainty / timeout discipline

When the parent delegates to an isolated child or a repo-start worker, keep these rules explicit:
- one failed run does **not** by itself prove prompt/worker semantic failure
- one successful run does **not** by itself prove hardening/robustness
- timeout by itself is **caller-side budget/scheduling failure**, not prompt evidence
- if a child times out before writing a usable verdict/draft set, widen timeout materially and rerun before making semantic judgments
- record timeout separately from stage truth; do not silently reinterpret timeout as `blocked-confirmed` or as worker quality evidence
- only inspected process evidence (dead loop, pathological drift, prompt-induced non-convergence, etc.) may justify promoting timeout into prompt/worker diagnosis
- for fragile output-shape-sensitive stages, the parent should be willing to compare multiple attempts before widening a repair lane or freezing a negative stage judgment
- workflow/agent retry mechanics belong to the parent dispatcher, not to opaque child defaults
- retry policy/strategy responsibility stays with the parent dispatcher
- child runs may expose evidence that a rerun is needed, but they may not silently own the rerun/replay policy themselves

## Hard rules

- active user-facing contract = **repo-complete only**
- stable repo-complete entry = **this skill family itself**; there is no second hidden canonical repo runner
- repo-level owner stays at the parent layer
- `repo-selection-pack` is the production default pre-start selection path
- `repo-start-pack` is the production default repo-start path
- `repo-task-brief` remains the mandatory repo-level start anchor inside that start pack
- explicit invocation of this skill is semantic authorization for the bounded `must-isolated` / `isolated-by-default` stages required by the same repo mainline
- explicit `repo_ref` always wins semantically, but it does **not** bypass selection checking
- `repo-selection-pack` is `must-isolated` and stage-only; it is not an independent child skill
- when `repo_ref` is absent, default selection must prefer repos needing repo-complete finish, not old proof/sample questions
- when `repo_ref` is explicit, `explicit-repo-check` may still return high-risk reject advice / manual-confirm-needed, but it may not silently override the requested repo
- explicit repo may still be kept against high-risk reject advice, but only by a visible parent override
- selection child timeout / interrupted run without usable proposal is caller-side runtime failure first, not repo-selection truth
- only accepted in-flight round anchors (`parent-selection-acceptance`, current round root, accepted brief/board) count as same-repo continuation authority; detached env/bootstrap/replay artifacts are support signals only
- repos already fully verified / ready for delivery / already holding complete repo verify summary must not be silently re-selected as the default next verify target
- auto-select has no authority to supersede canonical delivery suppressors; if `reports/<slug>/98-delivery-bundle.manifest.json` and `99-最终本地复盘.*` already exist, default verify auto-selection must back off
- reopening a delivered repo requires explicit repo / explicit reopen intent / visible parent override; silent continuation from detached historical artifacts is forbidden
- once a repo has truthfully reached `repo-mainline-done` + canonical `98/99` markers + an explicit sedimentation result, the default next recurring/auto-select turn must spend its slot on another unfinished repo or truthfully report that no eligible unfinished repo exists
- one delivered repo may receive at most one lightweight post-closure liveness/acceptance check by default, and that check belongs to the same repo mainline run rather than to a later hourly verify slot
- repeated liveness/status-sync revisits of a delivered repo are monitor/heartbeat work, not repo-complete progress, and may not be narrated as a fresh auto-select of that repo
- on a shared Tencent CVM, non-essential hot runtime from already-delivered repos should be stopped/released by default, but each delivered repo may retain one declared `published-final` public runtime when operators still need direct access; keep the rest as cold snapshots when useful, not always-running stacks
- old `loop9-poc-verification` / stripped verify shared surface is historical lineage only, not active default behavior
- `repo-start-pack` should consume accepted selection basis rather than raw multi-repo selection narration
- `repo-start-pack` reads a start-side minimal workset; closure-side material is invalid input rather than optional background
- `repo-start-pack` may return only the round-local start-side draft set plus proposal-only `parent-draft-pack`
- parent reject path is fail-closed; stale/mixed start packets must be rejected as a whole
- one repo round is **not** one active-finding round
- one decisive replay receipt does **not** imply repo completion
- every in-scope finding must receive a current-round terminal disposition before repo closure
- `historical-kept` may survive as history / seed / pointer only; it may not support repo closure, external readout, or repo verdict
- child stages may still be bounded and isolated, but the parent must keep iterating the repo queue until the queue is done
- stages marked `must-isolated` or `isolated-by-default` should bind to a platform-native child-agent / isolated-executor capability whenever that platform exposes one
- if a stricter platform/runtime policy still blocks child execution, the parent must make that block visible before proceeding; silent inline fallback is not allowed
- the skill contract must stay legible across OpenClaw / Codex / future platforms; platform-specific primitive names belong to the adapter layer, not the semantic contract layer
- if the parent freezes `runtime_target=tencent-cvm`, child execution should prefer direct SSH/server-local operation first rather than inventing a thicker remote-control plane
- if that Tencent CVM path later needs a proxy and the frozen remote loopback proxy is intentionally the operator Mac's local Clash path, prefer reverse `SSH -R` backhaul while keeping the Tencent CVM-facing endpoint stable rather than inventing an ad-hoc proxy process on the CVM
- child skills may not directly chain to each other
- child runtime binding stays parent-owned
- current first-wave child work is `isolated-by-default`; inline is a high-threshold explicit exception rather than a thin convenience path
- same repo full flow may wait / poll / block for child completion, but it may not depend on a new user turn, manual conversation continuation, or `sessions_yield`-style split to finish the same repo round
- parent-owned does **not** imply parent-executed; some parent-owned objects are intentionally `isolated-produced`
- `isolated-produced` does **not** imply child-owned; runtime placement is not semantic owner
- first replay friction is diagnosis input, not an excuse to stop early; if official seed, live-id relocation, auth refresh, or bounded control material can truthfully answer the question, the same repo round should attempt that repair before declaring failure
- one cheap shared blocker may be repaired once for a whole row cluster, but that shared unblock only changes replay-openable posture; it may not be mistaken for row-local confirmed truth or repo closure
- mutation-style claims require landing proof; `HTTP 200` or `resultCode = 200` alone does not justify `fresh-confirmed`
- helper scripts may still exist as deterministic bridges, but they may not become the active repo-complete brain
- final freeze of repo closure remains parent-only
- `repo-closure-review` is the only parent closure freeze point before outward projection
- `external-readout` may only project frozen `repo-closure-review + coverage_snapshot`; it may not rejudge repo truth
- `repo-round-verdict` remains the final parent-only round verdict and may not be silently replaced by outward wording
- `repo-round-verdict` closes repo-level verify truth, but it is **not** `repo-mainline-done`; the same repo mainline is not done until `delivery-report-bridge -> final-local-review` has either completed or truthfully blocked
- parent completion is fail-closed: while that tail remains unconsumed, the parent may not outwardly say “stop here”, “current flow done”, or any equivalent soft-stop wording
- if a current round root already exists and the delivery tail is still pending, the parent must self-check that state and continue inside the same run rather than treating a fresh user turn as the dispatcher
- the experience-sedimentation check is mandatory after the repo-mainline tail; its output may be `no-new-delta`, but the check itself may not be skipped
- child verdicts may return only stage-local truth plus thin writeback; they may not emit `repo-closed` by themselves
- real progress must come back as truth-backed receipt / blocked / manual-needed / policy-skip **plus** visible queue movement on the board
- `started / planning / shell-created` do not count as real progress

## First-wave child skills

The first-wave child skills currently frozen for this family are:
- `loop9-verify-v4-env-bootstrap`
- `loop9-verify-v4-finding-replay`
- `loop9-verify-v4-distillation`
- `loop9-delivery-reports`

No second-wave child skills are admitted yet.

`repo-selection-pack` is also `must-isolated`,
but it stays a built-in **stage**, not an independent child skill.

The following stay in the parent layer for now:
- final repo choice freeze / selection acceptance
- repo-state-relocation
- repo-closure-review
- external-readout
- repo-round-verdict

## Experience sedimentation

Experience sedimentation currently stays **inside this skill family as a built-in substage**.

It is not a standalone skill yet.

When a repo round finishes, the parent should always run one explicit
experience-sedimentation check after the repo-mainline tail.

That check should answer one of:
- a bounded reusable truth worth keeping,
- or a truthful `no-new-delta`,

read `references/experience-sedimentation.md`.

This is a **post-closure, non-gating follow-on**:
- it must not reopen the repo queue,
- it must not delay repo closure / readout / verdict,
- and it must not become a default intake or selector surface.
- it may include at most one lightweight same-run acceptance/liveness note when that closes the current repo readout,
- but it must not consume a later recurring verify slot or masquerade as next-run repo progress.

If a bounded reusable abstract truth is worth exposing to later executors, then and only then refresh:
- `references/experience-index.md`

Default discipline:
- abstraction first
- case layer second
- promotion judgment last
- by default, one round should emit at most one family-facing `learning-delta`, while repo-local experience cards may exist as a separate case-memory layer when explicitly requested
- repo-specific lessons stay in round/report artifacts first
- observed items may be exposed in the index layer without becoming defaults
- current deltas default to `observed` unless stronger cross-sample proof exists

## References

### Active repo-complete surfaces
- `references/current-status.md`
- `references/repo-execution-core.md`
- `references/parent-boundary.md`
- `references/owner-placement-matrix.md`
- `references/repo-selection.md`
- `references/repo-selection-pack.md`
- `references/parent-io-contract.md`
- `references/canonical-objects.md`
- `references/repo-start-pack.md`
- `references/parent-minimal-core.md`
- `references/parent-closure-chain.md`
- `references/board-closure-verdict.md`
- `references/repo-queue-workflow.md`
- `references/repo-task-brief.md`
- `references/stage-chain.md`
- `references/child-return-consume-seam.md`
- `references/first-wave-child-skills.md`
- `references/runtime-isolation.md`
- `references/runtime-target.tencent-cvm.md`
- `references/handoff-compiler.md`
- `references/round-storage.md`
- `references/experience-sedimentation.md`

### Historical / on-demand only
- `references/proof-gap-sample-selection.md` (historical background only; do not read as default intake)
- `references/experience-index.md` (visibility layer only; consult on-demand after explicit delta relevance)
