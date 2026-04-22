from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import re
import subprocess
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from .config import manual_queue_peek, max_concurrent
from .launch_guard import check_launch_allowed
from .run_identity import classify_loop9_run
from .state import current_cooldown, current_lock, current_locks, release_lock
from .target_gate import check_target_policy

WORKSPACE = Path('~/.openclaw/workspace').expanduser()
TARGETS_DIR = WORKSPACE / 'targets'
SUPER8_ROOT = WORKSPACE / 'Super8'
LOOP9_DIR = SUPER8_ROOT / 'temp' / 'loop9'
LOOP9_OBSERVE_DIR = SUPER8_ROOT / 'temp' / 'loop9-observe'
REAL_POC_OBSERVE_DIR = SUPER8_ROOT / 'temp' / 'loop9-real-poc-observe'
PUBLISHER_STATE = WORKSPACE / 'memory' / 'loop9-feishu-publisher-state.json'
PUBLISH_PLAN_SCRIPT = WORKSPACE / 'skills' / 'loop9-feishu-publisher' / 'scripts' / 'build_publish_plan.py'
REAL_POC_STATUS_SCRIPT = WORKSPACE / 'skills' / 'loop9-real-poc' / 'scripts' / 'refresh_real_poc_status.py'
RUN_REAL_POC_SCRIPT = WORKSPACE / 'skills' / 'loop9-real-poc' / 'scripts' / 'run_loop9_real_poc.py'
AUDIT_WRAPPER = SUPER8_ROOT / '.opencode' / '_scripts' / 'loop9_authorized_review.py'

# Minimal stop-bleed denylist for automatic audit dispatch.
# These targets are still allowed for explicit/manual human-invoked wrapper use,
# but the hourly auto-dispatcher must not silently consume them as if they were
# ordinary internal audit candidates.
AUTO_AUDIT_DENYLIST = {
    'pikachu',
    'webgoat',
}

RUN_ID_RE = re.compile(r'^\d{8}-\d{6}-.+')
TARGET_PATH_PATTERNS = [
    re.compile(r'target_repo_path\s*[:：]\s*([^\s`]+)'),
    re.compile(r'审计目标源码根目录[：:]\s*`([^`]+)`'),
    re.compile(r'(/Users/[^\s`]+/targets/[^\s`]+)'),
]
TARGET_NAME_PATTERNS = [
    re.compile(r'target_repo_name\s*[:：]\s*([A-Za-z0-9_.-]+)'),
    re.compile(r'审计目标源码项目名[：:]\s*`([^`]+)`'),
]


@dataclass
class DispatchPlan:
    kind: str
    action: str
    reason: str
    running: bool = False
    current_lock: dict[str, Any] | None = None
    candidate: str | None = None
    candidate_key: str | None = None
    launch_command: list[str] | None = None
    notes: list[str] = field(default_factory=list)
    cooldown: dict[str, Any] | None = None
    meta: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _safe_read_text(path: Path) -> str:
    try:
        return path.read_text(encoding='utf-8', errors='ignore')
    except Exception:
        return ''


def _read_json(path: Path) -> dict[str, Any] | None:
    try:
        return json.loads(path.read_text(encoding='utf-8'))
    except Exception:
        return None


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as fh:
        for chunk in iter(lambda: fh.read(65536), b''):
            h.update(chunk)
    return h.hexdigest()


def _sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode('utf-8')).hexdigest()


def _pid_is_alive(pid: Any) -> bool:
    try:
        pid_int = int(pid)
    except (TypeError, ValueError):
        return False
    if pid_int <= 0:
        return False
    try:
        os.kill(pid_int, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    except OSError:
        return False
    return True


def _auto_clear_dead_publish_lock() -> tuple[dict[str, Any] | None, list[str]]:
    lock = current_lock('publish')
    if not lock or lock.get('stale'):
        return lock, []
    if _pid_is_alive(lock.get('pid')):
        return {**lock, 'running': True}, []

    pid = lock.get('pid')
    token = lock.get('token')
    note = f'plan-publish-auto-clear-dead-pid:{pid}'
    if token:
        release_lock('publish', token=str(token), status='stale-auto-cleared', note=note)
    else:
        release_lock('publish', status='stale-auto-cleared', note=note)
    return None, [f'stale-auto-cleared-dead-pid:{pid}']


def _rendered_hash_for_doc(doc: dict[str, Any]) -> str | None:
    rendered = doc.get('rendered_markdown')
    if isinstance(rendered, str):
        return _sha256_text(rendered)
    return None


def _is_multipart_doc(doc: dict[str, Any]) -> bool:
    source_parts = doc.get('source_parts')
    return isinstance(source_parts, list) and len(source_parts) > 1


def _latest_version_dir(base: Path, prefix: str) -> Path | None:
    best: tuple[int, Path] | None = None
    if not base.exists():
        return None
    for child in base.iterdir():
        if not child.is_dir():
            continue
        m = re.fullmatch(rf'{re.escape(prefix)}(\d+)', child.name)
        if not m:
            continue
        version = int(m.group(1))
        if best is None or version > best[0]:
            best = (version, child)
    return best[1] if best else None


def _run_dirs() -> list[Path]:
    if not LOOP9_DIR.exists():
        return []
    rows = [p for p in LOOP9_DIR.iterdir() if p.is_dir() and RUN_ID_RE.match(p.name)]
    rows.sort(key=lambda p: p.stat().st_mtime)
    return rows


def _completed_run_dirs() -> list[Path]:
    rows: list[Path] = []
    for run_dir in _run_dirs():
        if _latest_version_dir(run_dir, 'validation_report_v'):
            rows.append(run_dir)
    return rows


def _extract_target_metadata(run_dir: Path) -> dict[str, str]:
    text = _safe_read_text(run_dir / 'original_goal' / 'part01.md')
    target_path = ''
    target_name = ''
    for pattern in TARGET_PATH_PATTERNS:
        m = pattern.search(text)
        if m:
            target_path = m.group(1).strip().strip('`')
            break
    for pattern in TARGET_NAME_PATTERNS:
        m = pattern.search(text)
        if m:
            target_name = m.group(1).strip().strip('`')
            break
    if not target_name and target_path:
        target_name = Path(target_path).name
    return {'target_path': target_path, 'target_name': target_name}


def _slugify(text: str) -> str:
    cleaned = ''.join(ch.lower() if ch.isalnum() else '-' for ch in text.strip())
    while '--' in cleaned:
        cleaned = cleaned.replace('--', '-')
    return cleaned.strip('-')


def _env_handoff_from_dir(env_dir: Path) -> dict[str, Any] | None:
    live_env = env_dir / 'env_result.live.json'
    raw_env = env_dir / 'env_result.json'
    env_path = live_env if live_env.exists() else raw_env
    if not env_path.exists():
        return None
    env_obj = _read_json(env_path)
    if not isinstance(env_obj, dict):
        return None
    live_handoff = env_dir / 'artifacts' / 'dispatcher_handoff.live.json'
    raw_handoff = env_dir / 'artifacts' / 'dispatcher_handoff.json'
    handoff_path = live_handoff if live_handoff.exists() else raw_handoff
    handoff_obj = _read_json(handoff_path) if handoff_path.exists() else {}
    access = env_obj.get('access') or {}
    handoff_access = (handoff_obj or {}).get('access') or {}
    base_url = access.get('base_url') or handoff_access.get('base_url') or env_obj.get('base_url') or (handoff_obj or {}).get('base_url')
    ready = bool(env_obj.get('ready_for_poc') or (handoff_obj or {}).get('ready_for_poc'))
    credentials = env_obj.get('credentials') or (handoff_obj or {}).get('credentials')
    return {
        'env_dir': str(env_dir),
        'env_result_path': str(env_path),
        'dispatcher_handoff_path': str(handoff_path) if handoff_path.exists() else None,
        'base_url': base_url,
        'ready_for_poc': ready,
        'credentials': credentials,
        'env_obj': env_obj,
        'handoff_obj': handoff_obj or {},
    }


def _pid_is_alive(pid: int) -> bool:
    if pid <= 0:
        return False
    try:
        os.kill(pid, 0)
        return True
    except OSError:
        return False


def _tmux_session_is_alive(session_name: str) -> bool:
    session_name = session_name.strip()
    if not session_name:
        return False
    result = subprocess.run(
        ['tmux', 'has-session', '-t', session_name],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
    )
    return result.returncode == 0


def _observe_runtime_is_dead(obs_dir: Path) -> bool:
    pid_text = _safe_read_text(obs_dir / 'process.pid').strip()
    tmux_session = _safe_read_text(obs_dir / 'tmux.session.txt').strip()

    has_runtime_marker = False
    pid_alive = False
    tmux_alive = False

    if pid_text:
        has_runtime_marker = True
        try:
            pid_alive = _pid_is_alive(int(pid_text))
        except ValueError:
            pid_alive = False

    if tmux_session:
        has_runtime_marker = True
        tmux_alive = _tmux_session_is_alive(tmux_session)

    return has_runtime_marker and not pid_alive and not tmux_alive


def _active_observe_dirs(base: Path, max_age_hours: int = 8) -> list[Path]:
    if not base.exists():
        return []
    now = os.path.getmtime(base) if base.exists() else 0
    rows: list[Path] = []
    for obs_dir in base.iterdir():
        if not obs_dir.is_dir():
            continue
        if (obs_dir / 'finished_at.txt').exists():
            continue
        if _observe_runtime_is_dead(obs_dir):
            continue
        age_hours = (now - obs_dir.stat().st_mtime) / 3600 if now else 0
        if age_hours <= max_age_hours:
            rows.append(obs_dir)
    return rows


def _observe_meta(obs_dir: Path) -> dict[str, Any]:
    meta_json = _read_json(obs_dir / 'run.meta.json') or {}
    if meta_json:
        return meta_json
    text = _safe_read_text(obs_dir / 'run.meta')
    meta: dict[str, Any] = {}
    for line in text.splitlines():
        if '=' in line:
            k, v = line.split('=', 1)
            meta[k.strip()] = v.strip()
    return meta


def _active_audit_for_target(target_path: Path) -> Path | None:
    target_path = target_path.resolve()
    for obs_dir in _active_observe_dirs(LOOP9_OBSERVE_DIR):
        meta = _observe_meta(obs_dir)
        meta_target = str(meta.get('target_path') or '')
        if meta_target and Path(meta_target).expanduser().resolve() == target_path:
            return obs_dir
        label = str(meta.get('label') or '')
        if target_path.name and target_path.name in label:
            return obs_dir
    return None


def _active_real_poc_for_run(audit_run_dir: Path) -> Path | None:
    audit_run_dir = audit_run_dir.resolve()
    for obs_dir in _active_observe_dirs(REAL_POC_OBSERVE_DIR):
        meta = _observe_meta(obs_dir)
        linked = str(meta.get('audit_run_dir') or '')
        if linked and Path(linked).expanduser().resolve() == audit_run_dir:
            return obs_dir
    return None


def _latest_real_poc_observe_for_run(audit_run_dir: Path) -> Path | None:
    audit_run_dir = audit_run_dir.resolve()
    rows: list[Path] = []
    if not REAL_POC_OBSERVE_DIR.exists():
        return None
    for obs_dir in REAL_POC_OBSERVE_DIR.iterdir():
        if not obs_dir.is_dir():
            continue
        meta = _observe_meta(obs_dir)
        linked = str(meta.get('audit_run_dir') or '')
        if linked and Path(linked).expanduser().resolve() == audit_run_dir:
            rows.append(obs_dir)
    if not rows:
        return None
    rows.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    return rows[0]


def _cleanup_finished_poc_locks() -> list[str]:
    notes: list[str] = []
    for row in current_locks('poc'):
        token = str(row.get('token') or '')
        candidate = str(row.get('candidate') or '')
        slot = row.get('slot')
        if not token:
            continue
        if row.get('stale'):
            result = release_lock('poc', token=token, status='stale-auto-cleared', note='plan-poc-auto-clear-stale')
            if result.get('ok'):
                notes.append(f'cleared-stale-slot:{slot}:{candidate}')
            continue
        if not candidate:
            continue
        try:
            audit_run_dir = Path(candidate).expanduser().resolve()
        except Exception:
            continue
        if _active_real_poc_for_run(audit_run_dir):
            continue
        latest_obs = _latest_real_poc_observe_for_run(audit_run_dir)
        if not latest_obs:
            continue
        if (latest_obs / 'finished_at.txt').exists() or _observe_runtime_is_dead(latest_obs):
            result = release_lock('poc', token=token, status='finished-auto-cleared', note=f'plan-poc-auto-clear:{latest_obs.name}')
            if result.get('ok'):
                notes.append(f'cleared-finished-slot:{slot}:{candidate}:{latest_obs.name}')
    return notes


def _active_audit_count() -> int:
    return len(_active_observe_dirs(LOOP9_OBSERVE_DIR))


def _active_real_poc_count() -> int:
    return len(_active_observe_dirs(REAL_POC_OBSERVE_DIR))


def _boolish(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    if isinstance(value, str):
        return value.strip().lower() in {'1', 'true', 'yes', 'y', 'passed'}
    return False


def _intish(value: Any, default: int = 0) -> int:
    try:
        if value is None:
            return default
        return int(value)
    except Exception:
        return default


def _shared_real_poc_rounds(run_dir: Path, status: dict[str, Any]) -> dict[str, Any]:
    real_pocs_dir = run_dir / 'real_pocs'
    solution_rounds: list[int] = []
    validation_rounds: list[int] = []
    if real_pocs_dir.is_dir():
        for child in real_pocs_dir.iterdir():
            if not child.is_dir():
                continue
            m_solution = re.fullmatch(r'real_poc_solution_v(\d+)', child.name)
            if m_solution:
                solution_rounds.append(int(m_solution.group(1)))
                continue
            m_validation = re.fullmatch(r'real_poc_validation_report_v(\d+)', child.name)
            if m_validation:
                validation_rounds.append(int(m_validation.group(1)))
                continue
    completed_rounds = sorted(set(solution_rounds) & set(validation_rounds))
    return {
        'solution_rounds': sorted(solution_rounds),
        'validation_rounds': sorted(validation_rounds),
        'completed_rounds': completed_rounds,
        'completed_round_count': len(completed_rounds),
        'latest_completed_round': completed_rounds[-1] if completed_rounds else 0,
    }


def _has_meaningful_shared_pocs(run_dir: Path, status: dict[str, Any]) -> bool:
    real_pocs_dir = run_dir / 'real_pocs'
    if not real_pocs_dir.is_dir():
        return False
    manifest_path = real_pocs_dir / 'manifest.json'
    final_status_path = real_pocs_dir / 'real_poc_final_status.json'
    if not manifest_path.exists() or not final_status_path.exists():
        return False

    rounds = _shared_real_poc_rounds(run_dir, status)
    if rounds.get('completed_round_count', 0) > 0:
        return True

    shared_poc_py_count = _intish(status.get('shared_poc_py_count'))
    if shared_poc_py_count > 0:
        return True

    manifest = status.get('manifest') if isinstance(status.get('manifest'), dict) else {}
    findings_total = _intish(manifest.get('findings_total'))
    all_findings_mapped = _boolish(manifest.get('all_findings_mapped'))
    all_findings_accepted_or_frozen = _boolish(manifest.get('all_findings_accepted_or_frozen'))
    if findings_total == 0 and all_findings_mapped and all_findings_accepted_or_frozen:
        return True

    return False


def _classify_poc_candidate(run_dir: Path, status: dict[str, Any]) -> tuple[str, str, dict[str, Any]]:
    workflow_completion = str(status.get('workflow_completion') or 'unknown')
    latest_round_validation_status = str(status.get('latest_round_validation_status') or '')
    latest_round = _intish(status.get('latest_round'))
    max_iterations = _intish(status.get('max_iterations'))
    min_iterations_satisfied = _boolish(status.get('min_iterations_satisfied'))
    latest_round_freeze_signal = _boolish(status.get('latest_round_freeze_signal'))
    manifest = status.get('manifest') if isinstance(status.get('manifest'), dict) else {}
    all_findings_mapped = _boolish(manifest.get('all_findings_mapped'))
    all_findings_accepted_or_frozen = _boolish(manifest.get('all_findings_accepted_or_frozen'))
    shared_poc_py_count = _intish(status.get('shared_poc_py_count'))
    shared_rounds = _shared_real_poc_rounds(run_dir, status)

    meta = {
        'workflow_completion': workflow_completion,
        'latest_round_validation_status': latest_round_validation_status or None,
        'latest_round': latest_round,
        'max_iterations': max_iterations,
        'min_iterations_satisfied': min_iterations_satisfied,
        'latest_round_freeze_signal': latest_round_freeze_signal,
        'all_findings_mapped': all_findings_mapped,
        'all_findings_accepted_or_frozen': all_findings_accepted_or_frozen,
        'shared_poc_py_count': shared_poc_py_count,
        'shared_completed_round_count': shared_rounds.get('completed_round_count', 0),
        'shared_latest_completed_round': shared_rounds.get('latest_completed_round', 0),
    }

    if workflow_completion == 'passed':
        return 'already_success', 'workflow-already-passed', meta

    if not _has_meaningful_shared_pocs(run_dir, status):
        return 'no_poc_yet', 'shared-real-poc-not-materialized', meta

    terminal_failure_reasons: list[str] = []
    if max_iterations > 0 and latest_round >= max_iterations:
        terminal_failure_reasons.append('max-iterations-reached')
    if min_iterations_satisfied and all_findings_mapped and all_findings_accepted_or_frozen and latest_round_validation_status.upper() != 'PASSED':
        terminal_failure_reasons.append('stop-conditions-met-but-final-not-success')
    if latest_round_freeze_signal and latest_round_validation_status.upper() != 'PASSED':
        terminal_failure_reasons.append('freeze-signal-without-final-success')

    if terminal_failure_reasons:
        meta['terminal_failure_reasons'] = terminal_failure_reasons
        return 'reached_stop_condition_but_not_success', ','.join(terminal_failure_reasons), meta

    return 'aborted_before_stop_condition', workflow_completion or 'workflow-incomplete', meta


def _import_real_poc_status_module():
    spec = importlib.util.spec_from_file_location('refresh_real_poc_status', REAL_POC_STATUS_SCRIPT)
    if not spec or not spec.loader:
        raise RuntimeError(f'Unable to load {REAL_POC_STATUS_SCRIPT}')
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _publish_plan(run_dir: Path) -> dict[str, Any]:
    result = subprocess.run(
        ['python3', str(PUBLISH_PLAN_SCRIPT), str(run_dir)],
        check=True,
        capture_output=True,
        text=True,
    )
    return json.loads(result.stdout)


def _publish_sync_needed(plan: dict[str, Any]) -> tuple[bool, list[str]]:
    state = _read_json(PUBLISHER_STATE) or {}
    project = plan.get('project', {}) if isinstance(plan, dict) else {}
    slug = str(project.get('slug') or '')
    docs = plan.get('docs', []) if isinstance(plan, dict) else []
    project_state = ((state.get('projects') or {}).get(slug) or {}) if slug else {}
    artifacts_state = project_state.get('artifacts') or {}
    reasons: list[str] = []
    actionable_reasons: list[str] = []
    if not slug or not project_state:
        return True, ['project-not-in-publisher-state']
    for doc in docs:
        doc_key = doc.get('doc_key')
        source_markdown = doc.get('source_markdown')
        artifact_state = artifacts_state.get(doc_key) if doc_key else None
        if not artifact_state:
            reason = f'missing-artifact:{doc_key}'
            reasons.append(reason)
            actionable_reasons.append(reason)
            continue
        if artifact_state.get('source_markdown') != source_markdown:
            reason = f'source-changed:{doc_key}'
            reasons.append(reason)
            actionable_reasons.append(reason)
            continue
        last_hash = artifact_state.get('last_content_hash')
        if not (last_hash and source_markdown and Path(source_markdown).exists()):
            continue
        current_raw_hash = _sha256(Path(source_markdown))
        if _is_multipart_doc(doc):
            current_rendered_hash = _rendered_hash_for_doc(doc)
            if current_rendered_hash and last_hash == current_rendered_hash:
                continue
            if last_hash == current_raw_hash:
                reasons.append(f'hash-semantics-anomaly:{doc_key}:multipart-state-uses-raw-first-part')
                continue
            reasons.append(f'hash-semantics-anomaly:{doc_key}:multipart-state-mismatch')
            continue
        if current_raw_hash != last_hash:
            reason = f'content-changed:{doc_key}'
            reasons.append(reason)
            actionable_reasons.append(reason)
    return (len(actionable_reasons) > 0, reasons or ['already-synced'])


def _publish_candidate_screen(run_dir: Path) -> tuple[bool, list[str], dict[str, Any]]:
    notes: list[str] = []
    identity = classify_loop9_run(run_dir)
    meta: dict[str, Any] = {
        'run_kind': identity.get('run_kind'),
        'root_audit_run_dir': identity.get('root_audit_run_dir'),
        'identity_source': identity.get('source'),
        'identity_observe_dir': identity.get('observe_dir'),
    }
    run_name_lc = run_dir.name.lower()
    rp_like = ('-rp' in run_name_lc) or ('-rpoc' in run_name_lc)
    real_pocs_dir = run_dir / 'real_pocs'
    has_real_pocs = real_pocs_dir.is_dir()
    manifest_path = real_pocs_dir / 'manifest.json'
    final_status_path = real_pocs_dir / 'real_poc_final_status.json'
    manifest = _read_json(manifest_path) if manifest_path.exists() else None
    final_status = _read_json(final_status_path) if final_status_path.exists() else None

    shared_poc_py_count = final_status.get('shared_poc_py_count') if isinstance(final_status, dict) else None
    workflow_completion = str(final_status.get('workflow_completion') or '') if isinstance(final_status, dict) else ''

    meta.update(
        {
            'rp_like': rp_like,
            'has_real_pocs': has_real_pocs,
            'manifest_exists': manifest_path.exists(),
            'final_status_exists': final_status_path.exists(),
            'shared_poc_py_count': shared_poc_py_count,
            'workflow_completion': workflow_completion or None,
        }
    )

    run_kind = str(identity.get('run_kind') or '')
    if run_kind and run_kind != 'audit-root':
        notes.append(f'screened-out:not-audit-root:{run_kind}')
    if rp_like:
        notes.append('screened-out:rp-like-run')
    if not has_real_pocs:
        notes.append('screened-out:no-shared-real-pocs')
    if has_real_pocs and not manifest_path.exists():
        notes.append('screened-out:missing-real-poc-manifest')
    if has_real_pocs and not final_status_path.exists():
        notes.append('screened-out:missing-real-poc-final-status')
    if has_real_pocs and (shared_poc_py_count is None or int(shared_poc_py_count or 0) <= 0):
        notes.append('screened-out:no-shared-poc-py')
    if has_real_pocs and final_status_path.exists() and workflow_completion != 'passed':
        notes.append(f'screened-out:workflow-not-passed:{workflow_completion or "missing"}')

    eligible = not notes
    return eligible, notes, meta


def _audit_manual_queue_head() -> dict[str, Any] | None:
    item = manual_queue_peek('audit')
    if not item:
        return None
    target_path = str(item.get('targetPath') or '').strip()
    if not target_path:
        return None
    policy = str(item.get('policy') or 'weibu-submission').strip() or 'weibu-submission'
    return {
        **item,
        'targetPath': target_path,
        'policy': policy,
        'note': str(item.get('note') or '').strip(),
        'bypassTargetGate': bool(item.get('bypassTargetGate')),
    }


def _poc_manual_queue_head() -> dict[str, Any] | None:
    item = manual_queue_peek('poc')
    if not item:
        return None
    audit_run_dir = str(item.get('auditRunDir') or '').strip()
    if not audit_run_dir:
        return None
    return {
        **item,
        'auditRunDir': audit_run_dir,
        'note': str(item.get('note') or '').strip(),
    }


def plan_audit_dispatch() -> DispatchPlan:
    active_count = _active_audit_count()
    audit_limit = max_concurrent('audit')
    manual_item = _audit_manual_queue_head()
    base_notes = [f'active_audit_count={active_count}', f'audit_max_concurrent={audit_limit}']
    if manual_item:
        base_notes = [f'manual-queue-head:{manual_item["targetPath"]}'] + base_notes

    guard = check_launch_allowed('audit')
    if not guard.get('ok'):
        return DispatchPlan(
            kind='audit',
            action='skip',
            reason='launch-guard-blocked',
            running=any(row.get('code') == 'slots-full' for row in guard.get('reasons', [])),
            candidate=str(manual_item['targetPath']) if manual_item else None,
            candidate_key=str(manual_item['targetPath']) if manual_item else None,
            notes=base_notes + [row.get('message', '') for row in guard.get('reasons', [])],
            meta={'manual_queue_item': manual_item} if manual_item else {},
        )

    lock = current_lock('audit')
    if lock and not lock.get('stale'):
        return DispatchPlan(kind='audit', action='skip', reason='audit-lock-active', running=True, current_lock=lock, notes=base_notes, meta={'manual_queue_item': manual_item} if manual_item else {})

    if manual_item:
        target = Path(manual_item['targetPath']).expanduser().resolve()
        if not target.exists() or not target.is_dir():
            return DispatchPlan(kind='audit', action='skip', reason='manual-queue-invalid-target', candidate=str(target), candidate_key=str(target), notes=base_notes + ['manual queue target is missing or not a directory'], meta={'manual_queue_item': manual_item})

        active_obs = _active_audit_for_target(target)
        if active_obs:
            return DispatchPlan(kind='audit', action='skip', reason='same-kind-already-running', running=True, candidate=str(target), candidate_key=str(target), notes=base_notes + [f'active observe: {active_obs}'], meta={'manual_queue_item': manual_item})

        cooldown = current_cooldown('audit', str(target))
        if cooldown:
            return DispatchPlan(kind='audit', action='skip', reason='candidate-in-cooldown', candidate=str(target), candidate_key=str(target), cooldown=cooldown, notes=base_notes, meta={'manual_queue_item': manual_item})

        if not manual_item.get('bypassTargetGate'):
            target_gate = check_target_policy(target, manual_item.get('policy') or 'weibu-submission')
            if not target_gate.get('ok'):
                reason_codes = ','.join(str(row.get('code') or 'unknown') for row in target_gate.get('reasons', []))
                return DispatchPlan(kind='audit', action='skip', reason='manual-queue-target-gate-blocked', candidate=str(target), candidate_key=str(target), notes=base_notes + [f'target-gate:{reason_codes}'], meta={'manual_queue_item': manual_item, 'target_gate': target_gate})

        launch = ['python3', str(AUDIT_WRAPPER), '--policy', str(manual_item.get('policy') or 'weibu-submission')]
        if manual_item.get('bypassTargetGate'):
            launch.extend(['--skip-target-gate', '--skip-target-gate-confirm', 'I-understand-and-confirm-target-gate-bypass'])
        launch.append(str(target))
        return DispatchPlan(kind='audit', action='launch', reason='manual-queue-target', candidate=str(target), candidate_key=str(target), launch_command=launch, notes=base_notes, meta={'manual_queue_item': manual_item})

    targets = [p for p in TARGETS_DIR.iterdir() if p.is_dir() and not p.name.startswith('.')]
    targets.sort(key=lambda p: p.name.lower())

    latest_by_target: dict[str, Path] = {}
    for run_dir in _run_dirs():
        meta = _extract_target_metadata(run_dir)
        target_path = meta.get('target_path') or ''
        target_name = meta.get('target_name') or ''
        key = target_path or target_name
        if key:
            latest_by_target[key] = run_dir

    skipped_denylisted: list[str] = []
    skipped_target_gate: list[str] = []
    for target in targets:
        if target.name.strip().lower() in AUTO_AUDIT_DENYLIST:
            skipped_denylisted.append(str(target))
            continue

        active_obs = _active_audit_for_target(target)
        if active_obs:
            return DispatchPlan(kind='audit', action='skip', reason='same-kind-already-running', running=True, candidate=str(target), notes=[f'active observe: {active_obs}'])

        target_gate = check_target_policy(target, 'weibu-submission')
        if not target_gate.get('ok'):
            reason_codes = ','.join(str(row.get('code') or 'unknown') for row in target_gate.get('reasons', []))
            skipped_target_gate.append(f'{target}:blocked-by-target-gate:{reason_codes}')
            continue

        cooldown = current_cooldown('audit', target.name)
        if cooldown:
            return DispatchPlan(kind='audit', action='skip', reason='candidate-in-cooldown', candidate=str(target), candidate_key=target.name, cooldown=cooldown)

        latest_run = latest_by_target.get(str(target.resolve())) or latest_by_target.get(target.name)
        if latest_run and _latest_version_dir(latest_run, 'validation_report_v'):
            continue
        launch = ['python3', str(AUDIT_WRAPPER), str(target)]
        return DispatchPlan(kind='audit', action='launch', reason='eligible-target-found', candidate=str(target), candidate_key=target.name, launch_command=launch, meta={'latest_run': str(latest_run) if latest_run else None, 'skipped_denylisted': skipped_denylisted, 'skipped_target_gate': skipped_target_gate})

    if skipped_denylisted or skipped_target_gate:
        return DispatchPlan(kind='audit', action='skip', reason='no-eligible-target', notes=[f'denylisted:{path}' for path in skipped_denylisted] + [f'target-gate:{path}' for path in skipped_target_gate])

    return DispatchPlan(kind='audit', action='skip', reason='no-eligible-target')


def plan_poc_dispatch() -> DispatchPlan:
    cleanup_notes = _cleanup_finished_poc_locks()
    active_count = _active_real_poc_count()
    poc_limit = max_concurrent('poc')
    manual_item = _poc_manual_queue_head()
    base_notes = cleanup_notes + [f'active_real_poc_count={active_count}', f'poc_max_concurrent={poc_limit}']
    if manual_item:
        base_notes = [f'manual-queue-head:{manual_item["auditRunDir"]}'] + base_notes

    guard = check_launch_allowed('poc')
    if not guard.get('ok'):
        return DispatchPlan(
            kind='poc',
            action='skip',
            reason='launch-guard-blocked',
            running=any(row.get('code') == 'slots-full' for row in guard.get('reasons', [])),
            candidate=str(manual_item['auditRunDir']) if manual_item else None,
            candidate_key=str(manual_item['auditRunDir']) if manual_item else None,
            notes=base_notes + [row.get('message', '') for row in guard.get('reasons', [])],
            meta={'manual_queue_item': manual_item} if manual_item else {},
        )

    status_mod = _import_real_poc_status_module()
    bucket_order = [
        'no_poc_yet',
        'aborted_before_stop_condition',
        'reached_stop_condition_but_not_success',
    ]
    bucket_reason = {
        'no_poc_yet': 'no-poc-yet',
        'aborted_before_stop_condition': 'resume-aborted-before-stop',
        'reached_stop_condition_but_not_success': 'stop-reached-but-final-not-success',
    }
    bucket_notes: dict[str, list[str]] = {name: [] for name in bucket_order}
    bucket_candidates: dict[str, list[tuple[Path, dict[str, Any], dict[str, Any], dict[str, Any]]]] = {name: [] for name in bucket_order}
    skipped: list[str] = base_notes.copy()

    if manual_item:
        run_dir = Path(manual_item['auditRunDir']).expanduser().resolve()
        if not run_dir.exists() or not run_dir.is_dir():
            return DispatchPlan(kind='poc', action='skip', reason='manual-queue-invalid-run', candidate=str(run_dir), candidate_key=str(run_dir), notes=base_notes + ['manual queue auditRunDir is missing or not a directory'], meta={'manual_queue_item': manual_item})
        identity = classify_loop9_run(run_dir)
        run_kind = str(identity.get('run_kind') or '')
        if run_kind != 'audit-root':
            return DispatchPlan(kind='poc', action='skip', reason='manual-queue-not-audit-root', candidate=str(run_dir), candidate_key=run_dir.name, notes=base_notes + [f'run_kind={run_kind or "missing"}'], meta={'manual_queue_item': manual_item, 'identity': identity})
        active_obs = _active_real_poc_for_run(run_dir)
        if active_obs:
            return DispatchPlan(kind='poc', action='skip', reason='same-kind-already-running', running=True, candidate=str(run_dir), candidate_key=run_dir.name, notes=base_notes + [f'active observe: {active_obs}'], meta={'manual_queue_item': manual_item})
        cooldown = current_cooldown('poc', run_dir.name)
        if cooldown:
            return DispatchPlan(kind='poc', action='skip', reason='candidate-in-cooldown', candidate=str(run_dir), candidate_key=run_dir.name, cooldown=cooldown, notes=base_notes, meta={'manual_queue_item': manual_item})
        try:
            status = status_mod.build_status(run_dir)
        except Exception as exc:
            return DispatchPlan(kind='poc', action='skip', reason='status-refresh-failed', candidate=str(run_dir), candidate_key=run_dir.name, notes=base_notes + [str(exc)], meta={'manual_queue_item': manual_item})
        bucket, detail_reason, classify_meta = _classify_poc_candidate(run_dir, status)
        if bucket == 'already_success':
            return DispatchPlan(kind='poc', action='skip', reason='manual-queue-already-success', candidate=str(run_dir), candidate_key=run_dir.name, notes=base_notes + [detail_reason], meta={'manual_queue_item': manual_item, 'classification': classify_meta, 'workflow_completion': status.get('workflow_completion'), 'workflow_reason': status.get('workflow_completion_reason')})
        if bucket not in bucket_reason:
            return DispatchPlan(kind='poc', action='skip', reason='manual-queue-unclassified', candidate=str(run_dir), candidate_key=run_dir.name, notes=base_notes + [detail_reason], meta={'manual_queue_item': manual_item, 'classification': classify_meta, 'workflow_completion': status.get('workflow_completion'), 'workflow_reason': status.get('workflow_completion_reason')})
        launch = ['python3', str(RUN_REAL_POC_SCRIPT), str(run_dir)]
        return DispatchPlan(
            kind='poc',
            action='launch',
            reason='manual-queue-target',
            candidate=str(run_dir),
            candidate_key=run_dir.name,
            launch_command=launch,
            notes=base_notes + [detail_reason],
            meta={
                'manual_queue_item': manual_item,
                'bucket': bucket,
                'bucket_reason': bucket_reason[bucket],
                'classification': classify_meta,
                'workflow_completion': status.get('workflow_completion'),
                'workflow_reason': status.get('workflow_completion_reason'),
                'run_kind': identity.get('run_kind'),
                'identity_source': identity.get('source'),
                'active_real_poc_count': active_count,
                'poc_max_concurrent': poc_limit,
            },
        )

    for run_dir in _completed_run_dirs():
        identity = classify_loop9_run(run_dir)
        run_kind = str(identity.get('run_kind') or '')
        if run_kind != 'audit-root':
            skipped.append(f'{run_dir.name}:skip-not-audit-root:{run_kind or "missing"}')
            continue
        active_obs = _active_real_poc_for_run(run_dir)
        if active_obs:
            skipped.append(f'{run_dir.name}:skip-active-real-poc:{active_obs}')
            continue
        cooldown = current_cooldown('poc', run_dir.name)
        if cooldown:
            skipped.append(f'{run_dir.name}:skip-cooldown')
            continue
        try:
            status = status_mod.build_status(run_dir)
        except Exception as exc:
            return DispatchPlan(kind='poc', action='skip', reason='status-refresh-failed', candidate=str(run_dir), notes=[str(exc)])

        bucket, detail_reason, classify_meta = _classify_poc_candidate(run_dir, status)
        if bucket == 'already_success':
            skipped.append(f'{run_dir.name}:skip-already-success')
            continue
        if bucket in bucket_candidates:
            bucket_candidates[bucket].append((run_dir, status, identity, classify_meta))
            bucket_notes[bucket].append(f'{run_dir.name}:{detail_reason}')
        else:
            skipped.append(f'{run_dir.name}:skip-unclassified:{detail_reason}')

    def _bucket_sort_key(item: tuple[Path, dict[str, Any], dict[str, Any], dict[str, Any]]) -> tuple[int, int, float, str]:
        run_dir, status, identity, classify_meta = item
        shared_completed_round_count = _intish(classify_meta.get('shared_completed_round_count'))
        shared_latest_completed_round = _intish(classify_meta.get('shared_latest_completed_round'))
        if shared_completed_round_count <= 0:
            return (0, 0, run_dir.stat().st_mtime, run_dir.name)
        return (1, shared_latest_completed_round or shared_completed_round_count, run_dir.stat().st_mtime, run_dir.name)

    for bucket in bucket_order:
        candidates = bucket_candidates[bucket]
        if not candidates:
            continue
        candidates = sorted(candidates, key=_bucket_sort_key)
        run_dir, status, identity, classify_meta = candidates[0]
        launch = ['python3', str(RUN_REAL_POC_SCRIPT), str(run_dir)]
        notes = bucket_notes[bucket] + skipped
        return DispatchPlan(
            kind='poc',
            action='launch',
            reason=bucket_reason[bucket],
            candidate=str(run_dir),
            candidate_key=run_dir.name,
            launch_command=launch,
            notes=notes,
            meta={
                'bucket': bucket,
                'bucket_reason': bucket_reason[bucket],
                'classification': classify_meta,
                'workflow_completion': status.get('workflow_completion'),
                'workflow_reason': status.get('workflow_completion_reason'),
                'run_kind': identity.get('run_kind'),
                'identity_source': identity.get('source'),
                'active_real_poc_count': active_count,
                'poc_max_concurrent': poc_limit,
                'bucket_counts': {name: len(items) for name, items in bucket_candidates.items()},
            },
        )

    return DispatchPlan(kind='poc', action='skip', reason='no-eligible-audit-run', notes=skipped)


def plan_publish_dispatch() -> DispatchPlan:
    lock, lock_notes = _auto_clear_dead_publish_lock()
    if lock and not lock.get('stale'):
        return DispatchPlan(
            kind='publish',
            action='skip',
            reason='publish-lock-active',
            running=bool(lock.get('running')),
            current_lock=lock,
            notes=lock_notes,
        )

    deferred_low_confidence: list[str] = []
    screened_out: list[str] = []
    anomaly_notes: list[str] = list(lock_notes)
    rows = list(reversed(_completed_run_dirs()))
    for run_dir in rows:
        eligible, screen_notes, screen_meta = _publish_candidate_screen(run_dir)
        if not eligible:
            screened_out.extend(f'{run_dir.name}:{note}' for note in screen_notes)
            continue
        try:
            plan = _publish_plan(run_dir)
        except Exception as exc:
            return DispatchPlan(kind='publish', action='skip', reason='publish-plan-failed', candidate=str(run_dir), notes=[str(exc)])
        candidate_key = str(plan.get('resolved_root') or run_dir.name)
        cooldown = current_cooldown('publish', candidate_key)
        if cooldown:
            return DispatchPlan(kind='publish', action='skip', reason='candidate-in-cooldown', candidate=str(run_dir), candidate_key=candidate_key, cooldown=cooldown, notes=screened_out + anomaly_notes)
        project = plan.get('project', {}) if isinstance(plan, dict) else {}
        confidence = str(project.get('confidence') or '')
        if confidence == 'low':
            deferred_low_confidence.append(str(run_dir))
            continue
        needed, reasons = _publish_sync_needed(plan)
        if not needed:
            anomaly_notes.extend(f'{run_dir.name}:{reason}' for reason in reasons if reason.startswith('hash-semantics-anomaly:'))
            continue
        return DispatchPlan(
            kind='publish',
            action='publish',
            reason='publish-sync-needed',
            candidate=str(run_dir),
            candidate_key=candidate_key,
            notes=screened_out + anomaly_notes + reasons,
            meta={'project': project, 'plan': plan, 'deferred_low_confidence': deferred_low_confidence, 'candidate_screen': screen_meta},
        )

    notes = [f'deferred-low-confidence:{path}' for path in deferred_low_confidence] + screened_out + anomaly_notes
    return DispatchPlan(kind='publish', action='skip', reason='no-eligible-publish-source', notes=notes)


def plan_dispatch(kind: str, *, prefer_run_dir: str | None = None, sticky_recovery: bool = False) -> DispatchPlan:
    kind = kind.strip().lower()
    if kind == 'audit':
        return plan_audit_dispatch()
    if kind in {'poc', 'real-poc', 'real_poc'}:
        return plan_poc_dispatch()
    if kind == 'publish':
        return plan_publish_dispatch()
    raise ValueError(f'Unsupported dispatch kind: {kind}')
