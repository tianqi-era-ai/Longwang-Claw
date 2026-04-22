# Owner / placement matrix (active V4.4 selection/start cut)

## Purpose

This ref freezes the current **high-visibility split** between:
- `semantic owner`
- `runtime placement`

These are no longer allowed to collapse into one vague idea.

Hard meaning:
- `semantic owner` = who owns meaning, accept/reject, final freeze, and repo-level truth responsibility
- `runtime placement` = where the object or stage is produced / executed

So:
- `parent-owned` does **not** imply `parent-executed`
- `isolated-produced` does **not** imply `child-owned`

---

## Current frozen matrix

### Parent-owned stage + must-isolated

#### `repo-selection-pack`
- semantic owner: `parent`
- runtime placement: `must-isolated`
- hard meaning:
  - selection meaning stays parent-owned,
  - but runtime execution now happens in one bounded child-agent / isolated-executor stage,
  - and the stage may return only proposal/check results rather than frozen repo choice

### Parent-owned + must-isolated-produced

#### `repo-selection-proposal`
- semantic owner: `parent`
- runtime placement: `must-isolated-produced`
- hard meaning:
  - this is the thin proposal returned from `repo-selection-pack`,
  - it may warn / compress / propose,
  - it may not freeze final repo choice

### Parent-owned + isolated-produced

#### `repo-state-relocation`
- semantic owner: `parent`
- runtime placement: `isolated-produced`
- hard meaning:
  - relocation truth still belongs to the parent,
  - but production execution is no longer assumed to be parent-inline by default

#### `repo-task-brief`
- semantic owner: `parent`
- runtime placement: `isolated-produced`
- hard meaning:
  - the brief is still the parent start anchor,
  - but it may be drafted in isolated runtime and then accepted/frozen by the parent

#### `repo-findings-board`
- semantic owner: `parent`
- runtime placement: `isolated-produced`
- hard meaning:
  - board ownership stays at the parent,
  - isolated runtime may prepare the draft,
  - coverage truth still becomes real only after parent consume/freeze

#### `parent-draft-pack`
- semantic owner: `parent`
- runtime placement: `isolated-produced`
- hard meaning:
  - this is the thin accept/reject packet returned from `repo-start-pack`,
  - it may propose queue scope,
  - it may not freeze queue scope or repo closure truth

#### `external-readout`
- semantic owner: `parent`
- runtime placement: `isolated-produced`
- hard meaning:
  - outward wording may be produced in isolated runtime,
  - but it is still only a projection of already-frozen parent closure truth,
  - and its allowed truth source is only frozen `repo-closure-review + coverage_snapshot`

### Parent-owned + parent-executed

#### `current queue posture`
- semantic owner: `parent`
- runtime placement: `parent-executed`

#### `parent-selection-acceptance`
- semantic owner: `parent`
- runtime placement: `parent-executed`
- hard meaning:
  - the parent accepts / rejects / overrides `repo-selection-proposal` here,
  - and final repo choice freeze still belongs only to the parent

#### `next queue item`
- semantic owner: `parent`
- runtime placement: `parent-executed`

#### `next gate`
- semantic owner: `parent`
- runtime placement: `parent-executed`

#### `repo-closure-review`
- semantic owner: `parent`
- runtime placement: `parent-executed`

#### `repo-round-verdict`
- semantic owner: `parent`
- runtime placement: `parent-executed`

#### `final-local-review`
- semantic owner: `parent`
- runtime placement: `parent-executed`

### Child-stage + must-isolated

#### `env-bootstrap`
- semantic owner: `child-stage`
- runtime placement: `must-isolated`

#### `finding-replay`
- semantic owner: `child-stage`
- runtime placement: `must-isolated`

#### `distillation`
- semantic owner: `child-stage`
- runtime placement: `must-isolated`

#### `delivery-reports`
- semantic owner: `child-stage`
- runtime placement: `must-isolated`

### Parent-owned handoff / child-owned verdict seam

#### `stage-handoff.<stage>.md`
- semantic owner: `parent`
- runtime placement: `parent-executed`
- hard meaning:
  - handoff compilation stays a parent control-surface act,
  - even when the child itself runs isolated

#### `stage-verdict.<stage>.md`
- semantic owner: `child-stage`
- runtime placement: `must-isolated-produced`
- hard meaning:
  - the child returns stage-local truth,
  - but repo-level freeze still belongs to the parent

---

## Queue-scope freeze rule

Even when early repo-start objects are isolated-produced,
final freeze of:
- `current queue posture`
- `next queue item`
- `next gate`

still belongs only to the parent.

Workers may:
- draft
- propose
- compress
- pre-structure

Workers may **not**:
- silently freeze queue scope
- silently reinterpret repo closure truth
- silently convert proposal into accepted board truth

---

## Immediate consequences

### 1. Do not read `parent-owned ~= parent inline`
That reading is now explicitly wrong.

### 2. Do not read `isolated-produced ~= child-owned`
That reading is now explicitly wrong.

### 3. Do not let `external-readout` become a second closure-review
Its placement may be isolated; its owner remains parent.

### 4. Do not let child runtime placement steal repo truth
A child may produce:
- receipt
- blocked
- fixed-point
- thin writeback
- stage-local verdict

A child may not produce:
- final repo choice freeze
- repo closure
- `repo-closed`
- final coverage truth
- final queue-scope freeze

---

## Relation to later cuts

- this ref freezes the **owner / placement split** itself
- `P2` formalized the repo-start side into `repo-start-pack / parent-draft-pack`
- `P3` froze board / closure / verdict semantics around current-round terminal disposition
- `P4` now freezes queue-scope final freeze as `current queue posture / next queue item / next gate`
- see also:
  - `references/repo-start-pack.md`
  - `references/repo-queue-workflow.md`
  - `references/parent-minimal-core.md`
- later runtime-policy tightening may further harden exception handling,
  but the dual-field reading frozen here should not drift back
