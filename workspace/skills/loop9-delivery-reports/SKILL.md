---
name: loop9-delivery-reports
description: Generate the canonical local `workspace/reports/<repo>/` delivery-report directory after Loop9 repo-level verification has already frozen repo closure truth. Use when a repo has either legacy `repo_verify_summary.json` inputs or a v4 round root / `delivery-report-input.*.json`, and you want the standard local bundle (`00-索引`, repo Chinese report, repo technical summary, included per-finding reports, effective PoCs, HTTP evidence, manifest) created or refreshed.
---

# Loop9 Delivery Reports

Use this skill when repo-level verification is already real and you want the **stable local delivery artifact tree** written immediately afterward.

AI-native control model:

- AI owns source-of-truth selection, drift judgment, discrepancy interpretation, and final acceptance.
- Code only owns bounded deterministic materialization: file emission, copying, manifest writeback, bridge receipts.

High-severity warning:

- if this skill starts being narrated as “run the report script first, then trust it,” treat that as AI-native drift
- if the scripts/ directory starts acting like the semantic owner of coverage truth, PoC binding truth, or publishability truth, stop expansion and repair the route first
- when a bug appears here, do **not** default to “add more Python checks” before re-checking whether the parent lane already drifted into script-first control

This skill is the local-report half of the next Loop9 stage:
- verifier / PoC automation closes technical truth
- this skill freezes that truth into a stable `reports/<repo>/` bundle
- a later Feishu publisher can sync that bundle to the wiki without rediscovering transient runtime artifacts

Boundary rule:
- for a repo that just finished current-round closure and reached `delivery-report-bridge`, **local standard report generation belongs here and is expected**
- Feishu/wiki publishing does **not** belong to this skill and should be treated as a separate later stage

## Mandatory AI-native activation

Before touching `scripts/` or proposing fixes, do all of the following:

1. Read `../ai-native-development/SKILL.md`
2. Read `references/ai-native-guardrails.md`
3. Inspect the live local control surface:
   - the chosen round truth objects
   - the current `workspace/reports/<repo>/` bundle if it exists
   - the active `scripts/` directory in this skill
4. Ask the hard question first:
   - `Did the mainline already drift from handoff/verdict/receipt into script-first control?`
5. If the answer is even plausibly yes:
   - pause feature growth
   - repair by subtraction / demotion / guardrail strengthening first
   - only keep code changes that are clearly deterministic hard-edge fixes

Do not let this skill silently reinterpret AI-native work as “generator engineering”.

## When to use

Use this skill when any of these are true:
- a repo just reached `next_action=deliver-now`
- a repo already has `runs/repo-verify-*/repo_verify_summary.json` and you want a standard local delivery bundle
- a repo already has a frozen v4 round root and you want to compile `stage-handoff.delivery-reports.*` into the canonical local bundle
- a repo already has `artifacts/delivery-report-input.<repo>.<round>.json` and you want to regenerate / refresh the bundle from that thin object
- a repo has partial ad-hoc reports and you want to normalize them toward the canonical structure
- the user asks whether a repo has a `tuoluojiang`-style standard report directory yet

Do **not** use this skill for:
- env bootstrap
- verifier execution itself
- Feishu publishing

## Canonical workflow

1. Read `../ai-native-development/SKILL.md`
2. Read `references/ai-native-guardrails.md`
3. Read `references/layout.md`
4. Inspect the current live truth and live bundle before running any bridge:
   - current round `repo-findings-board / repo-closure-review / repo-round-verdict`
   - relevant `attempt-receipt / stage-verdict / stage-handoff.finding-replay.*`
   - existing `workspace/reports/<repo>/` output if present
5. Decide in the AI lane whether the task is:
   - initial materialization
   - deterministic refresh
   - drift audit / mismatch repair
6. Only after the source truth is clear, use the thin deterministic bridge that matches the chosen input:

```bash
python3 {baseDir}/scripts/build_repo_delivery_reports.py --run-dir <loop9-run-dir>
```

Or:

```bash
python3 {baseDir}/scripts/build_repo_delivery_reports.py --summary-json <repo_verify_summary.json>
```

Or:

```bash
python3 {baseDir}/scripts/build_repo_delivery_reports.py --round-root <reports/.../rounds/<repo>/<round>>
```

Or:

```bash
python3 {baseDir}/scripts/build_repo_delivery_reports.py --delivery-input-json <artifacts/delivery-report-input.<repo>.<round>.json>
```

7. Inspect the generated directory under `workspace/reports/<repo>/`
8. In the AI lane, verify the bundle against the live round truth rather than trusting the script by default:
   - included finding set
   - held-out finding set
   - effective PoC set
   - root docs that should exist
   - whether any frozen counters/old summaries still disagree with row-level truth
9. Compare the generated result against the **original single-finding template family** first, and use `reports/tuoluojiang/` only as a realized sample reference rather than the root template truth
10. Single-finding docs should match the user-supplied 9-section family:
   - `漏洞描述 / 基础信息`
   - `漏洞核心原理`
   - `仓库下载地址`
   - `补充说明`
   - `公网验证链接`
   - `代码审计分析过程`
   - `EXP（Python 验证脚本）`
   - `漏洞验证`
   - `修复建议`
11. If the generated wording/sectioning is too thin, first ask whether the thinness is:
   - a source-truth problem
   - a bridge hard-edge problem
   - or an AI review problem
   Do **not** reflexively thicken Python ownership.
12. Treat the resulting local bundle as the input to the repo's **final local review** stage, not as an implicit publish trigger
13. `final-local-review` must consume the `delivery-report-bridge` ready receipt before treating missing bundle files as a real blocker; when the canonical bundle is still materializing, classify it as waiting-on-bridge rather than `missing-local-report-artifacts`

## Important design rules

- Keep the local layout stable. Downstream sync should depend on **paths**, not on rediscovering runtime artifacts every time.
- Program layer should own exact file placement and deterministic copying.
- AI layer should own:
  - truth-source selection
  - drift judgment
  - inclusion/hold-out interpretation
  - whether a mismatch is a hard blocker or an upstream paper-truth problem
  - post-generation acceptance
- Prefer one canonical report tree per repo over many ad-hoc files scattered in `workspace/reports/`.
- `delivery-report-bridge -> final-local-review` is a producer/consumer seam, not a parallel fan-out pair; if the consumer starts before the producer barrier is ready, the correct reading is `not-ready-yet`, not `missing`.
- The scripts in this skill are **bridges, not owners**. They may materialize a tree or write a receipt, but they must not become the primary semantic authority.
- If a script bug is discovered, fix the deterministic edge you can name precisely; do not compensate by burying more report-policy meaning in Python unless there is no thinner hard-edge option.

## Current implementation scope

The current bridges already generate/refresh:
- `00-索引.md`
- `01-仓库级中文交付报告.md`
- `02-仓库级技术汇总.md/json`
- one markdown doc per **默认正式交付项**
- effective PoC copies under `poc/`
- copied HTTP request/response evidence under `http/<finding_id>/`
- `98-delivery-bundle.manifest.json`

Current inclusion rule:
- 正式交付页默认只纳入 `fresh-confirmed` / 已 ready-for-delivery 的问题
- `fresh-blocked / fresh-manual-needed / fresh-skip-by-policy` 仍会保留在 repo 级报告、manifest 与后续 `99-最终本地复盘` 中，但不默认出单漏洞正式交付页

Durable HTTP evidence rule:
- local `reports/<repo>/http/<finding_id>/` is not complete unless it contains **both** request packets and response packets whenever the upstream verifier capture has both
- do not stop at `request-*.txt` only; `response-*.txt` must be copied too, and `00-索引.md` should list both sides

Durable quality rule:
- the root truth for single-finding markdown is the original user-supplied single-PoC template family, not any one derived repo sample
- `reports/tuoluojiang/` and `reports/ibos/` are useful realized examples, but they are not allowed to override the original 9-section family
- `00-索引.md`, `01-仓库级中文交付报告.md`, and per-finding `*.md` must all align to that chapter-heavy Chinese template style, not merely exist as thin technical placeholders
- if a newly generated repo looks materially thinner than `tuoluojiang`, fix the generator rather than hand-waving the gap in chat

AI-native repair preference:
- first repair the parent control model
- second repair the upstream truth object / handoff / receipt if it is wrong
- third repair a bounded deterministic bridge if the bug is truly at the hard edge
- do **not** count “the script now has more checks” as success unless the AI lane also became thinner and clearer

## References

- `references/layout.md` — canonical local directory structure and source-of-truth inputs
- `references/ai-native-guardrails.md` — delivery-report-specific AI-native drift audit and thin-bridge discipline
