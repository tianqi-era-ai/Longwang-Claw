#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
import sys

WORKSPACE = Path('~/.openclaw/workspace').expanduser()
if str(WORKSPACE) not in sys.path:
    sys.path.insert(0, str(WORKSPACE))

from lib.loop9_automation.run_identity import classify_loop9_run
SUPER8_ROOT = WORKSPACE / 'Super8'
LOOP9_DIR = SUPER8_ROOT / 'temp' / 'loop9'
REAL_POC_OBS_DIR = SUPER8_ROOT / 'temp' / 'loop9-real-poc-observe'

STATUS_PATTERNS = [
    re.compile(r'^-\s+Overall status:\s+`?([A-Z-]+)`?\s*$', re.M),
    re.compile(r'^-\s+overall_status:\s+`?([A-Z-]+)`?\s*$', re.M),
    re.compile(r'^-\s+overall status:\s+`?([A-Z-]+)`?\s*$', re.M),
    re.compile(r'^-\s+validation_status:\s+`?([A-Z-]+)`?\s*$', re.M),
    re.compile(r'^-\s+Validation status:\s+`?([A-Z-]+)`?\s*$', re.M),
    re.compile(r'^-\s+Status:\s+`?([A-Z-]+)`?\s*$', re.M),
    re.compile(r'^-\s+status:\s+`?([A-Z-]+)`?\s*$', re.M),
    re.compile(r'^-\s+status:\s+\*\*([A-Z-]+)\*\*\s*$', re.M),
    re.compile(r'^Status:\s*`?([A-Z-]+)`?\s*$', re.M),
    re.compile(r'^-\s+`status\s*=\s*([A-Z-]+)`\s*$', re.M),
    re.compile(r'^-\s+总体结论：\*\*([A-Z-]+)\*\*\s*$', re.M),
    re.compile(r'^\*\*Overall Status\*\*:\s+✅?\s*\*\*([A-Z-]+)\*\*', re.M),
    re.compile(r'^\*\*Validation Status\*\*:\s+\*\*([A-Z-]+)\*\*', re.M),
    re.compile(r'^##\s+Status\s*$\s*^([A-Z-]+)\s*$', re.M),
    re.compile(r'^##\s+最终判定\s*$\s*^\*\*([A-Z-]+)\*\*\s*$', re.M),
    re.compile(r'^##\s+最终判定\s*$\s*^([A-Z-]+)\s*$', re.M),
    re.compile(r'^##\s+最终结论\s*$\s*^\*\*([A-Z-]+)\*\*\s*$', re.M),
    re.compile(r'^##\s+最终结论\s*$\s*^([A-Z-]+)\s*$', re.M),
    re.compile(r'^##\s+Final Verdict\s*$\s*^\*\*([A-Z-]+)\*\*\s*$', re.M),
    re.compile(r'^##\s+Final Verdict\s*$\s*^([A-Z-]+)\s*$', re.M),
]

FREEZE_PATTERNS = [
    re.compile(r'状态：已冻结，无需修改'),
    re.compile(r'\bfrozen\b', re.I),
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description='Refresh deterministic file-based real-poc final status.')
    parser.add_argument('audit_run_dir', help='Completed Loop9 audit run dir or child path')
    parser.add_argument('--output', help='Output JSON path. Default: <audit_run_dir>/real_pocs/real_poc_final_status.json')
    parser.add_argument('--kv', action='store_true', help='Print key: value lines instead of JSON')
    parser.add_argument('--no-write', action='store_true', help='Do not write the output file; only print.')
    return parser.parse_args()


def normalize_audit_run_dir(input_path: str) -> Path:
    path = Path(input_path).expanduser().resolve()
    if not path.exists():
        raise SystemExit(f'Path does not exist: {path}')
    for candidate in [path, *path.parents]:
        if not candidate.is_dir():
            continue
        if any(candidate.glob('solution_v*')) and any(candidate.glob('validation_report_v*')):
            return candidate
        real_pocs = candidate / 'real_pocs'
        if real_pocs.is_dir() and (
            (real_pocs / 'manifest.json').exists()
            or any(real_pocs.glob('real_poc_solution_v*'))
            or any(real_pocs.glob('real_poc_validation_report_v*'))
            or any(real_pocs.glob('*.py'))
            or (real_pocs / 'real_poc_final_status.json').exists()
        ):
            return candidate
    raise SystemExit(f'Could not normalize to a completed Loop9 audit run dir from: {path}')


def safe_read_text(path: Path) -> str:
    try:
        return path.read_text(encoding='utf-8', errors='ignore')
    except Exception:
        return ''


def read_meta_value(path: Path, key: str) -> str:
    if not path.exists():
        return ''
    for line in safe_read_text(path).splitlines():
        if line.startswith(f'{key}='):
            return line.split('=', 1)[1].strip()
    return ''


def parse_json(path: Path) -> dict[str, Any] | None:
    try:
        return json.loads(path.read_text(encoding='utf-8'))
    except Exception:
        return None


def latest_dir(base: Path, pattern: str) -> Path | None:
    dirs = [p for p in base.glob(pattern) if p.is_dir()]
    if not dirs:
        return None
    dirs.sort(key=lambda p: p.stat().st_mtime)
    return dirs[-1]


def parse_status_from_markdown(path: Path) -> str | None:
    if not path.exists():
        return None
    text = safe_read_text(path)
    for pat in STATUS_PATTERNS:
        m = pat.search(text)
        if m:
            return m.group(1).strip().upper()
    return None


def parse_freeze_from_markdown(path: Path) -> bool:
    if not path.exists():
        return False
    text = safe_read_text(path)
    return any(p.search(text) for p in FREEZE_PATTERNS)


def parse_status_from_round_dir(round_dir: Path | None) -> str | None:
    if not round_dir or not round_dir.is_dir():
        return None
    for name in ('part01.md', 'index.md'):
        status = parse_status_from_markdown(round_dir / name)
        if status:
            return status
    return None


def parse_freeze_from_round_dir(round_dir: Path | None) -> bool:
    if not round_dir or not round_dir.is_dir():
        return False
    for name in ('part01.md', 'index.md'):
        if parse_freeze_from_markdown(round_dir / name):
            return True
    return False


def parse_round_from_dir(path: Path | None) -> int | None:
    if not path:
        return None
    m = re.search(r'_v(\d+)$', path.name)
    if not m:
        return None
    try:
        return int(m.group(1))
    except Exception:
        return None


def find_latest_matching_real_poc_observe(audit_run_dir: Path) -> Path | None:
    rows: list[tuple[float, Path]] = []
    if not REAL_POC_OBS_DIR.exists():
        return None
    for obs in REAL_POC_OBS_DIR.iterdir():
        if not obs.is_dir():
            continue
        meta_json = parse_json(obs / 'run.meta.json') or {}
        meta_txt = obs / 'run.meta'
        linked = ''
        if isinstance(meta_json, dict):
            linked = str(meta_json.get('audit_run_dir') or '')
        if not linked:
            linked = read_meta_value(meta_txt, 'audit_run_dir')
        if linked and Path(linked).resolve() == audit_run_dir:
            rows.append((obs.stat().st_mtime, obs))
    if not rows:
        return None
    rows.sort(key=lambda x: x[0])
    return rows[-1][1]


def find_latest_iteration_run(audit_run_dir: Path) -> Path | None:
    rows: list[tuple[float, Path]] = []
    if not LOOP9_DIR.exists():
        return None
    needle = str(audit_run_dir)
    for run_dir in LOOP9_DIR.iterdir():
        if not run_dir.is_dir() or run_dir == audit_run_dir:
            continue
        identity = classify_loop9_run(run_dir)
        if identity.get('run_kind') == 'real-poc-iteration' and str(identity.get('root_audit_run_dir') or '') == needle:
            rows.append((run_dir.stat().st_mtime, run_dir))
            continue
        original_goal = run_dir / 'original_goal' / 'part01.md'
        text = safe_read_text(original_goal)
        low = text.lower()
        if needle in text and ('loop9-real-poc' in low or 'real_poc_solution_v' in low or 'shared poc workspace' in low):
            rows.append((run_dir.stat().st_mtime, run_dir))
    if not rows:
        return None
    rows.sort(key=lambda x: x[0])
    return rows[-1][1]


def _resolve_manifest_mapped_file(shared_poc_dir: Path, mapped: str) -> Path | None:
    if not mapped:
        return None
    candidate = Path(mapped).expanduser()
    try:
        if candidate.exists():
            return candidate
    except OSError:
        return None
    fallback = shared_poc_dir / candidate.name
    if fallback.exists():
        return fallback
    relative = shared_poc_dir / mapped
    if relative.exists():
        return relative
    return None


def summarize_manifest(shared_poc_dir: Path) -> dict[str, Any]:
    manifest_path = shared_poc_dir / 'manifest.json'
    manifest = parse_json(manifest_path) or {}
    findings = manifest.get('findings') if isinstance(manifest, dict) else None
    if not isinstance(findings, list):
        findings = []
    mapping_summary = manifest.get('mapping_summary') if isinstance(manifest, dict) and isinstance(manifest.get('mapping_summary'), dict) else {}

    by_status: Counter[str] = Counter()
    by_verdict: Counter[str] = Counter()
    missing_files: list[str] = []
    mapped_files: list[str] = []
    all_frozen = True
    all_accepted_or_frozen = True

    for item in findings:
        if not isinstance(item, dict):
            continue
        status = str(item.get('status') or 'unknown').strip() or 'unknown'
        verdict = str(item.get('validator_verdict') or 'unknown').strip() or 'unknown'
        mapped = str(item.get('mapped_file') or '').strip()
        by_status[status] += 1
        by_verdict[verdict] += 1
        if mapped:
            mapped_files.append(mapped)
            if not _resolve_manifest_mapped_file(shared_poc_dir, mapped):
                missing_files.append(mapped)
        else:
            missing_files.append(f"<missing-mapped-file-for:{item.get('finding_id') or item.get('title') or 'unknown'}>")
        if status.lower() != 'frozen':
            all_frozen = False
        if verdict.lower() not in {'accepted', 'frozen'}:
            all_accepted_or_frozen = False

    if not findings:
        all_frozen = True
        all_accepted_or_frozen = True

    all_findings_mapped = bool(mapping_summary.get('all_findings_mapped')) if 'all_findings_mapped' in mapping_summary else len(missing_files) == 0
    all_findings_accepted_or_frozen = bool(mapping_summary.get('all_findings_accepted_or_frozen')) if 'all_findings_accepted_or_frozen' in mapping_summary else all_accepted_or_frozen
    all_findings_frozen = bool(mapping_summary.get('all_findings_frozen')) if 'all_findings_frozen' in mapping_summary else all_frozen
    latest_round = manifest.get('latest_round') if isinstance(manifest, dict) else None
    try:
        latest_round = int(latest_round) if latest_round is not None else None
    except Exception:
        latest_round = None

    return {
        'manifest_path': str(manifest_path),
        'manifest_exists': manifest_path.exists(),
        'latest_round': latest_round,
        'findings_total': len(findings),
        'findings_by_status': dict(by_status),
        'findings_by_validator_verdict': dict(by_verdict),
        'mapped_files': mapped_files,
        'missing_mapped_files': missing_files,
        'all_findings_mapped': all_findings_mapped,
        'all_findings_accepted_or_frozen': all_findings_accepted_or_frozen,
        'all_findings_frozen': all_findings_frozen,
    }


def iso_now() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat()


def infer_workflow_completion(latest_round_status: str | None, latest_round: int | None, min_iterations: int | None, manifest_summary: dict[str, Any]) -> tuple[str, str]:
    if latest_round_status == 'PASSED' and latest_round is not None and min_iterations is not None:
        if latest_round < min_iterations:
            return 'not-yet', 'latest round passed, but below min_iterations'
        if not manifest_summary.get('all_findings_mapped'):
            return 'not-yet', 'latest round passed, but manifest mapping is incomplete'
        if not manifest_summary.get('all_findings_accepted_or_frozen'):
            return 'not-yet', 'latest round passed, but manifest verdicts are not fully accepted/frozen'
        return 'passed', 'latest round passed, min_iterations satisfied, and manifest state converged'
    if latest_round_status in {'FAILED', 'PENDING'}:
        return 'not-yet', f'latest round validation status is {latest_round_status}'
    return 'unknown', 'insufficient file evidence to determine workflow completion'


def build_status(audit_run_dir: Path) -> dict[str, Any]:
    latest_obs = find_latest_matching_real_poc_observe(audit_run_dir)
    latest_iter_run = find_latest_iteration_run(audit_run_dir)

    meta_json = parse_json(latest_obs / 'run.meta.json') if latest_obs else None
    meta_txt = latest_obs / 'run.meta' if latest_obs else None

    def meta(key: str, default: str = '') -> str:
        if isinstance(meta_json, dict) and meta_json.get(key) not in (None, ''):
            return str(meta_json.get(key))
        if meta_txt:
            value = read_meta_value(meta_txt, key)
            if value:
                return value
        return default

    shared_poc_dir = Path(meta('shared_poc_dir') or (audit_run_dir / 'real_pocs')).resolve()
    min_iterations_raw = meta('min_iterations')
    min_iterations_source_kind = meta('min_iterations_source_kind') or 'legacy-unknown'
    max_iterations_raw = meta('max_iterations')
    try:
        recorded_min_iterations = int(min_iterations_raw) if min_iterations_raw else 3
    except Exception:
        recorded_min_iterations = 3
    try:
        max_iterations = int(max_iterations_raw) if max_iterations_raw else 20
    except Exception:
        max_iterations = 20

    if min_iterations_source_kind == 'legacy-unknown' and recorded_min_iterations == 10:
        min_iterations = 3
        min_iterations_normalization = 'legacy-default-10-normalized-to-3'
    else:
        min_iterations = recorded_min_iterations
        min_iterations_normalization = 'none'

    linked_solution_dir = latest_dir(shared_poc_dir, 'real_poc_solution_v*')
    linked_validation_dir = latest_dir(shared_poc_dir, 'real_poc_validation_report_v*')
    linked_validation_status = parse_status_from_round_dir(linked_validation_dir)

    iter_solution_dir = latest_dir(latest_iter_run, 'solution_v*') if latest_iter_run else None
    iter_validation_dir = latest_dir(latest_iter_run, 'validation_report_v*') if latest_iter_run else None
    iter_validation_status = parse_status_from_round_dir(iter_validation_dir)
    iter_validation_freeze = parse_freeze_from_round_dir(iter_validation_dir)

    iter_round = parse_round_from_dir(iter_validation_dir)
    linked_round = parse_round_from_dir(linked_validation_dir)

    latest_round = iter_round
    latest_round_source = str(iter_validation_dir) if iter_validation_dir else None
    latest_round_solution_dir = str(iter_solution_dir) if iter_solution_dir else None
    latest_round_validation_dir = str(iter_validation_dir) if iter_validation_dir else None
    latest_round_validation_status = iter_validation_status
    latest_round_freeze_signal = iter_validation_freeze
    latest_round_semantics = 'real-poc iteration round extracted from latest_real_poc_iteration_run_dir validation_report_vN'

    # Shared/manual retrofit rounds are legitimate shared state, even when there is no
    # newer iteration run to materialize them. Prefer the linked shared round when it is
    # newer than the latest iteration-derived round or when iteration data is absent.
    if linked_round is not None and linked_validation_status and (latest_round is None or linked_round > latest_round):
        latest_round = linked_round
        latest_round_source = str(linked_validation_dir)
        latest_round_solution_dir = str(linked_solution_dir) if linked_solution_dir else None
        latest_round_validation_dir = str(linked_validation_dir)
        latest_round_validation_status = linked_validation_status
        latest_round_freeze_signal = parse_freeze_from_round_dir(linked_validation_dir)
        latest_round_semantics = 'linked shared round extracted from linked audit validation dir'

    manifest_summary = summarize_manifest(shared_poc_dir)
    workflow_completion, completion_reason = infer_workflow_completion(
        latest_round_validation_status,
        latest_round,
        min_iterations,
        manifest_summary,
    )

    manifest_findings = []
    manifest_path = shared_poc_dir / 'manifest.json'
    manifest_json = parse_json(manifest_path)
    if isinstance(manifest_json, dict):
        raw_findings = manifest_json.get('findings')
        if isinstance(raw_findings, list):
            manifest_findings = [row for row in raw_findings if isinstance(row, dict)]
    manifest_history_round = max((int(row.get('last_round') or 0) for row in manifest_findings), default=0)
    manifest_latest_round = int(manifest_summary.get('latest_round') or 0)
    manifest_max_round = max(manifest_history_round, manifest_latest_round)
    over_limit_solution_dirs = list(shared_poc_dir.glob(f'real_poc_solution_v{max_iterations + 1}*')) if shared_poc_dir.exists() else []
    over_limit_validation_dirs = list(shared_poc_dir.glob(f'real_poc_validation_report_v{max_iterations + 1}*')) if shared_poc_dir.exists() else []

    # Repair-first guardrail:
    # If the shared workspace is already fully frozen and capped at max_iterations,
    # do not let a newer local wrapper run drag workflow_completion back to unknown/not-yet
    # merely because the latest local iteration has not materialized a newer accepted shared round yet.
    if (
        manifest_summary.get('all_findings_frozen')
        and manifest_summary.get('all_findings_mapped')
        and manifest_summary.get('all_findings_accepted_or_frozen')
        and manifest_max_round >= max_iterations
        and linked_solution_dir is not None
        and linked_validation_dir is not None
        and not over_limit_solution_dirs
        and not over_limit_validation_dirs
    ):
        workflow_completion = 'passed'
        completion_reason = 'shared workspace frozen and converged at max_iterations cap'

    exit_code = None
    if latest_obs and (latest_obs / 'opencode.exit_code').exists():
        text = safe_read_text(latest_obs / 'opencode.exit_code').strip()
        try:
            exit_code = int(text)
        except Exception:
            exit_code = text or None

    data: dict[str, Any] = {
        'schema': 'loop9.real-poc.final-status.v1',
        'refreshed_at': iso_now(),
        'audit_run_dir': str(audit_run_dir),
        'real_poc_final_status_path': str((shared_poc_dir / 'real_poc_final_status.json').resolve()),
        'shared_terminal_round': manifest_max_round if manifest_max_round > 0 else None,
        'shared_terminal_round_semantics': 'highest round currently recorded by shared manifest.json',
        'latest_real_poc_observe_dir': str(latest_obs) if latest_obs else None,
        'latest_real_poc_iteration_run_dir': str(latest_iter_run) if latest_iter_run else None,
        'shared_poc_dir': str(shared_poc_dir),
        'shared_poc_py_count': len(list(shared_poc_dir.glob('*.py'))) if shared_poc_dir.exists() else 0,
        'recorded_min_iterations': recorded_min_iterations,
        'min_iterations': min_iterations,
        'min_iterations_source_kind': min_iterations_source_kind,
        'min_iterations_normalization': min_iterations_normalization,
        'max_iterations': max_iterations,
        'min_iterations_source': str((latest_obs / 'run.meta.json')) if latest_obs else 'default(3)',
        'max_iterations_source': str((latest_obs / 'run.meta.json')) if latest_obs else 'default(20)',
        'latest_round': latest_round,
        'latest_round_semantics': latest_round_semantics,
        'latest_round_source': latest_round_source,
        'latest_round_solution_dir': latest_round_solution_dir,
        'latest_round_validation_dir': latest_round_validation_dir,
        'latest_round_validation_status': latest_round_validation_status,
        'latest_round_freeze_signal': latest_round_freeze_signal,
        'linked_audit_real_poc_solution_dir': str(linked_solution_dir) if linked_solution_dir else None,
        'linked_audit_real_poc_validation_dir': str(linked_validation_dir) if linked_validation_dir else None,
        'linked_audit_real_poc_validation_status': linked_validation_status,
        'observe_exit_code': exit_code,
        'manifest': manifest_summary,
        'min_iterations_satisfied': (latest_round is not None and latest_round >= min_iterations),
        'round_validation_passed': (latest_round_validation_status == 'PASSED'),
        'workflow_completion': workflow_completion,
        'workflow_completion_reason': completion_reason,
        'file_level_identification_rule': 'workflow_completion=passed only when latest_round_validation_status==PASSED && latest_round(real-poc iteration round)>=min_iterations && manifest.all_findings_mapped && manifest.all_findings_accepted_or_frozen',
    }
    return data


def emit_kv(data: dict[str, Any]) -> str:
    lines = [
        f"schema: {data.get('schema')}",
        f"audit_run_dir: {data.get('audit_run_dir')}",
        f"real_poc_final_status_path: {data.get('real_poc_final_status_path')}",
        f"latest_real_poc_observe_dir: {data.get('latest_real_poc_observe_dir') or ''}",
        f"latest_real_poc_iteration_run_dir: {data.get('latest_real_poc_iteration_run_dir') or ''}",
        f"shared_poc_dir: {data.get('shared_poc_dir')}",
        f"shared_poc_py_count: {data.get('shared_poc_py_count')}",
        f"recorded_min_iterations: {data.get('recorded_min_iterations')}",
        f"min_iterations: {data.get('min_iterations')}",
        f"min_iterations_source_kind: {data.get('min_iterations_source_kind')}",
        f"min_iterations_normalization: {data.get('min_iterations_normalization')}",
        f"max_iterations: {data.get('max_iterations')}",
        f"latest_round: {data.get('latest_round') if data.get('latest_round') is not None else ''}",
        f"latest_round_semantics: {data.get('latest_round_semantics') or ''}",
        f"latest_round_source: {data.get('latest_round_source') or ''}",
        f"latest_round_validation_status: {data.get('latest_round_validation_status') or ''}",
        f"min_iterations_satisfied: {'yes' if data.get('min_iterations_satisfied') else 'no'}",
        f"round_validation_passed: {'yes' if data.get('round_validation_passed') else 'no'}",
        f"manifest_findings_total: {data.get('manifest', {}).get('findings_total')}",
        f"manifest_all_findings_mapped: {'yes' if data.get('manifest', {}).get('all_findings_mapped') else 'no'}",
        f"manifest_all_findings_accepted_or_frozen: {'yes' if data.get('manifest', {}).get('all_findings_accepted_or_frozen') else 'no'}",
        f"manifest_all_findings_frozen: {'yes' if data.get('manifest', {}).get('all_findings_frozen') else 'no'}",
        f"workflow_completion: {data.get('workflow_completion')}",
        f"workflow_completion_reason: {data.get('workflow_completion_reason')}",
    ]
    return '\n'.join(lines)


def main() -> None:
    ns = parse_args()
    audit_run_dir = normalize_audit_run_dir(ns.audit_run_dir)
    data = build_status(audit_run_dir)
    output_path = Path(ns.output).expanduser().resolve() if ns.output else (audit_run_dir / 'real_pocs' / 'real_poc_final_status.json')

    if not ns.no_write:
        output_path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

    if ns.kv:
        print(emit_kv(data))
    else:
        print(json.dumps(data, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
