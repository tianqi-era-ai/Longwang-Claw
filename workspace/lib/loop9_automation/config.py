from __future__ import annotations

import copy
import json
import os
from pathlib import Path
from typing import Any

WORKSPACE = Path('~/.openclaw/workspace').expanduser()
CONFIG_PATH = WORKSPACE / 'config' / 'loop9-dispatch.json'

DEFAULT_CONFIG: dict[str, Any] = {
    'audit': {
        'maxConcurrent': 1,
        'manualQueue': [],
    },
    'poc': {
        'maxConcurrent': 1,
        'manualQueue': [],
    },
    'launchGuard': {
        'enabled': True,
        'swapUsedMiBMax': 8192,
        'dataAvailGiBMin': 20,
        'rootAvailGiBMin': 20,
        'activeOpencodeCountMax': 3,
        'activeOpencodeRssMiBMax': 12288,
        'virtualizationRssMiBMax': 2048,
    },
    'dockerCleanup': {
        'enabled': True,
        'diskAvailGiBMin': 25,
        'retainHours': 12,
        'maxConcurrent': 1,
        'protectCurrentDynamicVerify': True,
    },
}


def _deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    merged = copy.deepcopy(base)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = _deep_merge(merged[key], value)
        else:
            merged[key] = copy.deepcopy(value)
    return merged


def _int_at_least(value: Any, default: int, minimum: int) -> int:
    try:
        return max(minimum, int(value))
    except Exception:
        return max(minimum, default)


def _float_at_least(value: Any, default: float, minimum: float) -> float:
    try:
        return max(minimum, float(value))
    except Exception:
        return max(minimum, default)


def _as_bool(value: Any, default: bool = False) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        lowered = value.strip().lower()
        if lowered in {'1', 'true', 'yes', 'on'}:
            return True
        if lowered in {'0', 'false', 'no', 'off'}:
            return False
    if isinstance(value, (int, float)):
        return bool(value)
    return default


def _normalize_audit_manual_queue(raw: Any) -> list[dict[str, Any]]:
    if not isinstance(raw, list):
        return []
    rows: list[dict[str, Any]] = []
    for item in raw:
        if not isinstance(item, dict):
            continue
        target_path = str(item.get('targetPath') or '').strip()
        if not target_path:
            continue
        policy = str(item.get('policy') or 'weibu-submission').strip() or 'weibu-submission'
        rows.append(
            {
                'targetPath': target_path,
                'policy': policy,
                'note': str(item.get('note') or '').strip(),
                'bypassTargetGate': _as_bool(item.get('bypassTargetGate'), False),
            }
        )
    return rows


def _normalize_poc_manual_queue(raw: Any) -> list[dict[str, Any]]:
    if not isinstance(raw, list):
        return []
    rows: list[dict[str, Any]] = []
    for item in raw:
        if not isinstance(item, dict):
            continue
        audit_run_dir = str(item.get('auditRunDir') or '').strip()
        if not audit_run_dir:
            continue
        rows.append(
            {
                'auditRunDir': audit_run_dir,
                'note': str(item.get('note') or '').strip(),
            }
        )
    return rows


def _normalize_config(data: dict[str, Any]) -> dict[str, Any]:
    data.setdefault('audit', {})
    data.setdefault('poc', {})
    data.setdefault('launchGuard', {})
    data.setdefault('dockerCleanup', {})

    data['audit']['maxConcurrent'] = _int_at_least(data['audit'].get('maxConcurrent'), 1, 1)
    data['poc']['maxConcurrent'] = _int_at_least(data['poc'].get('maxConcurrent'), 1, 1)
    data['audit']['manualQueue'] = _normalize_audit_manual_queue(data['audit'].get('manualQueue'))
    data['poc']['manualQueue'] = _normalize_poc_manual_queue(data['poc'].get('manualQueue'))

    guard = data['launchGuard']
    guard['enabled'] = bool(guard.get('enabled', True))
    guard['swapUsedMiBMax'] = _float_at_least(guard.get('swapUsedMiBMax'), 8192, 0)
    guard['dataAvailGiBMin'] = _float_at_least(guard.get('dataAvailGiBMin'), 20, 0)
    guard['rootAvailGiBMin'] = _float_at_least(guard.get('rootAvailGiBMin'), 20, 0)
    guard['activeOpencodeCountMax'] = _int_at_least(guard.get('activeOpencodeCountMax'), 3, 0)
    guard['activeOpencodeRssMiBMax'] = _float_at_least(guard.get('activeOpencodeRssMiBMax'), 12288, 0)
    guard['virtualizationRssMiBMax'] = _float_at_least(guard.get('virtualizationRssMiBMax'), 2048, 0)

    cleanup = data['dockerCleanup']
    cleanup['enabled'] = _as_bool(cleanup.get('enabled'), True)
    cleanup['diskAvailGiBMin'] = _float_at_least(cleanup.get('diskAvailGiBMin'), 25, 0)
    cleanup['retainHours'] = _int_at_least(cleanup.get('retainHours'), 12, 1)
    cleanup['maxConcurrent'] = _int_at_least(cleanup.get('maxConcurrent'), 1, 1)
    cleanup['protectCurrentDynamicVerify'] = _as_bool(cleanup.get('protectCurrentDynamicVerify'), True)
    return data


def load_dispatch_config() -> dict[str, Any]:
    data = copy.deepcopy(DEFAULT_CONFIG)
    try:
        raw = json.loads(CONFIG_PATH.read_text(encoding='utf-8')) if CONFIG_PATH.exists() else {}
    except Exception:
        raw = {}
    if isinstance(raw, dict):
        data = _deep_merge(data, raw)
    return _normalize_config(data)


def save_dispatch_config(data: dict[str, Any]) -> dict[str, Any]:
    normalized = _normalize_config(copy.deepcopy(data))
    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    tmp = CONFIG_PATH.with_suffix(CONFIG_PATH.suffix + '.tmp')
    tmp.write_text(json.dumps(normalized, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    os.replace(tmp, CONFIG_PATH)
    return normalized


def max_concurrent(kind: str) -> int:
    data = load_dispatch_config()
    if kind == 'audit':
        return int(data['audit']['maxConcurrent'])
    if kind == 'poc':
        return int(data['poc']['maxConcurrent'])
    return 1


def launch_guard_config() -> dict[str, Any]:
    data = load_dispatch_config()
    return copy.deepcopy(data['launchGuard'])


def docker_cleanup_config() -> dict[str, Any]:
    data = load_dispatch_config()
    return copy.deepcopy(data.get('dockerCleanup') or {})


def manual_queue(kind: str) -> list[dict[str, Any]]:
    data = load_dispatch_config()
    if kind == 'audit':
        return copy.deepcopy(data['audit'].get('manualQueue') or [])
    if kind == 'poc':
        return copy.deepcopy(data['poc'].get('manualQueue') or [])
    return []


def manual_queue_peek(kind: str) -> dict[str, Any] | None:
    rows = manual_queue(kind)
    return copy.deepcopy(rows[0]) if rows else None


def _queue_candidate_value(kind: str, item: dict[str, Any]) -> str:
    if kind == 'audit':
        return str(item.get('targetPath') or '').strip()
    if kind == 'poc':
        return str(item.get('auditRunDir') or '').strip()
    return ''


def manual_queue_pop(kind: str, expected_candidate: str | None = None) -> dict[str, Any]:
    data = load_dispatch_config()
    section = data.get(kind)
    if not isinstance(section, dict):
        return {'ok': False, 'reason': 'invalid-kind'}
    queue = list(section.get('manualQueue') or [])
    if not queue:
        return {'ok': False, 'reason': 'empty'}
    head = copy.deepcopy(queue[0])
    head_candidate = _queue_candidate_value(kind, head)
    expected = str(expected_candidate or '').strip()
    if expected and expected != head_candidate:
        return {
            'ok': False,
            'reason': 'head-mismatch',
            'head': head,
            'head_candidate': head_candidate,
            'expected_candidate': expected,
        }
    section['manualQueue'] = queue[1:]
    saved = save_dispatch_config(data)
    return {'ok': True, 'popped': head, 'remaining': len(saved.get(kind, {}).get('manualQueue') or [])}
