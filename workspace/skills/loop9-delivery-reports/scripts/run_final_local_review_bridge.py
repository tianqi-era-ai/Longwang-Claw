#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

WORKSPACE = Path("~/.openclaw/workspace").expanduser()
RUNS = WORKSPACE / "runs"
REPORTS = WORKSPACE / "reports"
MANIFEST_NAME = "98-delivery-bundle.manifest.json"
CANONICAL_REPORT_KIND = "loop9-standard-delivery-report"
DEFAULT_BRIDGE_WAIT_SECONDS = 20.0
DEFAULT_BRIDGE_POLL_INTERVAL_SECONDS = 0.5
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


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def missing_template_headings(path: Path, required_headings: list[str]) -> list[str]:
    text = path.read_text(encoding="utf-8", errors="replace")
    return [heading for heading in required_headings if heading not in text]


def expected_effective_poc_relpath(finding_id: str, source_poc_path: str | None) -> str | None:
    value = str(source_poc_path or "").strip()
    if not finding_id or not value:
        return None
    suffix = Path(value).suffix or ".txt"
    return f"poc/{finding_id}-effective{suffix}"


def find_summary_for_run(run_dir: Path) -> Path:
    exact = RUNS / f"repo-verify-{run_dir.name}" / "repo_verify_summary.json"
    if exact.exists():
        return exact
    for path in sorted(RUNS.glob("repo-verify-*/repo_verify_summary.json")):
        try:
            summary = load_json(path)
        except Exception:
            continue
        if Path(str(summary.get("run_dir") or "")).resolve() == run_dir.resolve():
            return path
    raise FileNotFoundError(f"No repo_verify_summary.json found for run dir: {run_dir}")


def make_dispatcher_return(*, kind: str, reason_code: str, summary: str, next_stage: str | None) -> dict[str, Any]:
    return {
        "ownership": "return-to-dispatcher",
        "stop_authority": "dispatcher-only",
        "return_kind": kind,
        "reason_code": reason_code,
        "summary": summary,
        "next_stage": next_stage,
    }


def _final_local_review_bridge_owner_signal(result: dict[str, Any]) -> dict[str, Any]:
    final_action = str(result.get("final_action") or "").strip()
    final_reason = str(result.get("final_reason") or "").strip()
    repo_boundary_state = str(result.get("repo_boundary_state") or "").strip()
    missing_items = list(result.get("missing_items") or [])
    upstream_barrier = result.get("upstream_barrier") or {}
    upstream_phase = str(upstream_barrier.get("phase") or "unknown").strip() or "unknown"
    if repo_boundary_state == "repo-mainline-done" or final_reason == "final-local-review-complete" or final_action == "repo-mainline-done":
        return {
            "routing": "final-local-review-complete",
            "boundary_state": "repo-mainline-done",
            "priority_hint": 360,
            "owner_election_basis": [
                "object-declared-owner-signal",
                "final-local-review-bridge-object",
                "review-status:done",
                "repo-mainline-complete",
                f"upstream-barrier:{upstream_phase}",
            ],
        }
    if repo_boundary_state == "final-local-review-blocked" or final_reason == "missing-local-report-artifacts" or final_action == "final-local-review-blocked":
        return {
            "routing": "final-local-review-blocked",
            "boundary_state": "final-local-review-blocked",
            "priority_hint": 355,
            "owner_election_basis": [
                "object-declared-owner-signal",
                "final-local-review-bridge-object",
                "review-status:blocked",
                f"missing-item-count:{len(missing_items)}",
                f"upstream-barrier:{upstream_phase}",
            ],
        }
    return {
        "routing": "final-local-review-pending",
        "boundary_state": "final-local-review-pending",
        "priority_hint": 350,
        "owner_election_basis": [
            "object-declared-owner-signal",
            "final-local-review-bridge-object",
            "review-status:pending",
            f"missing-item-count:{len(missing_items)}",
            f"upstream-barrier:{upstream_phase}",
        ],
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Thin final-local-review bridge for Loop9 local delivery reports")
    src = parser.add_mutually_exclusive_group(required=True)
    src.add_argument("--run-dir")
    src.add_argument("--summary-json")
    src.add_argument("--round-root")
    src.add_argument("--delivery-input-json")
    parser.add_argument("--report-dir")
    parser.add_argument("--mark-done", action="store_true", help="mark final local review as done if auto checks pass")
    parser.add_argument("--review-note", default="thin final local review completed")
    parser.add_argument("--wait-for-bridge-seconds", type=float, default=DEFAULT_BRIDGE_WAIT_SECONDS)
    parser.add_argument("--bridge-poll-interval-seconds", type=float, default=DEFAULT_BRIDGE_POLL_INTERVAL_SECONDS)
    parser.add_argument("--output-json")
    parser.add_argument("--json", action="store_true")
    return parser.parse_args()


def load_manifest(report_dir: Path) -> tuple[Path | None, dict[str, Any] | None]:
    manifest_path = report_dir / MANIFEST_NAME
    if not manifest_path.exists():
        return None, None
    manifest = load_json(manifest_path)
    if manifest.get("report_kind") != CANONICAL_REPORT_KIND:
        return manifest_path, None
    return manifest_path, manifest


def load_json_if_exists(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    try:
        obj = load_json(path)
    except Exception:
        return None
    return obj if isinstance(obj, dict) else None


def unique_preserve_order(items: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for item in items:
        value = str(item).strip()
        if not value or value in seen:
            continue
        seen.add(value)
        result.append(value)
    return result


def finding_id_set(rows: list[dict[str, Any]]) -> set[str]:
    return {
        str(item.get("finding_id") or "").strip()
        for item in rows
        if isinstance(item, dict) and str(item.get("finding_id") or "").strip()
    }


def candidate_delivery_bridge_paths(target_slug: str, round_root: Path | None, out_path: Path) -> list[Path]:
    candidates: list[Path] = []
    if round_root is not None:
        round_id = round_root.name
        candidates.extend(
            [
                round_root / "artifacts" / "delivery_report_bridge.json",
                round_root / "objects" / f"stage-verdict.delivery-reports.{target_slug}.{round_id}.json",
            ]
        )
    candidates.append(out_path.parent / "delivery_report_bridge.json")
    deduped: list[Path] = []
    seen: set[Path] = set()
    for path in candidates:
        if path not in seen:
            deduped.append(path)
            seen.add(path)
    return deduped


def load_delivery_bridge_result(target_slug: str, round_root: Path | None, out_path: Path) -> tuple[Path | None, dict[str, Any] | None]:
    for path in candidate_delivery_bridge_paths(target_slug, round_root, out_path):
        obj = load_json_if_exists(path)
        if obj is not None:
            return path, obj
    return None, None


def describe_delivery_bridge_state(
    *,
    report_dir: Path,
    bridge_path: Path | None,
    bridge_result: dict[str, Any] | None,
) -> dict[str, Any]:
    final_local_review_barrier = ((bridge_result or {}).get("final_local_review_barrier") or {}) if bridge_result else {}
    bridge_final_action = str((bridge_result or {}).get("final_action") or "").strip()
    bridge_final_reason = str((bridge_result or {}).get("final_reason") or "").strip()
    bridge_repo_boundary_state = str((bridge_result or {}).get("repo_boundary_state") or "").strip()
    manifest_path_raw = str(
        final_local_review_barrier.get("manifest_path")
        or ((bridge_result or {}).get("manifest_path") or "")
    ).strip()
    bridge_report_dir_raw = str(
        final_local_review_barrier.get("report_dir")
        or ((bridge_result or {}).get("report_dir") or "")
    ).strip()
    manifest_path = Path(manifest_path_raw).expanduser().resolve() if manifest_path_raw else None
    bridge_report_dir = Path(bridge_report_dir_raw).expanduser().resolve() if bridge_report_dir_raw else None
    manifest_exists = bool(manifest_path and manifest_path.exists())
    bridge_report_dir_exists = bool(bridge_report_dir and bridge_report_dir.exists())
    barrier_status = str(final_local_review_barrier.get("status") or "").strip()
    if bridge_final_action == "delivery-report-bridge-failed" or bridge_repo_boundary_state == "delivery-report-bridge-failed":
        phase = "failed"
    elif barrier_status == "ready" or (bridge_final_action == "final-local-review-pending" and manifest_exists):
        phase = "ready"
    elif bridge_result is None:
        phase = "missing"
    else:
        phase = "pending"
    return {
        "phase": phase,
        "bridge_path": str(bridge_path) if bridge_path else None,
        "bridge_exists": bridge_result is not None,
        "bridge_final_action": bridge_final_action or None,
        "bridge_final_reason": bridge_final_reason or None,
        "bridge_repo_boundary_state": bridge_repo_boundary_state or None,
        "barrier_status": barrier_status or None,
        "barrier_next_stage": final_local_review_barrier.get("next_stage"),
        "bridge_manifest_path": str(manifest_path) if manifest_path else None,
        "bridge_manifest_exists": manifest_exists,
        "bridge_report_dir": str(bridge_report_dir) if bridge_report_dir else None,
        "bridge_report_dir_exists": bridge_report_dir_exists,
        "report_dir": str(report_dir),
    }


def wait_for_delivery_bridge(
    *,
    target_slug: str,
    round_root: Path | None,
    report_dir: Path,
    out_path: Path,
    wait_seconds: float,
    poll_interval_seconds: float,
) -> dict[str, Any]:
    start = time.monotonic()
    deadline = start + max(wait_seconds, 0.0)
    poll_interval = max(poll_interval_seconds, 0.1)
    bridge_path, bridge_result = load_delivery_bridge_result(target_slug, round_root, out_path)
    state = describe_delivery_bridge_state(report_dir=report_dir, bridge_path=bridge_path, bridge_result=bridge_result)
    if (report_dir / MANIFEST_NAME).exists() or state["phase"] == "failed":
        state["waited_seconds"] = 0.0
        return state
    while time.monotonic() < deadline:
        time.sleep(min(poll_interval, max(deadline - time.monotonic(), 0.0)))
        bridge_path, bridge_result = load_delivery_bridge_result(target_slug, round_root, out_path)
        state = describe_delivery_bridge_state(report_dir=report_dir, bridge_path=bridge_path, bridge_result=bridge_result)
        if (report_dir / MANIFEST_NAME).exists() or state["phase"] == "failed":
            break
    state["waited_seconds"] = round(max(time.monotonic() - start, 0.0), 3)
    return state


def resolve_context(ns: argparse.Namespace) -> tuple[str, Path | None, Path, Path]:
    summary_path: Path | None = None
    target_slug: str
    round_root: Path | None = None

    if ns.round_root:
        round_root = Path(ns.round_root).expanduser().resolve()
        target_slug = round_root.parent.name
        default_report_dir = REPORTS / target_slug
        out_path = Path(ns.output_json).expanduser().resolve() if ns.output_json else round_root / "artifacts" / "final_local_review_bridge.json"
    elif ns.delivery_input_json:
        bundle = load_json(Path(ns.delivery_input_json).expanduser().resolve())
        target_slug = str(((bundle.get("repo") or {}).get("slug")) or "unknown")
        round_root_raw = str(((bundle.get("round") or {}).get("round_root")) or "").strip()
        round_root = Path(round_root_raw).resolve() if round_root_raw else None
        default_report_dir = REPORTS / target_slug
        input_path = Path(ns.delivery_input_json).expanduser().resolve()
        out_path = Path(ns.output_json).expanduser().resolve() if ns.output_json else input_path.parent / "final_local_review_bridge.json"
    else:
        summary_path = Path(ns.summary_json).expanduser().resolve() if ns.summary_json else find_summary_for_run(Path(ns.run_dir).expanduser().resolve())
        summary = load_json(summary_path)
        target_slug = str(summary.get("target_slug") or "unknown")
        default_report_dir = REPORTS / target_slug
        out_path = Path(ns.output_json).expanduser().resolve() if ns.output_json else summary_path.parent / "final_local_review_bridge.json"

    report_dir = Path(ns.report_dir).expanduser().resolve() if ns.report_dir else default_report_dir
    return target_slug, round_root, report_dir, out_path


def render_stage_verdict_md(result: dict[str, Any], repo_slug: str, round_id: str) -> str:
    return "\n".join(
        [
            f"# stage-verdict.final-local-review — {repo_slug} / {round_id}",
            "",
            "## stage identity",
            "",
            "- stage: `final-local-review`",
            f"- repo: `{repo_slug}`",
            f"- round_id: `{round_id}`",
            "",
            "## result",
            "",
            f"- final_action: `{result.get('final_action')}`",
            f"- final_reason: `{result.get('final_reason')}`",
            f"- repo_boundary_state: `{result.get('repo_boundary_state')}`",
            f"- publish_ready: `{result.get('publish_ready')}`",
            f"- manifest_path: `{result.get('manifest_path')}`",
            f"- upstream_barrier_phase: `{((result.get('upstream_barrier') or {}).get('phase'))}`",
            "",
            "## review outcome",
            "",
            f"- delivery_findings: `{', '.join(result.get('delivery_findings') or []) or 'none'}`",
            f"- held_out_findings: `{', '.join(result.get('held_out_findings') or []) or 'none'}`",
            f"- missing_items: `{', '.join(result.get('missing_items') or []) or 'none'}`",
            "",
        ]
    ).rstrip() + "\n"


def main() -> int:
    ns = parse_args()
    target_slug, round_root, report_dir, out_path = resolve_context(ns)
    upstream_barrier = wait_for_delivery_bridge(
        target_slug=target_slug,
        round_root=round_root,
        report_dir=report_dir,
        out_path=out_path,
        wait_seconds=ns.wait_for_bridge_seconds,
        poll_interval_seconds=ns.bridge_poll_interval_seconds,
    )
    manifest_path, manifest = load_manifest(report_dir)

    required_root = unique_preserve_order(
        list((manifest or {}).get("root_docs") or [])
        or [
            "00-索引.md",
            "01-仓库级中文交付报告.md",
            "02-仓库级技术汇总.md",
            "02-仓库级技术汇总.json",
            MANIFEST_NAME,
        ]
    )
    missing_items: list[str] = []
    present_items: list[str] = []
    auto_checks: list[dict[str, Any]] = []

    for rel in required_root:
        ok = (report_dir / rel).exists()
        auto_checks.append({"kind": "root-doc", "path": rel, "ok": ok})
        if ok:
            present_items.append(rel)
        else:
            missing_items.append(rel)

    technical_summary = load_json_if_exists(report_dir / "02-仓库级技术汇总.json") or {}
    technical_summary_findings = {
        str(item.get("finding_id") or "").strip(): item
        for item in technical_summary.get("delivery_findings") or []
        if isinstance(item, dict) and str(item.get("finding_id") or "").strip()
    }
    technical_delivery_findings: list[dict[str, Any]] = list(technical_summary.get("delivery_findings") or [])
    technical_held_out_findings: list[dict[str, Any]] = list(technical_summary.get("held_out_findings") or [])
    delivery_findings: list[dict[str, Any]] = list((manifest or {}).get("delivery_findings") or [])
    held_out_findings: list[dict[str, Any]] = list((manifest or {}).get("held_out_findings") or [])
    manifest_snapshot = dict((manifest or {}).get("coverage_snapshot") or {})
    manifest_truth_audit = dict((manifest or {}).get("truth_audit") or {})
    required_findings_headings = list(
        (((manifest or {}).get("delivery_template") or {}).get("required_headings"))
        or DEFAULT_FINDING_TEMPLATE_HEADINGS
    )
    if manifest is None:
        auto_checks.append({"kind": "manifest", "path": MANIFEST_NAME, "ok": False})
        missing_items.append("canonical-manifest")

    manifest_delivery_ids = finding_id_set(delivery_findings)
    manifest_held_out_ids = finding_id_set(held_out_findings)
    technical_delivery_ids = finding_id_set(technical_delivery_findings)
    technical_held_out_ids = finding_id_set(technical_held_out_findings)

    delivery_id_sets_match = manifest_delivery_ids == technical_delivery_ids
    auto_checks.append(
        {
            "kind": "delivery-finding-set",
            "path": "manifest <-> 02-仓库级技术汇总.json",
            "ok": delivery_id_sets_match,
            "manifest_only": sorted(manifest_delivery_ids - technical_delivery_ids),
            "technical_summary_only": sorted(technical_delivery_ids - manifest_delivery_ids),
        }
    )
    if not delivery_id_sets_match:
        missing_items.append(
            "delivery_finding_set_mismatch "
            f"(manifest_only={sorted(manifest_delivery_ids - technical_delivery_ids)}, "
            f"technical_summary_only={sorted(technical_delivery_ids - manifest_delivery_ids)})"
        )

    held_out_id_sets_match = manifest_held_out_ids == technical_held_out_ids
    auto_checks.append(
        {
            "kind": "held-out-finding-set",
            "path": "manifest <-> 02-仓库级技术汇总.json",
            "ok": held_out_id_sets_match,
            "manifest_only": sorted(manifest_held_out_ids - technical_held_out_ids),
            "technical_summary_only": sorted(technical_held_out_ids - manifest_held_out_ids),
        }
    )
    if not held_out_id_sets_match:
        missing_items.append(
            "held_out_finding_set_mismatch "
            f"(manifest_only={sorted(manifest_held_out_ids - technical_held_out_ids)}, "
            f"technical_summary_only={sorted(technical_held_out_ids - manifest_held_out_ids)})"
        )

    expected_counts = {
        "delivery_findings_count": len(delivery_findings),
        "held_out_findings_count": len(held_out_findings),
        "terminal_disposition_count": len(delivery_findings) + len(held_out_findings),
    }
    for field, expected in expected_counts.items():
        actual = manifest_snapshot.get(field)
        ok = actual == expected
        auto_checks.append(
            {
                "kind": "coverage-snapshot",
                "path": field,
                "ok": ok,
                "expected": expected,
                "actual": actual,
            }
        )
        if not ok:
            missing_items.append(f"coverage_snapshot.{field} mismatch (expected {expected}, got {actual})")

    if "fresh_confirmed_count" in manifest_snapshot:
        expected_fresh_confirmed = len(delivery_findings)
        actual_fresh_confirmed = manifest_snapshot.get("fresh_confirmed_count")
        ok = actual_fresh_confirmed == expected_fresh_confirmed
        auto_checks.append(
            {
                "kind": "coverage-snapshot",
                "path": "fresh_confirmed_count",
                "ok": ok,
                "expected": expected_fresh_confirmed,
                "actual": actual_fresh_confirmed,
            }
        )
        if not ok:
            missing_items.append(
                f"coverage_snapshot.fresh_confirmed_count mismatch (expected {expected_fresh_confirmed}, got {actual_fresh_confirmed})"
            )

    if "fresh_blocked_count" in manifest_snapshot:
        expected_fresh_blocked = sum(
            1 for item in held_out_findings if str(item.get("disposition") or "").strip() == "fresh-blocked"
        )
        actual_fresh_blocked = manifest_snapshot.get("fresh_blocked_count")
        ok = actual_fresh_blocked == expected_fresh_blocked
        auto_checks.append(
            {
                "kind": "coverage-snapshot",
                "path": "fresh_blocked_count",
                "ok": ok,
                "expected": expected_fresh_blocked,
                "actual": actual_fresh_blocked,
            }
        )
        if not ok:
            missing_items.append(
                f"coverage_snapshot.fresh_blocked_count mismatch (expected {expected_fresh_blocked}, got {actual_fresh_blocked})"
            )

    coverage_truth_audit = dict(manifest_truth_audit.get("coverage_snapshot") or {})
    coverage_truth_mismatches = list(coverage_truth_audit.get("mismatches") or [])
    auto_checks.append(
        {
            "kind": "upstream-coverage-truth-audit",
            "path": "truth_audit.coverage_snapshot",
            "ok": not coverage_truth_mismatches,
            "mismatch_count": len(coverage_truth_mismatches),
        }
    )

    for finding in delivery_findings:
        finding_id = str(finding.get("finding_id") or "").strip()
        report_doc = str(finding.get("report_doc") or f"{finding_id}.md")
        doc_ok = (report_dir / report_doc).exists()
        auto_checks.append({"kind": "finding-doc", "path": report_doc, "finding_id": finding_id, "ok": doc_ok})
        if doc_ok:
            present_items.append(report_doc)
            template_missing = missing_template_headings(report_dir / report_doc, required_findings_headings)
            template_ok = not template_missing
            auto_checks.append(
                {
                    "kind": "finding-template",
                    "path": report_doc,
                    "finding_id": finding_id,
                    "ok": template_ok,
                    "missing_headings": template_missing,
                }
            )
            if not template_ok:
                missing_items.append(f"{report_doc} (missing template headings: {', '.join(template_missing)})")
        else:
            missing_items.append(report_doc)

        poc_files = [str(item).strip() for item in finding.get("poc_files") or [] if str(item).strip()]
        for poc_file in poc_files:
            poc_rel = f"poc/{poc_file}"
            poc_ok = (report_dir / poc_rel).exists()
            auto_checks.append({"kind": "effective-poc", "path": poc_rel, "finding_id": finding_id, "ok": poc_ok})
            if poc_ok:
                present_items.append(poc_rel)
            else:
                missing_items.append(poc_rel)
        if not poc_files:
            summary_finding = technical_summary_findings.get(finding_id) or {}
            expected_poc_rel = expected_effective_poc_relpath(finding_id, summary_finding.get("poc_path"))
            if expected_poc_rel:
                poc_ok = (report_dir / expected_poc_rel).exists()
                auto_checks.append(
                    {
                        "kind": "effective-poc-derived",
                        "path": expected_poc_rel,
                        "finding_id": finding_id,
                        "ok": poc_ok,
                        "source": "02-仓库级技术汇总.json:poc_path",
                    }
                )
                auto_checks.append(
                    {
                        "kind": "manifest-poc-binding",
                        "path": expected_poc_rel,
                        "finding_id": finding_id,
                        "ok": False,
                        "source": "02-仓库级技术汇总.json:poc_path",
                    }
                )
                if poc_ok:
                    present_items.append(expected_poc_rel)
                    missing_items.append(f"{expected_poc_rel} (missing manifest poc binding)")
                else:
                    missing_items.append(f"{expected_poc_rel} (missing manifest poc binding and effective poc file)")

        http_rel = str(finding.get("http_dir") or "").strip()
        if http_rel:
            http_dir = report_dir / http_rel
            req_count = len(sorted(http_dir.glob("request-*.txt"))) if http_dir.exists() else 0
            resp_count = len(sorted(http_dir.glob("response-*.txt"))) if http_dir.exists() else 0
            http_ok = http_dir.exists() and req_count > 0 and resp_count > 0
            auto_checks.append(
                {
                    "kind": "http-evidence",
                    "path": http_rel,
                    "finding_id": finding_id,
                    "ok": http_ok,
                    "request_count": req_count,
                    "response_count": resp_count,
                }
            )
            if http_ok:
                present_items.append(http_rel)
            else:
                missing_items.append(f"{http_rel} (need both request and response)")

    review_record_json = report_dir / "99-最终本地复盘.json"
    review_record_md = report_dir / "99-最终本地复盘.md"
    previous_review_record = load_json_if_exists(review_record_json) or {}

    result: dict[str, Any] = {
        "target_slug": target_slug,
        "round_root": str(round_root) if round_root else None,
        "report_dir": str(report_dir),
        "manifest_path": str(manifest_path) if manifest_path else None,
        "delivery_findings": [str(item.get("finding_id") or "") for item in delivery_findings],
        "held_out_findings": [str(item.get("finding_id") or "") for item in held_out_findings],
        "auto_checks": auto_checks,
        "missing_items": missing_items,
        "present_items": present_items,
        "truth_audit": manifest_truth_audit,
        "review_checklist": [
            "检查 repo 中文交付报告是否只默认纳入正式交付项，并保留 hold-out 说明",
            "确认 per-finding docs / poc / http 只覆盖正式交付项，且不把 blocked/manual 项硬升级成正式交付页",
            "确认每份正式单漏洞文档都具备原始模板家族要求的章节结构，而不是薄版占位文档",
            "确认 manifest、00-索引、99-最终本地复盘三类 marker 一致",
            "确认 coverage_snapshot、manifest finding 集合、02-仓库级技术汇总.json 三者彼此自洽",
            "确认本地交付包已就绪，但尚未触发 Feishu/wiki 发布",
        ],
        "review_note": ns.review_note,
        "review_record_json": str(review_record_json),
        "review_record_md": str(review_record_md),
        "upstream_barrier": upstream_barrier,
        "final_action": None,
        "final_reason": None,
        "repo_boundary_state": None,
        "dispatcher_should_reenter": False,
        "next_repo_stage": None,
        "terminal_kind": None,
        "dispatcher_return": None,
        "publish_ready": False,
        "stage_verdict_json": None,
        "stage_verdict_md": None,
    }
    previous_publish_closure = previous_review_record.get("publish_closure")
    if isinstance(previous_publish_closure, dict):
        result["publish_closure"] = previous_publish_closure
    has_delivery_findings = bool(delivery_findings)
    upstream_phase = str(upstream_barrier.get("phase") or "").strip()
    waiting_on_bridge = manifest is None and upstream_phase in {"missing", "pending"}
    blocked_by_bridge_failure = manifest is None and upstream_phase == "failed"

    if waiting_on_bridge:
        result["final_action"] = "final-local-review-pending"
        result["final_reason"] = "waiting-delivery-report-bridge"
        result["repo_boundary_state"] = "final-local-review-pending"
        result["next_repo_stage"] = "delivery-report-bridge"
        result["terminal_kind"] = "wait-delivery-bridge"
        result["dispatcher_return"] = make_dispatcher_return(
            kind="handoff",
            reason_code="WAITING_DELIVERY_REPORT_BRIDGE",
            summary="final local review is waiting for delivery-report-bridge to finish materializing the canonical local bundle",
            next_stage="delivery-report-bridge",
        )
    elif blocked_by_bridge_failure:
        result["final_action"] = "final-local-review-blocked"
        result["final_reason"] = "delivery-report-bridge-failed"
        result["repo_boundary_state"] = "final-local-review-blocked"
        result["next_repo_stage"] = "delivery-report-bridge"
        result["terminal_kind"] = "blocked-upstream-failure"
        result["dispatcher_return"] = make_dispatcher_return(
            kind="blocker",
            reason_code="DELIVERY_REPORT_BRIDGE_FAILED",
            summary="final local review is blocked because delivery-report-bridge failed upstream",
            next_stage="delivery-report-bridge",
        )
    elif missing_items:
        result["final_action"] = "final-local-review-blocked"
        result["final_reason"] = "missing-local-report-artifacts"
        result["repo_boundary_state"] = "final-local-review-blocked"
        result["next_repo_stage"] = "local-report-generation"
        result["terminal_kind"] = "blocked-missing-artifacts"
        result["dispatcher_return"] = make_dispatcher_return(
            kind="blocker",
            reason_code="MISSING_LOCAL_REPORT_ARTIFACTS",
            summary="final local review is blocked by missing report artifacts",
            next_stage="local-report-generation",
        )
    elif ns.mark_done:
        result["final_action"] = "repo-mainline-done"
        result["final_reason"] = (
            "final-local-review-complete" if has_delivery_findings else "final-local-review-complete-no-delivery-findings"
        )
        result["repo_boundary_state"] = "repo-mainline-done"
        result["next_repo_stage"] = None
        result["terminal_kind"] = "done"
        result["publish_ready"] = has_delivery_findings
        result["dispatcher_return"] = make_dispatcher_return(
            kind="hard-stop",
            reason_code="REPO_MAINLINE_DONE",
            summary="final local review completed and repo mainline is done",
            next_stage=None,
        )
    else:
        result["final_action"] = "final-local-review-pending"
        result["final_reason"] = "ready-for-review-checklist"
        result["repo_boundary_state"] = "final-local-review-pending"
        result["next_repo_stage"] = "final-local-review"
        result["terminal_kind"] = "wait-final-review"
        result["dispatcher_return"] = make_dispatcher_return(
            kind="handoff",
            reason_code="READY_FOR_REVIEW_CHECKLIST",
            summary="final local review remains pending and control returns to dispatcher/review checklist stage",
            next_stage="final-local-review",
        )

    if manifest_path and manifest:
        manifest["final_local_review"] = {
            "status": (
                "complete"
                if (ns.mark_done and not missing_items)
                else ("blocked" if result["final_action"] == "final-local-review-blocked" else "pending")
            ),
            "publish_can_be_considered": result["publish_ready"],
            "review_record_md": str(review_record_md),
            "review_record_json": str(review_record_json),
            "completed_at": now_iso() if (ns.mark_done and not missing_items) else None,
            "missing_items": missing_items,
            "review_note": ns.review_note,
            "delivery_findings": result["delivery_findings"],
            "held_out_findings": result["held_out_findings"],
        }
        manifest["publish_ready"] = result["publish_ready"]
        write_json(manifest_path, manifest)

    review_md_lines = [
        f"# {target_slug} 最终本地复盘",
        "",
        f"- review_time: {now_iso()}",
        f"- final_action: {result['final_action']}",
        f"- final_reason: {result['final_reason']}",
        f"- report_dir: {report_dir}",
        f"- manifest_path: {manifest_path or 'missing'}",
        f"- upstream_barrier_phase: {upstream_barrier.get('phase') or 'unknown'}",
        f"- publish_can_be_considered: {str(result['publish_ready']).lower()}",
        "",
        "## 正式交付项",
        *(f"- {finding.get('finding_id')}｜{finding.get('title')}" for finding in delivery_findings),
        *([] if delivery_findings else ["- none｜当前 round 没有满足默认正式交付条件的 fresh-confirmed finding"]),
        "",
        "## Hold-out 项",
        *(f"- {finding.get('finding_id')}｜{finding.get('disposition')}｜{finding.get('hold_out_reason') or finding.get('summary')}" for finding in held_out_findings),
        "",
        "## 检查清单",
        *(f"- {item}" for item in result["review_checklist"]),
        "",
        "## 自动检查结果",
        *[
            f"- [{'OK' if row.get('ok') else 'MISS'}] {row.get('kind')}: {row.get('path')}"
            for row in auto_checks
        ],
        "",
    ]
    if coverage_truth_mismatches:
        review_md_lines.extend(
            [
                "## 上游真相漂移记录",
                *(
                    f"- {row.get('source')}::{row.get('field')} declared={row.get('declared')} derived={row.get('derived')}"
                    for row in coverage_truth_mismatches
                ),
                "",
            ]
        )
    review_md_lines.extend(
        [
        "## 复盘备注",
        f"- {ns.review_note}",
        "",
        ]
    )
    publish_closure = result.get("publish_closure")
    if isinstance(publish_closure, dict) and publish_closure:
        review_md_lines.extend(
            [
                "## 发布收口结果",
                f"- publish_time: {publish_closure.get('publish_time') or 'unknown'}",
                f"- feishu_delivery_container: {publish_closure.get('feishu_delivery_container') or 'unknown'}",
                f"- feishu_repro_doc: {publish_closure.get('feishu_repro_doc') or 'unknown'}",
                f"- publish_synced_docs_total: {publish_closure.get('publish_synced_docs_total') or 0}",
                f"- publish_created_docs: {'、'.join(f'`{item}`' for item in (publish_closure.get('publish_created_docs') or [])) or 'none'}",
                f"- publish_updated_docs: {'、'.join(f'`{item}`' for item in (publish_closure.get('publish_updated_docs') or [])) or 'none'}",
                (
                    "- post_publish_self_check: "
                    f"`issues={publish_closure.get('post_publish_self_check', {}).get('issues', [])}`、"
                    f"`needs_sync={publish_closure.get('post_publish_self_check', {}).get('needs_sync')}`、"
                    f"`missing_docs={publish_closure.get('post_publish_self_check', {}).get('missing_docs', [])}`、"
                    f"`changed_docs={publish_closure.get('post_publish_self_check', {}).get('changed_docs', [])}`、"
                    f"`invalid_bindings={publish_closure.get('post_publish_self_check', {}).get('invalid_bindings', [])}`"
                ),
                "",
            ]
        )
    result["owner_signal"] = _final_local_review_bridge_owner_signal(result)
    if round_root is not None:
        repo_slug = round_root.parent.name
        round_id = round_root.name
        stage_verdict_json = round_root / "objects" / f"stage-verdict.final-local-review.{repo_slug}.{round_id}.json"
        stage_verdict_md = round_root / "objects" / f"stage-verdict.final-local-review.{repo_slug}.{round_id}.md"
        result["stage_verdict_json"] = str(stage_verdict_json)
        result["stage_verdict_md"] = str(stage_verdict_md)
        write_json(stage_verdict_json, result)
        write_text(stage_verdict_md, render_stage_verdict_md(result, repo_slug, round_id))
    write_json(review_record_json, result)
    write_text(review_record_md, "\n".join(review_md_lines).rstrip() + "\n")

    write_json(out_path, result)
    if ns.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(f"review={out_path}")
        print(f"final_action={result['final_action']}")
        print(f"final_reason={result['final_reason']}")
        print(f"repo_boundary_state={result['repo_boundary_state']}")
        print(f"terminal_kind={result['terminal_kind']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
