#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import urllib.parse
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

WORKSPACE = Path("~/.openclaw/workspace").expanduser()
RUNS = WORKSPACE / "runs"
REPORTS = WORKSPACE / "reports"
TARGETS = WORKSPACE / "targets"
MANIFEST_NAME = "98-delivery-bundle.manifest.json"
CANONICAL_REPORT_KIND = "loop9-standard-delivery-report"
SOURCE_KIND_V4 = "loop9-v4-round"
SOURCE_KIND_LEGACY = "legacy-repo-verify-summary"
V4_INCLUDED_DISPOSITIONS = {"fresh-confirmed"}
LEGACY_INCLUDED_STATUSES = {"confirmed-as-is", "confirmed-after-adjustment"}
TEXTUAL_HTTP_SUFFIXES = {".txt", ".json", ".html", ".md"}
CODE_EXTENSIONS = {".php", ".py", ".java", ".js", ".ts", ".go", ".rb", ".cs", ".scala", ".kt", ".jsp", ".jspx"}
SINGLE_FINDING_TEMPLATE_FAMILY = "single-poc-docx-9-section"
SINGLE_FINDING_TEMPLATE_HEADINGS = [
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
PHP_CALL_EXCLUDE = {
    "if",
    "elseif",
    "else",
    "switch",
    "case",
    "while",
    "for",
    "foreach",
    "catch",
    "isset",
    "empty",
    "array",
    "list",
    "echo",
    "print",
    "return",
    "include",
    "require",
    "clone",
    "new",
}


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def write_json(path: Path, data: dict[str, Any]) -> None:
    write_text(path, json.dumps(data, ensure_ascii=False, indent=2) + "\n")


def copy_file(src: Path, dst: Path) -> bool:
    if not src.exists() or not src.is_file():
        return False
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)
    return True


def slugify(text: str) -> str:
    text = re.sub(r"[^0-9A-Za-z\u4e00-\u9fff]+", "-", text.strip())
    text = re.sub(r"-+", "-", text).strip("-")
    return text.lower() or "unnamed"


def strip_ticks(text: str) -> str:
    value = text.strip()
    if len(value) >= 2 and value.startswith("`") and value.endswith("`"):
        return value[1:-1]
    return value


def coerce_int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def dedupe_preserve_order(items: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for item in items:
        if not item or item in seen:
            continue
        seen.add(item)
        result.append(item)
    return result


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build canonical Loop9 delivery report directory from legacy summary or v4 round-local truth"
    )
    src = parser.add_mutually_exclusive_group(required=True)
    src.add_argument("--run-dir", help="Loop9 run dir under Super8/temp/loop9/...")
    src.add_argument("--summary-json", help="Explicit repo_verify_summary.json path")
    src.add_argument("--round-root", help="V4 round root under reports/.../rounds/<repo>/<round>")
    src.add_argument("--delivery-input-json", help="Canonical delivery input JSON produced from v4 round truth")
    parser.add_argument("--out-dir", help="Output report dir (default: workspace/reports/<repo>)")
    return parser.parse_args()


def find_summary_for_run(run_dir: Path) -> Path:
    exact = RUNS / f"repo-verify-{run_dir.name}" / "repo_verify_summary.json"
    if exact.exists():
        return exact
    for path in sorted(RUNS.glob("repo-verify-*/repo_verify_summary.json")):
        try:
            summary = read_json(path)
        except Exception:
            continue
        if Path(str(summary.get("run_dir") or "")).resolve() == run_dir.resolve():
            return path
    raise FileNotFoundError(f"No repo_verify_summary.json found for run dir: {run_dir}")


def git_output(repo: Path | None, args: list[str]) -> str | None:
    if repo is None or not repo.exists():
        return None
    proc = subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True, check=False)
    value = proc.stdout.strip()
    return value or None


def repo_remote_url(repo: Path | None) -> str | None:
    return git_output(repo, ["config", "--get", "remote.origin.url"])


def repo_commit(repo: Path | None) -> str | None:
    return git_output(repo, ["rev-parse", "HEAD"])


def repo_branch(repo: Path | None) -> str | None:
    return git_output(repo, ["rev-parse", "--abbrev-ref", "HEAD"])


def maybe_target_repo(slug: str) -> Path | None:
    repo = TARGETS / slug
    return repo if repo.exists() else None


def zh_product_name(slug: str) -> str:
    mapping = {
        "tuoluojiang": "陀螺匠（tuoluojiang）",
        "mcms": "铭飞MCms（mcms）",
        "sparkshop": "SparkShop（sparkshop）",
    }
    return mapping.get(slug.lower(), slug)


def vulnerability_type_from_title(title: str) -> str:
    lower = title.lower()
    if ("default" in lower and "credential" in lower) or ("默认" in title and ("凭据" in title or "口令" in title)):
        return "默认口令 / 默认凭据风险"
    if "upload" in lower or "editor" in lower or "catchimage" in lower or "上传" in title:
        return "文件上传 / 文件写入链"
    if "sql" in lower:
        return "SQL 执行 / 数据查询风险"
    if "read" in lower or "file read" in lower or "读取" in title:
        return "文件读取"
    if "ssrf" in lower or "远程抓取" in title:
        return "服务端请求伪造（SSRF）"
    return "待人工细化的高风险问题"


def generic_fix_suggestions(title: str) -> list[str]:
    lower = title.lower()
    if "default" in lower and "credential" in lower:
        return [
            "1. 删除或强制重置所有默认后台凭据；首次启动必须改密。",
            "2. 对后台登录增加失败限制、二次校验与审计告警。",
            "3. 排查历史部署是否仍保留官方示例口令。",
        ]
    if "upload" in lower or "editor" in lower or "catchimage" in lower:
        return [
            "1. 收紧上传 / 远程抓取相关入口的服务端鉴权、输入白名单与日志审计。",
            "2. 把上传目录与可执行目录隔离，避免同源主动内容托管被继续利用。",
            "3. 对后台插件 / 配置装配链增加完整性校验，避免功能在半损坏态下继续暴露风险面。",
        ]
    if "read" in lower or "读取" in title:
        return [
            "1. 为文件读取链补齐白名单与路径约束，不要把任意输入直接送入本地文件读取函数。",
            "2. 对高风险读取入口增加访问控制、审计与异常告警。",
            "3. 用回归测试覆盖图片路径、非图片路径与异常路径三类行为边界。",
        ]
    return [
        "1. 结合真实业务入口补齐服务端权限控制。",
        "2. 为关键风险路径增加更明确的输入约束与日志审计。",
        "3. 对已验证成功的利用链做专项修复与回归测试。",
    ]


def detailed_fix_sections(title: str) -> dict[str, list[str]]:
    lower = title.lower()
    if "default" in lower and "credential" in lower:
        return {
            "core": [
                "1. 删除或强制重置所有默认后台凭据；首次启动必须完成改密。",
                "2. 为后台登录入口补齐强密码策略与首次初始化闭环，避免官方示例口令继续遗留。",
                "3. 对历史部署与镜像进行统一排查，确认不存在默认凭据回滚或弱口令复用。",
            ],
            "hardening": [
                "1. 为登录入口增加失败限制、二次校验与异常登录告警。",
                "2. 对后台认证流程补齐来源限制与会话异常检测，降低默认凭据被批量探测的风险。",
                "3. 在发布流程中加入默认凭据扫描，避免新版本再次带出示例账号。",
            ],
            "audit": [
                "1. 回归验证应覆盖首次安装、升级迁移、密码重置与历史管理员账号兼容路径。",
                "2. 将默认凭据、弱口令与初始化逻辑纳入后续安全基线检查。",
                "3. 对历史访问日志做一次排查，确认默认凭据未被外部命中利用。",
            ],
        }
    if "upload" in lower or "editor" in lower or "catchimage" in lower or "上传" in title:
        return {
            "core": [
                "1. 将上传/抓取入口从匿名暴露面移出，至少要求已登录且具备明确业务权限的角色才能调用。",
                "2. 不要使用扩展名 denylist 作为主防线，应改为严格的扩展名、MIME 与文件内容 allowlist。",
                "3. 将上传结果与 Web 可直接访问目录隔离，避免同源主动内容托管继续暴露利用面。",
            ],
            "hardening": [
                "1. 对 SVG、XML、文本类主动内容单独处理或默认拒绝，不要只依赖少量黑名单特征。",
                "2. 为上传/远程抓取入口增加速率限制、异常内容告警与统一的日志审计。",
                "3. 若系统支持对象存储，需收紧公开回源域名、内容类型与跨域策略，避免放大主动内容风险。",
            ],
            "audit": [
                "1. 回归验证至少覆盖常规图片、SVG、伪装扩展名、黑名单关键片段与上传后回取行为。",
                "2. 将“匿名上传/抓取 + 可直接访问 URL + 弱黑名单”纳入后续代码审计规则。",
                "3. 结合历史日志排查是否已有异常上传、异常抓取或同源托管内容被访问的痕迹。",
            ],
        }
    if "sql" in lower:
        return {
            "core": [
                "1. 将动态 SQL 改为参数化查询，不要把用户可控输入直接拼接进 SQL 片段。",
                "2. 对相关查询入口补齐权限控制、输入约束与最小必要字段白名单。",
                "3. 若问题涉及搜索、排序或导出能力，应同步收紧可拼接的列名与表达式范围。",
            ],
            "hardening": [
                "1. 为异常 SQL 报错、语句耗时与可疑关键字命中增加数据库审计与告警。",
                "2. 在应用层补齐统一的输入校验与高风险关键字拦截，降低同类注入面扩散。",
                "3. 结合最小权限原则收紧数据库账号能力，降低成功利用后的横向影响。",
            ],
            "audit": [
                "1. 回归验证需覆盖正常查询、报错路径、盲注边界与排序/筛选等变体输入。",
                "2. 将同一模块内所有拼接式 SQL 与 ORM 原生表达式一并复查。",
                "3. 检查历史日志，确认是否已存在异常查询、长时间延迟或报错放大迹象。",
            ],
        }
    if "read" in lower or "读取" in title:
        return {
            "core": [
                "1. 不要把用户可控路径直接送入本地文件读取函数，应改为严格目录白名单与类型校验。",
                "2. 在读取前使用 `realpath()` 等规范化手段校验目标仍落在允许目录内。",
                "3. 为高风险读取入口补齐身份校验与最小权限控制，避免匿名或越权直接触达文件读取面。",
            ],
            "hardening": [
                "1. 明确限制 `http://`、`https://`、`file://`、`php://` 等非预期协议输入。",
                "2. 为异常路径、跨目录读取与协议型输入增加日志审计与告警。",
                "3. 在 Web 层补齐对敏感路径、包装器与明显异常输入的统一拦截。",
            ],
            "audit": [
                "1. 回归验证至少覆盖业务允许目录、应用目录外文件、非图片/非目标类型文件与协议型输入。",
                "2. 将“鉴权缺失 + 路径白名单缺失 + helper 继续读取”纳入后续审计规则。",
                "3. 复查同类 helper、文件预览与远程抓取接口，确认不存在同型读取链路。",
            ],
        }
    return {
        "core": [
            "1. 结合真实业务入口补齐服务端权限控制。",
            "2. 为关键风险路径增加更明确的输入约束与边界校验。",
            "3. 对已验证成功的利用链做专项修复与回归测试。",
        ],
        "hardening": [
            "1. 为相关接口增加统一日志审计、异常告警与速率限制。",
            "2. 收紧高风险功能的默认暴露面，避免匿名或低权限直接命中。",
            "3. 在发布流程中加入对应规则，避免同类问题在其它模块重复出现。",
        ],
        "audit": [
            "1. 回归验证覆盖正常路径、异常路径与边界输入。",
            "2. 对同模块相似功能做一次横向代码审计。",
            "3. 结合历史日志排查是否已有异常利用痕迹。",
        ],
    }


def parse_poc_metadata(path: Path | None) -> dict[str, str]:
    result: dict[str, str] = {}
    if path is None or not path.exists():
        return result
    for line in read_text(path).splitlines()[:40]:
        if not line.startswith("#"):
            continue
        match = re.match(r"^#\s*([^:]+):\s*(.*)$", line)
        if not match:
            continue
        key = match.group(1).strip().lower().replace(" ", "_").replace("-", "_")
        result[key] = match.group(2).strip()
    return result


def choose_effective_poc(vr: dict[str, Any]) -> Path | None:
    for key in ["adjusted_poc_path", "original_poc_path"]:
        value = vr.get(key)
        if value:
            path = Path(str(value)).expanduser()
            if path.exists() and path.is_file():
                return path
    return None


def choose_original_poc(vr: dict[str, Any]) -> Path | None:
    value = vr.get("original_poc_path")
    if not value:
        return None
    path = Path(str(value)).expanduser()
    return path if path.exists() and path.is_file() else None


def extract_heading_section(text: str, title: str) -> str:
    pattern = re.compile(rf"^##\s+{re.escape(title)}\s*$\n(.*?)(?=^##\s+|\Z)", re.MULTILINE | re.DOTALL)
    match = pattern.search(text)
    return match.group(1).strip() if match else ""


def parse_key_value_lines(text: str) -> dict[str, str]:
    result: dict[str, str] = {}
    for raw_line in text.splitlines():
        line = raw_line.rstrip()
        match = re.match(r"^\s*-\s+([A-Za-z0-9_.-]+):\s*(.+?)\s*$", line)
        if not match:
            continue
        result[match.group(1)] = strip_ticks(match.group(2))
    return result


def parse_numbered_paths(text: str) -> list[str]:
    paths: list[str] = []
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not re.match(r"^\d+\.\s+", line):
            continue
        backticked = [item for item in re.findall(r"`([^`]+)`", line) if "/" in item]
        if backticked:
            paths.append(strip_ticks(backticked[-1]))
            continue
        match = re.search(r"(/[^)\s]+)", line)
        if match:
            paths.append(strip_ticks(match.group(1)))
    return paths


def parse_paths_from_section(text: str, title: str) -> list[str]:
    return parse_numbered_paths(extract_heading_section(text, title))


def parse_board_findings(board_text: str) -> list[dict[str, Any]]:
    ledger_text = extract_heading_section(board_text, "findings ledger") or board_text
    pattern = re.compile(r"^###\s+\d+\.\s+(.+?)\n(.*?)(?=^###\s+\d+\.\s+|\Z)", re.MULTILINE | re.DOTALL)
    findings: list[dict[str, Any]] = []
    for match in pattern.finditer(ledger_text):
        heading = match.group(1).strip()
        body = match.group(2).strip()
        data = parse_key_value_lines(body)
        if not any(key in data for key in ("queue_id", "current_round_disposition", "current_round_state")):
            continue
        if "｜" in heading:
            slot, title = [part.strip() for part in heading.split("｜", 1)]
        else:
            slot = str(data.get("queue_id") or "").strip()
            title = heading
            if title and not str(data.get("finding_id") or "").strip():
                data["finding_id"] = title
        data["slot"] = slot
        data["title"] = title
        findings.append(data)
    return findings


def normalize_round_coverage_snapshot(raw: dict[str, str], findings: list[dict[str, Any]]) -> dict[str, int]:
    if findings:
        return derive_round_coverage_snapshot(findings)
    total = coerce_int(raw.get("relevant_findings_total") or raw.get("in_scope_findings_total") or raw.get("findings_total"), 0)
    fresh_confirmed = coerce_int(raw.get("fresh_confirmed_count"), 0)
    fresh_blocked = coerce_int(raw.get("fresh_blocked_count"), 0)
    fresh_manual_needed = coerce_int(raw.get("fresh_manual_needed_count"), 0)
    fresh_skip_by_policy = coerce_int(raw.get("fresh_skip_by_policy_count"), 0)
    terminal = coerce_int(
        raw.get("terminal_disposition_count") or raw.get("current_round_terminalized_count"),
        fresh_confirmed + fresh_blocked + fresh_manual_needed + fresh_skip_by_policy,
    )
    remaining = coerce_int(raw.get("remaining_unfinished_count"), max(total - terminal, 0))
    return {
        "in_scope_findings_total": total,
        "terminal_disposition_count": terminal,
        "delivery_findings_count": fresh_confirmed,
        "held_out_findings_count": fresh_blocked + fresh_manual_needed + fresh_skip_by_policy,
        "fresh_confirmed_count": fresh_confirmed,
        "fresh_blocked_count": fresh_blocked,
        "fresh_manual_needed_count": fresh_manual_needed,
        "fresh_skip_by_policy_count": fresh_skip_by_policy,
        "remaining_unfinished_count": remaining,
    }


def derive_round_coverage_snapshot(findings: list[dict[str, Any]]) -> dict[str, int]:
    counts = {
        "fresh-confirmed": 0,
        "fresh-blocked": 0,
        "fresh-manual-needed": 0,
        "fresh-skip-by-policy": 0,
    }
    terminal = 0
    for finding_row in findings:
        disposition = normalize_v4_disposition(finding_row)
        state = str(finding_row.get("current_round_state") or "").strip()
        if state == "terminal" or disposition:
            terminal += 1
        if disposition in counts:
            counts[disposition] += 1
    delivery_count = sum(counts[item] for item in V4_INCLUDED_DISPOSITIONS)
    held_out_count = max(terminal - delivery_count, 0)
    total = len(findings)
    return {
        "in_scope_findings_total": total,
        "terminal_disposition_count": terminal,
        "delivery_findings_count": delivery_count,
        "held_out_findings_count": held_out_count,
        "fresh_confirmed_count": counts["fresh-confirmed"],
        "fresh_blocked_count": counts["fresh-blocked"],
        "fresh_manual_needed_count": counts["fresh-manual-needed"],
        "fresh_skip_by_policy_count": counts["fresh-skip-by-policy"],
        "remaining_unfinished_count": max(total - terminal, 0),
    }


def audit_round_coverage_snapshot(findings: list[dict[str, Any]], raw_sources: list[tuple[str, dict[str, str]]]) -> dict[str, Any]:
    derived = derive_round_coverage_snapshot(findings)
    mismatches: list[dict[str, Any]] = []
    compared_fields = [
        "in_scope_findings_total",
        "terminal_disposition_count",
        "delivery_findings_count",
        "held_out_findings_count",
        "fresh_confirmed_count",
        "fresh_blocked_count",
        "fresh_manual_needed_count",
        "fresh_skip_by_policy_count",
        "remaining_unfinished_count",
    ]
    for source_name, raw in raw_sources:
        if not raw:
            continue
        declared = normalize_round_coverage_snapshot(raw, [])
        for field in compared_fields:
            if field not in declared:
                continue
            if declared.get(field) != derived.get(field):
                mismatches.append(
                    {
                        "source": source_name,
                        "field": field,
                        "declared": declared.get(field),
                        "derived": derived.get(field),
                    }
                )
    return {
        "basis": "row-level-findings-ledger",
        "derived_snapshot": derived,
        "mismatches": mismatches,
        "status": "drift-detected" if mismatches else "aligned",
    }


def normalize_v4_disposition(finding_row: dict[str, Any]) -> str:
    for key in ("current_round_disposition", "coverage_state", "disposition"):
        value = str(finding_row.get(key) or "").strip()
        if value:
            return value
    return ""


def fallback_v4_finding_id(repo_slug: str, slot: str, title: str) -> str:
    explicit = slugify(f"{repo_slug}-{slot}") if repo_slug and slot else ""
    if explicit:
        return explicit
    from_title = slugify(f"{repo_slug}-{title}" if repo_slug else title)
    return from_title or "unnamed"


def normalize_legacy_coverage_snapshot(summary: dict[str, Any], delivery_findings: list[dict[str, Any]], held_out_findings: list[dict[str, Any]]) -> dict[str, int]:
    counts = summary.get("counts") or {}
    delivery = summary.get("delivery") or {}
    total = coerce_int(counts.get("total"), len(delivery_findings) + len(held_out_findings))
    ready = coerce_int(delivery.get("ready_for_delivery"), len(delivery_findings))
    need_review = coerce_int(delivery.get("need_human_review"), len(held_out_findings))
    return {
        "in_scope_findings_total": total,
        "terminal_disposition_count": len(delivery_findings) + len(held_out_findings),
        "delivery_findings_count": len(delivery_findings),
        "held_out_findings_count": len(held_out_findings),
        "legacy_ready_for_delivery_count": ready,
        "legacy_need_human_review_count": need_review,
        "remaining_unfinished_count": max(total - len(delivery_findings) - len(held_out_findings), 0),
    }


def extract_http_request_lines(receipt_text: str) -> list[str]:
    lines: list[str] = []
    section = extract_heading_section(receipt_text, "fresh evidence")
    for raw_line in section.splitlines():
        line = raw_line.strip().replace("`", "")
        match = re.match(r"-\s*((?:GET|POST|PUT|PATCH|DELETE)\s+.+?\s*->\s*HTTP\s+\d+)", line)
        if match:
            lines.append(match.group(1))
    return lines


def extract_no_overclaim_note(receipt_text: str) -> str:
    for title in ["no-overclaim note", "truthful boundary"]:
        section = extract_heading_section(receipt_text, title)
        if section:
            parts = [line.strip().lstrip("-").strip() for line in section.splitlines() if line.strip()]
            cleaned = "；".join(part for part in parts if part)
            return cleaned.strip()
    return ""


def guess_auth_boundary(title: str, summary: str, preconditions: str) -> str:
    merged = f"{title}\n{summary}\n{preconditions}".lower()
    explicit_raw_token_markers = (
        "authenticated raw authorization token",
        "authenticated scheduler access",
        "authorization: <raw_token>",
        "raw access token header",
        "raw token",
        "不是匿名访问",
        "bearer <token>",
        "bearer-prefixed",
    )
    raw_token_auth_present = any(marker in merged for marker in explicit_raw_token_markers)
    anonymous_rejected_present = (
        ("anonymous" in merged or "匿名" in merged)
        and ("body code 401" in merged or "code=401" in merged or "401" in merged)
    )
    if raw_token_auth_present or ("authenticated" in merged and anonymous_rejected_present):
        return "当前 round 依赖已登录后取得的合法后台 raw Authorization token；匿名请求与 Bearer 前缀 token 在当前 receipt 中均未通过，不能误读成匿名路径。"
    if (
        "authenticated rerun" in merged
        or "authenticated-adjustment" in merged
        or "saved current-round admin cookie" in merged
        or "saved-cookie" in merged
    ):
        return "当前 round 的 decisive receipt 依赖 authenticated rerun / saved session；no-cookie 分支未直接成功，不能误读成匿名路径复现。"
    explicit_unauth_markers = (
        "anonymous /",
        "anonymous login",
        "anonymous user",
        "匿名用户",
        "匿名访问",
        "匿名路径复现",
        "不依赖登录态",
        "未授权安装链",
        "未授权可达",
        "installer-open-chain",
    )
    if any(marker in merged for marker in explicit_unauth_markers):
        return "当前 round 以未授权 / 匿名路径复现，不依赖登录态。"
    if "anonymous" in merged or "unauth" in merged or "未授权" in merged or "前台无权限" in title:
        return "当前 round 以未授权 / 匿名路径复现，不依赖登录态。"
    explicit_app_credential_markers = (
        "accepted app credential",
        "app-credential",
        "app credential",
        "openapi app credential",
        "accepted live openapi app credential",
        "restapipermissionadapter",
    )
    if any(marker in merged for marker in explicit_app_credential_markers):
        return "当前 round 依赖一个已接受的 OpenAPI / app credential；这条链路不是匿名入口，也不要求后台管理员会话。"
    if "admin" in merged or "后台" in title or "管理员" in merged:
        return "需要后台管理员会话或等价后台权限；这条链路不应被误读成匿名风险。"
    return "需要结合当前验证环境满足相应入口与权限前提。"


def find_round_object(objects_dir: Path, prefix: str) -> Path | None:
    matches = sorted(objects_dir.glob(f"{prefix}*.md"))
    return matches[0] if matches else None


def slot_token_from_object_path(path: Path, repo_slug: str) -> str | None:
    parts = path.name.split(".")
    for idx, part in enumerate(parts):
        if part == repo_slug and idx + 1 < len(parts):
            token = parts[idx + 1].strip()
            return token or None
    return None


def finding_slot_object(
    objects_dir: Path,
    prefix: str,
    repo_slug: str,
    slot: str,
    preferred_slot_token: str | None = None,
) -> Path | None:
    patterns = [
        f"{prefix}.{repo_slug}.{slot}.*.md",
        f"{prefix}.*.{slot}.{repo_slug}.*.md",
        f"{prefix}.*.{slot}.*.md",
        # Reopened findings often materialize as `B5-reopen`, `B3-recheck`, etc.
        # Keep the canonical slot anchor (`B5`) but allow one suffixed variant hop.
        f"{prefix}.{repo_slug}.{slot}-*.md",
        f"{prefix}.*.{slot}-*.md",
    ]
    matches: list[Path] = []
    seen: set[Path] = set()
    for pattern in patterns:
        for match in sorted(objects_dir.glob(pattern)):
            if match in seen:
                continue
            matches.append(match)
            seen.add(match)
    if not matches:
        return None

    base_slot = str(slot).strip()
    preferred_token = str(preferred_slot_token or "").strip()

    def score(path: Path) -> tuple[int, int, str]:
        token = slot_token_from_object_path(path, repo_slug) or ""
        if preferred_token and token == preferred_token:
            rank = 0
        elif preferred_token and token.startswith(f"{base_slot}-"):
            rank = 1
        elif token.startswith(f"{base_slot}-"):
            rank = 2
        elif token == base_slot:
            rank = 3
        else:
            rank = 4
        return (rank, 0 if token else 1, path.name)

    return sorted(matches, key=score)[0]


def select_textual_http_refs(paths: list[str]) -> list[str]:
    refs: list[str] = []
    for raw in paths:
        path = Path(raw)
        if not path.exists() or not path.is_file():
            continue
        if "/artifacts/" not in str(path):
            continue
        if path.suffix.lower() not in TEXTUAL_HTTP_SUFFIXES:
            continue
        refs.append(str(path))
    return dedupe_preserve_order(refs)


def build_v4_http_entries(request_lines: list[str], http_refs: list[str], finding_id: str) -> list[dict[str, Any]]:
    if not http_refs:
        return []
    request_body = [
        "# Synthesized from current-round attempt receipt and retained HTTP artifacts",
        f"# finding_id: {finding_id}",
        "",
    ]
    if request_lines:
        request_body.append("## Observed request steps")
        request_body.extend(f"- {line}" for line in request_lines)
    else:
        request_body.append("## Observed request steps")
        request_body.append("- current-round receipt retained the response-side artifacts but did not preserve a raw request packet")
    return [
        {
            "label": "fresh-round-http-evidence",
            "request_text": "\n".join(request_body).rstrip() + "\n",
            "response_paths": http_refs[:8],
        }
    ]


def build_legacy_http_entries(vr: dict[str, Any]) -> list[dict[str, Any]]:
    evidence = vr.get("evidence") or {}
    idx_path = evidence.get("request_response_index")
    if not idx_path:
        return []
    path = Path(str(idx_path)).expanduser()
    if not path.exists():
        return []
    try:
        idx = read_json(path)
    except Exception:
        return []
    entries: list[dict[str, Any]] = []
    for row in idx.get("entries") or []:
        request_path = str(row.get("request_path") or "").strip()
        response_path = str(row.get("response_path") or "").strip()
        if request_path and response_path and Path(request_path).exists() and Path(response_path).exists():
            entries.append(
                {
                    "label": row.get("label") or f"attempt-{len(entries) + 1:03d}",
                    "request_path": request_path,
                    "response_path": response_path,
                }
            )
    return entries


def render_http_response_text(response_paths: list[str]) -> str:
    parts: list[str] = []
    for raw in response_paths:
        path = Path(raw)
        if not path.exists() or not path.is_file():
            continue
        parts.append(f"## source: {path}")
        parts.append("")
        parts.append(read_text(path).rstrip())
        parts.append("")
    return "\n".join(parts).rstrip() + "\n"


def normalize_inline_text(text: Any) -> str:
    return re.sub(r"\s+", " ", str(text or "")).strip()


def split_conditions(text: str) -> list[str]:
    normalized = normalize_inline_text(text)
    if not normalized:
        return []
    parts = [part.strip(" -") for part in re.split(r"\s*[;；]\s*", normalized) if part.strip(" -")]
    return dedupe_preserve_order(parts) or [normalized]


def extract_urls(text: str) -> list[str]:
    return re.findall(r"https?://[^\s`\"'<>]+", text or "")


def extract_request_lines_from_text(text: str) -> list[str]:
    lines: list[str] = []
    for raw_line in str(text or "").splitlines():
        line = raw_line.strip().replace("`", "")
        match = re.match(r"^-?\s*((?:GET|POST|PUT|PATCH|DELETE)\s+\S+.*)$", line)
        if match:
            lines.append(match.group(1).strip().rstrip("；;"))
    return lines


def request_lines_from_finding(finding: dict[str, Any]) -> list[str]:
    explicit = [normalize_inline_text(item) for item in finding.get("request_lines") or [] if normalize_inline_text(item)]
    if explicit:
        return dedupe_preserve_order(explicit)

    lines: list[str] = []
    for entry in finding.get("http_entries") or []:
        request_path = str(entry.get("request_path") or "").strip()
        if request_path and Path(request_path).exists():
            lines.extend(extract_request_lines_from_text(read_text(Path(request_path))))
        request_text = str(entry.get("request_text") or "").strip()
        if request_text:
            lines.extend(extract_request_lines_from_text(request_text))
    return dedupe_preserve_order(lines)


def endpoint_paths_from_request_lines(request_lines: list[str]) -> list[str]:
    paths: list[str] = []
    for line in request_lines:
        match = re.match(r"^(?:GET|POST|PUT|PATCH|DELETE)\s+(\S+)", line)
        if not match:
            continue
        raw_target = match.group(1)
        if raw_target.startswith("http://") or raw_target.startswith("https://"):
            parsed = urllib.parse.urlsplit(raw_target)
            path = parsed.path or raw_target
            query = parsed.query
        else:
            target = raw_target
            if "?" in target:
                path, query = target.split("?", 1)
            else:
                path, query = target, ""
        if query and path.endswith("/index"):
            action = urllib.parse.parse_qs(query).get("action", [None])[0]
            if action:
                paths.append(f"{path}?action={action}")
                continue
        paths.append(path or raw_target)
    return dedupe_preserve_order(paths)


def title_endpoint_hint(title: str) -> str | None:
    match = re.search(r"((?:[A-Za-z0-9_-]+/)+[A-Za-z0-9_-]+)", title)
    if not match:
        return None
    return "/" + match.group(1).lstrip("/")


def likely_endpoint_paths(finding: dict[str, Any]) -> list[str]:
    request_lines = request_lines_from_finding(finding)
    paths = endpoint_paths_from_request_lines(request_lines)
    title_hint = title_endpoint_hint(str(finding.get("title") or ""))
    if title_hint:
        paths.append(title_hint)
    return dedupe_preserve_order(paths)


def primary_base_url(bundle: dict[str, Any], finding: dict[str, Any]) -> str | None:
    candidates: list[str] = []
    round_info = bundle.get("round") or {}
    if round_info.get("base_url"):
        candidates.append(str(round_info.get("base_url")))
    for raw in [
        finding.get("base_url"),
        finding.get("summary"),
        finding.get("no_overclaim_note"),
        finding.get("preconditions"),
    ]:
        candidates.extend(extract_urls(str(raw or "")))

    origins: list[str] = []
    for raw in candidates:
        parsed = urllib.parse.urlsplit(raw)
        if not parsed.scheme or not parsed.netloc:
            continue
        path = parsed.path or ""
        if path in {"", "/"}:
            origin = f"{parsed.scheme}://{parsed.netloc}"
        else:
            origin = f"{parsed.scheme}://{parsed.netloc}"
        origins.append(origin)
    deduped = dedupe_preserve_order(origins)
    return deduped[0] if deduped else None


def repo_relative_path(bundle: dict[str, Any], raw_path: str) -> str:
    repo_local = str(((bundle.get("repo") or {}).get("local_path")) or "").strip()
    if not repo_local:
        return raw_path
    try:
        repo_root = Path(repo_local).expanduser().resolve()
        path = Path(raw_path).expanduser().resolve()
        return str(path.relative_to(repo_root))
    except Exception:
        return raw_path


def collect_candidate_refs(finding: dict[str, Any]) -> list[str]:
    refs: list[str] = []
    refs.extend([str(item) for item in finding.get("handoff_refs") or [] if str(item).strip()])
    refs.extend([str(item) for item in finding.get("artifact_refs") or [] if str(item).strip()])
    for value in (finding.get("source_refs") or {}).values():
        if value:
            refs.append(str(value))
    poc_path = str(finding.get("poc_path") or "").strip()
    if poc_path:
        refs.append(poc_path)
    return dedupe_preserve_order(refs)


def collect_repo_source_refs(bundle: dict[str, Any], finding: dict[str, Any]) -> list[str]:
    repo_local = str(((bundle.get("repo") or {}).get("local_path")) or "").strip()
    if not repo_local:
        return []
    try:
        repo_root = Path(repo_local).expanduser().resolve()
    except Exception:
        return []

    refs: list[str] = []
    for raw in collect_candidate_refs(finding):
        path = Path(raw).expanduser()
        try:
            resolved = path.resolve()
        except Exception:
            continue
        if not resolved.exists() or not resolved.is_file():
            continue
        if not str(resolved).startswith(str(repo_root)):
            continue
        lower = str(resolved).lower()
        if resolved.suffix.lower() not in CODE_EXTENSIONS and "/app/" not in lower and "/src/" not in lower and "/vendor/" not in lower:
            continue
        refs.append(str(resolved))
    refs = dedupe_preserve_order(refs)
    return sorted(
        refs,
        key=lambda raw: (
            0 if "/controller/" in raw.lower() else 1 if "/app/" in raw.lower() or "/src/" in raw.lower() else 2,
            len(raw),
        ),
    )


def guess_method_name(finding: dict[str, Any]) -> str | None:
    for endpoint in likely_endpoint_paths(finding):
        if endpoint.startswith("http://") or endpoint.startswith("https://"):
            parsed = urllib.parse.urlsplit(endpoint)
        else:
            parsed = urllib.parse.urlsplit(f"https://placeholder{endpoint if endpoint.startswith('/') else '/' + endpoint}")
        action = urllib.parse.parse_qs(parsed.query).get("action", [None])[0]
        if parsed.path.endswith("/index") and action and re.match(r"^[A-Za-z_][A-Za-z0-9_]*$", action):
            return action
        basename = parsed.path.rstrip("/").split("/")[-1]
        if basename and re.match(r"^[A-Za-z_][A-Za-z0-9_]*$", basename):
            return basename

    title = str(finding.get("title") or "")
    match = re.search(r"/([A-Za-z_][A-Za-z0-9_]*)\b", title)
    if match:
        return match.group(1)
    return None


def guess_trigger_method(finding: dict[str, Any], primary_source_ref: str | None) -> str | None:
    method = guess_method_name(finding)
    if not method:
        return None
    if primary_source_ref:
        stem = Path(primary_source_ref).stem
        if re.match(r"^[A-Za-z_][A-Za-z0-9_]*$", stem):
            return f"{stem}::{method}()"
    return f"{method}()"


def extract_php_method_body(source_path: Path, method_name: str) -> str:
    text = read_text(source_path)
    match = re.search(rf"function\s+{re.escape(method_name)}\s*\(", text)
    if not match:
        return ""
    brace_start = text.find("{", match.end())
    if brace_start == -1:
        return ""
    depth = 0
    for idx in range(brace_start, len(text)):
        char = text[idx]
        if char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                return text[brace_start + 1 : idx]
    return ""


def extract_component_hints(primary_source_ref: str | None, finding: dict[str, Any], bundle: dict[str, Any]) -> list[str]:
    hints: list[str] = []
    method_name = guess_method_name(finding)
    if primary_source_ref and method_name:
        source_path = Path(primary_source_ref)
        if source_path.suffix.lower() == ".php":
            body = extract_php_method_body(source_path, method_name)
            for class_name, call_name in re.findall(r"([A-Z][A-Za-z0-9_\\\\]+)::([A-Za-z_][A-Za-z0-9_]*)\s*\(", body):
                class_short = class_name.split("\\")[-1]
                hints.append(f"{class_short}::{call_name}()")
            for call_name in re.findall(r"(?<!->)(?<!::)\b([A-Za-z_][A-Za-z0-9_]*)\s*\(", body):
                lower = call_name.lower()
                if lower in PHP_CALL_EXCLUDE:
                    continue
                hints.append(f"{call_name}()")
    for raw in collect_repo_source_refs(bundle, finding)[1:4]:
        hints.append(repo_relative_path(bundle, raw))
    return dedupe_preserve_order(hints)[:6]


def inferred_severity(finding: dict[str, Any]) -> str:
    merged = f"{finding.get('title')}\n{finding.get('summary')}\n{finding.get('no_overclaim_note')}".lower()
    if "read" in merged or "文件读取" in str(finding.get("title") or "") or "sql" in merged or "default credential" in merged:
        return "高危"
    if "upload" in merged or "上传" in str(finding.get("title") or "") or "ssrf" in merged:
        return "中危"
    return "待人工评估"


def impact_scope_text(finding: dict[str, Any]) -> str:
    explicit = normalize_inline_text(finding.get("impact_scope"))
    if explicit:
        return explicit
    summary = normalize_inline_text(finding.get("summary"))
    if summary:
        return summary
    boundary = normalize_inline_text(finding.get("no_overclaim_note"))
    if boundary:
        return boundary
    return "当前 round 已确认存在可复现风险，但具体影响边界仍应以后文不过度宣称说明为准。"


def effective_poc_filename(finding: dict[str, Any]) -> str | None:
    poc_path = resolve_poc_path(finding)
    if poc_path is None:
        return None
    suffix = poc_path.suffix or ".txt"
    return f"{finding['finding_id']}-effective{suffix}"


def report_effective_poc_path(report_dir: Path, finding: dict[str, Any]) -> Path | None:
    filename = effective_poc_filename(finding)
    if not filename:
        return None
    return report_dir / "poc" / filename


def resolve_poc_path(finding: dict[str, Any]) -> Path | None:
    value = str(finding.get("poc_path") or "").strip()
    if not value:
        return None
    path = Path(value).expanduser()
    return path if path.exists() and path.is_file() else None


def render_count_lines(bundle: dict[str, Any]) -> list[str]:
    snapshot = bundle.get("coverage_snapshot") or {}
    lines: list[str] = []
    for key in [
        "in_scope_findings_total",
        "terminal_disposition_count",
        "delivery_findings_count",
        "held_out_findings_count",
        "fresh_confirmed_count",
        "fresh_blocked_count",
        "fresh_manual_needed_count",
        "fresh_skip_by_policy_count",
        "legacy_ready_for_delivery_count",
        "legacy_need_human_review_count",
        "remaining_unfinished_count",
    ]:
        if key in snapshot:
            lines.append(f"- `{key}` = {snapshot[key]}")
    return lines


def summarize_repo_source(bundle: dict[str, Any]) -> list[str]:
    round_info = bundle.get("round") or {}
    lines = [
        f"- source_kind：`{bundle.get('source_kind')}`",
    ]
    if round_info.get("round_root"):
        lines.append(f"- current round root：`{round_info['round_root']}`")
    if round_info.get("run_dir"):
        lines.append(f"- run dir：`{round_info['run_dir']}`")
    if round_info.get("env_dir"):
        lines.append(f"- env dir：`{round_info['env_dir']}`")
    if round_info.get("base_url"):
        lines.append(f"- 验证基线：`{round_info['base_url']}`")
    lines.append(f"- round_status：`{bundle.get('round_status')}`")
    lines.append(f"- repo_status：`{bundle.get('repo_status')}`")
    return lines


def render_repo_cn_report(bundle: dict[str, Any]) -> str:
    repo = bundle.get("repo") or {}
    round_info = bundle.get("round") or {}
    delivery_findings = bundle.get("delivery_findings") or []
    held_out_findings = bundle.get("held_out_findings") or []
    title = repo.get("display_name") or zh_product_name(str(repo.get("slug") or "unknown"))

    lines = [
        f"# {title} 仓库级漏洞审计与交付报告",
        "",
        "> 说明：本报告保持当前标准交付报告目录形状，但输入 owner 已切到 current-round truth / canonical delivery input，而不再依赖旧 summary 偷当主真源。",
        "",
        "---",
        "",
        "# 漏洞描述",
        "",
        f"本轮 `{repo.get('slug')}` 的 repo 主线已经完成 current-round queue closure，并在本地标准交付包中默认纳入 **{len(delivery_findings)} 条正式交付项**。",
        "",
    ]
    if delivery_findings:
        lines.append("当前默认进入正式交付层的问题如下：")
        lines.append("")
        for idx, finding in enumerate(delivery_findings, start=1):
            lines.append(f"{idx}. **{finding['title']}**")
    else:
        lines.append("本轮没有满足默认正式交付条件的 fresh-confirmed 问题。")
    lines.extend(
        [
            "",
            "---",
            "",
            "# 基础信息",
            "",
            "## 影响产品",
            "",
            f"- 产品名称：**{title}**",
            f"- 仓库标识：`{repo.get('slug')}`",
            f"- 仓库地址：`{repo.get('remote_url') or '待补充'}`",
            f"- 本地源码路径：`{repo.get('local_path') or '待补充'}`",
            f"- 当前核对版本：`{repo.get('commit') or '待补充'}`（`{repo.get('branch') or '待补充'}`）",
            "",
            "## 本轮真源",
            "",
        ]
    )
    lines.extend(summarize_repo_source(bundle))
    lines.extend(
        [
            "",
            "## 总体结论",
            "",
        ]
    )
    lines.extend(render_count_lines(bundle))
    lines.extend(
        [
            "",
            "当前冻结口径是：",
            "",
            "- 默认正式交付页只围绕 `fresh-confirmed` / 已 ready-for-delivery 的问题展开。",
            "- `fresh-blocked / fresh-manual-needed / fresh-skip-by-policy` 不会消失，但也不会被硬升级成正式漏洞页。",
            "",
            "---",
            "",
            "# 正式交付项",
            "",
        ]
    )
    if delivery_findings:
        for finding in delivery_findings:
            lines.extend(
                [
                    f"## {finding['title']}",
                    "",
                    f"- finding_id：`{finding['finding_id']}`",
                    f"- 当前 disposition：`{finding['disposition']}`",
                    f"- 漏洞类型：{vulnerability_type_from_title(finding['title'])}",
                    f"- 当前结论：{finding['summary']}",
                    f"- 认证 / 触达边界：{finding['auth_boundary']}",
                    f"- 不过度宣称说明：{finding['no_overclaim_note'] or '保持当前 round truth，不扩写为超出 receipt 边界的结论。'}",
                    "",
                ]
            )
    else:
        lines.extend(["- none", ""])

    lines.extend(
        [
            "---",
            "",
            "# 本轮保留但未纳入正式交付项的问题",
            "",
        ]
    )
    if held_out_findings:
        for finding in held_out_findings:
            lines.extend(
                [
                    f"## {finding['title']}",
                    "",
                    f"- finding_id：`{finding['finding_id']}`",
                    f"- 当前 disposition：`{finding['disposition']}`",
                    f"- hold-out 原因：{finding['hold_out_reason'] or finding['summary']}",
                    f"- 当前 truth：{finding['summary']}",
                    f"- 认证 / 触达边界：{finding['auth_boundary']}",
                    f"- 不过度宣称说明：{finding['no_overclaim_note'] or '这条问题保留在 repo 级收口与复盘层，不默认提升为正式交付页。'}",
                    "",
                ]
            )
    else:
        lines.extend(["- none", ""])

    lines.extend(
        [
            "---",
            "",
            "# 修复建议",
            "",
            "## 仓库级共性修复建议",
            "",
            "1. 对所有已 fresh-confirmed 的风险链补齐服务端权限校验、输入校验与日志审计。",
            "2. 对本轮 hold-out 问题补齐阻断点修复或额外验证条件，再决定是否进入正式交付页。",
            "3. 对正式修复版本做一次面向交付清单的回归验证，避免 runtime/plugin/config 漂移继续遮蔽真实边界。",
            "",
        ]
    )
    return "\n".join(lines).rstrip() + "\n"


def render_finding_md(bundle: dict[str, Any], finding: dict[str, Any], report_dir: Path) -> str:
    repo = bundle.get("repo") or {}
    poc_path = resolve_poc_path(finding)
    poc_meta = dict(finding.get("poc_meta") or {})
    if not poc_meta:
        poc_meta = parse_poc_metadata(poc_path)

    request_lines = request_lines_from_finding(finding)
    endpoint_paths = likely_endpoint_paths(finding)
    primary_source_refs = collect_repo_source_refs(bundle, finding)
    primary_source_ref = primary_source_refs[0] if primary_source_refs else None
    trigger_method = guess_trigger_method(finding, primary_source_ref)
    component_hints = extract_component_hints(primary_source_ref, finding, bundle)
    effective_poc_path = report_effective_poc_path(report_dir, finding)
    local_http_dir = report_dir / "http" / finding["finding_id"]
    base_url = primary_base_url(bundle, finding)
    no_overclaim = normalize_inline_text(
        finding.get("no_overclaim_note")
        or "当前文档只覆盖 current-round 已拿到的 decisive receipt，不把旁路猜测、历史 receipt 或源码层可能性偷写成 fresh success。"
    )
    summary = normalize_inline_text(finding.get("summary"))
    auth_boundary = normalize_inline_text(finding.get("auth_boundary"))
    preconditions = split_conditions(str(finding.get("preconditions") or "需要结合当前验证环境满足对应入口与权限前提。"))
    defense_notes = normalize_inline_text(finding.get("defense_notes") or "需要结合源码与当前 receipt 继续解读。")
    source_finding = normalize_inline_text(poc_meta.get("source_finding") or "")
    payload_constraints = normalize_inline_text(poc_meta.get("payload_constraints") or "")
    confidence = normalize_inline_text(poc_meta.get("confidence") or finding.get("confidence") or "unknown")
    fix_sections = detailed_fix_sections(finding["title"])
    proof_refs = [ref for ref in finding.get("artifact_refs") or [] if "/artifacts/http/" in ref][:8]

    lines = [
        "# 漏洞描述",
        "",
        "## 基础信息",
        "",
        f"- 漏洞标题：{finding['title']}",
        f"- finding_id：`{finding['finding_id']}`",
        f"- 漏洞类型：{vulnerability_type_from_title(finding['title'])}",
        f"- 危害等级：{inferred_severity(finding)}",
        f"- 影响产品：{repo.get('display_name') or repo.get('slug') or '待补充'}",
        f"- 仓库地址：`{repo.get('remote_url') or '待补充'}`",
        f"- 当前核对版本：`{repo.get('commit') or '待补充'}`（`{repo.get('branch') or '待补充'}`）",
        f"- 影响范围：{impact_scope_text(finding)}",
        f"- 利用条件：{'; '.join(preconditions) if preconditions else '需要结合当前验证环境满足对应入口与权限前提。'}",
        f"- formal verifier 结果：`{finding['disposition']}`",
        "- 交付状态：`ready_for_delivery = True`",
        "",
        "# 漏洞核心原理",
        "",
        f"当前 round 的核心结论是：{summary or '需要结合当前验证结果进一步细化。'}",
        "",
    ]
    if primary_source_ref or trigger_method:
        source_sentence = "从当前可回溯的入口位置看，"
        if primary_source_ref:
            source_sentence += f"主要入口位于 `{repo_relative_path(bundle, primary_source_ref)}`"
        else:
            source_sentence += "主要入口文件仍需人工补充"
        if trigger_method:
            source_sentence += f" 的 `{trigger_method}`"
        source_sentence += "。"
        lines.extend([source_sentence, ""])
    if auth_boundary:
        lines.extend([f"当前权限/触达边界为：{auth_boundary}", ""])
    if component_hints:
        lines.extend(
            [
                "当前可直接回溯到的关键处理链包括：",
                "",
                *(f"- `{item}`" for item in component_hints),
                "",
            ]
        )
    lines.extend([no_overclaim, "", "# 仓库下载地址", "", f"- 仓库地址：`{repo.get('remote_url') or '待补充'}`"])
    if repo.get("local_path"):
        lines.append(f"- 本地源码路径：`{repo.get('local_path')}`")
    lines.extend(["", "# 补充说明", ""])
    lines.extend(
        [
            f"- 本报告以 `{bundle.get('source_kind')}` 对应的 current-round truth 为准；若与更早阶段的泛化表述冲突，应以后文不过度宣称边界为准。",
            f"- 不过度宣称说明：{no_overclaim}",
            f"- 关键防线/约束：{defense_notes}",
        ]
    )
    if effective_poc_path:
        lines.append(f"- 当前 formal 交付 PoC：`{effective_poc_path}`")
    elif poc_path:
        lines.append(f"- 当前 formal 交付 PoC：`{poc_path}`")
    if poc_path and effective_poc_path and poc_path.resolve() != effective_poc_path.resolve():
        lines.append(f"- 来源 PoC：`{poc_path}`")
    if finding.get("http_entries"):
        lines.append(f"- 当前 HTTP 记录目录：`{local_http_dir}`")
    elif local_http_dir.exists():
        lines.append(f"- 当前 HTTP 记录目录：`{local_http_dir}`")
    else:
        lines.append(f"- 当前 HTTP 记录目录：`{local_http_dir}`（待本地生成）")
    if finding.get("main_evidence_ref"):
        lines.append(f"- 关键证据主锚点：`{finding.get('main_evidence_ref')}`")
    if source_finding:
        lines.append(f"- 来源 finding 描述：{source_finding}")

    lines.extend(["", "# 公网验证链接", "", "当前没有固定公网交付链接可直接附在本报告中。", ""])
    if base_url:
        lines.extend(["本轮正式验证基线为：", "", f"- `{base_url}`"])
        for endpoint in endpoint_paths[:4]:
            lines.append(f"- 关键接口：`{endpoint}`")
    else:
        lines.extend(["本轮正式验证在本地或临时 lab 中完成，当前未从输入对象中稳定抽到统一基线 URL。"])

    lines.extend(["", "# 代码审计分析过程", "", "## 漏洞基本信息", ""])
    if primary_source_ref:
        lines.extend(["### 漏洞入口文件", "", f"- `{repo_relative_path(bundle, primary_source_ref)}`", ""])
    if trigger_method:
        lines.extend(["### 漏洞触发方法", "", f"- `{trigger_method}`", ""])
    if component_hints:
        lines.extend(["### 受影响核心组件", "", *(f"- `{item}`" for item in component_hints), ""])
    if preconditions:
        lines.extend(["### 利用条件", "", *(f"- {item}" for item in preconditions), ""])
    lines.extend(["## 漏洞原理深度分析", "", "### 步骤 1：确认入口与权限边界", ""])
    if primary_source_ref:
        lines.append(
            f"当前可直接回溯到的入口文件为 `{repo_relative_path(bundle, primary_source_ref)}`；结合 `{trigger_method or '对应入口方法'}` 与 current-round handoff，可先把这条链路的暴露面和权限边界收敛到：{auth_boundary or '需要结合真实业务入口继续细化。'}"
        )
    else:
        lines.append(f"当前 round 已确认这条问题可产生 terminal disposition，但入口文件仍需结合上游源码与 receipt 再做补充；现阶段先以权限边界 `{auth_boundary or '待补充'}` 保持 truthful 落点。")
    lines.extend(["", "### 步骤 2：确认危险处理链与关键约束", ""])
    if component_hints:
        lines.append(
            "结合当前源码线索与 PoC 元信息，可直接回溯到的关键处理链包括："
            + "、".join(f"`{item}`" for item in component_hints)
            + "；这些组件共同决定了用户输入如何进入读取、上传、抓取或执行链。"
        )
    else:
        lines.append("当前 delivery 输入已经保留了当前 round 的关键证据与 PoC，但源码级组件链尚不够厚；这里先保留为需要结合上游源码继续补强的分析位。")
    lines.append(f"当前已确认的关键防线/约束为：{defense_notes}")
    lines.extend(["", "### 步骤 3：结合 current-round receipt 收窄正式结论", ""])
    lines.append(f"本轮正式结论应落在：{summary or '需要结合当前 round receipt 继续细化。'}")
    lines.append(no_overclaim)

    lines.extend(["", "# EXP（Python 验证脚本）", "", "## 脚本说明", ""])
    if effective_poc_path:
        lines.append(f"- 交付 PoC：`{effective_poc_path}`")
    if poc_path:
        lines.append(f"- 来源 PoC：`{poc_path}`")
    if source_finding:
        lines.append(f"- Source-Finding：{source_finding}")
    lines.append(f"- confidence：`{confidence}`")
    if payload_constraints:
        lines.append(f"- Payload-Constraints：{payload_constraints}")
    if endpoint_paths:
        for endpoint in endpoint_paths[:4]:
            lines.append(f"- 默认验证入口：`{endpoint}`")

    lines.extend(["", "# 漏洞验证", "", "## 验证前提", ""])
    if preconditions:
        lines.extend(f"- {item}" for item in preconditions)
    else:
        lines.append("- 需要结合当前验证环境满足对应入口与权限前提。")
    lines.extend(["", "## 验证步骤", ""])
    if request_lines:
        lines.extend(f"{idx}. {line}" for idx, line in enumerate(request_lines, start=1))
    else:
        lines.extend(
            [
                "1. 复用 current-round 已冻结的 PoC 与环境基线。",
                "2. 按最小可验证路径触发目标入口并保留请求/回包证据。",
                "3. 结合当前 round receipt 与不过度宣称边界，收口正式交付结论。",
            ]
        )

    lines.extend(["", "## 请求 / 回包证明", ""])
    lines.append(f"- 交付层 HTTP 记录目录：`{local_http_dir}`")
    if request_lines:
        lines.extend(f"- 关键请求步骤：{item}" for item in request_lines[:8])
    if proof_refs:
        lines.extend(f"- decisive receipt：`{ref}`" for ref in proof_refs)
    elif finding.get("main_evidence_ref"):
        lines.append(f"- decisive receipt：`{finding.get('main_evidence_ref')}`")

    lines.extend(["", "# 修复建议", "", "## 核心漏洞修复（高优先级）", ""])
    lines.extend(fix_sections["core"])
    lines.extend(["", "## 防护增强（中优先级）", ""])
    lines.extend(fix_sections["hardening"])
    lines.extend(["", "## 权限与日志加固（辅助）", ""])
    lines.extend(fix_sections["audit"])
    lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def render_technical_summary(bundle: dict[str, Any]) -> str:
    repo = bundle.get("repo") or {}
    lines = [
        f"# {repo.get('slug')} 仓库级技术汇总",
        "",
        "## 输入真源",
        "",
    ]
    lines.extend(summarize_repo_source(bundle))
    lines.extend(
        [
            "",
            "## 覆盖快照",
            "",
        ]
    )
    lines.extend(render_count_lines(bundle))
    lines.extend(
        [
            "",
            "## 正式交付项",
            "",
        ]
    )
    for finding in bundle.get("delivery_findings") or []:
        lines.extend(
            [
                f"### {finding['title']}",
                "",
                f"- finding_id：`{finding['finding_id']}`",
                f"- disposition：`{finding['disposition']}`",
                f"- summary：{finding['summary']}",
                f"- main_evidence_ref：`{finding.get('main_evidence_ref') or '待补充'}`",
                f"- poc_path：`{finding.get('poc_path') or '待补充'}`",
                "",
            ]
        )
    if not (bundle.get("delivery_findings") or []):
        lines.extend(["- none", ""])

    lines.extend(
        [
            "## Hold-out 项",
            "",
        ]
    )
    for finding in bundle.get("held_out_findings") or []:
        lines.extend(
            [
                f"### {finding['title']}",
                "",
                f"- finding_id：`{finding['finding_id']}`",
                f"- disposition：`{finding['disposition']}`",
                f"- hold_out_reason：{finding['hold_out_reason'] or finding['summary']}",
                f"- main_evidence_ref：`{finding.get('main_evidence_ref') or '待补充'}`",
                "",
            ]
        )
    if not (bundle.get("held_out_findings") or []):
        lines.extend(["- none", ""])
    return "\n".join(lines).rstrip() + "\n"


def render_index(
    report_dir: Path,
    bundle: dict[str, Any],
    finding_docs: list[str],
    poc_files: list[str],
    http_dirs: list[str],
) -> str:
    slug = (bundle.get("repo") or {}).get("slug") or report_dir.name
    held_out_findings = bundle.get("held_out_findings") or []
    lines = [
        f"# {slug} 交付产物索引",
        "",
        "## 目录说明",
        "",
        f"这个目录用于集中存放 `{slug}` 的标准交付相关产物，并把 current-round truth 固定到可复核的本地 bundle 中。",
        "",
        "当前包含六类内容：",
        "",
        "1. **Repo 级中文报告**",
        "2. **单漏洞中文报告（默认仅正式交付项）**",
        "3. **真正生效的 PoC 文件**",
        "4. **HTTP 证据目录**",
        "5. **canonical manifest**",
        "6. **final-local-review 记录（由后续阶段写入）**",
        "",
        "---",
        "",
        "## 1）Repo 级报告",
        "",
        "- `01-仓库级中文交付报告.md`",
        "- `02-仓库级技术汇总.md`",
        "- `02-仓库级技术汇总.json`",
        "",
        "---",
        "",
        "## 2）单漏洞中文报告",
        "",
    ]
    if finding_docs:
        for name in finding_docs:
            lines.append(f"- `{name}`")
    else:
        lines.append("- none")
    lines.extend(
        [
            "",
            "---",
            "",
            "## 3）真正生效的 PoC 文件",
            "",
            "目录：`poc/`",
            "",
        ]
    )
    if poc_files:
        for name in poc_files:
            lines.append(f"- `poc/{name}`")
    else:
        lines.append("- none")
    lines.extend(
        [
            "",
            "---",
            "",
            "## 4）HTTP 请求包记录",
            "",
            "目录：`http/`",
            "",
        ]
    )
    if http_dirs:
        for name in http_dirs:
            lines.append(f"- `http/{name}/`")
    else:
        lines.append("- none")
    lines.extend(
        [
            "",
            "---",
            "",
            "## 5）Canonical Marker",
            "",
            f"- `{MANIFEST_NAME}`",
            "  - 当前标准交付 bundle 的 canonical manifest；publisher / cron / final-local-review 都应优先依赖它，而不是靠目录猜测。",
            "",
            "---",
            "",
            "## 6）Final Local Review Marker",
            "",
            "- `99-最终本地复盘.md`",
            "- `99-最终本地复盘.json`",
            "",
            "---",
            "",
            "## 当前状态",
            "",
        ]
    )
    lines.extend(render_count_lines(bundle))
    if held_out_findings:
        lines.extend(
            [
                "",
                "本轮保留但未纳入正式交付页的问题：",
                "",
            ]
        )
        for finding in held_out_findings:
            lines.append(f"- `{finding['finding_id']}` → `{finding['disposition']}`")
    lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def copy_poc_files(finding: dict[str, Any], out_dir: Path) -> list[str]:
    poc_path = resolve_poc_path(finding)
    filename = effective_poc_filename(finding)
    if poc_path is None or not filename:
        return []
    if copy_file(poc_path, out_dir / "poc" / filename):
        return [filename]
    return []


def build_http_artifacts_for_finding(finding: dict[str, Any], out_dir: Path) -> str | None:
    entries = list(finding.get("http_entries") or [])
    if not entries:
        return None
    target = out_dir / "http" / finding["finding_id"]
    target.mkdir(parents=True, exist_ok=True)
    built = 0
    for idx, entry in enumerate(entries, start=1):
        request_dst = target / f"request-{idx:03d}.txt"
        response_dst = target / f"response-{idx:03d}.txt"

        request_copied = False
        request_path = str(entry.get("request_path") or "").strip()
        if request_path:
            request_copied = copy_file(Path(request_path), request_dst)
        if not request_copied:
            request_text = str(entry.get("request_text") or "").strip()
            if request_text:
                write_text(request_dst, request_text.rstrip() + "\n")
                request_copied = True

        response_copied = False
        response_path = str(entry.get("response_path") or "").strip()
        if response_path:
            response_copied = copy_file(Path(response_path), response_dst)
        if not response_copied:
            response_paths = [str(x) for x in entry.get("response_paths") or [] if str(x).strip()]
            if response_paths:
                write_text(response_dst, render_http_response_text(response_paths))
                response_copied = True
        if not response_copied:
            response_text = str(entry.get("response_text") or "").strip()
            if response_text:
                write_text(response_dst, response_text.rstrip() + "\n")
                response_copied = True

        if request_copied and response_copied:
            built += 1
    return finding["finding_id"] if built > 0 else None


def build_manifest(
    bundle: dict[str, Any],
    report_dir: Path,
    finding_docs: list[str],
    poc_files: list[str],
    http_dirs: list[str],
) -> dict[str, Any]:
    delivery_findings: list[dict[str, Any]] = []
    held_out_findings: list[dict[str, Any]] = []
    finding_doc_map = {name[:-3]: name for name in finding_docs if name.endswith(".md")}

    for finding in bundle.get("delivery_findings") or []:
        bound_poc = effective_poc_filename(finding)
        delivery_findings.append(
            {
                "finding_id": finding["finding_id"],
                "title": finding["title"],
                "disposition": finding["disposition"],
                "summary": finding["summary"],
                "report_doc": finding_doc_map.get(finding["finding_id"]),
                "poc_files": [bound_poc] if bound_poc and bound_poc in poc_files else [],
                "http_dir": f"http/{finding['finding_id']}" if finding["finding_id"] in http_dirs else None,
                "main_evidence_ref": finding.get("main_evidence_ref"),
                "auth_boundary": finding.get("auth_boundary"),
                "no_overclaim_note": finding.get("no_overclaim_note"),
            }
        )

    for finding in bundle.get("held_out_findings") or []:
        held_out_findings.append(
            {
                "finding_id": finding["finding_id"],
                "title": finding["title"],
                "disposition": finding["disposition"],
                "summary": finding["summary"],
                "hold_out_reason": finding.get("hold_out_reason") or finding["summary"],
                "main_evidence_ref": finding.get("main_evidence_ref"),
                "auth_boundary": finding.get("auth_boundary"),
                "no_overclaim_note": finding.get("no_overclaim_note"),
            }
        )

    return {
        "schema_version": 1,
        "report_kind": CANONICAL_REPORT_KIND,
        "generator": {
            "name": "build_repo_delivery_reports.py",
            "version": "v4-template-bridge",
            "generated_at": now_iso(),
        },
        "delivery_template": {
            "family": SINGLE_FINDING_TEMPLATE_FAMILY,
            "required_headings": SINGLE_FINDING_TEMPLATE_HEADINGS,
        },
        "repo": bundle.get("repo") or {},
        "round": bundle.get("round") or {},
        "source_kind": bundle.get("source_kind"),
        "selection_mode": bundle.get("selection_mode"),
        "round_status": bundle.get("round_status"),
        "repo_status": bundle.get("repo_status"),
        "coverage_snapshot": bundle.get("coverage_snapshot") or {},
        "truth_audit": bundle.get("truth_audit") or {},
        "inclusion_policy": bundle.get("inclusion_policy") or {},
        "report_dir": str(report_dir),
        "root_docs": [
            "00-索引.md",
            "01-仓库级中文交付报告.md",
            "02-仓库级技术汇总.md",
            "02-仓库级技术汇总.json",
            *(
                ["03-复现实验信息.md"]
                if (report_dir / "03-复现实验信息.md").exists()
                else []
            ),
            MANIFEST_NAME,
        ],
        "delivery_findings": delivery_findings,
        "held_out_findings": held_out_findings,
        "final_local_review": {
            "status": "pending",
            "publish_can_be_considered": False,
            "review_record_md": str(report_dir / "99-最终本地复盘.md"),
            "review_record_json": str(report_dir / "99-最终本地复盘.json"),
            "completed_at": None,
        },
        "publish_ready": False,
    }


def normalize_bundle_repo(slug: str, repo_path: Path | None) -> dict[str, Any]:
    return {
        "slug": slug,
        "display_name": zh_product_name(slug),
        "local_path": str(repo_path) if repo_path else None,
        "remote_url": repo_remote_url(repo_path),
        "branch": repo_branch(repo_path),
        "commit": repo_commit(repo_path),
    }


def normalize_legacy_delivery_input(summary_path: Path) -> dict[str, Any]:
    summary = read_json(summary_path)
    slug = str(summary.get("target_slug") or Path(str(summary.get("run_dir") or "")).name or "unknown")
    repo_path = maybe_target_repo(slug)
    delivery_findings: list[dict[str, Any]] = []
    held_out_findings: list[dict[str, Any]] = []

    for row in summary.get("entries") or []:
        finding_id = str(row.get("finding_id") or "").strip()
        if not finding_id:
            continue
        vr_path = str(row.get("verification_result") or "").strip()
        vr = read_json(Path(vr_path)) if vr_path and Path(vr_path).exists() else {}
        poc_path = choose_effective_poc(vr) or choose_original_poc(vr)
        poc_meta = parse_poc_metadata(poc_path)
        title = str(row.get("title") or finding_id)
        status = str(vr.get("status") or row.get("status") or "unknown")
        summary_text = str(vr.get("summary") or row.get("summary") or "").strip() or "需要结合当前 verifier 收口结果进一步细化。"
        preconditions = poc_meta.get("preconditions") or "需要结合当前验证环境满足对应入口与权限前提。"
        defense_notes = poc_meta.get("defense_notes") or poc_meta.get("payload_constraints") or "需要结合当前 PoC 与 verifier 结果进一步细化。"
        finding = {
            "finding_id": finding_id,
            "title": title,
            "disposition": status,
            "summary": summary_text,
            "hold_out_reason": summary_text,
            "auth_boundary": guess_auth_boundary(title, summary_text, preconditions),
            "no_overclaim_note": poc_meta.get("payload_constraints") or str(vr.get("exploitability_note") or ""),
            "preconditions": preconditions,
            "defense_notes": defense_notes,
            "poc_path": str(poc_path) if poc_path else None,
            "http_entries": build_legacy_http_entries(vr),
            "request_lines": [],
            "artifact_refs": dedupe_preserve_order(
                [
                    str((vr.get("evidence") or {}).get("request_response_index") or "").strip(),
                    str((vr.get("evidence") or {}).get("evidence_manifest") or "").strip(),
                    str((vr.get("evidence") or {}).get("candidate_signature") or "").strip(),
                    str(((vr.get("evidence") or {}).get("baseline_run") or {}).get("stdout") or "").strip(),
                    str(((vr.get("evidence") or {}).get("baseline_run") or {}).get("stderr") or "").strip(),
                ]
            ),
            "main_evidence_ref": str((vr.get("evidence") or {}).get("request_response_index") or "").strip() or vr_path or None,
            "main_evidence_mode": str(vr.get("main_evidence_mode") or row.get("main_evidence_mode") or "legacy-verifier"),
            "confidence": str(vr.get("confidence") or row.get("confidence") or ""),
            "poc_meta": poc_meta,
            "base_url": str(summary.get("base_url") or ""),
            "source_refs": {
                "verification_result": vr_path or None,
            },
        }
        if status in LEGACY_INCLUDED_STATUSES:
            delivery_findings.append(finding)
        else:
            held_out_findings.append(finding)

    return {
        "schema_version": 1,
        "source_kind": SOURCE_KIND_LEGACY,
        "repo": normalize_bundle_repo(slug, repo_path),
        "round": {
            "run_dir": summary.get("run_dir"),
            "env_dir": summary.get("env_dir"),
            "base_url": summary.get("base_url"),
            "summary_json": str(summary_path),
        },
        "selection_mode": "legacy-summary-handoff",
        "round_status": "legacy-summary-ready" if str(summary.get("next_action") or "") == "deliver-now" else "legacy-summary-open",
        "repo_status": "legacy-ready-for-delivery" if str(summary.get("next_action") or "") == "deliver-now" else "legacy-not-ready",
        "coverage_snapshot": normalize_legacy_coverage_snapshot(summary, delivery_findings, held_out_findings),
        "inclusion_policy": {
            "default_included_dispositions": sorted(LEGACY_INCLUDED_STATUSES),
            "default_held_out_dispositions": ["not-confirmed-manual-needed", "preflight-block-needs-human"],
            "notes": "legacy summary path keeps backward compatibility, but canonical v4 owner should migrate to delivery-input.json over time",
        },
        "delivery_findings": delivery_findings,
        "held_out_findings": held_out_findings,
    }


def normalize_v4_delivery_input(round_root: Path) -> dict[str, Any]:
    objects_dir = round_root / "objects"
    if not objects_dir.exists():
        raise FileNotFoundError(f"round root has no objects dir: {round_root}")

    repo_slug = round_root.parent.name
    repo_path = maybe_target_repo(repo_slug)
    board_path = find_round_object(objects_dir, "repo-findings-board")
    closure_path = find_round_object(objects_dir, "repo-closure-review")
    verdict_path = find_round_object(objects_dir, "repo-round-verdict")
    if board_path is None or closure_path is None or verdict_path is None:
        raise FileNotFoundError("round root is missing repo-findings-board / repo-closure-review / repo-round-verdict")

    board_text = read_text(board_path)
    closure_text = read_text(closure_path)
    verdict_text = read_text(verdict_path)
    board_findings = parse_board_findings(board_text)

    verdict_kv = parse_key_value_lines(verdict_text)
    closure_kv = parse_key_value_lines(extract_heading_section(closure_text, "frozen coverage_snapshot"))
    board_kv = parse_key_value_lines(extract_heading_section(board_text, "coverage counters"))
    coverage_snapshot = normalize_round_coverage_snapshot(closure_kv, board_findings)
    truth_audit = {
        "coverage_snapshot": audit_round_coverage_snapshot(
            board_findings,
            [
                ("repo-findings-board.coverage-counters", board_kv),
                ("repo-closure-review.frozen-coverage-snapshot", closure_kv),
                ("repo-round-verdict.refreshed-coverage-snapshot", verdict_kv),
            ],
        )
    }

    delivery_findings: list[dict[str, Any]] = []
    held_out_findings: list[dict[str, Any]] = []

    for finding_row in board_findings:
        slot = finding_row.get("slot", "")
        title = str(finding_row.get("title") or "").strip()
        finding_id = str(finding_row.get("finding_id") or "").strip() or fallback_v4_finding_id(repo_slug, str(slot), title)
        disposition = normalize_v4_disposition(finding_row)
        title = title or finding_id or str(slot)
        last_evidence_ref = str(finding_row.get("last_evidence_ref") or "").strip()
        preferred_slot_token = slot_token_from_object_path(Path(last_evidence_ref), repo_slug) if last_evidence_ref else None
        attempt_path = finding_slot_object(objects_dir, "attempt-receipt", repo_slug, slot, preferred_slot_token)
        stage_verdict_path = (
            Path(last_evidence_ref).expanduser()
            if last_evidence_ref and Path(last_evidence_ref).expanduser().exists()
            else finding_slot_object(objects_dir, "stage-verdict.finding-replay", repo_slug, slot, preferred_slot_token)
        )
        handoff_path = finding_slot_object(objects_dir, "stage-handoff.finding-replay", repo_slug, slot, preferred_slot_token)
        attempt_text = read_text(attempt_path) if attempt_path else ""
        stage_verdict_text = read_text(stage_verdict_path) if stage_verdict_path else ""
        handoff_text = read_text(handoff_path) if handoff_path else ""
        handoff_refs = parse_paths_from_section(handoff_text, "hot refs")
        artifact_refs = dedupe_preserve_order(
            parse_paths_from_section(attempt_text, "artifact refs") + parse_paths_from_section(stage_verdict_text, "artifact refs")
        )
        poc_path = next((ref for ref in handoff_refs if ref.endswith(".py") and Path(ref).exists()), None)
        poc_meta = parse_poc_metadata(Path(poc_path) if poc_path else None)
        request_lines = extract_http_request_lines(attempt_text)
        http_refs = select_textual_http_refs(artifact_refs)
        current_round_truth = str(finding_row.get("current_round_truth") or "").strip()
        no_overclaim = extract_no_overclaim_note(attempt_text) or current_round_truth
        preconditions = poc_meta.get("preconditions") or "需要结合当前验证环境满足对应入口与权限前提。"
        defense_notes = poc_meta.get("defense_notes") or poc_meta.get("payload_constraints") or "需要结合当前 round receipt 与源码位置进一步解读。"

        finding = {
            "finding_id": finding_id,
            "slot": slot,
            "title": title,
            "disposition": disposition,
            "summary": current_round_truth,
            "hold_out_reason": current_round_truth,
            "auth_boundary": guess_auth_boundary(title, current_round_truth + "\n" + no_overclaim, preconditions),
            "no_overclaim_note": no_overclaim,
            "preconditions": preconditions,
            "defense_notes": defense_notes,
            "poc_path": poc_path,
            "http_entries": build_v4_http_entries(request_lines, http_refs, finding_id),
            "request_lines": request_lines,
            "artifact_refs": artifact_refs,
            "main_evidence_ref": last_evidence_ref or (artifact_refs[0] if artifact_refs else None),
            "main_evidence_mode": "current-round-artifacts",
            "confidence": poc_meta.get("confidence") or "medium",
            "poc_meta": poc_meta,
            "handoff_refs": handoff_refs,
            "base_url": next(iter(extract_urls(attempt_text + "\n" + current_round_truth)), None),
            "source_refs": {
                "attempt_receipt": str(attempt_path) if attempt_path else None,
                "stage_verdict": str(stage_verdict_path) if stage_verdict_path else None,
                "handoff": str(handoff_path) if handoff_path else None,
            },
        }
        if disposition in V4_INCLUDED_DISPOSITIONS:
            delivery_findings.append(finding)
        else:
            held_out_findings.append(finding)

    return {
        "schema_version": 1,
        "source_kind": SOURCE_KIND_V4,
        "repo": normalize_bundle_repo(repo_slug, repo_path),
        "round": {
            "round_root": str(round_root),
            "report_root": str(round_root.parents[2]),
            "round_id": round_root.name,
        },
        "selection_mode": verdict_kv.get("selection_mode") or "repo-complete / delivery-report-bridge",
        "round_status": verdict_kv.get("round_status") or "round-closed",
        "repo_status": verdict_kv.get("repo_status") or "repo-coverage-complete",
        "coverage_snapshot": coverage_snapshot,
        "truth_audit": truth_audit,
        "inclusion_policy": {
            "default_included_dispositions": sorted(V4_INCLUDED_DISPOSITIONS),
            "default_held_out_dispositions": ["fresh-blocked", "fresh-manual-needed", "fresh-skip-by-policy"],
            "notes": "repo 主线保留所有 terminal dispositions，但正式交付页默认只纳入 fresh-confirmed",
        },
        "delivery_findings": delivery_findings,
        "held_out_findings": held_out_findings,
    }


def build_reports(bundle: dict[str, Any], out_dir: Path) -> dict[str, Any]:
    out_dir.mkdir(parents=True, exist_ok=True)

    write_text(out_dir / "02-仓库级技术汇总.md", render_technical_summary(bundle))
    write_json(out_dir / "02-仓库级技术汇总.json", bundle)
    write_text(out_dir / "01-仓库级中文交付报告.md", render_repo_cn_report(bundle))

    finding_docs: list[str] = []
    poc_files: list[str] = []
    http_dirs: list[str] = []

    for finding in bundle.get("delivery_findings") or []:
        doc_name = f"{finding['finding_id']}.md"
        write_text(out_dir / doc_name, render_finding_md(bundle, finding, out_dir))
        finding_docs.append(doc_name)
        poc_files.extend(copy_poc_files(finding, out_dir))
        http_dir = build_http_artifacts_for_finding(finding, out_dir)
        if http_dir:
            http_dirs.append(http_dir)

    write_text(out_dir / "00-索引.md", render_index(out_dir, bundle, sorted(finding_docs), sorted(poc_files), sorted(http_dirs)))

    manifest = build_manifest(bundle, out_dir, sorted(finding_docs), sorted(poc_files), sorted(http_dirs))
    manifest_path = out_dir / MANIFEST_NAME
    write_json(manifest_path, manifest)

    return {
        "report_dir": str(out_dir),
        "manifest_path": str(manifest_path),
        "target_slug": (bundle.get("repo") or {}).get("slug"),
        "source_kind": bundle.get("source_kind"),
        "round_root": (bundle.get("round") or {}).get("round_root"),
        "generated_docs": [
            "00-索引.md",
            "01-仓库级中文交付报告.md",
            "02-仓库级技术汇总.md",
            "02-仓库级技术汇总.json",
            MANIFEST_NAME,
            *sorted(finding_docs),
        ],
        "generated_poc_files": sorted(poc_files),
        "generated_http_dirs": sorted(http_dirs),
        "coverage_snapshot": bundle.get("coverage_snapshot") or {},
        "delivery_findings": [finding["finding_id"] for finding in bundle.get("delivery_findings") or []],
        "held_out_findings": [finding["finding_id"] for finding in bundle.get("held_out_findings") or []],
    }


def render_delivery_stage_verdict_md(bundle: dict[str, Any], result: dict[str, Any], delivery_input_path: Path, round_root: Path) -> str:
    repo = bundle.get("repo") or {}
    snapshot = bundle.get("coverage_snapshot") or {}
    delivery_findings = bundle.get("delivery_findings") or []
    held_out_findings = bundle.get("held_out_findings") or []
    manifest_path = Path(str(result["manifest_path"]))
    report_dir = Path(str(result["report_dir"]))
    stage_md_path = round_root / "objects" / f"stage-verdict.delivery-reports.{repo.get('slug')}.{round_root.name}.md"
    stage_json_path = round_root / "objects" / f"stage-verdict.delivery-reports.{repo.get('slug')}.{round_root.name}.json"

    lines = [
        f"# stage-verdict.delivery-reports — {repo.get('slug')} / {round_root.name}",
        "",
        "## stage result",
        "- stage: `delivery-reports`",
        "- status: `completed`",
        "- publish_status: `not-triggered`",
        "- bundle_status: `canonical-local-bundle-written`",
        f"- report_dir: `{report_dir}`",
        f"- manifest_path: `{manifest_path}`",
        f"- delivery_input_json: `{delivery_input_path}`",
        "",
        "## coverage snapshot",
    ]
    lines.extend(render_count_lines(bundle))
    lines.extend(
        [
            "",
            "## delivery policy verdict",
            "",
            f"- 正式交付页默认纳入：`fresh-confirmed`（本轮共 {len(delivery_findings)} 条）",
            f"- truthful hold-out 保留：`fresh-blocked / fresh-manual-needed / fresh-skip-by-policy`（本轮共 {len(held_out_findings)} 条）",
            "- 本阶段只生成 canonical local bundle，不触发外部 publish。",
            "",
            "## included delivery findings",
            "",
        ]
    )
    if delivery_findings:
        for finding in delivery_findings:
            lines.append(f"- `{finding['finding_id']}` → `{finding['disposition']}`")
    else:
        lines.append("- none")
    lines.extend(
        [
            "",
            "## held-out findings",
            "",
        ]
    )
    if held_out_findings:
        for finding in held_out_findings:
            lines.append(f"- `{finding['finding_id']}` → `{finding['disposition']}`")
    else:
        lines.append("- none")
    lines.extend(
        [
            "",
            "## emitted local outputs",
            "",
            f"1. `{delivery_input_path}`",
            f"2. `{stage_md_path}`",
            f"3. `{stage_json_path}`",
            f"4. `{report_dir}`",
            "",
            "## next stage hint",
            "",
            "- `final-local-review` can now consume the canonical local bundle and manifest.",
            f"- frozen result class: `round-closed + repo-coverage-complete ({snapshot.get('fresh_confirmed_count', 0)} fresh-confirmed + {snapshot.get('fresh_blocked_count', 0)} fresh-blocked + {snapshot.get('fresh_manual_needed_count', 0)} fresh-manual-needed)`",
            "",
        ]
    )
    return "\n".join(lines).rstrip() + "\n"


def build_delivery_stage_verdict_json(bundle: dict[str, Any], result: dict[str, Any], delivery_input_path: Path, round_root: Path) -> dict[str, Any]:
    repo = bundle.get("repo") or {}
    return {
        "schema_version": 1,
        "stage": "delivery-reports",
        "status": "completed",
        "publish_status": "not-triggered",
        "source_kind": bundle.get("source_kind"),
        "repo": repo.get("slug"),
        "round_id": round_root.name,
        "round_root": str(round_root),
        "delivery_input_json": str(delivery_input_path),
        "report_dir": str(result["report_dir"]),
        "manifest_path": str(result["manifest_path"]),
        "coverage_snapshot": bundle.get("coverage_snapshot") or {},
        "inclusion_policy": bundle.get("inclusion_policy") or {},
        "delivery_findings": [finding["finding_id"] for finding in bundle.get("delivery_findings") or []],
        "held_out_findings": [
            {
                "finding_id": finding["finding_id"],
                "disposition": finding["disposition"],
                "hold_out_reason": finding.get("hold_out_reason") or finding.get("summary"),
            }
            for finding in bundle.get("held_out_findings") or []
        ],
        "outputs": {
            "delivery_input_json": str(delivery_input_path),
            "report_dir": str(result["report_dir"]),
            "manifest_path": str(result["manifest_path"]),
        },
        "next_stage": "final-local-review",
        "generated_at": now_iso(),
    }


def maybe_write_v4_stage_verdict(bundle: dict[str, Any], result: dict[str, Any], delivery_input_path: Path | None) -> None:
    if bundle.get("source_kind") != SOURCE_KIND_V4 or delivery_input_path is None:
        return
    round_root_raw = str((bundle.get("round") or {}).get("round_root") or "").strip()
    repo_slug = str((bundle.get("repo") or {}).get("slug") or "").strip()
    if not round_root_raw or not repo_slug:
        return
    round_root = Path(round_root_raw)
    objects_dir = round_root / "objects"
    md_path = objects_dir / f"stage-verdict.delivery-reports.{repo_slug}.{round_root.name}.md"
    json_path = objects_dir / f"stage-verdict.delivery-reports.{repo_slug}.{round_root.name}.json"
    write_text(md_path, render_delivery_stage_verdict_md(bundle, result, delivery_input_path, round_root))
    write_json(json_path, build_delivery_stage_verdict_json(bundle, result, delivery_input_path, round_root))


def resolve_bundle(ns: argparse.Namespace) -> tuple[dict[str, Any], Path | None]:
    if ns.delivery_input_json:
        input_path = Path(ns.delivery_input_json).expanduser().resolve()
        return read_json(input_path), input_path
    if ns.round_root:
        round_root = Path(ns.round_root).expanduser().resolve()
        bundle = normalize_v4_delivery_input(round_root)
        input_path = round_root / "artifacts" / f"delivery-report-input.{bundle['repo']['slug']}.{round_root.name}.json"
        write_json(input_path, bundle)
        return bundle, input_path
    summary_path = Path(ns.summary_json).expanduser().resolve() if ns.summary_json else find_summary_for_run(Path(ns.run_dir).expanduser().resolve())
    return normalize_legacy_delivery_input(summary_path), None


def default_out_dir(bundle: dict[str, Any]) -> Path:
    repo = bundle.get("repo") or {}
    return REPORTS / slugify(str(repo.get("slug") or "unknown"))


def main() -> int:
    ns = parse_args()
    bundle, delivery_input_path = resolve_bundle(ns)
    out_dir = Path(ns.out_dir).expanduser().resolve() if ns.out_dir else default_out_dir(bundle)
    result = build_reports(bundle, out_dir)
    result["delivery_input_json"] = str(delivery_input_path) if delivery_input_path else None
    maybe_write_v4_stage_verdict(bundle, result, delivery_input_path)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
