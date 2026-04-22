---
name: loop9-real-poc
description: Use the OpenCode Loop9 workflow itself to turn an existing completed Super8 Loop9 audit run into shared reusable PoC Python files. Use when the user wants PoC generation to stay inside the core Loop9 workflow instead of using the heavier outer PoC-builder path; especially when they want: (1) an existing Loop9 audit run as input, (2) one passed vulnerability → one Python PoC file, (3) a shared PoC directory that is reused across Loop9 iterations, and (4) iterative refinement with a default minimum of 3 rounds when no stricter user-specified round count is required.
user-invocable: true
---

# Loop9 Real PoC

Use this skill when the user wants a **completed Loop9 audit result** to be converted into real PoC `.py` files by the **OpenCode Loop9 workflow itself**.

Important real-usage note:
- In the user's common manual prompt style, this skill is used as a selector over `~/.openclaw/workspace/Super8/temp/loop9`: choose **one completed audit project that has not yet gone through `loop9_real_poc`**, then launch the skill flow on that project.
- So this skill should not be mentally reduced to “just run on any path”; in the user's real workflow it often includes the pre-step of scanning the Loop9 run pool, finding one suitable completed audit result, and only then starting PoC generation.

## Core idea

Keep the outer layer thin.

Outer layer responsibilities:
- choose the completed audit run dir
- define the shared PoC directory
- define the global manifest path inside `real_pocs/manifest.json`
- define the file-level workflow status path inside `real_pocs/real_poc_final_status.json`
- define the round-output naming convention for `real_pocs/real_poc_solution_vN/` and `real_pocs/real_poc_validation_report_vN/`
- provide the PoC task prompt template
- provide the simple Python PoC template
- launch OpenCode `loop9`

Inner Loop9 responsibilities:
- read the existing audit results
- identify passed findings
- create or refine one PoC `.py` per passed finding
- reuse the shared PoC directory across iterations instead of restarting from zero
- leave auditable per-round solution / validation artifacts instead of only editing final `.py` files

## Canonical entrypoint

```bash
python3 {baseDir}/scripts/run_loop9_real_poc.py <completed-loop9-run-dir>
```

Run on the host.

## Accepted input

Pass a path inside or equal to a completed Loop9 audit run directory, for example:

- `~/.openclaw/workspace/Super8/temp/loop9/20260312-125445-DiscuzX-b123`
- `~/.openclaw/workspace/Super8/temp/loop9/20260312-125445-DiscuzX-b123/solution_v3`
- `~/.openclaw/workspace/Super8/temp/loop9/20260312-125445-DiscuzX-b123/validation_report_v3`

The script will normalize upward to the run dir.

## Shared PoC directory rule

Default shared PoC directory:

```text
<loop9-run-dir>/real_pocs/
```

This directory is the persistent shared state.

Loop9 must:
- read existing `.py` files from this directory every round
- update them in place when a better version is produced
- create a new file only when that finding has no PoC file yet
- avoid rewriting all files from zero on every round

But `real_pocs/` is not the only trustworthy record. Important work must also be reflected in per-round solution / validation artifacts.

## Manifest rule

Maintain a global manifest at:

```text
<loop9-run-dir>/real_pocs/manifest.json
```

This file is the global mapping layer for the shared PoC workspace. It should summarize the current finding ↔ file ↔ status relationship, and it complements rather than replaces file headers or per-round artifacts.

Also maintain a file-level workflow status marker at:

```text
<loop9-run-dir>/real_pocs/real_poc_final_status.json
```

This file is for **workflow-level completion semantics**, not per-round acceptance semantics. The critical distinction is:
- `real_pocs/real_poc_validation_report_vN` PASSED = the current round passed
- `real_pocs/real_poc_final_status.json` workflow_completion = whether the overall PoC workflow is actually finished

Use the deterministic helper below whenever you need to refresh the file from disk state:

```bash
python3 {baseDir}/scripts/refresh_real_poc_status.py <completed-loop9-run-dir>
```

## Round artifact rule

For the MVP old-pattern alignment, every round must leave two directories under the shared PoC workspace:

```text
<loop9-run-dir>/real_pocs/real_poc_solution_vN/
<loop9-run-dir>/real_pocs/real_poc_validation_report_vN/
```

Each directory must contain at least:

```text
index.md
```

These round artifacts exist to preserve:
- attempted modifications
- validation objections / acceptance
- justification for freezing or continuing
- anti-shortcut evidence that the controller/solver/refiner did not skip process and jump straight to final file edits

## PoC file rule

- one passed finding → one Python PoC file
- keep the style close to `template/poc_template.py`
- prefer simple, direct, sufficiently usable PoCs over decorative framework-heavy output
- if full exploit closure is unsafe or blocked, produce the best bounded lab-safe PoC the finding honestly supports
- every `.py` must include a fixed source-trace header (`Source-Run`, `Source-Report`, `Source-Finding`, `Classification`, `Preconditions`, `Defense-Model`, `Defense-Notes`, `Payload-Constraints`, `Confidence`, `Status`)
- do **not** force fake defense analysis onto every finding; if no meaningful defense signal is observed, use `Defense-Model: none-observed` and `Defense-Notes/Payload-Constraints: none`
- if source evidence or the payload design suggests filters / allowlists / deny-lists / `disable_functions` / dynamic config-or-database-driven policy sources, treat defense awareness as part of the PoC design rather than an optional afterthought

## Mapping rule

Before modifying files in any round, Loop9 must first reconcile the current report set against the current shared PoC directory.

Required behavior:
- enumerate all relevant passed findings from the completed audit run
- read `real_pocs/manifest.json` if it already exists
- enumerate existing `.py` files under `real_pocs/`
- use the source-trace header to build a strict 1v1 finding ↔ file mapping
- update the manifest to reflect the current mapping state
- detect duplicates, omissions, and ambiguous mappings before creating or editing files

Do not let one finding fan out into multiple overlapping files unless their role difference is explicit and necessary.

## Iteration rule

The generated prompt explicitly asks Loop9 to:
- use the existing audit run as source material
- target all already-passed findings
- continue refining shared PoC files across rounds
- write a round `solution/index.md` before major file edits
- write a round `validation/index.md` after those edits
- avoid meaningless structural churn once a PoC is already mature
- switch later rounds into static parameter-level acceptance/freeze checks once the PoCs are materially complete
- keep reporting `状态：已冻结，无需修改` when a freeze-check round finds nothing worth changing
- still write round artifacts even when a freeze-check round results in zero code changes

## Useful optional flags

- `--poc-dir <dir>` — override shared PoC directory
- `--min-iterations <n>` — default `3`
- workflow-level max-iteration semantics follow the core Loop9 controller default of `20`
- `--transport tmux|direct` — default `tmux`
- `--prompt-out <path>` — override generated prompt file path
- `--dry-run` — build prompt + directories but do not launch OpenCode

## Response style after launch

After launching, report briefly:
- normalized audit run dir
- shared PoC dir
- file-level workflow status path (`real_pocs/real_poc_final_status.json`)
- that OpenCode Loop9 real-PoC workflow has been launched
- that it is long-running and will reuse the shared PoC directory across rounds
