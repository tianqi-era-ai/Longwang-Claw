# Loop9 Delivery Publisher Cron — AI-Native Thin Bridges

这份文档只提供**可见、可删、可替换**的薄桥接片段。

控制边界必须保持为：

- AI 负责：
  - 读取候选现场
  - 判断坏候选 / 健康候选
  - 决定 `publish / skip / incident`
  - 决定通知中如何表述真实 issue
- 代码只负责：
  - 读取本地 JSON / 文件系统事实
  - 清理 / claim / release slot
  - 写入 incident markdown
  - 构造 publish plan

禁止把下面这些片段重新包装回一个新的 orchestration-heavy runner。

## 1. 读取 config 并清理陈旧 slot

```bash
python3 - <<'PY'
from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

workspace = Path("~/.openclaw/workspace").expanduser()
config_path = workspace / "config" / "loop9-dispatch.json"
locks_dir = workspace / "automation-state" / "loop9" / "locks"
cfg = json.loads(config_path.read_text(encoding="utf-8")) if config_path.exists() else {}
node = cfg.get("deliveryReportPublish") or {}
max_concurrent = int(node.get("maxConcurrent") or 1)
lock_stale_minutes = int(node.get("lockStaleMinutes") or 180)
manual_queue = list(node.get("manualQueue") or [])
locks_dir.mkdir(parents=True, exist_ok=True)
stale_before = datetime.now(timezone.utc) - timedelta(minutes=lock_stale_minutes)
cleaned = []
for path in sorted(locks_dir.glob("delivery-report-publish-slot-*.json")):
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
        started = datetime.fromisoformat(str(payload.get("startedAt")))
    except Exception:
        path.unlink(missing_ok=True)
        cleaned.append(path.name)
        continue
    if started.tzinfo is None:
        started = started.replace(tzinfo=timezone.utc)
    if started < stale_before:
        path.unlink(missing_ok=True)
        cleaned.append(path.name)
print(json.dumps({
    "maxConcurrent": max_concurrent,
    "lockStaleMinutes": lock_stale_minutes,
    "manualQueue": manual_queue,
    "cleanedSlots": cleaned,
}, ensure_ascii=False, indent=2))
PY
```

## 2. 列出 canonical report 目录

```bash
find ~/.openclaw/workspace/reports -mindepth 1 -maxdepth 1 -type d | sort
```

AI 自己决定扫描顺序。
默认优先级：

1. `manualQueue` 中显式点名的 repo
2. 其余候选里 `needs_sync=true` 的 repo
3. 若都健康，则优先 `phase_missing=true`
4. 再看缺失 / 变更 / binding 异常数量
5. 最后再看 `report_mtime`

坏候选只跳过，不阻塞继续扫描。
只有当本轮没有任何健康可发 repo 时，才允许写 blocking incident。

## 3. 对单个 report_dir 生成 preflight receipt

这一步**只产出事实 receipt**，不返回 `publish / incident / skip` 决策。

强约束：

- 一次只对 **1 个** `REPORT_DIR` 运行这段 snippet
- AI 逐个读取 receipt 并自行决定要继续扫描、还是已经可以 publish
- 不要把这段 snippet 改写成“遍历所有 repo 并生成总表”的 mega-script；那会重新长回隐藏 runner / 隐藏策略 owner

使用方式：

```bash
REPORT_DIR=/abs/path/to/workspace/reports/<repo>
python3 - <<'PY'
from __future__ import annotations

import hashlib
import importlib.util
import json
import os
from pathlib import Path

WORKSPACE = Path("~/.openclaw/workspace").expanduser()
STATE_PATH = WORKSPACE / "memory" / "loop9-feishu-publisher-state.json"
BUILD_PLAN_SCRIPT = WORKSPACE / "skills" / "loop9-feishu-delivery-publisher" / "scripts" / "build_report_publish_plan.py"
DEFAULT_FINDING_TEMPLATE_HEADINGS = [
    "# 漏洞描述",
    "## 基础信息",
    "# 漏洞核心原理",
    "# 仓库下载地址",
    "# 补充说明",
    "# 公网验证链接",
    "# 代码审计分析过程",
    "## 漏洞基本信息",
    "## 漏洞原理深度分析",
    "# EXP（Python 验证脚本）",
    "## 脚本说明",
    "# 漏洞验证",
    "## 验证前提",
    "## 验证步骤",
    "## 请求 / 回包证明",
    "# 修复建议",
    "## 核心漏洞修复（高优先级）",
    "## 防护增强（中优先级）",
    "## 权限与日志加固（辅助）",
]

report_dir = Path(os.environ["REPORT_DIR"]).expanduser().resolve()
manifest_path = report_dir / "98-delivery-bundle.manifest.json"
manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
state = json.loads(STATE_PATH.read_text(encoding="utf-8")) if STATE_PATH.exists() else {"projects": {}}

def rendered_hash(markdown: str) -> str:
    return hashlib.sha256(markdown.encode("utf-8")).hexdigest()

def missing_template_headings(path: Path, required_headings: list[str]) -> list[str]:
    text = path.read_text(encoding="utf-8", errors="replace")
    return [heading for heading in required_headings if heading not in text]

def humanize_issue(issue: str) -> str:
    code, _, rest = issue.partition(":")
    if code == "missing-root":
        return f"缺少根文档 `{rest}`"
    if code == "final-local-review-not-complete":
        return "manifest 中 `final_local_review.status` 不是 `complete`"
    if code == "publish-not-ready":
        return "manifest 中 `publish_ready` 不是 `true`"
    if code == "missing-final-local-review-md":
        return "缺少 `99-最终本地复盘.md`"
    if code == "missing-final-local-review-json":
        return "缺少 `99-最终本地复盘.json`"
    if code == "missing-delivery-finding-layer":
        return "manifest 缺少 `delivery_findings` 正式交付层"
    if code == "missing-finding-doc":
        return f"缺少 finding 文档 `{rest}`"
    if code == "thin-finding-doc":
        doc_name, _, headings_raw = rest.partition(":")
        headings = [item for item in headings_raw.split("|") if item]
        if headings:
            return f"`{doc_name}` 缺少模板章节：{', '.join(headings)}"
        return f"`{doc_name}` 被判定为 thin-finding-doc"
    if code == "missing-poc":
        return f"缺少 PoC 文件 `{rest}`"
    if code == "missing-http-layer":
        return f"缺少 HTTP 证据目录 `{rest}`"
    if code == "missing-http-requests":
        return f"HTTP 证据目录 `{rest}` 缺少 request 文件"
    if code == "missing-http-responses":
        return f"HTTP 证据目录 `{rest}` 缺少 response 文件"
    if code == "http-request-response-count-mismatch":
        http_dir, _, counts = rest.partition(":")
        return f"HTTP 证据目录 `{http_dir}` 的 request / response 数量不一致（{counts}）"
    if code == "no-publishable-docs":
        return "publish plan 没有生成可发布文档"
    return issue

def summarize_issues(issues: list[str]) -> str:
    if not issues:
        return "无"
    missing_roots = []
    thin_docs = []
    missing_finding_docs = []
    missing_pocs = []
    missing_http_layers = []
    missing_http_requests = []
    missing_http_responses = []
    http_mismatches = []
    other = []
    final_local_review_not_complete = False
    publish_not_ready = False
    missing_review_md = False
    missing_review_json = False
    missing_delivery_layer = False
    no_publishable_docs = False
    for issue in issues:
        code, _, rest = issue.partition(":")
        if code == "missing-root":
            missing_roots.append(rest)
        elif code == "final-local-review-not-complete":
            final_local_review_not_complete = True
        elif code == "publish-not-ready":
            publish_not_ready = True
        elif code == "missing-final-local-review-md":
            missing_review_md = True
        elif code == "missing-final-local-review-json":
            missing_review_json = True
        elif code == "missing-delivery-finding-layer":
            missing_delivery_layer = True
        elif code == "missing-finding-doc":
            missing_finding_docs.append(rest)
        elif code == "thin-finding-doc":
            doc_name, _, _ = rest.partition(":")
            thin_docs.append(doc_name)
        elif code == "missing-poc":
            missing_pocs.append(rest)
        elif code == "missing-http-layer":
            missing_http_layers.append(rest)
        elif code == "missing-http-requests":
            missing_http_requests.append(rest)
        elif code == "missing-http-responses":
            missing_http_responses.append(rest)
        elif code == "http-request-response-count-mismatch":
            http_dir, _, _ = rest.partition(":")
            http_mismatches.append(http_dir)
        elif code == "no-publishable-docs":
            no_publishable_docs = True
        else:
            other.append(humanize_issue(issue))
    parts = []
    if missing_roots:
        parts.append(f"缺少根文档：{', '.join(f'`{item}`' for item in missing_roots)}")
    if final_local_review_not_complete:
        parts.append("`final_local_review.status` 不是 `complete`")
    if publish_not_ready:
        parts.append("`publish_ready` 不是 `true`")
    if missing_review_md:
        parts.append("缺少 `99-最终本地复盘.md`")
    if missing_review_json:
        parts.append("缺少 `99-最终本地复盘.json`")
    if missing_delivery_layer:
        parts.append("manifest 缺少正式交付 finding 层")
    if missing_finding_docs:
        parts.append(f"缺少 {len(missing_finding_docs)} 篇 finding 文档")
    if thin_docs:
        parts.append(f"{len(thin_docs)} 篇 finding 文档缺少模板章节")
    if missing_pocs:
        parts.append(f"缺少 {len(missing_pocs)} 个 PoC 文件")
    if missing_http_layers:
        parts.append(f"缺少 {len(missing_http_layers)} 个 HTTP 证据目录")
    if missing_http_requests:
        parts.append(f"{len(missing_http_requests)} 个 HTTP 证据目录缺少 request 文件")
    if missing_http_responses:
        parts.append(f"{len(missing_http_responses)} 个 HTTP 证据目录缺少 response 文件")
    if http_mismatches:
        parts.append(f"{len(http_mismatches)} 个 HTTP 证据目录的 request / response 数量不一致")
    if no_publishable_docs:
        parts.append("publish plan 没有生成可发布文档")
    parts.extend(other)
    return "；".join(parts)

issues = []
required_findings_headings = list((((manifest.get("delivery_template") or {}).get("required_headings")) or DEFAULT_FINDING_TEMPLATE_HEADINGS))
for rel in [
    "00-索引.md",
    "01-仓库级中文交付报告.md",
    "02-仓库级技术汇总.md",
    "02-仓库级技术汇总.json",
    "98-delivery-bundle.manifest.json",
]:
    if not (report_dir / rel).exists():
        issues.append(f"missing-root:{rel}")

review = manifest.get("final_local_review") or {}
review_md = Path(str(review.get("review_record_md") or ""))
review_json = Path(str(review.get("review_record_json") or ""))
if review.get("status") != "complete":
    issues.append("final-local-review-not-complete")
if not manifest.get("publish_ready"):
    issues.append("publish-not-ready")
if not review_md.exists():
    issues.append("missing-final-local-review-md")
if not review_json.exists():
    issues.append("missing-final-local-review-json")

delivery_findings = list(manifest.get("delivery_findings") or [])
if not delivery_findings:
    issues.append("missing-delivery-finding-layer")

for finding in delivery_findings:
    report_doc = str(finding.get("report_doc") or "").strip()
    if report_doc:
        report_doc_path = report_dir / report_doc
        if not report_doc_path.exists():
            issues.append(f"missing-finding-doc:{report_doc}")
        else:
            missing_headings = missing_template_headings(report_doc_path, required_findings_headings)
            if missing_headings:
                issues.append(f"thin-finding-doc:{report_doc}:{'|'.join(missing_headings)}")
    for poc_name in finding.get("poc_files") or []:
        poc_path = report_dir / "poc" / poc_name
        if not (poc_path.exists() and poc_path.is_file()):
            issues.append(f"missing-poc:{poc_name}")
    http_dir_rel = str(finding.get("http_dir") or "").strip()
    if http_dir_rel:
        http_dir = report_dir / http_dir_rel
        if not http_dir.exists() or not http_dir.is_dir():
            issues.append(f"missing-http-layer:{http_dir_rel}")
            continue
        requests = sorted(http_dir.glob("request-*.txt"))
        responses = sorted(http_dir.glob("response-*.txt"))
        if not requests:
            issues.append(f"missing-http-requests:{http_dir.name}")
        if not responses:
            issues.append(f"missing-http-responses:{http_dir.name}")
        if requests and responses and len(requests) != len(responses):
            issues.append(f"http-request-response-count-mismatch:{http_dir.name}:{len(requests)}:{len(responses)}")

spec = importlib.util.spec_from_file_location("loop9_delivery_publish_plan", BUILD_PLAN_SCRIPT)
module = importlib.util.module_from_spec(spec)
assert spec is not None and spec.loader is not None
spec.loader.exec_module(module)
project_slug = str(((manifest.get("repo") or {}).get("slug")) or report_dir.name)
docs = module.collect_docs(report_dir, project_slug)
if not docs:
    issues.append("no-publishable-docs")

project_state = ((state.get("projects") or {}).get(project_slug) or {})
phase = ((project_state.get("phases") or {}).get("delivery_reports") or {})
delivery_state = project_state.get("delivery_reports") or {}
missing_docs = []
changed_docs = []
invalid_bindings = []
for doc in docs:
    key = doc["doc_key"]
    local_hash = rendered_hash(str(doc["rendered_markdown"]))
    saved = delivery_state.get(key)
    if not saved:
        missing_docs.append(doc["title"])
        continue
    if not saved.get("doc_id") or not saved.get("node_token"):
        invalid_bindings.append(doc["title"])
        continue
    if saved.get("last_content_hash") != local_hash:
        changed_docs.append(doc["title"])

print(json.dumps({
    "project_slug": project_slug,
    "report_dir": str(report_dir),
    "manifest_path": str(manifest_path),
    "publish_ready": bool(manifest.get("publish_ready")),
    "final_local_review_status": review.get("status"),
    "issues": issues,
    "issue_summary": summarize_issues(issues),
    "issue_details": [humanize_issue(item) for item in issues],
    "phase_missing": not bool(phase.get("doc_id") and phase.get("node_token")),
    "project_node_missing": not bool((project_state.get("project_node") or {}).get("node_token")),
    "missing_docs": missing_docs,
    "changed_docs": changed_docs,
    "invalid_bindings": invalid_bindings,
    "needs_sync": bool(
        not phase.get("doc_id")
        or not phase.get("node_token")
        or missing_docs
        or changed_docs
        or invalid_bindings
    ),
    "docs_total": len(docs),
    "report_mtime": report_dir.stat().st_mtime,
}, ensure_ascii=False, indent=2))
PY
```

AI 在这里必须自己判断：

- `issues=[]` 才算本地报告树健康
- `issues!=[]` 就是坏候选
- 坏候选只跳过，不阻塞继续扫描
- 只有当没有任何健康且 `needs_sync=true` 的 repo 时，才对最值得人工介入的坏候选写 incident

补充约束：

- 如果当前 bundle / current-round 对象里已经存在稳定的 runtime / repro 事实，但本地报告树还没有 `03-复现实验信息.md`，AI 应先把这份根文档补齐或刷新，再继续 preflight / publish。
- receipt / state 里的 `last_content_hash` 必须按“真正发给 Feishu 的 markdown payload”口径比较；不要把 `.py` / `.json` / `http/*` 这类页面重新退回成原始源文件 hash。
- 这同一段 receipt snippet 也是发布后的自检桥接。写完 Feishu 之后，重新对刚发布的同一 `REPORT_DIR` 跑一次；只有当 receipt 回来满足 `issues=[]`、`needs_sync=false`、`missing_docs=[]`、`changed_docs=[]`、`invalid_bindings=[]` 时，才允许宣布“发布完成”。

## 4. claim 一个 publish slot

```bash
SLOT_REPO=<repo-slug>
SLOT_REPORT_DIR=/abs/path/to/workspace/reports/<repo>
MAX_CONCURRENT=<from config receipt>
python3 - <<'PY'
from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path

locks_dir = Path("~/.openclaw/workspace/automation-state/loop9/locks").expanduser()
locks_dir.mkdir(parents=True, exist_ok=True)
claimed = None
max_concurrent = max(1, int(os.environ.get("MAX_CONCURRENT", "1")))
for idx in range(1, max_concurrent + 1):
    path = locks_dir / f"delivery-report-publish-slot-{idx}.json"
    if path.exists():
        continue
    payload = {
        "slotIndex": idx,
        "startedAt": datetime.now(timezone.utc).isoformat(),
        "project_slug": os.environ["SLOT_REPO"],
        "report_dir": os.environ["SLOT_REPORT_DIR"],
    }
    try:
        with path.open("x", encoding="utf-8") as handle:
            json.dump(payload, handle, ensure_ascii=False, indent=2)
    except FileExistsError:
        continue
    payload["path"] = str(path)
    claimed = payload
    break
print(json.dumps({"slot": claimed}, ensure_ascii=False, indent=2))
PY
```

如果 `slot=null`，AI 应把本轮判成健康跳过，不要硬写 incident。

## 5. release slot

```bash
SLOT_PATH=/abs/path/to/slot.json
python3 - <<'PY'
from __future__ import annotations

import json
import os
from pathlib import Path

path = Path(os.environ["SLOT_PATH"]).expanduser()
existed = path.exists()
path.unlink(missing_ok=True)
print(json.dumps({"released": existed, "path": str(path)}, ensure_ascii=False, indent=2))
PY
```

## 6. 写 incident markdown

AI 必须自己先确定：

- 本轮没有任何健康候选可发
- 选中的坏候选为什么值得人工介入
- 通知里只能复述本次 receipt 的 `issue_summary` / `issue_details`

然后再写本地 incident：

```bash
INCIDENT_REPO=<repo-slug>
INCIDENT_STAGE=preflight-local-report-check
INCIDENT_REASON=local-report-incomplete
INCIDENT_SUMMARY='<只写真实 issue 摘要>'
INCIDENT_DETAILS_JSON='<JSON 数组，例如 ["缺少根文档 `01-...`","..."]>'
INCIDENT_RELATED_1=/abs/path/to/report_dir
INCIDENT_RELATED_2=/abs/path/to/98-delivery-bundle.manifest.json
python3 - <<'PY'
from __future__ import annotations

import json
import os
from datetime import datetime
from pathlib import Path

incident_dir = Path("~/.openclaw/workspace/automation-state/loop9/loop9-feishu-delivery-publisher-incidents").expanduser()
incident_dir.mkdir(parents=True, exist_ok=True)
slug = os.environ["INCIDENT_REPO"]
ts = datetime.now().astimezone().strftime("%Y-%m-%d-%H%M")
path = incident_dir / f"{ts}-{slug}-publish-incident.md"
details = json.loads(os.environ["INCIDENT_DETAILS_JSON"])
related = [
    os.environ.get("INCIDENT_RELATED_1", "").strip(),
    os.environ.get("INCIDENT_RELATED_2", "").strip(),
]
related = [item for item in related if item]
lines = [
    f"# Loop9 Delivery Report Publisher Incident · {slug}",
    "",
    f"- generated_at: `{datetime.now().astimezone().isoformat()}`",
    f"- repo: `{slug}`",
    f"- stage: `{os.environ['INCIDENT_STAGE']}`",
    f"- reason: `{os.environ['INCIDENT_REASON']}`",
    f"- summary: {os.environ['INCIDENT_SUMMARY']}",
]
if related:
    lines.extend(["", "## Related paths", ""])
    for item in related:
        lines.append(f"- `{item}`")
if details:
    lines.extend(["", "## Details", ""])
    for item in details:
        lines.append(f"- {item}")
path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
print(json.dumps({"incident_path": str(path)}, ensure_ascii=False, indent=2))
PY
```

通知里必须直接复述 `INCIDENT_SUMMARY`，不要再另行脑补。
