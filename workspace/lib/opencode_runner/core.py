#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import re
import shlex
import subprocess
import textwrap
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional


def shell_quote(value) -> str:
    return shlex.quote(str(value))


def write_text(path: Path, content: str, executable: bool = False) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding='utf-8')
    if executable:
        path.chmod(path.stat().st_mode | 0o111)


def write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def sanitize_tmux_name(name: str) -> str:
    table = str.maketrans({c: '_' for c in '/: .'})
    return name.translate(table)


@dataclass
class OpenCodeRunConfig:
    workflow_name: str
    repo_root: Path
    observe_root: Path
    prompt_dir: Path
    label: str
    prompt_file_stem: str
    prompt_content: str
    prompt_text: str
    command_name: str
    prompt_out_override: Optional[Path] = None
    command_cwd: Optional[Path] = None
    transport: str = 'tmux'
    print_prefix: Optional[str] = None
    extra_run_meta: Optional[dict[str, str]] = None
    launch_summary_extra: Optional[dict[str, str]] = None
    tmux_session_prefix: str = 'opencode'
    # Critical maintenance note:
    # `fixed_agent` is not just a cosmetic override slot. For some workflows
    # (especially Loop9 in this environment), pairing `--command ...` with a
    # specific `--agent ...` is an experience-backed stability guardrail.
    # Do NOT casually change/remove a populated `fixed_agent` at call sites just
    # because it looks redundant. If a workflow depends on it, future
    # maintainers will often inspect this core file first; keep that in mind.
    # Re-validate on real long-running runs before changing such pairings.
    fixed_agent: Optional[str] = None
    enable_session_export: bool = True
    stamp_override: Optional[str] = None
    dry_run: bool = False


def _write_export_helper(obs_dir: Path) -> None:
    export_session_py = textwrap.dedent(
        """\
        #!/usr/bin/env python3
        import json
        import subprocess
        import sys
        from pathlib import Path

        obs_dir = Path(sys.argv[1])
        session_id = (obs_dir / 'session.id').read_text(encoding='utf-8').strip()
        out = obs_dir / 'session.export.json'
        res = subprocess.run(['opencode', 'export', session_id], capture_output=True, text=True)
        out.write_text(res.stdout, encoding='utf-8')
        (obs_dir / 'session.export.stderr.log').write_text(res.stderr, encoding='utf-8')
        if res.returncode != 0:
            raise SystemExit(res.returncode)
        obj = json.loads(res.stdout)
        (obs_dir / 'session.title.txt').write_text(obj.get('info', {}).get('title', '') + '\\n', encoding='utf-8')
        (obs_dir / 'session.updated.txt').write_text(str(obj.get('info', {}).get('time', {}).get('updated', '')) + '\\n', encoding='utf-8')
        """
    )
    write_text(obs_dir / 'export_session.py', export_session_py, executable=True)


def _build_run_and_capture_script(config: OpenCodeRunConfig, obs_dir: Path) -> str:
    repo_root_q = shell_quote(config.repo_root)
    command_cwd = config.command_cwd or config.repo_root
    opencode_args = ['opencode', 'run', '--print-logs', '--command', config.command_name]
    if config.fixed_agent:
        # Important: this is where a workflow-level fixed agent becomes part of
        # the actual `opencode run` invocation. Treat it as semantically
        # significant, not as optional decoration. Example: Loop9 relies on the
        # `--command loop9` + `--agent loop9-controller` pairing as a practical
        # stability guardrail for its multi-SubAgent orchestration.
        opencode_args.extend(['--agent', config.fixed_agent])
    opencode_args_str = ' '.join(shell_quote(part) for part in opencode_args)
    export_tail = ''
    if config.enable_session_export:
        export_tail = (
            'if [[ -f "$OBS_DIR/session.id" ]]; then\n'
            '  python3 "$OBS_DIR/export_session.py" "$OBS_DIR" || true\n'
            'fi\n'
        )
    body = f"""#!/usr/bin/env bash
set -euo pipefail
OBS_DIR="$1"
shift
cd {repo_root_q}
status=0
printf '%s\\n' "$$" > "$OBS_DIR/process.pid"
started_at=$(date '+%Y-%m-%d %H:%M:%S %z')
printf '%s\\n' "$started_at" > "$OBS_DIR/started_at.txt"
if [[ -t 0 && -t 1 && -t 2 ]] && command -v script >/dev/null 2>&1; then
  script -q "$OBS_DIR/opencode.typescript.log" {opencode_args_str} "$@" || status=$?
else
  {opencode_args_str} "$@" > >(tee "$OBS_DIR/opencode.typescript.log") 2>&1 || status=$?
fi
printf '%s\\n' "$status" > "$OBS_DIR/opencode.exit_code"
printf '%s\\n' "$(date '+%Y-%m-%d %H:%M:%S %z')" > "$OBS_DIR/finished_at.txt"
python3 - "$OBS_DIR" <<'PY'
import json, re, sys
from pathlib import Path
obs = Path(sys.argv[1])
text = (obs / 'opencode.typescript.log').read_text(errors='ignore')
ansi = re.compile(r'\\x1b\\[[0-9;?]*[ -/]*[@-~]')
clean = ansi.sub('', text)
(obs / 'opencode.clean.log').write_text(clean, encoding='utf-8')
pat = re.compile(r'session[_ ]id\\s*[:=]\\s*(ses_[A-Za-z0-9]+)|\\b(ses_[A-Za-z0-9]{{10,}})\\b')
ids = []
for m in pat.finditer(clean):
    sid = m.group(1) or m.group(2)
    if sid and sid not in ids:
        ids.append(sid)
if ids:
    (obs / 'session.id').write_text(ids[-1] + '\\n', encoding='utf-8')
summary = {{
    'has_clean_log': True,
    'session_ids_found': ids,
    'last_lines': clean.splitlines()[-20:],
}}
(obs / 'observe.summary.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding='utf-8')
PY
{export_tail}exit "$status"
"""
    return body


def launch_opencode_run(config: OpenCodeRunConfig) -> dict[str, str]:
    stamp = config.stamp_override or datetime.now().strftime('%Y%m%d-%H%M%S')
    observe_root = config.observe_root
    prompt_dir = config.prompt_dir
    observe_root.mkdir(parents=True, exist_ok=True)
    prompt_dir.mkdir(parents=True, exist_ok=True)

    prompt_out = config.prompt_out_override.expanduser().resolve() if config.prompt_out_override else (prompt_dir / f'{config.prompt_file_stem}-{stamp}.md')
    prompt_out.write_text(config.prompt_content, encoding='utf-8')

    obs_dir = observe_root / f'{config.label}-{stamp}'
    obs_dir.mkdir(parents=True, exist_ok=True)

    run_meta = {
        'schema': 'opencode.run.meta.v1',
        'stamp': stamp,
        'workflow_name': config.workflow_name,
        'transport': config.transport,
        'repo_root': str(config.repo_root),
        'prompt_out': str(prompt_out),
        'obs_dir': str(obs_dir),
        'observe_dir': str(obs_dir),
        'command_name': config.command_name,
        'command_cwd': str(config.command_cwd or config.repo_root),
        'fixed_agent': config.fixed_agent or '',
        'created_at': datetime.now().astimezone().strftime('%Y-%m-%d %H:%M:%S %z'),
    }
    if config.extra_run_meta:
        run_meta.update({k: str(v) for k, v in config.extra_run_meta.items()})
    run_meta_text = ''.join(f'{k}={v}\n' for k, v in run_meta.items())
    write_text(obs_dir / 'run.meta', run_meta_text)
    write_json(obs_dir / 'run.meta.json', run_meta)
    write_text(obs_dir / 'prompt.txt', config.prompt_text + '\n')
    write_text(obs_dir / 'command.txt', config.command_name + '\n')
    if config.enable_session_export:
        _write_export_helper(obs_dir)

    run_script = _build_run_and_capture_script(config, obs_dir)
    run_script_path = obs_dir / 'run_and_capture.sh'
    write_text(run_script_path, run_script, executable=True)

    result = {
        'prompt_out': str(prompt_out),
        'obs_dir': str(obs_dir),
        'status': 'prepared',
    }

    if config.dry_run:
        result['status'] = 'dry-run'
        return result

    if config.transport == 'tmux':
        from shutil import which
        if which('tmux') is None:
            raise SystemExit('tmux not found but --transport tmux was requested')
        tmux_session = sanitize_tmux_name(f'{config.tmux_session_prefix}-{config.label}-{stamp}')
        subprocess.run(['tmux', 'kill-session', '-t', tmux_session], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        tmux_command = (
            f'cd {shell_quote(config.repo_root)} && '
            f'{shell_quote(run_script_path)} {shell_quote(obs_dir)} {shell_quote(config.prompt_text)}'
        )
        subprocess.run(['tmux', 'new-session', '-d', '-s', tmux_session, tmux_command], check=True)
        subprocess.run(['tmux', 'pipe-pane', '-o', '-t', f'{tmux_session}:0.0', f'cat >> {shell_quote(obs_dir / "tmux.pipe.log")}'], check=True)
        with (obs_dir / 'tmux.capture.initial.log').open('w', encoding='utf-8') as fh:
            subprocess.run(['tmux', 'capture-pane', '-p', '-t', f'{tmux_session}:0.0'], stdout=fh, stderr=subprocess.DEVNULL, check=False)
        write_text(obs_dir / 'tmux.session.txt', tmux_session + '\n')
        write_text(obs_dir / 'tmux.attach.txt', f'tmux attach -t {tmux_session}\n')
        launch_summary = {
            'schema': 'opencode.launch.summary.v1',
            'status': 'launched-in-tmux',
            'workflow_name': config.workflow_name,
            'command_name': config.command_name,
            'transport': 'tmux',
            'tmux_session': tmux_session,
            'tmux_attach': f'tmux attach -t {tmux_session}',
            'obs_dir': str(obs_dir),
            'observe_dir': str(obs_dir),
            'prompt_out': str(prompt_out),
        }
        if config.launch_summary_extra:
            launch_summary.update({k: str(v) for k, v in config.launch_summary_extra.items()})
        launch_summary_text = ''.join(f'{k}={v}\n' for k, v in launch_summary.items())
        write_text(obs_dir / 'launch.summary.txt', launch_summary_text)
        write_json(obs_dir / 'launch.summary.json', launch_summary)
        result.update({'status': 'launched-in-tmux', 'tmux_session': tmux_session})
        return result

    os.chdir(config.repo_root)
    os.execvp(str(run_script_path), [str(run_script_path), str(obs_dir), config.prompt_text])
    raise AssertionError('unreachable')
