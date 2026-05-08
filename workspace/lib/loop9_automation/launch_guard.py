from __future__ import annotations

import re
import shutil
import subprocess
from pathlib import Path
from typing import Any

from .config import CONFIG_PATH, launch_guard_config, max_concurrent
from .docker_cleanup import maybe_run_docker_cleanup

WORKSPACE = Path('~/.openclaw/workspace').expanduser()
SUPER8_ROOT = WORKSPACE / 'Super8'
LOOP9_OBSERVE_DIR = SUPER8_ROOT / 'temp' / 'loop9-observe'
REAL_POC_OBSERVE_DIR = SUPER8_ROOT / 'temp' / 'loop9-real-poc-observe'

SWAP_RE = re.compile(r'used\s*=\s*([0-9.]+)([MG])', re.I)
OPENCODE_PROMPT_RE = re.compile(r'((?:~|/[^\s\'\"]+)(?:/[^\s\'\"]+)*/(?:loop9-prompts|loop9-real-poc-prompts)/[^\s\'\"]+\.md)')


def _pid_is_alive(pid: int) -> bool:
    if pid <= 0:
        return False
    try:
        import os
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


def _safe_read_text(path: Path) -> str:
    try:
        return path.read_text(encoding='utf-8', errors='ignore')
    except Exception:
        return ''


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
    import os
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


def _active_count(kind: str) -> int:
    if kind == 'audit':
        return len(_active_observe_dirs(LOOP9_OBSERVE_DIR))
    if kind == 'poc':
        return len(_active_observe_dirs(REAL_POC_OBSERVE_DIR))
    return 0


def _parse_swap_used_mib() -> float | None:
    sysctl_bin = shutil.which('sysctl') or '/usr/sbin/sysctl'
    try:
        result = subprocess.run([sysctl_bin, 'vm.swapusage'], capture_output=True, text=True, check=False)
    except FileNotFoundError:
        return None
    if result.returncode != 0:
        return None
    match = SWAP_RE.search(result.stdout)
    if not match:
        return None
    value = float(match.group(1))
    unit = match.group(2).upper()
    if unit == 'G':
        return value * 1024
    return value


def _disk_avail_gib(path: Path) -> float | None:
    try:
        usage = shutil.disk_usage(path)
    except Exception:
        return None
    return usage.free / 1024 / 1024 / 1024


def _process_table() -> list[dict[str, Any]]:
    result = subprocess.run(
        ['ps', '-axo', 'pid=,rss=,comm=,args='],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        return []

    rows: list[dict[str, Any]] = []
    for line in result.stdout.splitlines():
        raw = line.strip()
        if not raw:
            continue
        parts = raw.split(None, 3)
        if len(parts) < 4:
            continue
        pid_raw, rss_raw, comm, args = parts
        try:
            pid = int(pid_raw)
            rss_kib = int(rss_raw)
        except Exception:
            continue
        rows.append({
            'pid': pid,
            'rssMiB': rss_kib / 1024,
            'comm': comm,
            'args': args,
        })
    return rows


def _is_primary_loop9_opencode(row: dict[str, Any]) -> bool:
    comm = Path(str(row.get('comm') or '')).name
    args = str(row.get('args') or '')
    if comm == 'script':
        return False
    if '--print-logs' not in args or '--command loop9' not in args:
        return False
    return ('/opt/homebrew/bin/opencode run ' in args) or ('/.opencode run ' in args) or (' opencode run ' in args)


def _is_auxiliary_opencode(row: dict[str, Any]) -> bool:
    comm = Path(str(row.get('comm') or '')).name
    args = str(row.get('args') or '')
    if comm == 'script':
        return False
    if not ('/opt/homebrew/bin/opencode ' in args or '/.opencode ' in args or ' opencode ' in args):
        return False
    if _is_primary_loop9_opencode(row):
        return False
    return True


def _loop9_lane_key(row: dict[str, Any]) -> str:
    args = str(row.get('args') or '')
    prompt_match = OPENCODE_PROMPT_RE.search(args)
    if prompt_match:
        return prompt_match.group(1)

    normalized = args
    for prefix in [
        'node /opt/homebrew/bin/opencode run ',
        '/opt/homebrew/lib/node_modules/opencode-ai/bin/.opencode run ',
        'opencode run ',
    ]:
        if normalized.startswith(prefix):
            normalized = normalized[len(prefix):]
            break
    return normalized


def _group_process_metrics(rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    opencode = [row for row in rows if _is_primary_loop9_opencode(row)]
    opencode_auxiliary = [row for row in rows if _is_auxiliary_opencode(row)]
    docker_backend = [row for row in rows if 'com.docker.backend' in row['comm'] or 'com.docker.backend' in row['args']]
    virtualization = [row for row in rows if 'com.apple.Virtualization.VirtualMachine' in row['comm'] or 'com.apple.Virtualization.VirtualMachine' in row['args']]

    def summarize(name: str, subset: list[dict[str, Any]], *, lane_aware: bool = False) -> dict[str, Any]:
        lane_count = None
        lane_top = None
        if lane_aware:
            lane_buckets: dict[str, dict[str, Any]] = {}
            for row in subset:
                key = _loop9_lane_key(row)
                bucket = lane_buckets.setdefault(key, {'rssMiB': 0.0, 'processCount': 0})
                bucket['rssMiB'] += float(row['rssMiB'])
                bucket['processCount'] += 1
            lane_count = len(lane_buckets)
            lane_top = [
                {
                    'laneKey': key,
                    'rssMiB': round(info['rssMiB'], 2),
                    'processCount': info['processCount'],
                }
                for key, info in sorted(lane_buckets.items(), key=lambda item: item[1]['rssMiB'], reverse=True)[:5]
            ]
        payload = {
            'name': name,
            'count': lane_count if lane_aware else len(subset),
            'processCount': len(subset),
            'rssMiB': round(sum(row['rssMiB'] for row in subset), 2),
            'top': [
                {
                    'pid': row['pid'],
                    'rssMiB': round(row['rssMiB'], 2),
                    'comm': row['comm'],
                }
                for row in sorted(subset, key=lambda item: item['rssMiB'], reverse=True)[:5]
            ],
        }
        if lane_aware:
            payload['laneTop'] = lane_top or []
        return payload

    return {
        'opencode': summarize('opencode', opencode, lane_aware=True),
        'opencodeAuxiliary': summarize('opencodeAuxiliary', opencode_auxiliary),
        'dockerBackend': summarize('dockerBackend', docker_backend),
        'virtualization': summarize('virtualization', virtualization),
    }


def build_launch_snapshot(kind: str) -> dict[str, Any]:
    rows = _process_table()
    grouped = _group_process_metrics(rows)
    data_path = Path('/System/Volumes/Data') if Path('/System/Volumes/Data').exists() else Path('/')
    root_path = Path('/')
    return {
        'kind': kind,
        'configPath': str(CONFIG_PATH),
        'maxConcurrent': max_concurrent(kind),
        'activeCount': _active_count(kind),
        'swapUsedMiB': _parse_swap_used_mib(),
        'dataAvailGiB': _disk_avail_gib(data_path),
        'rootAvailGiB': _disk_avail_gib(root_path),
        'opencode': grouped['opencode'],
        'opencodeAuxiliary': grouped['opencodeAuxiliary'],
        'dockerBackend': grouped['dockerBackend'],
        'virtualization': grouped['virtualization'],
    }


def check_launch_allowed(kind: str) -> dict[str, Any]:
    snapshot = build_launch_snapshot(kind)
    guard = launch_guard_config()
    reasons: list[dict[str, Any]] = []

    active_count = int(snapshot['activeCount'])
    max_slots = int(snapshot['maxConcurrent'])
    if active_count >= max_slots:
        reasons.append({
            'code': 'slots-full',
            'message': f'active_{kind}_count={active_count} >= maxConcurrent={max_slots}',
        })

    cleanup_result: dict[str, Any] | None = None
    if guard.get('enabled', True):
        data_avail = snapshot.get('dataAvailGiB')
        root_avail = snapshot.get('rootAvailGiB')
        disk_low = (
            (isinstance(data_avail, (int, float)) and float(guard.get('dataAvailGiBMin', 0)) > 0 and data_avail <= float(guard['dataAvailGiBMin']))
            or (isinstance(root_avail, (int, float)) and float(guard.get('rootAvailGiBMin', 0)) > 0 and root_avail <= float(guard['rootAvailGiBMin']))
        )
        if disk_low:
            cleanup_result = maybe_run_docker_cleanup(data_avail_gib=data_avail, root_avail_gib=root_avail)
            if cleanup_result.get('attempted'):
                snapshot = build_launch_snapshot(kind)
                data_avail = snapshot.get('dataAvailGiB')
                root_avail = snapshot.get('rootAvailGiB')

        swap_used = snapshot.get('swapUsedMiB')
        if isinstance(swap_used, (int, float)) and float(guard.get('swapUsedMiBMax', 0)) > 0 and swap_used >= float(guard['swapUsedMiBMax']):
            reasons.append({
                'code': 'swap-too-high',
                'message': f'swapUsedMiB={swap_used:.2f} >= limit={float(guard["swapUsedMiBMax"]):.2f}',
            })

        if isinstance(data_avail, (int, float)) and float(guard.get('dataAvailGiBMin', 0)) > 0 and data_avail <= float(guard['dataAvailGiBMin']):
            reasons.append({
                'code': 'data-disk-too-low',
                'message': f'dataAvailGiB={data_avail:.2f} <= minimum={float(guard["dataAvailGiBMin"]):.2f}',
            })

        if isinstance(root_avail, (int, float)) and float(guard.get('rootAvailGiBMin', 0)) > 0 and root_avail <= float(guard['rootAvailGiBMin']):
            reasons.append({
                'code': 'root-disk-too-low',
                'message': f'rootAvailGiB={root_avail:.2f} <= minimum={float(guard["rootAvailGiBMin"]):.2f}',
            })

        opencode = snapshot['opencode']
        opencode_process_count = int(opencode.get('processCount') or 0)
        if int(guard.get('activeOpencodeCountMax', 0)) > 0 and opencode_process_count >= int(guard['activeOpencodeCountMax']):
            reasons.append({
                'code': 'opencode-count-too-high',
                'message': f'activeOpencodeProcessCount={opencode_process_count} >= limit={int(guard["activeOpencodeCountMax"])}',
            })
        if float(guard.get('activeOpencodeRssMiBMax', 0)) > 0 and float(opencode['rssMiB']) >= float(guard['activeOpencodeRssMiBMax']):
            reasons.append({
                'code': 'opencode-rss-too-high',
                'message': f'activeOpencodeRssMiB={float(opencode["rssMiB"]):.2f} >= limit={float(guard["activeOpencodeRssMiBMax"]):.2f}',
            })

        virtualization = snapshot['virtualization']
        if float(guard.get('virtualizationRssMiBMax', 0)) > 0 and float(virtualization['rssMiB']) >= float(guard['virtualizationRssMiBMax']):
            reasons.append({
                'code': 'virtualization-rss-too-high',
                'message': f'virtualizationRssMiB={float(virtualization["rssMiB"]):.2f} >= limit={float(guard["virtualizationRssMiBMax"]):.2f}',
            })

    return {
        'ok': len(reasons) == 0,
        'kind': kind,
        'snapshot': snapshot,
        'guard': guard,
        'dockerCleanup': cleanup_result,
        'reasons': reasons,
    }


def format_guard_block(result: dict[str, Any]) -> str:
    kind = result.get('kind') or 'unknown'
    lines = [
        f'[loop9-guard] Launch blocked for kind={kind}',
        f'[loop9-guard] Config: {result.get("snapshot", {}).get("configPath")}',
    ]
    for row in result.get('reasons', []):
        lines.append(f'- {row.get("code")}: {row.get("message")}')
    snap = result.get('snapshot', {})
    cleanup = result.get('dockerCleanup') or {}
    lines.extend([
        f'- activeCount={snap.get("activeCount")} / maxConcurrent={snap.get("maxConcurrent")}',
        f'- swapUsedMiB={snap.get("swapUsedMiB")}',
        f'- dataAvailGiB={snap.get("dataAvailGiB")}',
        f'- rootAvailGiB={snap.get("rootAvailGiB")}',
        f'- activeOpencodeCount={snap.get("opencode", {}).get("count")}',
        f'- activeOpencodeProcessCount={snap.get("opencode", {}).get("processCount")}',
        f'- activeOpencodeRssMiB={snap.get("opencode", {}).get("rssMiB")}',
        f'- virtualizationRssMiB={snap.get("virtualization", {}).get("rssMiB")}',
    ])
    if cleanup:
        lines.append(f'- dockerCleanup.status={cleanup.get("status")}')
        if cleanup.get('notes'):
            for note in cleanup.get('notes')[:6]:
                lines.append(f'  - {note}')
    lines.append('Edit config/loop9-dispatch.json if you want to adjust the limits.')
    return '\n'.join(lines)
