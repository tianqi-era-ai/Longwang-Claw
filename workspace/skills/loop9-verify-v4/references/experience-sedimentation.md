# Experience sedimentation

This is the current **built-in substage** for repo-level experience sedimentation inside `loop9-verify-v4`.

It is **not** a separate skill yet.

## Why this exists

The family already has a real `distillation` child, but later executors still need one explicit place that answers:
- what the current sedimentation unit is,
- how it inherits the older V2 experience-card discipline,
- what may stay case-local,
- and what is absolutely not allowed to be promoted into skill-level default truth too early.

## Current carrier in V4/V4.1

Use this three-layer reading order:

1. **Abstract layer first**
   - write the smallest reusable truth in one sentence
   - this comes before repo-specific narration
2. **Case layer second**
   - explain how that abstract truth manifested in the current repo round
   - attach receipts / board state / blocker shape
3. **Promotion judgment last**
   - decide whether the result is only `observed`, or deserves later `validated` / `promoted` discussion

Do **not** start by writing a repo-specific lesson and then pretending it is the abstract rule.

## Relation to older V2 method

The current discipline inherits the older V2 experience-card method:
- smallest durable unit must be AI-readable
- promotion levels stay:
  - `trial`
  - `observed`
  - `validated`
  - `promoted`
- what gets promoted should be the **higher-level cross-sample truth**, not the route-specific / project-specific card itself

In the current V4/V4.1 family, the immediate thin output is still usually a **`learning-delta` object**, not a separate full standalone card system.

## Carrier split in current practice

The current mechanism now has three distinct carriers, and they should not be mixed together:

1. **Family-facing thin carrier**
   - at most one round-local `learning-delta.*.md` by default
   - lives under the current round root `objects/`
   - this is the only carrier that should compete for family-level visibility
2. **Repo-local case carrier**
   - zero to many repo-local experience cards when the user explicitly asks for them, or when several distinct PoC-level tricks are worth retaining
   - lives under the current report root `experience/cards/`
   - these cards are explanatory case memory, not family defaults
3. **Visibility carrier**
   - at most one thin index exposure in `references/experience-index.md`
   - this is only a pointer layer for later executors

If one repo round yields several useful PoC-level tricks but they all roll up to one higher-level abstract truth, prefer:
- **one** family-facing `learning-delta`
- plus **multiple** repo-local experience cards

Do **not** try to make every useful PoC trick become its own family-facing delta.

## Where this substage lives in the workflow

Current location:
- repo board refresh
- repo closure review
- external readout
- repo round verdict
- delivery-report-bridge
- final-local-review
- **experience sedimentation check (current built-in substage)**

The current distillation-side seam remains:
- child may return `learning-delta refs` or `no-coverage-delta`
- parent still owns repo closure and final interpretation

So the current substage is:
- **distillation-compatible**
- **parent-owned for keep / no-keep / no-new-delta judgment**
- **post-closure / post-tail**
- **non-gating for repo closure itself, but still a required explicit check before repo-mainline completion**
- **not** an excuse to reopen replay or grow a thick planner
- **not** a recurring liveness-monitor lane for later hourly verify turns

## Default output rule

For one finished repo mainline, the parent should always run one explicit sedimentation check.

That check should default to one of these:
- `no-new-delta`
- or at most **one thin observed learning-delta**
- by default, exactly one explicit sedimentation check belongs to one finished repo mainline
- if a final live acceptance note is useful, keep it lightweight and inside the same run rather than turning it into a later recurring verify slot

Prefer `no-new-delta` when the round only reconfirms already-known family truth.

Do **not** force a new delta just because a repo round happened.
Do **not** skip the check just because the likely answer is `no-new-delta`.
Do **not** turn later periodic liveness/status-sync of the delivered repo into fake repo-complete progress; that belongs to a separate monitor/heartbeat/status lane.

If the user explicitly asks for repo-local经验卡 / experience cards, the parent may also write
auxiliary case-layer cards under the report's own experience tree.
Those cards stay repo-local and explanatory:
- they do **not** replace the thin family-facing `learning-delta`
- they do **not** automatically become skill-level defaults
- they should still follow the same ordering: abstractable trick first, case manifestation second, promotion judgment last

## Output selection ladder

Use this order after the delivery tail has completed or truthfully blocked:

1. ask whether the round produced a **new bounded abstract truth**
   - if no, prefer `no-new-delta`
2. if yes, ask whether that truth is still **one family-facing abstract unit**
   - if yes, write one thin `learning-delta`
3. separately ask whether the user explicitly wants repo-local case memory, or whether multiple distinct PoC-level tricks deserve retention
   - if yes, write repo-local experience cards
4. only if the new abstract truth is worth later executor visibility, refresh `references/experience-index.md`

This means one round may legitimately end with:
- `no-new-delta`
- or `no-new-delta + several repo-local cards`
- or `one learning-delta`
- or `one learning-delta + several repo-local cards`

That is not a contradiction because the carriers serve different scopes.

## What counts as reusable truth

Useful sedimentation is **not** limited to “a new exploit landed”.

A round may also produce reusable truth such as:
- a blocker-diagnosis pattern that prevented a false negative freeze
- a shared-unblock pattern that reopened a whole row cluster
- a payload-minimization / validator-noise bypass that preserved the same sink claim
- a landing-proof discipline that prevented overclaim
- a truthful blocked outcome that clarified a family boundary

The reusable unit should name the method/boundary,
not merely the fact that one repo happened to pass or fail.

## Storage and write-set boundary

Keep the write targets explicit:
- family-facing `learning-delta` -> current round root `objects/`
- repo-local experience cards -> current report root `experience/cards/`
- family visibility pointer -> `skills/loop9-verify-v4/references/experience-index.md`

Do not blur these layers together:
- round-local objects should not be replaced by report-level cards
- report-level cards should not be dumped into `references/`
- the visibility index should not become a case library

If a new bounded abstract truth is worth exposing to later executors, refresh the lightweight registry at `references/experience-index.md` with:
- one short abstract entry,
- its current state,
- relevance hints,
- and deep refs back to the round-level artifact.

The index entry is visibility only; it is not the full sedimentation artifact.

## Minimal structure for a V4-native learning-delta

Use a thin shape like:
- `delta identity`
- `abstract layer`
- `case layer`
- `evidence refs`
- `level judgment`
- `no-overclaim note`

The key ordering is:
- **abstract truth first**
- **case manifestation second**
- **promotion judgment last**

For repo-local cards, keep the same ordering in a case-friendly shape such as:
- `Identity`
- `Applicability`
- `What Worked`
- `What Did Not Work`
- `Evidence Refs`
- `Safe Reuse Rule`
- `Recommended Next Jump`

The important point is that even a card should still expose the reusable trick before drifting into narration.

## Promotion discipline

### `observed`
Use when:
- the truth is newly visible,
- one repo round supports it,
- but it is still too early to call it cross-sample stable.

This is the current default for V4-native deltas.

### `validated`
Use only when:
- multiple near-enough samples support the same abstract truth,
- the truth is not just a bridge accident,
- and the boundary of applicability is materially clearer.

### `promoted`
Use only when:
- the promoted item is the **higher-level abstract rule**,
- not the repo-specific or route-specific card itself,
- and it is safe for that rule to influence the family's default reading / next-step selection.

## Explicit anti-patterns

Do **not**:
- write repo-specific lessons straight into skill-level canonical references
- promote a single repo's concrete lesson into family default truth
- let experience sedimentation impersonate repo closure
- let new cards/deltas count as live progress by themselves
- let multiple PoC-specific cards pressure the parent into inventing multiple family-facing deltas for the same round
- grow a thick repo-specific fixture tower just to make a harder finding look completed

## One-line freeze

> Abstract first, case second, promotion last.
> Keep repo-specific truth in round artifacts; only lift cross-sample abstract truth toward family defaults.
