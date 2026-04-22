# Stage chain (frozen first-wave form)

## Owner / placement note

The chain below is the **semantic order of control**,
not a promise that every parent-owned object is produced by parent-inline execution.

Read this together with:
- `references/owner-placement-matrix.md`
- `references/repo-queue-workflow.md`
- `references/parent-closure-chain.md`
- `references/runtime-isolation.md`

Current corollary:
- `repo-state-relocation / repo-task-brief / repo-findings-board` remain parent-owned even when their runtime placement is isolated-produced
- final freeze of `current queue posture / next queue item / next gate` remains parent-only

Cross-platform reading:
- when this ref says `child stage`, `isolated`, or `must-isolated`, read that as a cross-platform context-isolation requirement
- platform-native runtime names are adapter detail; the semantic contract is “one bounded child-agent / isolated-executor unit with thin handoff and same-root writeback”

## Default parent skeleton

The default first-wave parent skeleton is now:
- `repo-selection-pack -> parent selection accept/reject -> current round root fix -> repo-start-pack -> parent accept/reject -> current queue posture freeze -> next queue item freeze -> next gate freeze`

`repo-selection-pack` is a **pre-start stage**:
- it runs before current round root fix
- it stays stage-only rather than becoming an independent child skill
- and its proposal returns to one bounded pre-start intake surface before the parent freezes final repo choice

Inside `repo-start-pack`, the current default start-side drafts are:
- `repo-state-relocation`
- `repo-task-brief`
- `repo-findings-board`
- `parent-draft-pack`

After `repo-start-pack` returns, the parent must:
- accept or reject the start-side drafts first,
- choose and freeze the current queue posture first,
- then choose and freeze the next queue item,
- then choose and freeze the next stage from the current next gate.

If a child stage is chosen, the parent must first compile `stage-handoff.<stage>.md`
using the frozen minimal-workset discipline from `references/handoff-compiler.md`,
and keep the current round `objects/` / `artifacts/` targets fixed.

The parent should then bind that stage to one bounded platform-native `child agent / isolated executor`
rather than silently broadening parent inline context.

After that, the parent may choose one of:
- `env-bootstrap`
- `finding-replay`
- `distillation`
- `repo-closure-review` (parent-owned, only after queue completion)

If the chosen stage is a child stage, the parent is expected to keep the same repo flow alive while the isolated child runs:
- waiting / polling / blocking is allowed,
- but splitting the same repo round across a fresh user turn or manual conversation continuation is not the normal continuation path.

After any child stage returns, the parent must re-enter in this order:
- consume `stage-verdict.<stage>.md` as stage-local truth + thin `parent_consume.writeback`
- `repo-findings-board refresh`
- check whether every in-scope finding now has a current-round terminal disposition
- if the queue is still unfinished:
  - freeze refreshed `current queue posture`
  - freeze refreshed `next queue item`
  - freeze refreshed `next gate`
  - choose the next truthful queue move
- only if the queue is fully terminal, run:
  - `repo-closure-review`
  - freeze `coverage_snapshot`
  - `external-readout` as projection-only
  - `repo-round-verdict`
- after repo-level verify truth is frozen, continue the same repo mainline with:
  - `delivery-report-bridge`
  - `final-local-review`
- then run the built-in `experience-sedimentation` check (see `references/experience-sedimentation.md`)
  - explicit output must be `no-new-delta` or one thin `learning-delta`
- if that substage yields a bounded abstract truth worth exposing, refresh `references/experience-index.md`
- only after the delivery tail has completed or truthfully blocked, and after that explicit sedimentation check exists, may the parent treat the repo mainline as done

## Hard rules

- children may not directly chain to each other
- children must return to the parent first
- `repo-selection-pack` is mandatory before repo mainline start, even when `repo_ref` is explicit
- `must-isolated` / `isolated-by-default` stages should use a platform-native child-agent / isolated-executor capability whenever the current platform exposes one
- the same stage-chain contract must stay legible across OpenClaw / Codex / future platforms; API names are mapping detail, not control truth
- the same repo mainline may wait for isolated child work, but it may not default to a `sessions_yield` / fresh-user-turn continuation split
- `repo-selection-pack` may not freeze final repo choice or create the current round root by itself
- `repo-start-pack` is mandatory before entering child work
- `repo-state-relocation` remains mandatory inside that start pack
- `repo-task-brief` refresh is mandatory before child work and before the parent chooses the next queue move
- one bounded live round should keep one current round root
- child outputs and raw evidence must return to that same root
- only the parent may conclude repo-level status
- child verdicts may not emit `round_status`, `repo_status`, `coverage_snapshot`, or `repo-closed`
- `round-closed` does **not** imply `repo-closed`
- if any in-scope finding is still `unfinished`, the parent must keep working the queue rather than emitting closure-side objects
- the parent must apply the thin writeback, then update board first; closure review + frozen coverage snapshot come only after full queue completion
- `external-readout` may only project that frozen closure truth; it may not become a second closure-review
- `delivery-report-bridge -> final-local-review` is the required completion tail after `repo-round-verdict`; it is not an optional nice-to-have
- `repo-round-verdict` may not be outwardly narrated as `repo-mainline-done` while that tail remains unconsumed
- the experience-sedimentation check is mandatory post-tail even when the truthful output is only `no-new-delta`
- only accepted in-flight round anchors count as continuation authority; detached old env/replay artifacts are support-only and may not silently reopen a suppressed repo in `auto-select`
- parent-owned start surfaces may be isolated-produced, but queue-scope final freeze remains parent-only

## Runtime placement defaults (current V4.3 cross-platform reading)

Current first-wave child placement is now:
- `repo-selection-pack = must-isolated` (pre-start only)
- `env-bootstrap = must-isolated`
- `finding-replay = must-isolated`
- `distillation = must-isolated`
- `delivery-reports = isolated-by-default`

Current hard meaning:
- first-wave child work is now `isolated-by-default` in runtime policy
- inline is no longer a current production default for first-wave child work
- any future inline use would be an explicit manual exception, not a silent fallback
- when the platform offers child agents / isolated workers, that is the default carrier for these stages
- regardless of placement, the parent still owns handoff compilation, verdict consumption, board refresh, queue continuation, closure review, final outward truth, and same-repo continuation

## First-wave child stages

The only independent child stages frozen for first-wave repo-mainline use are:
- `env-bootstrap`
- `finding-replay`
- `distillation`
- `delivery-reports`

Pre-start special case:
- `repo-selection-pack` is also `must-isolated`,
- but it remains a built-in stage rather than a named independent child skill.

## Stages kept in the parent layer

These stay in the parent layer for now:
- final repo choice freeze / selection acceptance
- repo-state-relocation
- repo-closure-review
- external-readout
- repo-round-verdict
- final-local-review
