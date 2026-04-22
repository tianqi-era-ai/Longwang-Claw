# Parent I/O contract (thin form)

Before drilling into thinner field-level details here, read:
- `references/parent-boundary.md`
- `references/owner-placement-matrix.md`
- `references/parent-closure-chain.md`
- `references/board-closure-verdict.md`

Those refs are the current one-eye compression of:
- what the parent always owns,
- what children may never steal,
- what still does not count as progress,
- and how `semantic owner` is no longer allowed to collapse into runtime placement.

## Accepted input

The parent skill should only accept thin repo-level intent:
- `repo_ref` (optional)
- `goal_hint` (optional)
- `context_refs` (optional)
- `hard_constraints` (optional)

If `repo_ref` is missing, the parent chooses a repo itself.

## High-visibility owner / placement split

Current production reading uses two fields:
- `semantic owner`
- `runtime placement`

Authoritative current matrix lives at:
- `references/owner-placement-matrix.md`

Immediate current interpretation:
- `repo-state-relocation / repo-task-brief / repo-findings-board = parent-owned + isolated-produced`
- `parent-draft-pack = parent-owned + isolated-produced`
- `env-bootstrap / finding-replay / distillation = child-stage + must-isolated`
- `repo-closure-review / repo-round-verdict = parent-owned + parent-executed`
- `external-readout = parent-owned + isolated-produced + projection-only`

Hard meaning:
- `parent-owned` does **not** imply `parent-executed`
- `isolated-produced` does **not** imply `child-owned`
- final freeze of repo-level truth remains parent-only

Cross-platform execution reading:
- placement labels such as `must-isolated` / `isolated-produced` are semantic runtime categories, not one platform's API names
- if the current platform exposes `child agent / subagent / isolated worker / isolated session`, use that capability as the default carrier for child-stage isolation
- if it does not, choose the nearest equivalent bounded isolated executor rather than silently widening parent inline context

## Required pre-start selection stage

Authoritative active selection surfaces now live at:
- `references/repo-selection.md`
- `references/repo-selection-pack.md`

Thin contract here is only:
- every repo intake first goes through `repo-selection-pack`
- `repo-selection-pack` runs as one bounded `child agent / isolated executor`
- missing `repo_ref` means auto-select by **repo-complete need**, not proof-gap convenience
- explicit `repo_ref` means run `explicit-repo-check`, not bypass selection
- current-round continuation anchors should beat fresh re-selection only when they are accepted active in-flight anchors
- `repo_verify_summary.json` + canonical delivery manifest presence are the minimum real state sources
- detached env/bootstrap/replay artifacts are support-level only and may not outrank canonical delivery markers
- finished / ready-for-delivery historical sample repos should be suppressed by default
- `auto-select` may not reopen a repo already behind canonical delivery suppressors; reopen requires explicit repo/reopen intent plus visible parent override
- the child may return high-risk reject advice / manual-confirm-needed, but may not silently override explicit repo
- the parent still owns final repo choice freeze

Hard boundary:
- do not choose repo by glamour, size, or historical sample convenience first
- do not let older proof/sample refs secretly drive default selection
- do not let a previously useful sample repo stay pinned in the default mainline after it is effectively finished
- do not let explicit repo jump straight into `repo-start-pack`

## Required repo-start worker

Current production start default is:
- `repo-selection-pack` first
- parent selection accept/reject second
- current round root fix third
- `repo-start-pack` fourth
- parent accept/reject fifth
- queue-scope freeze sixth

`repo-start-pack` must return:
- `repo-state-relocation.*.md`
- `repo-task-brief.*.md`
- `repo-findings-board.*.md`
- `parent-draft-pack.*.md`

`parent-draft-pack` may propose:
- `current queue posture`
- `next queue item`
- `next gate`

It may **not** freeze them.

Current production output meaning:
- those four outputs are the full valid start packet
- they must stay under the current round root
- `parent-draft-pack` remains proposal-only
- closure-side objects / verdict wording / coverage-freeze wording may not appear in the packet at all

Current production compiler meaning:
- `repo-start-pack` must be compiled as a **start-only minimal workset**, not as a softened repo-wide context packet
- allowed inputs are only thin repo intake / accepted selection basis / current round root / thin constraints / start-side refs sufficient to draft relocation + brief + board + `parent-draft-pack`
- `repo-closure-review`, `external-readout`, `repo-round-verdict`, old closure prose, old `V4.1/V4.2` closure material, and thick receipt/log dumps are hard-denied even as warm refs or cold pointers
- if the parent feels the worker “needs” those anyway, the correct answer is `compiler drift / invalid start input`, then recompile thinner; do not silently widen the packet

Current production reject gate meaning:
- if the return packet contains closure-side material, old closure refs, accepted-truth wording, or a mixed packet of valid drafts plus stale material, treat it as `invalid-start-draft / stale-drift` and reject the **whole** packet
- do not half-accept or cherry-pick one pretty draft out of a stale packet
- write a thin `parent-start-acceptance.*.md` decision, then either recompile thinner or manually repair the start-side canonical drafts before any queue-scope freeze

See also:
- `references/repo-start-pack.md`
- `references/parent-minimal-core.md`

## Required repo start anchor

Before child work begins, the parent should already have refreshed one current-round `repo-task-brief.*.md`.

This object is expected to carry at least:
- `repo identity`
- `why this repo now`
- `current repo truth`
- `this-round repo goal`
- `explicit non-goals`
- `current active stage guess`
- `minimum refs`
- `round exit condition`

Runtime expectation:
- refresh it after `repo-state-relocation + current round root fix`
- before board refresh / queue-item choice
- let the next parent cycle start from it rather than from the loudest finding or latest receipt

Current owner/placement expectation:
- the brief remains parent-owned even if it is isolated-produced
- acceptance/freeze of that brief still belongs to the parent

Boundary:
- it is **not** the full board
- **not** the stage handoff
- **not** the closure review
- and **not** a thick repo summary

See also:
- `references/repo-task-brief.md`

## Required parent output

Each parent cycle should keep repo-level truth legible with at least:
- `repo_ref`
- `selection_mode`
- `current_stage_owner`
- `round_status`
- `repo_status`
- `coverage_snapshot`
- `artifact_refs`
- `next_recommended_stage`
- `closure_note`

Default selection-mode expectation:
- use something like `explicit-repo-intake` when the repo was fixed externally
- use something like `auto-repo-complete-intake` when the parent selected the repo by repo-complete need
- keep this thin; it is not a second protocol layer

Default expectation:
- `artifact_refs` should prefer current-round refs first
- older evidence may be pointed to only when it is intentionally reused as background, never as a completion substitute

### Required `coverage_snapshot`
At minimum this should keep current-round queue truth visible, for example:
- `in_scope_findings_total`
- `terminal_disposition_count`
- `fresh_confirmed_count`
- `fresh_blocked_count`
- `fresh_manual_needed_count`
- `fresh_skip_by_policy_count`
- `remaining_unfinished_count`

Compatibility note:
- older artifacts may still mention shapes like `historical_kept_count` or `not_yet_replayed_count`
- those may survive only as historical compatibility / migration signals
- they may not act as closure support in the active contract

### Closure-side freeze rule
Before any outward readout is produced, the parent must already have frozen:
- `repo-closure-review`
- `coverage_snapshot`

Hard gate:
- if any in-scope finding still lacks a current-round terminal disposition,
- then the parent may refresh the board and continue queue progression,
- but may **not** emit `repo-closure-review`, `external-readout`, or `repo-round-verdict` yet.

`external-readout` may consume only those frozen objects plus accepted artifact refs.
It may not:
- rejudge `round_status`
- rejudge `repo_status`
- invent a new `coverage_snapshot`
- turn unfinished queue state into repo closure
- silently promote historical evidence into this round's handling

`repo-round-verdict` remains the final parent-only verdict.
Its truth source stays the frozen closure review + coverage snapshot rather than outward wording.

## Allowed status fields

### `round_status`
At minimum the active contract should distinguish:
- `round-in-progress`
- `round-closed`

### `repo_status`
At minimum the active contract should distinguish:
- `repo-queue-in-progress`
- `repo-closed`

Hard meaning:
- do not use `repo-coverage-incomplete` as the default comfort-state for partial current-round handling
- partial current-round work should stay visibly unfinished rather than being cosmetically re-labeled as a soft closure

## Hard boundary

The parent may delegate bounded work,
but may not delegate away:
- repo selection
- repo truth relocation
- accept / reject of `repo-start-pack / parent-draft-pack` drafts produced in isolated runtime
- repo-level start-anchor ownership (`repo-task-brief` refresh / rewrite)
- queue posture / next queue item / next gate freeze
- child runtime binding
- handoff compilation / minimal-workset ownership
- repo-findings-board maintenance
- same-repo continuation ownership while isolated child work is running
- repo-level closure judgment
- closure-side `coverage_snapshot` freeze before outward projection
- external readout / repo-round verdict ownership
- delivery-report-bridge handoff compilation / verdict consumption
- final-local-review completion freeze

## Stage handoff compiler boundary

`stage-handoff.<stage>.md` is the parent-owned compiled entry for child work.

It must stay:
- minimal-workset first
- Markdown-first
- path/ref heavy rather than body-copy heavy
- bounded to one stage-local question
- explicit about the current round root / output targets

Default expectation:
- hot refs first
- warm refs only if still needed
- cold refs as pointers only
- no disguised larger context just because the child is isolated

Cross-platform note:
- the compiled handoff is the portability seam
- child runtime primitive may vary by platform, but the handoff/verdict shape must stay stable across OpenClaw / Codex / future platforms

## Same-repo continuation boundary

If the current round launches a child stage, the parent still owns continuation of the same repo flow.

Current production meaning:
- parent may wait / poll / block while the isolated child runs
- child may take time
- the same repo mainline may not default to “launch now, consume verdict in a later user turn”
- using an isolated child on one platform and a different isolated executor on another platform must not change repo owner/closure semantics
- if a current round root already exists and the delivery tail is still pending, the parent must keep the same run alive rather than outwardly soft-stopping after `repo-round-verdict`

So the repo flow should only be treated as truthfully paused when there is a real bounded blocker,
not merely because child work is still running.

## Tail completion boundary

`repo-round-verdict` is not the repo-mainline completion gate.

Fail-closed meaning:
- the parent may not outwardly say the repo flow is done while `delivery-report-bridge` / `final-local-review` remain unconsumed
- after the delivery tail, the parent should still run one explicit experience-sedimentation check (`no-new-delta` or one thin `learning-delta`)
- only then may the parent freeze `repo-mainline-done` or a truthful blocked-tail boundary

## Round storage boundary

Each bounded live round should have one current round root.

Default first-cut shape:
- `reports/.../rounds/<repo>/<round>/`
- `round-summary.md`
- `objects/`
- `artifacts/`

Runtime instances belong there:
- parent round objects
- child verdict / receipt objects
- raw artifacts or thin artifact pointers

Top-level refs/contracts do **not** become runtime sinks.

## Hard truth rules

- one finished finding does **not** imply repo queue completion
- `historical accepted` does **not** imply current-round handling
- if any in-scope finding still lacks a current-round terminal disposition, the repo is still unfinished
- if any row is still `unfinished`, closure-side objects do not exist yet in the truthful active contract
- repo-level output must answer the full disposition matrix, not only the prettiest fresh receipt
