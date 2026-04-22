#!/usr/bin/env python3
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any


def _read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding='utf-8', errors='ignore'))
    except Exception:
        return {}


def _read_text(path: Path) -> str | None:
    if not path.exists():
        return None
    return path.read_text(encoding='utf-8', errors='ignore').strip()


def _tail_lines(path: Path, limit: int = 20) -> list[str]:
    if not path.exists():
        return []
    lines = path.read_text(encoding='utf-8', errors='ignore').splitlines()
    return lines[-limit:]


def _parse_meta(path: Path) -> dict[str, str]:
    data: dict[str, str] = {}
    if not path.exists():
        return data
    for raw in path.read_text(encoding='utf-8', errors='ignore').splitlines():
        if '=' not in raw:
            continue
        key, value = raw.split('=', 1)
        data[key.strip()] = value.strip()
    return data




def _tmux_session_alive(session_name: str | None) -> bool | None:
    if not session_name:
        return None
    import subprocess
    res = subprocess.run(['tmux', 'has-session', '-t', session_name], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return res.returncode == 0

def _pid_alive(pid_text: str | None) -> bool | None:
    if not pid_text:
        return None
    try:
        pid = int(pid_text)
    except ValueError:
        return None
    try:
        os.kill(pid, 0)
    except OSError:
        return False
    return True


def inspect_observe_dir(observe_dir: str | Path) -> dict[str, Any]:
    obs = Path(observe_dir).expanduser().resolve()
    if not obs.exists() or not obs.is_dir():
        raise FileNotFoundError(f'Observe dir not found: {obs}')

    run_meta = _read_json(obs / 'run.meta.json') or _parse_meta(obs / 'run.meta')
    launch_summary = _read_json(obs / 'launch.summary.json') or _parse_meta(obs / 'launch.summary.txt')
    exit_code = _read_text(obs / 'opencode.exit_code')
    session_id = _read_text(obs / 'session.id')
    started_at = _read_text(obs / 'started_at.txt')
    finished_at = _read_text(obs / 'finished_at.txt')
    tmux_session = _read_text(obs / 'tmux.session.txt')
    tmux_attach = _read_text(obs / 'tmux.attach.txt')
    clean_log = obs / 'opencode.clean.log'
    typescript_log = obs / 'opencode.typescript.log'
    summary_json = obs / 'observe.summary.json'
    observe_summary = {}
    if summary_json.exists():
        try:
            observe_summary = json.loads(summary_json.read_text(encoding='utf-8', errors='ignore'))
        except Exception:
            observe_summary = {}

    pid_text = _read_text(obs / 'tmux.pid') or _read_text(obs / 'process.pid')
    tmux_session_name = tmux_session or launch_summary.get('tmux_session')
    tmux_alive = _tmux_session_alive(tmux_session_name)
    status = 'running-ish'
    if exit_code is not None:
        status = 'finished'
    elif tmux_alive is True:
        status = 'launched-in-tmux'
    elif launch_summary.get('status') == 'launched-in-tmux':
        status = 'launched-in-tmux-stale-or-not-yet-observed'
    elif started_at:
        status = 'started-no-exit-yet'

    result = {
        'schema': 'opencode.observe.status.v1',
        'observe_dir': str(obs),
        'workflow_name': run_meta.get('workflow_name'),
        'command_name': run_meta.get('command_name'),
        'transport': run_meta.get('transport') or launch_summary.get('transport'),
        'status': status,
        'started_at': started_at,
        'finished_at': finished_at,
        'exit_code': exit_code,
        'session_id': session_id,
        'tmux_session': tmux_session_name,
        'tmux_session_alive': tmux_alive,
        'tmux_attach': tmux_attach or launch_summary.get('tmux_attach'),
        'prompt_out': run_meta.get('prompt_out') or launch_summary.get('prompt_out'),
        'pid': pid_text,
        'pid_alive': _pid_alive(pid_text),
        'log_files': {
            'typescript': str(typescript_log) if typescript_log.exists() else None,
            'clean': str(clean_log) if clean_log.exists() else None,
        },
        'last_clean_lines': _tail_lines(clean_log, 20),
        'last_typescript_lines': _tail_lines(typescript_log, 20),
        'run_meta': run_meta,
        'launch_summary': launch_summary,
        'observe_summary': observe_summary,
    }
    return result


def main() -> None:
    import argparse
    parser = argparse.ArgumentParser(description='Inspect a shared OpenCode observe directory and return structured status JSON.')
    parser.add_argument('observe_dir')
    args = parser.parse_args()
    result = inspect_observe_dir(args.observe_dir)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
