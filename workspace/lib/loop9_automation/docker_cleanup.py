from __future__ import annotations

import json
import os
import shutil
import subprocess
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from .config import docker_cleanup_config

UTC = timezone.utc
WORKSPACE = Path('~/.openclaw/workspace').expanduser()
STATE_DIR = WORKSPACE / 'automation-state' / 'loop9' / 'docker-cleanup'
LOCKS_DIR = STATE_DIR / 'locks'
_DYNAMIC_VERIFY_MARKERS = (
    'run_loop9_env_poc_dynamic_verify.py',
    'run_verify_dispatch_cycle.py',
    'execute_return_to_env.py',
    'run_loop9_env_bootstrap.py',
)
_PROTECTED_RETENTION_LABELS: tuple[tuple[str, set[str]], ...] = (
    ('io.openclaw.retention.class', {'published-final', 'keep'}),
    ('io.openclaw.retention.keep', {'1', 'on', 'true', 'yes'}),
)


def _iso_now() -> str:
    return datetime.now(tz=UTC).isoformat()


def _slot_path(index: int) -> Path:
    return LOCKS_DIR / f'docker-cleanup-slot-{index}.json'


def _safe_read_json(path: Path) -> dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding='utf-8'))
    except Exception:
        return {}


def _pid_alive(pid: int) -> bool:
    if pid <= 0:
        return False
    try:
        os.kill(pid, 0)
        return True
    except OSError:
        return False


def _cleanup_stale_slots(config: dict[str, Any]) -> list[str]:
    LOCKS_DIR.mkdir(parents=True, exist_ok=True)
    cleaned: list[str] = []
    stale_before = datetime.now(tz=UTC) - timedelta(hours=max(6, int(config.get('retainHours', 12)) * 2))
    for path in sorted(LOCKS_DIR.glob('docker-cleanup-slot-*.json')):
        payload = _safe_read_json(path)
        if not payload:
            path.unlink(missing_ok=True)
            cleaned.append(path.name)
            continue
        pid = int(payload.get('pid') or 0)
        started_raw = str(payload.get('startedAt') or '')
        started: datetime | None = None
        try:
            started = datetime.fromisoformat(started_raw)
            if started.tzinfo is None:
                started = started.replace(tzinfo=UTC)
        except Exception:
            started = None
        if pid and _pid_alive(pid):
            continue
        if pid and not _pid_alive(pid):
            path.unlink(missing_ok=True)
            cleaned.append(path.name)
            continue
        if started is None or started < stale_before:
            path.unlink(missing_ok=True)
            cleaned.append(path.name)
    return cleaned


def _claim_slot(config: dict[str, Any]) -> dict[str, Any] | None:
    LOCKS_DIR.mkdir(parents=True, exist_ok=True)
    max_slots = max(1, int(config.get('maxConcurrent') or 1))
    for idx in range(1, max_slots + 1):
        path = _slot_path(idx)
        if path.exists():
            continue
        payload = {
            'slotIndex': idx,
            'startedAt': _iso_now(),
            'pid': os.getpid(),
        }
        try:
            with path.open('x', encoding='utf-8') as fh:
                json.dump(payload, fh, ensure_ascii=False, indent=2)
        except FileExistsError:
            continue
        payload['path'] = str(path)
        return payload
    return None


def _release_slot(slot: dict[str, Any] | None) -> None:
    if not slot:
        return
    try:
        Path(str(slot.get('path') or '')).unlink(missing_ok=True)
    except Exception:
        pass


def _run(args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, capture_output=True, text=True, check=False)


def _docker_ok() -> tuple[bool, str]:
    if not shutil.which('docker'):
        return False, 'docker-not-installed'
    probe = _run(['docker', 'info'])
    if probe.returncode != 0:
        return False, 'docker-unavailable'
    return True, 'ok'


def _parse_dt(raw: Any) -> datetime | None:
    text = str(raw or '').strip()
    if not text:
        return None
    if text.startswith('0001-01-01T00:00:00'):
        return None
    if text.endswith('Z'):
        text = text[:-1] + '+00:00'
    if '.' in text:
        head, tail = text.split('.', 1)
        sign = ''
        offset = ''
        if '+' in tail:
            frac, offset = tail.split('+', 1)
            sign = '+'
        elif '-' in tail:
            frac, offset = tail.split('-', 1)
            sign = '-'
        else:
            frac = tail
        frac = (frac + '000000')[:6]
        text = head + '.' + frac
        if sign and offset:
            text += sign + offset
    try:
        dt = datetime.fromisoformat(text)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=UTC)
        return dt.astimezone(UTC)
    except Exception:
        return None


def _container_retention_anchor(row: dict[str, Any]) -> tuple[datetime | None, str]:
    state = row.get('State') or {}
    candidates = [
        ('startedAt', _parse_dt(state.get('StartedAt'))),
        ('finishedAt', _parse_dt(state.get('FinishedAt'))),
        ('createdAt', _parse_dt(row.get('Created') or row.get('CreatedAt'))),
    ]
    valid = [(label, dt) for label, dt in candidates if dt is not None]
    if not valid:
        return None, ''
    label, dt = max(valid, key=lambda item: item[1])
    return dt, label


def _json_lines(args: list[str]) -> list[dict[str, Any]]:
    proc = _run(args)
    if proc.returncode != 0:
        return []
    rows: list[dict[str, Any]] = []
    for line in proc.stdout.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            rows.append(json.loads(line))
        except Exception:
            continue
    return rows


def _container_ids(all_containers: bool = False) -> list[str]:
    args = ['docker', 'ps', '-q']
    if all_containers:
        args.insert(2, '-a')
    proc = _run(args)
    if proc.returncode != 0:
        return []
    return [line.strip() for line in proc.stdout.splitlines() if line.strip()]


def _inspect(kind: str, ids: list[str]) -> list[dict[str, Any]]:
    if not ids:
        return []
    proc = _run(['docker', kind, 'inspect', *ids])
    if proc.returncode != 0:
        return []
    try:
        payload = json.loads(proc.stdout)
        if isinstance(payload, list):
            return payload
    except Exception:
        return []
    return []


def _volume_names() -> list[str]:
    rows = _json_lines(['docker', 'volume', 'ls', '--format', '{{json .}}'])
    names: list[str] = []
    for row in rows:
        name = str(row.get('Name') or '').strip()
        if name:
            names.append(name)
    return names


def _active_dynamic_verify() -> dict[str, Any]:
    proc = _run(['ps', '-axo', 'pid=,args='])
    if proc.returncode != 0:
        return {'active': False, 'matches': []}
    matches: list[dict[str, Any]] = []
    for line in proc.stdout.splitlines():
        raw = line.strip()
        if not raw:
            continue
        parts = raw.split(None, 1)
        if len(parts) != 2:
            continue
        pid_raw, args = parts
        try:
            pid = int(pid_raw)
        except Exception:
            continue
        if any(marker in args for marker in _DYNAMIC_VERIFY_MARKERS):
            matches.append({'pid': pid, 'args': args})
    return {'active': bool(matches), 'matches': matches}


def _protected_compose_projects(container_rows: list[dict[str, Any]]) -> set[str]:
    projects: set[str] = set()
    for row in container_rows:
        if not bool(row.get('State', {}).get('Running')):
            continue
        labels = row.get('Config', {}).get('Labels') or {}
        project = str(labels.get('com.docker.compose.project') or '').strip()
        if project:
            projects.add(project)
    return projects


def _used_volume_names(container_rows: list[dict[str, Any]]) -> set[str]:
    used: set[str] = set()
    for row in container_rows:
        for mount in row.get('Mounts') or []:
            if str(mount.get('Type') or '') != 'volume':
                continue
            name = str(mount.get('Name') or '').strip()
            if name:
                used.add(name)
    return used


def _normalize_label_value(value: Any) -> str:
    return str(value or '').strip().lower()


def _labels_have_retention_protection(labels: dict[str, Any]) -> bool:
    for key, allowed_values in _PROTECTED_RETENTION_LABELS:
        value = _normalize_label_value(labels.get(key))
        if value and value in allowed_values:
            return True
    return False


def _container_labels(row: dict[str, Any]) -> dict[str, Any]:
    labels = row.get('Config', {}).get('Labels')
    return labels if isinstance(labels, dict) else {}


def _container_is_retention_protected(row: dict[str, Any]) -> bool:
    return _labels_have_retention_protection(_container_labels(row))


def _remove_containers(rows: list[dict[str, Any]], *, retain_before: datetime, protected_projects: set[str]) -> dict[str, Any]:
    removed: list[str] = []
    skipped: list[str] = []
    candidate_ids: list[str] = []
    for row in rows:
        state = row.get('State') or {}
        if bool(state.get('Running')):
            continue
        if _container_is_retention_protected(row):
            skipped.append(str(row.get('Name') or row.get('Id') or 'unknown'))
            continue
        labels = row.get('Config', {}).get('Labels') or {}
        project = str(labels.get('com.docker.compose.project') or '').strip()
        if project and project in protected_projects:
            skipped.append(str(row.get('Name') or row.get('Id') or 'unknown'))
            continue
        anchor_dt, _anchor_source = _container_retention_anchor(row)
        if anchor_dt and anchor_dt > retain_before:
            skipped.append(str(row.get('Name') or row.get('Id') or 'unknown'))
            continue
        cid = str(row.get('Id') or '').strip()
        if cid:
            candidate_ids.append(cid)
    if candidate_ids:
        proc = _run(['docker', 'rm', '-f', *candidate_ids])
        if proc.returncode == 0:
            removed = candidate_ids
    return {'removedCount': len(removed), 'removed': removed[:20], 'skippedCount': len(skipped)}


def _prune_builder(retain_hours: int) -> dict[str, Any]:
    proc = _run(['docker', 'builder', 'prune', '-f', '--filter', f'until={retain_hours}h'])
    return {'ok': proc.returncode == 0, 'stdout': proc.stdout.strip()[:1000], 'stderr': proc.stderr.strip()[:500]}


def _prune_dangling_images(retain_hours: int) -> dict[str, Any]:
    proc = _run(['docker', 'image', 'prune', '-f', '--filter', f'until={retain_hours}h'])
    return {'ok': proc.returncode == 0, 'stdout': proc.stdout.strip()[:1000], 'stderr': proc.stderr.strip()[:500]}


def _prune_unused_images(retain_hours: int) -> dict[str, Any]:
    proc = _run(['docker', 'image', 'prune', '-a', '-f', '--filter', f'until={retain_hours}h'])
    return {'ok': proc.returncode == 0, 'stdout': proc.stdout.strip()[:1000], 'stderr': proc.stderr.strip()[:500]}


def _remove_unused_volumes(*, retain_before: datetime, protected_projects: set[str], used_volumes: set[str]) -> dict[str, Any]:
    names = _volume_names()
    rows = _inspect('volume', names)
    removed: list[str] = []
    skipped = 0
    candidate_names: list[str] = []
    for row in rows:
        name = str(row.get('Name') or '').strip()
        if not name:
            continue
        if name in used_volumes:
            skipped += 1
            continue
        labels = row.get('Labels') or {}
        project = str(labels.get('com.docker.compose.project') or '').strip()
        if project and project in protected_projects:
            skipped += 1
            continue
        created = _parse_dt(row.get('CreatedAt'))
        if created and created > retain_before:
            skipped += 1
            continue
        candidate_names.append(name)
    if candidate_names:
        proc = _run(['docker', 'volume', 'rm', *candidate_names])
        if proc.returncode == 0:
            removed = candidate_names
    return {'removedCount': len(removed), 'removed': removed[:20], 'skippedCount': skipped}


def maybe_run_docker_cleanup(*, data_avail_gib: float | None, root_avail_gib: float | None) -> dict[str, Any]:
    config = docker_cleanup_config()
    result: dict[str, Any] = {
        'enabled': bool(config.get('enabled')),
        'triggered': False,
        'attempted': False,
        'status': 'disabled',
        'config': config,
        'notes': [],
    }
    if not config.get('enabled'):
        return result

    threshold = float(config.get('diskAvailGiBMin') or 0)
    current_min = min(v for v in [data_avail_gib, root_avail_gib] if isinstance(v, (int, float))) if any(isinstance(v, (int, float)) for v in [data_avail_gib, root_avail_gib]) else None
    if current_min is None or current_min > threshold:
        result['status'] = 'not-needed'
        return result

    result['triggered'] = True
    ok, reason = _docker_ok()
    if not ok:
        result['status'] = reason
        return result

    cleaned_slots = _cleanup_stale_slots(config)
    if cleaned_slots:
        result['notes'].append(f'cleaned_stale_slots={cleaned_slots}')
    slot = _claim_slot(config)
    if slot is None:
        result['status'] = 'max-concurrent-reached'
        return result

    result['attempted'] = True
    result['status'] = 'running'
    result['slot'] = slot
    try:
        dynamic = _active_dynamic_verify()
        result['dynamicVerify'] = dynamic
        retain_hours = int(config.get('retainHours') or 12)
        retain_before = datetime.now(tz=UTC) - timedelta(hours=retain_hours)

        all_container_rows = _inspect('container', _container_ids(all_containers=True))
        protected_projects = _protected_compose_projects(all_container_rows)
        for row in all_container_rows:
            if not _container_is_retention_protected(row):
                continue
            project = str(_container_labels(row).get('com.docker.compose.project') or '').strip()
            if project:
                protected_projects.add(project)
        used_volumes = _used_volume_names(all_container_rows)
        safe_mode = bool(config.get('protectCurrentDynamicVerify')) and bool(dynamic.get('active'))
        if safe_mode:
            result['notes'].append('active dynamic verify detected; using conservative cleanup mode')

        steps: dict[str, Any] = {}
        steps['containers'] = _remove_containers(all_container_rows, retain_before=retain_before, protected_projects=protected_projects)
        steps['danglingImages'] = _prune_dangling_images(retain_hours)

        if safe_mode:
            steps['builderCache'] = {'ok': False, 'skipped': True, 'reason': 'protect-current-dynamic-verify'}
            steps['unusedImages'] = {'ok': False, 'skipped': True, 'reason': 'protect-current-dynamic-verify'}
            steps['volumes'] = {'removedCount': 0, 'removed': [], 'skipped': True, 'reason': 'protect-current-dynamic-verify'}
        else:
            steps['builderCache'] = _prune_builder(retain_hours)
            steps['unusedImages'] = _prune_unused_images(retain_hours)
            steps['volumes'] = _remove_unused_volumes(retain_before=retain_before, protected_projects=protected_projects, used_volumes=used_volumes)

        result['steps'] = steps
        result['status'] = 'completed'
        return result
    finally:
        _release_slot(slot)
