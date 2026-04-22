# Content selection and publishing rules

## Supported source shapes

### 1. Loop9 run directory

Typical shape:
- `original_goal/`
- `shared_context/`
- `solution_v*/`
- `validation_report_v*/`
- optional `medium_risks.md`

Publishing rule:
- for sharded artifact directories, discover **all** `partNN.md` files and concatenate them in numeric order as the canonical doc body
- do not publish only `part01.md` when later parts exist
- keep `index.md`, `manifest.json`, and other sibling files as attachments or side references when useful
- prefer the **highest** `solution_vN`
- prefer the **highest** `validation_report_vN`
- if the run also contains `real_pocs/real_poc_solution_vN`, `real_pocs/real_poc_validation_report_vN`, `real_pocs/real_poc_final_status.json`, or `real_pocs/*.py`, treat those as first-class `05-PoC与验证` artifacts too

### 2. PoC bundle directory

Typical shape:
- `brief.md`
- `solution.md`
- `validation_report.md`
- `shared_context.md`
- `poc-drafts/overview.md`
- `verification-pack/verification-overview.md`
- `verification-pack/verification-matrix.md`

Publishing rule:
- `brief.md` goes under `05-PoC与验证`
- `solution.md` goes under `03-审计结论`
- `validation_report.md` and verification overviews go under `04-验证报告`
- `shared_context.md` goes under `02-审计过程`
- PoC drafts and runnable artifacts are internal-only and should remain in `05-PoC与验证`

## Naming rule for run-specific docs

Use stable, source-derived titles:
- `<run-id> · 原始目标`
- `<run-id> · 共享上下文`
- `<run-id> · solution_vN`
- `<run-id> · validation_report_vN`
- `<bundle-id> · brief`
- `<bundle-id> · poc overview`

## Project inference rule

Try in this order:
1. explicit user-provided project title
2. non-generic suffix in the run/bundle directory name
3. artifact content hints (repo path, GitHub URL, target path)
4. fallback to root directory name

If inference confidence is low, explicitly say so and prefer an operator-provided title before publishing broadly.

## Internal-only posture

This skill is for the **internal main knowledge base** only.
Do not auto-create external sharing links or client-facing public spaces.
Do not weaken the wording of sensitive internal notes just to make them presentation-friendly.

## Python body sync rule

When a run contains `real_pocs/*.py`:
- create one dedicated doc per `.py` file under `05-PoC与验证`
- the doc body should contain the **full source code**, not just a summary
- do not manually compress, rewrite, or shorten the code body during sync
- use a stable artifact key like `realpoc::<run-id>::py::<filename>.py`
- later syncs should **overwrite** that same doc when the file content changes
- do not treat `.py` bodies as disposable attachments only; the readable doc page is part of the archive design

## Update strategy

### Stable index docs
- `00-总览与目录`
- `00-项目总览`
- phase landing pages like `03-审计结论`

These should usually be overwritten from generated markdown.

### Artifact docs
Run-specific or bundle-specific docs should be treated as stable records:
- overwrite only when syncing the exact same artifact key again
- otherwise create a new child doc for the new artifact/version

### Sync log
Append short timestamped lines or rewrite from a structured log model if needed.
