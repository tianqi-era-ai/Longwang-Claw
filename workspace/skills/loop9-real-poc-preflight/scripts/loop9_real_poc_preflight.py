#!/usr/bin/env python3
from __future__ import annotations

import argparse
import importlib.util
import json
import re
import sys
from pathlib import Path
from typing import Any

WORKSPACE = Path('~/.openclaw/workspace').expanduser()
if str(WORKSPACE) not in sys.path:
    sys.path.insert(0, str(WORKSPACE))

from lib.loop9_automation.detect import _classify_poc_candidate

SKILL_ROOT = WORKSPACE / 'skills' / 'loop9-real-poc'
REFRESH_SCRIPT = SKILL_ROOT / 'scripts' / 'refresh_real_poc_status.py'

POSITIVE_DEFENSE_TERMS = (
    'blacklist',
    'whitelist',
    'allowlist',
    'denylist',
    'waf',
    'sanitize',
    'intercept',
    'disable_functions',
    'safecheck',
    'sysconfig',
    'config.cache.inc.php',
    '数据库',
    '黑名单',
    '白名单',
    '过滤',
    '拦截',
    '禁用函数',
)
NEGATION_TERMS = ('无', '未', '没有', 'not ', 'no ', 'without ')
DEFENSE_HEADER_KEYS = ('Defense-Model', 'Defense-Notes', 'Payload-Constraints', 'Confidence')
BYPASS_HINT_TERMS = (
    'base64_decode(',
    'cmd_start',
    'cmd_end',
    '`' + '$' + '__c',
    'disable_functions',
)


def _load_refresh_module():
    spec = importlib.util.spec_from_file_location('refresh_real_poc_status', REFRESH_SCRIPT)
    if not spec or not spec.loader:
        raise RuntimeError(f'Unable to load {REFRESH_SCRIPT}')
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _read_json(path: Path) -> dict[str, Any] | None:
    try:
        data = json.loads(path.read_text(encoding='utf-8'))
    except Exception:
        return None
    return data if isinstance(data, dict) else None


def _status_core(status: dict[str, Any] | None) -> dict[str, Any]:
    status = status or {}
    manifest = status.get('manifest') if isinstance(status.get('manifest'), dict) else {}
    return {
        'workflow_completion': status.get('workflow_completion'),
        'workflow_completion_reason': status.get('workflow_completion_reason'),
        'latest_round_validation_status': status.get('latest_round_validation_status'),
        'linked_audit_real_poc_validation_status': status.get('linked_audit_real_poc_validation_status'),
        'latest_round': status.get('latest_round'),
        'min_iterations_satisfied': status.get('min_iterations_satisfied'),
        'round_validation_passed': status.get('round_validation_passed'),
        'shared_poc_py_count': status.get('shared_poc_py_count'),
        'manifest_findings_total': manifest.get('findings_total'),
        'manifest_all_findings_mapped': manifest.get('all_findings_mapped'),
        'manifest_all_findings_accepted_or_frozen': manifest.get('all_findings_accepted_or_frozen'),
        'manifest_all_findings_frozen': manifest.get('all_findings_frozen'),
    }


def _read_text(path: Path) -> str:
    try:
        return path.read_text(encoding='utf-8', errors='ignore')
    except Exception:
        return ''


def _header_value(text: str, key: str) -> str:
    prefix = f'# {key}:'
    for line in text.splitlines():
        if line.startswith(prefix):
            return line[len(prefix):].strip()
    return ''


def _term_is_negated(text_lower: str, start: int) -> bool:
    window = text_lower[max(0, start - 12): start]
    return any(term in window for term in NEGATION_TERMS)


def _find_positive_defense_terms(text: str) -> list[str]:
    text_lower = text.lower()
    hits: list[str] = []
    for term in POSITIVE_DEFENSE_TERMS:
        needle = term.lower()
        index = text_lower.find(needle)
        while index != -1:
            if not _term_is_negated(text_lower, index):
                hits.append(term)
                break
            index = text_lower.find(needle, index + len(needle))
    return hits


def _resolve_mapped_file(run_dir: Path, mapped_file: str) -> Path | None:
    if not mapped_file:
        return None
    candidate = Path(mapped_file).expanduser()
    if candidate.exists():
        return candidate
    fallback = run_dir / 'real_pocs' / candidate.name
    if fallback.exists():
        return fallback
    return None


def _normalize_external_path(run_dir: Path, raw_path: str) -> Path | None:
    try:
        path = Path(raw_path).expanduser()
    except (OSError, ValueError):
        return None
    try:
        if path.exists():
            return path
    except OSError:
        return None
    parts = list(path.parts)
    try:
        anchor = parts.index(run_dir.name)
    except ValueError:
        return None
    suffix = parts[anchor + 1:]
    candidate = run_dir.joinpath(*suffix)
    return candidate if candidate.exists() else None


def _source_report_items(source_report: Any) -> list[str]:
    if isinstance(source_report, list):
        return [str(item).strip() for item in source_report if str(item).strip()]
    text = str(source_report or '').strip()
    if not text:
        return []
    if text.startswith('[') and text.endswith(']'):
        try:
            parsed = json.loads(text)
            if isinstance(parsed, list):
                return [str(item).strip() for item in parsed if str(item).strip()]
        except Exception:
            pass
    return [item.strip() for item in text.split(';') if item.strip()]


def _report_paths(run_dir: Path, source_report: Any) -> list[Path]:
    paths: list[Path] = []
    for item in _source_report_items(source_report):
        resolved = _normalize_external_path(run_dir, item)
        if resolved:
            paths.append(resolved)
    return paths


def _report_needles(finding: dict[str, Any], mapped_path: Path | None) -> list[str]:
    needles: list[str] = []
    title = str(finding.get('title') or '')
    raw_tokens = [title, mapped_path.name if mapped_path else '', str(finding.get('finding_id') or '')]
    for token in raw_tokens:
        for piece in re.split(r'[^a-zA-Z0-9_./-]+', token):
            piece = piece.strip()
            if len(piece) >= 4:
                needles.append(piece)
                if '/' in piece or piece.endswith('.php') or piece.endswith('.py'):
                    needles.append(Path(piece).name)
                    needles.append(Path(piece).stem)
    ordered: list[str] = []
    seen: set[str] = set()
    for needle in needles:
        lower = needle.lower()
        if lower not in seen:
            seen.add(lower)
            ordered.append(needle)
    return ordered


def _report_local_context(report_text: str, needles: list[str], window: int = 1) -> str:
    lines = report_text.splitlines()
    lowered = [line.lower() for line in lines]
    candidates: list[tuple[int, str]] = []
    for needle in needles:
        needle_lower = needle.lower()
        for idx, line in enumerate(lowered):
            if needle_lower in line:
                start = max(0, idx - window)
                end = min(len(lines), idx + window + 1)
                snippet = '\n'.join(lines[start:end])
                score = len(_find_positive_defense_terms(snippet))
                candidates.append((score, snippet))
    if not candidates:
        return ''
    candidates.sort(key=lambda item: item[0], reverse=True)
    return candidates[0][1]


def _defense_awareness_gap(run_dir: Path) -> dict[str, Any]:
    manifest = _read_json(run_dir / 'real_pocs' / 'manifest.json') or {}
    findings = manifest.get('findings') if isinstance(manifest.get('findings'), list) else []
    flagged: list[dict[str, Any]] = []

    for finding in findings:
        if not isinstance(finding, dict):
            continue
        mapped_path = _resolve_mapped_file(run_dir, str(finding.get('mapped_file') or ''))
        poc_text = _read_text(mapped_path) if mapped_path else ''

        signal_sources: list[str] = []
        finding_text = ' '.join(
            str(finding.get(key) or '')
            for key in ('finding_id', 'title', 'classification', 'preconditions')
        )
        finding_hits = _find_positive_defense_terms(finding_text)
        if finding_hits:
            signal_sources.append('finding-meta:' + ','.join(sorted(set(finding_hits))))

        needles = _report_needles(finding, mapped_path)
        for report_path in _report_paths(run_dir, str(finding.get('source_report') or '')):
            report_text = _read_text(report_path)
            scoped_text = _report_local_context(report_text, needles)
            if not scoped_text:
                continue
            report_hits = _find_positive_defense_terms(scoped_text)
            if report_hits:
                signal_sources.append(f'report:{report_path.name}:' + ','.join(sorted(set(report_hits))))
                break

        poc_lower = poc_text.lower()
        bypass_hits = [term for term in BYPASS_HINT_TERMS if term in poc_lower]
        if bypass_hits:
            signal_sources.append('poc-bypass-hints:' + ','.join(sorted(set(bypass_hits))))

        if not signal_sources:
            continue

        missing_headers = [key for key in DEFENSE_HEADER_KEYS if not _header_value(poc_text, key)]
        if not missing_headers:
            continue

        flagged.append({
            'finding_id': finding.get('finding_id') or finding.get('title'),
            'mapped_file': str(mapped_path) if mapped_path else str(finding.get('mapped_file') or ''),
            'signal_sources': signal_sources,
            'missing_headers': missing_headers,
        })

    return {
        'requires_follow_up': bool(flagged),
        'flagged_count': len(flagged),
        'flagged_findings': flagged,
        'policy': (
            'Only flag findings that show explicit defense/filter/bypass sensitivity signals. '
            'Do not require fabricated defense notes for projects with no such signals.'
        ),
    }


def _classify(run_dir: Path, status: dict[str, Any]) -> dict[str, Any]:
    bucket, reason, meta = _classify_poc_candidate(run_dir, status)
    return {
        'bucket': bucket,
        'reason': reason,
        'meta': meta,
    }


def _current_file_backed_success(run_dir: Path, current_status: dict[str, Any] | None) -> tuple[bool, str]:
    current_status = current_status or {}
    workflow = str(current_status.get('workflow_completion') or '')
    latest_status = str(current_status.get('latest_round_validation_status') or '')
    linked_status = str(current_status.get('linked_audit_real_poc_validation_status') or '')
    manifest = current_status.get('manifest') if isinstance(current_status.get('manifest'), dict) else {}

    if workflow not in {'passed', 'completed'}:
        return False, 'current-workflow-not-final'
    if latest_status != 'PASSED' and linked_status != 'PASSED':
        return False, 'current-validation-status-not-passed'
    if not manifest.get('all_findings_mapped'):
        return False, 'current-manifest-not-fully-mapped'
    if not manifest.get('all_findings_accepted_or_frozen'):
        return False, 'current-manifest-verdicts-not-converged'

    latest_solution_dir = str(current_status.get('latest_round_solution_dir') or '')
    latest_validation_dir = str(current_status.get('latest_round_validation_dir') or '')
    linked_solution_dir = str(current_status.get('linked_audit_real_poc_solution_dir') or '')
    linked_validation_dir = str(current_status.get('linked_audit_real_poc_validation_dir') or '')

    latest_pair_ok = bool(latest_solution_dir and latest_validation_dir and Path(latest_solution_dir).is_dir() and Path(latest_validation_dir).is_dir())
    linked_pair_ok = bool(linked_solution_dir and linked_validation_dir and Path(linked_solution_dir).is_dir() and Path(linked_validation_dir).is_dir())

    if not latest_pair_ok and not linked_pair_ok:
        return False, 'current-final-status-points-to-missing-round-artifacts'

    return True, 'current-final-status-is-file-backed-success'


def _safe_fix_eligible(current_status: dict[str, Any] | None, fresh_status: dict[str, Any], fresh_classification: dict[str, Any]) -> tuple[bool, str]:
    current_status = current_status or {}
    current_workflow = str(current_status.get('workflow_completion') or '')
    current_latest = str(current_status.get('latest_round_validation_status') or '')
    current_round_passed = bool(current_status.get('round_validation_passed'))

    fresh_workflow = str(fresh_status.get('workflow_completion') or '')
    fresh_latest = str(fresh_status.get('latest_round_validation_status') or '')
    manifest = fresh_status.get('manifest') if isinstance(fresh_status.get('manifest'), dict) else {}

    if fresh_classification.get('bucket') != 'already_success':
        return False, 'fresh-classification-not-already-success'
    if fresh_workflow != 'passed':
        return False, 'fresh-workflow-not-passed'
    if fresh_latest != 'PASSED':
        return False, 'fresh-latest-round-not-passed'
    if not fresh_status.get('min_iterations_satisfied'):
        return False, 'fresh-min-iterations-not-satisfied'
    if not manifest.get('all_findings_mapped'):
        return False, 'fresh-manifest-not-fully-mapped'
    if not manifest.get('all_findings_accepted_or_frozen'):
        return False, 'fresh-manifest-verdicts-not-converged'

    # Intentionally narrow:
    # only repair the classic parser/materialization gap where the on-disk file
    # still says unknown + blank latest status, rather than overwriting runs that
    # already carry an explicit non-success state like FAILED/not-yet.
    if current_workflow not in {'', 'unknown'}:
        return False, 'current-workflow-not-unknown'
    if current_latest not in {'', 'null'}:
        return False, 'current-latest-status-not-blank'
    if current_round_passed:
        return False, 'current-round-already-marked-passed'

    return True, 'narrow-parser-gap-safe-fix'


def _decision(
    run_dir: Path,
    current_status: dict[str, Any] | None,
    current_classification: dict[str, Any] | None,
    fresh_classification: dict[str, Any],
    safe_fix_eligible: bool,
    safe_fix_applied: bool,
    defense_awareness: dict[str, Any],
) -> str:
    current_success, _ = _current_file_backed_success(run_dir, current_status)
    bucket = fresh_classification.get('bucket')
    if bucket == 'already_success' or current_success:
        if defense_awareness.get('requires_follow_up'):
            return 'block-needs-human'
        if safe_fix_applied:
            return 'skip-already-success-after-safe-fix'
        if safe_fix_eligible:
            return 'safe-fix-available'
        return 'skip-already-success'
    if bucket in {'no_poc_yet', 'aborted_before_stop_condition'}:
        return 'allow-launch'
    return 'block-needs-human'


def _exit_code(decision: str) -> int:
    if decision == 'block-needs-human':
        return 20
    if decision == 'safe-fix-available':
        return 10
    return 0


def preflight_one(run_input: str, apply_safe_fixes: bool) -> dict[str, Any]:
    mod = _load_refresh_module()
    run_dir = mod.normalize_audit_run_dir(run_input)
    final_status_path = run_dir / 'real_pocs' / 'real_poc_final_status.json'

    current_status = _read_json(final_status_path)
    current_classification = _classify(run_dir, current_status) if current_status else None

    fresh_status = mod.build_status(run_dir)
    fresh_classification = _classify(run_dir, fresh_status)
    defense_awareness = _defense_awareness_gap(run_dir)

    safe_fix_eligible, safe_fix_reason = _safe_fix_eligible(current_status, fresh_status, fresh_classification)
    safe_fix_applied = False
    applied_status = None
    applied_classification = None

    if apply_safe_fixes and safe_fix_eligible:
        mod.main = getattr(mod, 'main', None)  # no-op; keep module loaded for parity
        final_status_path.write_text(json.dumps(fresh_status, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
        safe_fix_applied = True
        applied_status = _read_json(final_status_path)
        if applied_status:
            applied_classification = _classify(run_dir, applied_status)

    decision = _decision(
        run_dir,
        current_status,
        current_classification,
        fresh_classification,
        safe_fix_eligible,
        safe_fix_applied,
        defense_awareness,
    )

    result = {
        'run_dir': str(run_dir),
        'final_status_path': str(final_status_path),
        'current': {
            'status': _status_core(current_status),
            'classification': current_classification,
        },
        'fresh': {
            'status': _status_core(fresh_status),
            'classification': fresh_classification,
        },
        'safe_fix': {
            'eligible': safe_fix_eligible,
            'reason': safe_fix_reason,
            'applied': safe_fix_applied,
            'applied_status': _status_core(applied_status),
            'applied_classification': applied_classification,
        },
        'defense_awareness': defense_awareness,
        'preflight_decision': decision,
        'cron_guidance': {
            'before-formal-selection-or-launch': True,
            'recommended_behavior': {
                'skip-already-success': 'do not launch this run again',
                'skip-already-success-after-safe-fix': 'do not launch; keep refreshed status on disk',
                'safe-fix-available': 're-run with --apply-safe-fixes or let a wrapper decide',
                'allow-launch': 'candidate is still legitimately launchable',
                'block-needs-human': 'do not launch automatically; escalate for human review',
            }.get(decision),
            'defense_awareness_note': (
                'If explicit defense/filter/bypass-sensitivity signals exist but the mapped PoC headers '
                'still lack Defense-* metadata, treat the run as not safely auto-closable.'
            ),
        },
    }
    return result


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description='Preflight self-check for Loop9 real-poc runs before formal selection/launch.')
    parser.add_argument('run_inputs', nargs='+', help='One or more completed Loop9 audit run dirs (or child paths).')
    parser.add_argument('--apply-safe-fixes', action='store_true', help='Apply only narrow parser-gap safe fixes to real_poc_final_status.json when eligible.')
    parser.add_argument('--json', action='store_true', help='Emit JSON only.')
    return parser.parse_args()


def main() -> None:
    ns = parse_args()
    results = [preflight_one(item, ns.apply_safe_fixes) for item in ns.run_inputs]
    payload: dict[str, Any] = {'results': results}

    blocking = any(r.get('preflight_decision') == 'block-needs-human' for r in results)
    safe_fix_available = any(r.get('preflight_decision') == 'safe-fix-available' for r in results)
    payload['summary'] = {
        'total': len(results),
        'blocking': blocking,
        'safe_fix_available': safe_fix_available,
    }

    if ns.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        for item in results:
            print(f"run_dir={item['run_dir']}")
            print(f"decision={item['preflight_decision']}")
            print(f"fresh_bucket={item['fresh']['classification']['bucket']}")
            print(f"fresh_reason={item['fresh']['classification']['reason']}")
            print(f"fresh_workflow={item['fresh']['status']['workflow_completion']}")
            print(f"fresh_latest_round_validation_status={item['fresh']['status']['latest_round_validation_status']}")
            print(f"safe_fix_eligible={'yes' if item['safe_fix']['eligible'] else 'no'}")
            print(f"safe_fix_applied={'yes' if item['safe_fix']['applied'] else 'no'}")
            print(f"defense_awareness_requires_follow_up={'yes' if item['defense_awareness']['requires_follow_up'] else 'no'}")
            print(f"defense_awareness_flagged_count={item['defense_awareness']['flagged_count']}")
            print('---')

    raise SystemExit(_exit_code('block-needs-human' if blocking else ('safe-fix-available' if safe_fix_available else 'allow-launch')))


if __name__ == '__main__':
    main()
