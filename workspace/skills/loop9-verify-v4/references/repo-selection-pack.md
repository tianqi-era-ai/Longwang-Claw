# Repo-selection-pack / parent-selection-acceptance (production V4.4 cut)

## Purpose

This ref freezes the current production **pre-start selection carrier** for `loop9-verify-v4`.

One-line freeze:

> repo intake should no longer default to a parent-inline selection narration.
> Before repo mainline starts, selection should run through one thin, bounded,
> cross-platform `child agent / isolated executor` stage,
> then return to the parent for the final repo-choice freeze.

## What `repo-selection-pack` is

`repo-selection-pack` is a **parent-owned pre-start selection stage**.

Current owner / placement:
- semantic owner: `parent`
- runtime placement: `must-isolated`

It is not:
- an independent child skill,
- a second parent,
- a thick selector / ranking system,
- a repo-start worker,
- or a closure surface.

Its job is only to compress repo selection into one bounded pre-start cut.

## Two modes

The stage now covers both:

### 1. `selection_mode = auto-select`
Use when `repo_ref` is absent and the parent needs a truthful default repo.

Hard meaning:
- answer repo-complete need,
- not proof/sample convenience,
- not glamour,
- and not historical replay beauty.
- `auto-select` has no authority to supersede canonical delivery suppressors.

### 2. `selection_mode = explicit-repo-check`
Use when the user already provided `repo_ref`.

Hard meaning:
- the explicit repo still has semantic priority,
- but it does **not** bypass selection checking,
- and the child stage may still say the requested repo looks high-risk / already delivered / continuation-conflicted.

The child may return:
- `accept-advice`
- `high-risk-reject-advice`
- `manual-confirm-needed`

The child may **not**:
- silently override the explicit repo,
- silently pick another repo as frozen truth,
- or directly enter repo mainline.

## Required input posture

The parent should compile one thin `repo-selection-pack` request with only:
- `selection_mode`
- `requested_repo_ref` when provided
- current continuation anchors
- the smallest state sources needed to judge repo-complete need
- explicit stop line / non-goals
- bounded output expectations

### Default allowlist

By default the stage may read only:
- current-round continuation anchors
- `runs/repo-verify-*/repo_verify_summary.json`
- canonical delivery markers
- support-level `real_pocs/manifest.json`

Reading rule:
- only accepted **in-flight** continuation anchors count as continuation authority
- detached old env/bootstrap/replay artifacts may be cited only as support when stronger suppressors do not already close the repo

### Default denylist

By default the stage may **not** read:
- thick audit prose
- large replay receipt dumps
- closure-side objects
- `experience-index.md`
- thick shared context / historical retrospectives
- thick ranking prose / scoreboards

If the child seems to "need" those anyway, read that as:
- `selection-compiler drift / invalid pre-start input`

not as permission to widen the packet.

## Required outputs

A valid `repo-selection-pack` may return only:
- one thin `repo-selection-proposal.*.md`

The parent must then write:
- one thin `parent-selection-acceptance.*.md`

`repo-selection-proposal` should carry at least:
- `selection_mode`
- `requested_repo_ref` when present
- `proposed_repo_ref`
- `continuation_anchor_status`
- `selection_basis`
- `suppressed_candidates`
- `next_action`

Hard meaning:
- proposal only,
- no queue freeze,
- no repo closure truth,
- no current round root creation,
- no direct jump into `repo-start-pack`.

## Parent accept / reject rule

The parent still owns:
- accept / reject
- explicit override
- and final repo choice freeze

Current production reading:
- explicit `repo_ref` still wins semantically
- but if the child returns `high-risk-reject-advice`, the parent should make any override explicit rather than silently ignoring it
- if the child exits without a usable `repo-selection-proposal`, the parent should record caller-side timeout-budget failure and rerun before any repo-choice freeze
- if `selection_mode = auto-select` and canonical delivery suppressors already exist, accepting the same repo anyway is invalid unless the intake has first become an explicit reopen path
- if `selection_mode = auto-select` and the candidate only offers post-closure live verification / status sync of an already-delivered repo, that proposal is invalid; the slot should move to another unfinished repo or return `no eligible unfinished repo`
- once selection is accepted, later start-side objects should inherit only the accepted thin basis rather than replaying the whole selection narration

## Storage note

`repo-selection-pack` runs **before** current round root fix.

So its request / proposal / acceptance are a bounded **pre-start intake surface**,
not yet ordinary current-round objects.

Current hard meaning:
- the parent chooses one bounded pre-start write surface for this stage
- only after selection acceptance does the parent fix the current round root
- once the round root exists, `repo-task-brief` should cite the accepted selection basis rather than re-copying the entire selection narration

## Cross-platform runtime reading

Canonical runtime meaning is only:
- one bounded `child agent / isolated executor`
- separate context boundary from the parent
- thin input packet
- proposal-only return

Platform mappings may differ:
- `OpenClaw = bounded subagent / isolated runtime`
- `Codex = bounded child-agent thread`
- `other platforms = nearest equivalent isolated executor`

The mapping is adapter detail, not the contract itself.

## Hard rules

- `repo-selection-pack` is the production default pre-start selection path
- it is `must-isolated`
- it is stage-only, not an independent child skill
- explicit `repo_ref` keeps semantic priority, but not bypass privilege
- `repo-selection-pack` may propose, compress, and warn
- it may not freeze final repo choice
- it may not create the current round root
- it may not call `repo-start-pack` by itself
- detached historical env/replay artifacts are support-only and may not silently act as continuation anchors in `auto-select`
- `auto-select` may not supersede canonical delivery suppressors
- old runtime liveness on a shared Tencent CVM is support-only and may not by itself justify selecting an already-delivered repo again
- `repo-start-pack` should consume accepted selection basis, not raw multi-repo narration
