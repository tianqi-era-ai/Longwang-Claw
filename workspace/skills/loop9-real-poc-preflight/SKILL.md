---
name: loop9-real-poc-preflight
description: Preflight self-check for Super8 Loop9 real-poc candidates before formal selection, claim, or launch. Use when a Loop9 real-poc cron job, wrapper, or manual operator needs to inspect one or more completed audit runs and decide whether they are: (1) already-success and should be skipped, (2) still legitimately launchable, (3) blocked for human review, or (4) eligible for a narrow safe-fix that only repairs parser/materialization gaps in `real_poc_final_status.json` without changing real PoC content.
---

# Loop9 Real POC Preflight

Use this skill as the **thin self-check layer** immediately before the real-poc workflow does its formal selection / claim / launch work.

This skill is not a new orchestrator. It should only:
- inspect current file-backed state
- classify the candidate conservatively
- optionally apply a **narrow safe-fix** to `real_poc_final_status.json`
- return an explicit preflight decision

## Canonical command

```bash
python3 {baseDir}/scripts/loop9_real_poc_preflight.py <completed-loop9-run-dir-or-child>
```

Optional safe-fix mode:

```bash
python3 {baseDir}/scripts/loop9_real_poc_preflight.py --apply-safe-fixes <completed-loop9-run-dir-or-child>
```

For machine consumption, prefer:

```bash
python3 {baseDir}/scripts/loop9_real_poc_preflight.py --json <run-dir>
```

Run on the host.

## Intended cron / wrapper position

Use this skill **after** a candidate audit run has been identified, but **before** any formal `claim poc` / launch step.

Recommended order:
1. pick candidate
2. run this preflight
3. branch on `preflight_decision`
4. only then claim / launch if allowed

Do not let the cron wrapper skip this check once it is adopted as the formal gate.

## Decision semantics

The script emits one of these decisions:

- `skip-already-success`
  - the run is already in a file-backed success state
  - this may come from either:
    - the fresh deterministic rebuild, or
    - the current on-disk `real_poc_final_status.json` when that file itself is still a verifiable success record with existing round artifacts
  - do not launch again
- `skip-already-success-after-safe-fix`
  - the run was stale only because of a narrow parser/materialization gap
  - safe-fix was applied successfully
  - do not launch again
- `safe-fix-available`
  - a narrow safe-fix appears eligible
  - re-run with `--apply-safe-fixes` or let the wrapper decide
- `allow-launch`
  - the run still appears legitimately launchable
- `block-needs-human`
  - the state is not trustworthy enough for automatic launch
  - escalate instead of guessing

## What counts as a safe-fix

Safe-fix scope is intentionally narrow.

Allowed:
- refresh `real_poc_final_status.json` when the run is already-success under the current deterministic parser, but the on-disk file still says `workflow_completion=unknown` with blank latest validation status
- parser/materialization repairs only

Not allowed:
- changing PoC `.py` files
- changing `manifest.json`
- promoting a run just because some run-local validator says `PASSED`
- overwriting explicit non-success states like `FAILED` / `not-yet` just to make the state look prettier

## Important guardrail

Do **not** equate these two things:
- a run-local validator artifact saying `PASSED`
- the shared real-poc workflow having truly finished

This distinction is the whole reason this preflight exists.

A run may still be `block-needs-human` even if some local validation note looks positive.

## Current implementation boundary

This skill currently relies on the existing deterministic state builders:
- `workspace/skills/loop9-real-poc/scripts/refresh_real_poc_status.py`
- `workspace/lib/loop9_automation/detect.py::_classify_poc_candidate()`

So treat this skill as a **formal preflight adapter** over the current Loop9 state model, not an independent source of truth.

## Output contract for wrappers

When consuming JSON output, read:
- `results[].preflight_decision`
- `results[].fresh.classification.bucket`
- `results[].safe_fix.eligible`
- `results[].safe_fix.applied`

Wrapper guidance:
- `skip-already-success*` → skip candidate
- `safe-fix-available` → apply only if your wrapper explicitly allows safe-fixes
- `allow-launch` → proceed to formal claim / launch
- `block-needs-human` → stop automation and surface the case

## Exit codes

- `0` → no blocking condition
- `10` → safe-fix available but not applied
- `20` → block-needs-human present

Use JSON output as the primary machine interface; treat exit codes as coarse control signals.
