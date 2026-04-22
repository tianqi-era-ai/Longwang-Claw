from __future__ import annotations

import json
import os
import time
import uuid
from pathlib import Path
from typing import Any

from .config import max_concurrent

WORKSPACE = Path('~/.openclaw/workspace').expanduser()
STATE_ROOT = WORKSPACE / 'automation-state' / 'loop9'
LOCKS_DIR = STATE_ROOT / 'locks'
COOLDOWNS_DIR = STATE_ROOT / 'cooldowns'
HISTORY_PATH = STATE_ROOT / 'history.jsonl'
DEFERRED_PATH = STATE_ROOT / 'deferred.jsonl'

DEFAULT_LOCK_MINUTES = {
    'audit': 45,
    'poc': 45,
    'verify': 45,
    'publish': 120,
}

DEFAULT_COOLDOWN_MINUTES = {
    'audit': 120,
    'poc': 180,
    'verify': 180,
    'publish': 60,
}


def ensure_state_dirs() -> None:
    LOCKS_DIR.mkdir(parents=True, exist_ok=True)
    COOLDOWNS_DIR.mkdir(parents=True, exist_ok=True)
    STATE_ROOT.mkdir(parents=True, exist_ok=True)


def _atomic_write_json(path: Path, data: dict[str, Any]) -> None:
    ensure_state_dirs()
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(f"{path.name}.{os.getpid()}.{uuid.uuid4().hex}.tmp")
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    os.replace(tmp, path)


def _append_jsonl(path: Path, row: dict[str, Any]) -> None:
    ensure_state_dirs()
    with path.open('a', encoding='utf-8') as fh:
        fh.write(json.dumps(row, ensure_ascii=False) + '\n')


def now_ts() -> float:
    return time.time()


def now_iso() -> str:
    return time.strftime('%Y-%m-%dT%H:%M:%S%z', time.localtime())


def _configured_poc_lock_paths() -> list[Path]:
    slot_count = max(1, int(max_concurrent('poc')))
    return [LOCKS_DIR / f'poc-slot-{idx}.json' for idx in range(1, slot_count + 1)]


def _all_poc_lock_paths() -> list[Path]:
    configured = {str(path): path for path in _configured_poc_lock_paths()}
    for path in sorted(LOCKS_DIR.glob('poc-slot-*.json')):
        configured.setdefault(str(path), path)
    return list(configured.values())


def lock_path(kind: str) -> Path:
    if kind == 'poc':
        return _configured_poc_lock_paths()[0]
    return LOCKS_DIR / f'{kind}.json'


def lock_paths(kind: str) -> list[Path]:
    if kind == 'poc':
        return _all_poc_lock_paths()
    return [lock_path(kind)]


def _safe_name(text: str) -> str:
    cleaned = ''.join(ch if ch.isalnum() or ch in ('-', '_', '.') else '-' for ch in text.strip())
    while '--' in cleaned:
        cleaned = cleaned.replace('--', '-')
    return (cleaned.strip('-') or 'unnamed')[:180]


def cooldown_path(kind: str, candidate_key: str) -> Path:
    bucket = COOLDOWNS_DIR / kind
    bucket.mkdir(parents=True, exist_ok=True)
    return bucket / f'{_safe_name(candidate_key)}.json'


def _read_lock_file(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text(encoding='utf-8'))
    except Exception:
        return None
    expires_at = float(data.get('expires_at_ts') or 0)
    row = {**data, '_path': str(path)}
    if expires_at and expires_at < now_ts():
        return {'stale': True, **row}
    return row


def current_locks(kind: str) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for path in lock_paths(kind):
        row = _read_lock_file(path)
        if row:
            rows.append(row)
    rows.sort(key=lambda row: float(row.get('claimed_at_ts') or 0), reverse=True)
    return rows


def current_lock(kind: str) -> dict[str, Any] | None:
    rows = current_locks(kind)
    if not rows:
        return None
    for row in rows:
        if not row.get('stale'):
            return row
    return rows[0]


def active_lock_count(kind: str) -> int:
    return sum(1 for row in current_locks(kind) if not row.get('stale'))


def acquire_lock(kind: str, candidate: str, note: str = '', minutes: int | None = None, meta: dict[str, Any] | None = None) -> dict[str, Any]:
    ensure_state_dirs()
    minutes = minutes or DEFAULT_LOCK_MINUTES.get(kind, 45)
    now = now_ts()

    if kind == 'poc':
        chosen_path: Path | None = None
        chosen_slot: int | None = None
        active_rows = [row for row in current_locks(kind) if not row.get('stale')]
        for idx, path in enumerate(_configured_poc_lock_paths(), start=1):
            row = _read_lock_file(path)
            if not row or row.get('stale'):
                chosen_path = path
                chosen_slot = idx
                break
        if not chosen_path or chosen_slot is None:
            return {'ok': False, 'reason': 'lock-active', 'locks': active_rows}

        token = f'{kind}-{uuid.uuid4().hex[:12]}'
        data = {
            'kind': kind,
            'candidate': candidate,
            'token': token,
            'slot': chosen_slot,
            'claimed_at_ts': now,
            'claimed_at': now_iso(),
            'expires_at_ts': now + minutes * 60,
            'expires_in_minutes': minutes,
            'note': note,
            'pid': os.getpid(),
            'meta': meta or {},
        }
        _atomic_write_json(chosen_path, data)
        _append_jsonl(HISTORY_PATH, {'ts': now_iso(), 'event': 'claim', **data})
        return {'ok': True, 'lock': data}

    existing = current_lock(kind)
    if existing and not existing.get('stale'):
        return {'ok': False, 'reason': 'lock-active', 'lock': existing}

    token = f'{kind}-{uuid.uuid4().hex[:12]}'
    data = {
        'kind': kind,
        'candidate': candidate,
        'token': token,
        'claimed_at_ts': now,
        'claimed_at': now_iso(),
        'expires_at_ts': now + minutes * 60,
        'expires_in_minutes': minutes,
        'note': note,
        'pid': os.getpid(),
        'meta': meta or {},
    }
    _atomic_write_json(lock_path(kind), data)
    _append_jsonl(HISTORY_PATH, {'ts': now_iso(), 'event': 'claim', **data})
    return {'ok': True, 'lock': data}


def release_lock(kind: str, token: str | None = None, status: str = 'released', note: str = '', meta: dict[str, Any] | None = None) -> dict[str, Any]:
    rows = current_locks(kind)
    if not rows:
        return {'ok': False, 'reason': 'no-lock'}

    target: dict[str, Any] | None = None
    if token:
        for row in rows:
            if row.get('token') == token:
                target = row
                break
        if not target:
            return {'ok': False, 'reason': 'token-mismatch', 'locks': rows}
    else:
        target = current_lock(kind)
        if not target:
            return {'ok': False, 'reason': 'no-lock'}

    path = Path(str(target.get('_path') or lock_path(kind)))
    row = {
        'ts': now_iso(),
        'event': 'release',
        'kind': kind,
        'candidate': target.get('candidate'),
        'token': target.get('token'),
        'slot': target.get('slot'),
        'status': status,
        'note': note,
        'meta': meta or {},
    }
    _append_jsonl(HISTORY_PATH, row)
    try:
        path.unlink()
    except FileNotFoundError:
        pass
    return {'ok': True, 'released': row}


def clear_lock(kind: str, note: str = '') -> dict[str, Any]:
    rows = current_locks(kind)
    for path in lock_paths(kind):
        if path.exists():
            path.unlink()
    row = {'ts': now_iso(), 'event': 'clear', 'kind': kind, 'note': note, 'previous': rows}
    _append_jsonl(HISTORY_PATH, row)
    return {'ok': True, 'cleared': row}


def current_cooldown(kind: str, candidate_key: str) -> dict[str, Any] | None:
    path = cooldown_path(kind, candidate_key)
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text(encoding='utf-8'))
    except Exception:
        return None
    expires_at = float(data.get('expires_at_ts') or 0)
    if expires_at and expires_at < now_ts():
        try:
            path.unlink()
        except FileNotFoundError:
            pass
        return None
    return data


def set_cooldown(kind: str, candidate_key: str, reason: str, minutes: int | None = None, meta: dict[str, Any] | None = None) -> dict[str, Any]:
    ensure_state_dirs()
    minutes = minutes or DEFAULT_COOLDOWN_MINUTES.get(kind, 60)
    started_at = now_ts()
    data = {
        'kind': kind,
        'candidate_key': candidate_key,
        'reason': reason,
        'set_at_ts': started_at,
        'set_at': now_iso(),
        'expires_at_ts': started_at + minutes * 60,
        'expires_in_minutes': minutes,
        'meta': meta or {},
    }
    _atomic_write_json(cooldown_path(kind, candidate_key), data)
    _append_jsonl(HISTORY_PATH, {'ts': now_iso(), 'event': 'cooldown-set', **data})
    return {'ok': True, 'cooldown': data}


def clear_cooldown(kind: str, candidate_key: str, note: str = '') -> dict[str, Any]:
    path = cooldown_path(kind, candidate_key)
    existing = current_cooldown(kind, candidate_key)
    if path.exists():
        path.unlink()
    row = {'ts': now_iso(), 'event': 'cooldown-clear', 'kind': kind, 'candidate_key': candidate_key, 'note': note, 'previous': existing}
    _append_jsonl(HISTORY_PATH, row)
    return {'ok': True, 'cleared': row}


def defer_item(kind: str, candidate: str, reason: str, meta: dict[str, Any] | None = None) -> dict[str, Any]:
    row = {
        'ts': now_iso(),
        'event': 'defer',
        'kind': kind,
        'candidate': candidate,
        'reason': reason,
        'meta': meta or {},
    }
    _append_jsonl(DEFERRED_PATH, row)
    _append_jsonl(HISTORY_PATH, row)
    return {'ok': True, 'deferred': row}
