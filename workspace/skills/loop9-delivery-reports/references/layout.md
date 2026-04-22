# Canonical local report layout

Target output directory:

```text
workspace/reports/<repo>/
```

Expected files/directories:

- `00-索引.md`
- `01-仓库级中文交付报告.md`
- `02-仓库级技术汇总.md`
- `02-仓库级技术汇总.json`
- `<finding_id>.md` for each finding included in the formal delivery layer
- `poc/<finding_id>-effective.py` (or original extension)
- `http/<finding_id>/request-NNN.txt`
- `http/<finding_id>/response-NNN.txt`
- `98-delivery-bundle.manifest.json`
- `99-最终本地复盘.md/json` (written by `final-local-review`)

Generation stance:

- AI layer should own source-truth selection, drift judgment, and final acceptance of the generated bundle
- program layer should only generate the exact directory tree and deterministic technical references
- AI is not limited to wording polish; it is the semantic owner of whether the local bundle truthfully reflects the round
- keep the structure stable even when some sections are sparse; stable paths matter for later sync and review
- each formal single-finding markdown must follow the original 9-section template family:
  - `漏洞描述 / 基础信息`
  - `漏洞核心原理`
  - `仓库下载地址`
  - `补充说明`
  - `公网验证链接`
  - `代码审计分析过程`
  - `EXP（Python 验证脚本）`
  - `漏洞验证`
  - `修复建议`
- `reports/tuoluojiang/` is only a realized sample tree; it must not replace the original template family as the source of truth

Current intended source of truth:

- legacy path:
  - `runs/repo-verify-*/repo_verify_summary.json`
  - each finding's `verification_result.json`
  - `request_response_index.json`
  - effective PoC path from `adjusted_poc_path` first, else `original_poc_path`
- v4 path:
  - `stage-handoff.delivery-reports.<repo>.<round>.md`
  - `artifacts/delivery-report-input.<repo>.<round>.json`
  - current round `repo-findings-board / repo-closure-review / repo-round-verdict / attempt-receipt.*`

Guardrail:

- if any generated aggregate counter or manifest summary disagrees with row-level round truth, AI must treat that as a drift signal to inspect, not as a reason to blindly trust the generated paper layer
