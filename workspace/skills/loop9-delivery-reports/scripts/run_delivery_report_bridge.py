#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path
from typing import Any

WORKSPACE = Path("~/.openclaw/workspace").expanduser()
RUNS = WORKSPACE / "runs"
BUILD = WORKSPACE / "skills" / "loop9-delivery-reports" / "scripts" / "build_repo_delivery_reports.py"


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def run_cmd(cmd: list[str]) -> dict[str, Any]:
    proc = subprocess.run(cmd, capture_output=True, text=True, cwd=str(WORKSPACE), check=False)
    return {"cmd": cmd, "returncode": proc.returncode, "stdout": proc.stdout, "stderr": proc.stderr}


def parse_json_stdout(run: dict[str, Any]) -> dict[str, Any] | None:
    text = str(run.get("stdout") or "").strip()
    if not text:
        return None
    try:
        obj = json.loads(text)
        return obj if isinstance(obj, dict) else None
    except Exception:
        return None


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


def _delivery_report_bridge_owner_signal(result: dict[str, Any]) -> dict[str, Any]:
    report_dir = str(result.get("report_dir") or "").strip()
    ready = bool(report_dir)
    barrier = result.get("final_local_review_barrier") or {}
    barrier_status = str(barrier.get("status") or "unknown").strip() or "unknown"
    return {
        "routing": "delivery-report-bridge-ready",
        "boundary_state": "final-local-review-pending",
        "priority_hint": 340,
        "owner_election_basis": [
            "object-declared-owner-signal",
            "delivery-report-bridge-object",
            "next-stage:final-local-review",
            f"report-dir-ready:{str(ready).lower()}",
            f"manifest-ready:{str(bool(result.get('manifest_path'))).lower()}",
            f"final-local-review-barrier:{barrier_status}",
        ],
    }


def _final_local_review_barrier(result: dict[str, Any]) -> dict[str, Any]:
    report_dir_raw = str(result.get("report_dir") or "").strip()
    manifest_path_raw = str(result.get("manifest_path") or "").strip()
    report_dir = Path(report_dir_raw).expanduser() if report_dir_raw else None
    manifest_path = Path(manifest_path_raw).expanduser() if manifest_path_raw else None
    report_dir_exists = bool(report_dir and report_dir.exists())
    manifest_exists = bool(manifest_path and manifest_path.exists())
    final_action = str(result.get("final_action") or "").strip()
    if final_action == "delivery-report-bridge-failed":
        status = "failed"
    elif manifest_exists and report_dir_exists:
        status = "ready"
    else:
        status = "pending"
    return {
        "consumer": "final-local-review",
        "status": status,
        "report_dir": report_dir_raw or None,
        "report_dir_exists": report_dir_exists,
        "manifest_path": manifest_path_raw or None,
        "manifest_exists": manifest_exists,
        "next_stage": "final-local-review",
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Thin bridge from repo closure to local delivery reports")
    src = parser.add_mutually_exclusive_group(required=True)
    src.add_argument("--run-dir")
    src.add_argument("--summary-json")
    src.add_argument("--round-root")
    src.add_argument("--delivery-input-json")
    parser.add_argument("--output-json")
    parser.add_argument("--json", action="store_true")
    return parser.parse_args()


def round_context_from_root(round_root: Path) -> dict[str, Any]:
    return {
        "repo_slug": round_root.parent.name,
        "round_id": round_root.name,
        "round_root": str(round_root),
        "objects_dir": round_root / "objects",
        "artifacts_dir": round_root / "artifacts",
    }


def find_round_object(objects_dir: Path, prefix: str) -> Path | None:
    matches = sorted(objects_dir.glob(f"{prefix}*.md"))
    return matches[0] if matches else None


def build_delivery_handoff(round_root: Path) -> Path:
    ctx = round_context_from_root(round_root)
    objects_dir = Path(ctx["objects_dir"])
    handoff_path = objects_dir / f"stage-handoff.delivery-reports.{ctx['repo_slug']}.{ctx['round_id']}.md"
    board = find_round_object(objects_dir, "repo-findings-board")
    closure = find_round_object(objects_dir, "repo-closure-review")
    verdict = find_round_object(objects_dir, "repo-round-verdict")
    delivery_input = round_root / "artifacts" / f"delivery-report-input.{ctx['repo_slug']}.{ctx['round_id']}.json"
    text = "\n".join(
        [
            f"# stage-handoff.delivery-reports — {ctx['repo_slug']} / {ctx['round_id']}",
            "",
            "## stage identity",
            "",
            "- stage: `delivery-reports`",
            f"- repo: `{ctx['repo_slug']}`",
            f"- current_round_root: `{round_root}`",
            "- parent_owner: `loop9-verify-v4`",
            "",
            "## bounded question",
            "",
            "> 在 repo queue 已 fully terminal、closure truth 已冻结的前提下，能否把 current-round truth 薄编译成 canonical local delivery bundle，并保持“默认只纳入 fresh-confirmed、hold-out 仍被 truthful 保留”的口径？",
            "",
            "## hot refs",
            "",
            *(f"{idx}. `{path}`" for idx, path in enumerate([board, closure, verdict], start=1) if path),
            "",
            "## required outputs",
            "",
            f"1. `{delivery_input}`",
            f"2. `{objects_dir / ('stage-verdict.delivery-reports.' + ctx['repo_slug'] + '.' + ctx['round_id'] + '.md')}`",
            f"3. `{objects_dir / ('stage-verdict.delivery-reports.' + ctx['repo_slug'] + '.' + ctx['round_id'] + '.json')}`",
            f"4. `reports/{ctx['repo_slug']}/` canonical local bundle + manifest",
            "",
            "## hard boundary",
            "",
            "- 这一步只负责 local delivery bundle，不触发 publish。",
            "- 正式交付页默认只纳入 `fresh-confirmed`；`fresh-blocked / fresh-manual-needed / fresh-skip-by-policy` 只能进入 hold-out / repo-level 说明层。",
            "",
        ]
    ).rstrip() + "\n"
    write_text(handoff_path, text)
    return handoff_path


def render_stage_verdict_md(result: dict[str, Any], repo_slug: str, round_id: str) -> str:
    return "\n".join(
        [
            f"# stage-verdict.delivery-reports — {repo_slug} / {round_id}",
            "",
            "## stage identity",
            "",
            "- stage: `delivery-reports`",
            f"- repo: `{repo_slug}`",
            f"- round_id: `{round_id}`",
            "- child_owner: `loop9-delivery-reports`",
            "",
            "## result",
            "",
            f"- final_action: `{result.get('final_action')}`",
            f"- final_reason: `{result.get('final_reason')}`",
            f"- repo_boundary_state: `{result.get('repo_boundary_state')}`",
            f"- next_repo_stage: `{result.get('next_repo_stage')}`",
            f"- report_dir: `{result.get('report_dir')}`",
            f"- manifest_path: `{result.get('manifest_path')}`",
            "",
            "## delivery outcome",
            "",
            f"- delivery_findings: `{', '.join(result.get('delivery_findings') or []) or 'none'}`",
            f"- held_out_findings: `{', '.join(result.get('held_out_findings') or []) or 'none'}`",
            "",
        ]
    ).rstrip() + "\n"


def main() -> int:
    ns = parse_args()

    summary_path: Path | None = None
    round_root: Path | None = None
    delivery_input_json: Path | None = None
    target_slug = "unknown"

    if ns.round_root:
        round_root = Path(ns.round_root).expanduser().resolve()
        ctx = round_context_from_root(round_root)
        target_slug = str(ctx["repo_slug"])
        out_path = Path(ns.output_json).expanduser().resolve() if ns.output_json else round_root / "artifacts" / "delivery_report_bridge.json"
        handoff_path = build_delivery_handoff(round_root)
        build_run = run_cmd(["python3", str(BUILD), "--round-root", str(round_root)])
    elif ns.delivery_input_json:
        delivery_input_json = Path(ns.delivery_input_json).expanduser().resolve()
        bundle = load_json(delivery_input_json)
        target_slug = str(((bundle.get("repo") or {}).get("slug")) or "unknown")
        round_root_raw = str(((bundle.get("round") or {}).get("round_root")) or "").strip()
        round_root = Path(round_root_raw).resolve() if round_root_raw else None
        out_path = Path(ns.output_json).expanduser().resolve() if ns.output_json else delivery_input_json.parent / "delivery_report_bridge.json"
        handoff_path = build_delivery_handoff(round_root) if round_root else None
        build_run = run_cmd(["python3", str(BUILD), "--delivery-input-json", str(delivery_input_json)])
    else:
        summary_path = Path(ns.summary_json).expanduser().resolve() if ns.summary_json else find_summary_for_run(Path(ns.run_dir).expanduser().resolve())
        summary = load_json(summary_path)
        target_slug = str(summary.get("target_slug") or "unknown")
        out_path = Path(ns.output_json).expanduser().resolve() if ns.output_json else summary_path.parent / "delivery_report_bridge.json"
        handoff_path = None

        if summary.get("next_action") != "deliver-now":
            result: dict[str, Any] = {
                "summary_json": str(summary_path),
                "run_dir": summary.get("run_dir"),
                "target_slug": target_slug,
                "summary_next_action": summary.get("next_action"),
                "executed": [],
                "final_action": "report-bridge-skipped",
                "final_reason": f"summary.next_action={summary.get('next_action')}",
                "repo_boundary_state": "not-deliver-now",
                "dispatcher_should_reenter": False,
                "next_repo_stage": None,
                "terminal_kind": "skip",
                "dispatcher_return": make_dispatcher_return(
                    kind="handoff",
                    reason_code=f"summary.next_action={summary.get('next_action')}",
                    summary="delivery-report bridge skipped because summary.next_action is not deliver-now",
                    next_stage=None,
                ),
                "stage_handoff": None,
                "delivery_input_json": None,
                "manifest_path": None,
            }
            write_json(out_path, result)
            if ns.json:
                print(json.dumps(result, ensure_ascii=False, indent=2))
            else:
                print(f"bridge={out_path}")
                print(f"final_action={result['final_action']}")
                print(f"final_reason={result['final_reason']}")
                print(f"repo_boundary_state={result['repo_boundary_state']}")
                print(f"next_repo_stage={result['next_repo_stage']}")
            return 0

        build_run = run_cmd(["python3", str(BUILD), "--summary-json", str(summary_path)])

    build_result = parse_json_stdout(build_run) or {}
    result = {
        "summary_json": str(summary_path) if summary_path else None,
        "run_dir": None,
        "round_root": str(round_root) if round_root else None,
        "target_slug": target_slug,
        "summary_next_action": None,
        "executed": [{"kind": "build-local-delivery-reports", "run": build_run, "result": build_result}],
        "final_action": None,
        "final_reason": None,
        "repo_boundary_state": None,
        "dispatcher_should_reenter": False,
        "next_repo_stage": None,
        "terminal_kind": None,
        "dispatcher_return": None,
        "report_dir": build_result.get("report_dir"),
        "manifest_path": build_result.get("manifest_path"),
        "delivery_input_json": build_result.get("delivery_input_json") or (str(delivery_input_json) if delivery_input_json else None),
        "delivery_findings": build_result.get("delivery_findings") or [],
        "held_out_findings": build_result.get("held_out_findings") or [],
        "coverage_snapshot": build_result.get("coverage_snapshot") or {},
        "stage_handoff": str(handoff_path) if handoff_path else None,
        "stage_verdict_json": None,
        "stage_verdict_md": None,
    }

    if build_run.get("returncode") != 0:
        result["final_action"] = "delivery-report-bridge-failed"
        result["final_reason"] = "build-local-delivery-reports-failed"
        result["repo_boundary_state"] = "delivery-report-bridge-failed"
        result["next_repo_stage"] = None
        result["terminal_kind"] = "failed"
        result["dispatcher_return"] = make_dispatcher_return(
            kind="blocker",
            reason_code="LOCAL_DELIVERY_REPORT_BUILD_FAILED",
            summary="local delivery report generation failed and needs inspection",
            next_stage=None,
        )
    else:
        result["final_action"] = "final-local-review-pending"
        result["final_reason"] = "local-delivery-reports-generated"
        result["repo_boundary_state"] = "final-local-review-pending"
        result["next_repo_stage"] = "final-local-review"
        result["terminal_kind"] = "wait-final-review"
        result["dispatcher_return"] = make_dispatcher_return(
            kind="handoff",
            reason_code="LOCAL_DELIVERY_REPORTS_GENERATED",
            summary="local delivery reports generated and control returns to dispatcher/final-local-review stage",
            next_stage="final-local-review",
        )

    result["final_local_review_barrier"] = _final_local_review_barrier(result)
    if result["final_action"] == "final-local-review-pending":
        result["owner_signal"] = _delivery_report_bridge_owner_signal(result)

    if round_root is not None:
        ctx = round_context_from_root(round_root)
        stage_verdict_json_path = round_root / "objects" / f"stage-verdict.delivery-reports.{ctx['repo_slug']}.{ctx['round_id']}.json"
        stage_verdict_md_path = round_root / "objects" / f"stage-verdict.delivery-reports.{ctx['repo_slug']}.{ctx['round_id']}.md"
        result["stage_verdict_json"] = str(stage_verdict_json_path)
        result["stage_verdict_md"] = str(stage_verdict_md_path)
        write_json(stage_verdict_json_path, result)
        write_text(stage_verdict_md_path, render_stage_verdict_md(result, ctx["repo_slug"], ctx["round_id"]))

    write_json(out_path, result)
    if ns.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(f"bridge={out_path}")
        print(f"final_action={result['final_action']}")
        print(f"final_reason={result['final_reason']}")
        print(f"repo_boundary_state={result['repo_boundary_state']}")
        print(f"next_repo_stage={result['next_repo_stage']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
