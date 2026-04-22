---
name: loop9-status
description: Check the current Super8 Loop9 long-task status from chat. Use when the user asks for the latest progress, wants to inspect recent output, or wants a short status summary for a running Loop9 audit workflow, including linked `loop9-real-poc` observe runs, shared PoC workspace state, and recent real-PoC iteration runs.
user-invocable: true
metadata: {"openclaw":{"emoji":"📡","requires":{"bins":["bash"]}}}
---

Check the current Super8 Loop9 long-task state through the single standard status script.

## Canonical command

Always run exactly:

```bash
cd ~/.openclaw/workspace/Super8
./.opencode/_scripts/loop9_status.sh
```

Use `exec` on the host.

## What to summarize for the user

After running the status script, summarize briefly:
- whether a long task appears active or recently active
- fleet-level concurrency when relevant (`active_waves`, `active_unique_targets`)
- latest main audit observe directory
- latest `loop9-real-poc` observe directory when present
- linked audit-run PoC state when present (`latest_real_poc_solution_dir`, `latest_real_poc_validation_dir`, `shared_poc_py_count`)
- file-level real-PoC workflow status when present (`real_poc_final_status.json`, `workflow_completion`, `workflow_completion_reason`, `min_iterations_satisfied`)
- latest standalone real-PoC iteration run when present (`latest_real_poc_iteration_run_dir`, latest solution/validation, validation status)
- whether report files already exist
- latest session title
- whether there is meaningful progress since the last known state
- whether heartbeat-style sync looks due when relevant (`latest_activity_*`, `last_user_sync_*`, `heartbeat_sync_due`)
- whether a runtime failure looks like a provider/API/model-interface problem versus a likely workflow/content problem

If `runtime_issue_summary` appears, surface it prominently and bias toward: **do not initially blame the Loop9 workflow itself** unless the evidence points to file/layout/control-flow mistakes instead of provider-side failure.

## Important behavior

- Do not kill anything while checking status.
- Treat this as a read-only inspection.
- Do not overreact to short quiet periods.
- 1-2 hours is normal; 3-5 hours is possible.

## Output style

Be concise and operational.
Mention exact file paths when useful.
If a final report exists, point to it first.

### Preferred human-readable summary format (Telegram / mobile-friendly)

Default to a **card-style summary with red/yellow/green status markers**, not markdown tables.

Recommended structure:

- `🟢` = completed / healthy / usable result ready
- `🟡` = running / partial / warning / needs watching
- `🔴` = failed / stalled / hard blocker

Preferred layout:

- `🟡 1) <current active task>`
  - status
  - target / policy when useful
  - observe path
  - short judgment
- `🟡 2) <current risk or blocker>`
  - current error / uncertainty
  - whether it looks like provider/API/model-interface vs workflow/content problem
- `🟡 3) <fleet / concurrency snapshot>`
  - active waves / active targets only if relevant
- `🟡 4) <whether new deliverables exist>`
  - reports present or absent
- `🟢 5) <most complete finished result>`
  - latest usable passed run
  - best paths to read next
- `🟡 6) <real-poc or secondary workflow state>`
  - shared PoC count
  - single-round validation vs overall workflow completion

Finish with a short `一句话总览` block using the same markers.

Avoid markdown tables by default because Telegram renders them poorly.
Only use a table if the user explicitly asks for one.
