from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

WORKSPACE = Path('~/.openclaw/workspace').expanduser()
SUPER8_ROOT = WORKSPACE / 'Super8'
LOOP9_DIR = SUPER8_ROOT / 'temp' / 'loop9'
LOOP9_OBSERVE_DIR = SUPER8_ROOT / 'temp' / 'loop9-observe'
REAL_POC_OBSERVE_DIR = SUPER8_ROOT / 'temp' / 'loop9-real-poc-observe'

RUN_KIND_PATTERNS = [
    re.compile(r'^\s*-\s*run_kind\s*[:：]\s*`?([^`\n]+)`?\s*$', re.M),
    re.compile(r'^\s*run_kind\s*[:：]\s*`?([^`\n]+)`?\s*$', re.M),
]
ROOT_AUDIT_PATTERNS = [
    re.compile(r'^\s*-\s*root_audit_run_dir\s*[:：]\s*`?([^`\n]+)`?\s*$', re.M),
    re.compile(r'^\s*root_audit_run_dir\s*[:：]\s*`?([^`\n]+)`?\s*$', re.M),
    re.compile(r'^\s*-\s*audit_run_dir\s*[:：]\s*`?([^`\n]+)`?\s*$', re.M),
]
PROMPT_OUT_PATTERNS = [
    re.compile(r'authoritative task file\s*[:：]\s*`([^`]+)`', re.I),
    re.compile(r'Authoritative task spec\s*[:：]\s*`([^`]+)`', re.I),
]


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


def _observe_meta(obs_dir: Path) -> dict[str, Any]:
    meta_json = _read_json(obs_dir / 'run.meta.json') or {}
    if meta_json:
        return meta_json
    text = _safe_read_text(obs_dir / 'run.meta')
    data: dict[str, Any] = {}
    for line in text.splitlines():
        if '=' not in line:
            continue
        k, v = line.split('=', 1)
        data[k.strip()] = v.strip()
    return data


def _extract_first(text: str, patterns: list[re.Pattern[str]]) -> str:
    for pattern in patterns:
        m = pattern.search(text)
        if m:
            return m.group(1).strip().strip('`')
    return ''


def _original_goal_text(run_dir: Path) -> str:
    return _safe_read_text(run_dir / 'original_goal' / 'part01.md')


def _prompt_out_from_run(run_dir: Path) -> str:
    text = _original_goal_text(run_dir)
    return _extract_first(text, PROMPT_OUT_PATTERNS)


def _find_observe_by_prompt_out(prompt_out: str) -> tuple[Path | None, dict[str, Any] | None]:
    if not prompt_out:
        return None, None
    for base in (LOOP9_OBSERVE_DIR, REAL_POC_OBSERVE_DIR):
        if not base.exists():
            continue
        for obs_dir in base.iterdir():
            if not obs_dir.is_dir():
                continue
            meta = _observe_meta(obs_dir)
            if str(meta.get('prompt_out') or '') == prompt_out:
                return obs_dir, meta
    return None, None


def classify_loop9_run(run_dir: str | Path) -> dict[str, Any]:
    run_path = Path(run_dir).expanduser().resolve()
    text = _original_goal_text(run_path)
    prompt_out = _prompt_out_from_run(run_path)
    obs_dir, obs_meta = _find_observe_by_prompt_out(prompt_out)

    local_run_kind = _extract_first(text, RUN_KIND_PATTERNS)
    local_root_audit = _extract_first(text, ROOT_AUDIT_PATTERNS)
    obs_run_kind = str((obs_meta or {}).get('run_kind') or '').strip()
    obs_root_audit = str((obs_meta or {}).get('root_audit_run_dir') or (obs_meta or {}).get('audit_run_dir') or '').strip()

    run_name_lc = run_path.name.lower()
    low = text.lower()

    source = 'unknown'
    run_kind = ''
    root_audit_run_dir = ''

    if local_run_kind:
        run_kind = local_run_kind
        root_audit_run_dir = local_root_audit
        source = 'original-goal-explicit'
    elif obs_run_kind:
        run_kind = obs_run_kind
        root_audit_run_dir = obs_root_audit
        source = 'observe-meta'
    elif 'loop9-real-poc' in low or 'shared_poc_dir' in low or 'real_poc_solution_v' in low or 'read the audit run' in low:
        run_kind = 'real-poc-iteration'
        root_audit_run_dir = local_root_audit or obs_root_audit
        source = 'heuristic-real-poc'
    else:
        run_kind = 'audit-root'
        source = 'heuristic-audit-root'

    if not root_audit_run_dir:
        if run_kind == 'audit-root':
            root_audit_run_dir = str(run_path)
        elif obs_root_audit:
            root_audit_run_dir = obs_root_audit
        elif local_root_audit:
            root_audit_run_dir = local_root_audit

    rp_like = ('-rp' in run_name_lc) or ('-rpoc' in run_name_lc)

    return {
        'run_dir': str(run_path),
        'run_kind': run_kind,
        'root_audit_run_dir': root_audit_run_dir or None,
        'source': source,
        'prompt_out': prompt_out or None,
        'observe_dir': str(obs_dir) if obs_dir else None,
        'observe_workflow_name': str((obs_meta or {}).get('workflow_name') or '') or None,
        'rp_like': rp_like,
        'has_original_goal_explicit': bool(local_run_kind),
        'has_observe_meta': bool(obs_meta),
    }


def read_run_kind(run_dir: str | Path) -> str | None:
    return classify_loop9_run(run_dir).get('run_kind')


def read_root_audit_run_dir(run_dir: str | Path) -> str | None:
    return classify_loop9_run(run_dir).get('root_audit_run_dir')
