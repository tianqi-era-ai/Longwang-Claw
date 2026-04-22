#!/usr/bin/env python3
import importlib.util
import subprocess
import sys
from pathlib import Path

WORKSPACE = Path('~/.openclaw/workspace').expanduser()
if str(WORKSPACE) not in sys.path:
    sys.path.insert(0, str(WORKSPACE))

from lib.loop9_automation.launch_guard import check_launch_allowed, format_guard_block
from lib.opencode_runner import OpenCodeRunConfig, launch_opencode_run

import argparse

# Critical maintenance note:
# For Loop9-driven PoC refinement in this environment, the command path keeps a
# deliberate `--agent loop9-controller` pairing on top of `--command loop9`.
# Do NOT casually remove/change this because it appears redundant. This is a
# real stability guardrail for Loop9's multi-SubAgent orchestration.
# If future-you wants to revisit it, re-read
# `plans/loop9-authorized-review-must-keep.md` and validate against real runs.
LOOP9_FIXED_AGENT = 'loop9-controller'
DEFAULT_MIN_ITERATIONS = 3
DEFAULT_MAX_ITERATIONS = 20

SUPER8_ROOT = WORKSPACE / 'Super8'
SKILL_ROOT = WORKSPACE / 'skills' / 'loop9-real-poc'
PROMPT_TEMPLATE = SKILL_ROOT / 'template' / 'prompt_template.md'
POC_TEMPLATE = SKILL_ROOT / 'template' / 'poc_template.py'
STATUS_SCRIPT = SKILL_ROOT / 'scripts' / 'refresh_real_poc_status.py'
PROMPT_DIR = SUPER8_ROOT / 'temp' / 'loop9-real-poc-prompts'
OBSERVE_ROOT = SUPER8_ROOT / 'temp' / 'loop9-real-poc-observe'


def usage(exit_code: int = 0) -> None:
    print(
        'Usage:\n'
        '  run_loop9_real_poc.py [--poc-dir DIR] [--min-iterations N] [--transport tmux|direct] [--prompt-out FILE] [--dry-run] <completed-loop9-run-dir-or-child>\n\n'
        'Example:\n'
        '  python3 run_loop9_real_poc.py ~/.openclaw/workspace/Super8/temp/loop9/20260312-125445-DiscuzX-b123\n',
        end=''
    )
    raise SystemExit(exit_code)


def parse_args(argv: list[str]) -> argparse.Namespace:
    if not argv or argv[0] in {'-h', '--help'}:
        usage(0)
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument('--poc-dir')
    parser.add_argument('--min-iterations', type=int, default=DEFAULT_MIN_ITERATIONS)
    parser.add_argument('--transport', choices=['tmux', 'direct'], default='tmux')
    parser.add_argument('--prompt-out')
    parser.add_argument('--dry-run', action='store_true')
    parser.add_argument('input_path', nargs='?')
    parser.add_argument('-h', '--help', action='store_true')
    ns = parser.parse_args(argv)
    if ns.help or not ns.input_path:
        usage(0)
    return ns


def normalize_run_dir(input_path: str) -> Path:
    path = Path(input_path).expanduser().resolve()
    if not path.exists():
        raise SystemExit(f'Path does not exist: {path}')

    candidates = [path, *path.parents]
    for candidate in candidates:
        if not candidate.is_dir():
            continue
        if any(candidate.glob('solution_v*')) and any(candidate.glob('validation_report_v*')):
            return candidate
        real_pocs = candidate / 'real_pocs'
        if real_pocs.is_dir() and (
            (real_pocs / 'manifest.json').exists()
            or (real_pocs / 'real_poc_final_status.json').exists()
            or any(real_pocs.glob('real_poc_solution_v*'))
            or any(real_pocs.glob('real_poc_validation_report_v*'))
            or any(real_pocs.glob('*.py'))
        ):
            return candidate
    raise SystemExit(f'Could not normalize to a completed Loop9 run dir from: {path}')


def _load_status_module():
    spec = importlib.util.spec_from_file_location('refresh_real_poc_status', STATUS_SCRIPT)
    if not spec or not spec.loader:
        raise RuntimeError(f'Unable to load {STATUS_SCRIPT}')
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def shared_workspace_is_terminal(audit_run_dir: Path) -> tuple[bool, dict]:
    if not STATUS_SCRIPT.exists():
        return False, {}
    mod = _load_status_module()
    data = mod.build_status(audit_run_dir)
    manifest = data.get('manifest') or {}
    max_iterations = int(data.get('max_iterations') or DEFAULT_MAX_ITERATIONS)
    linked_solution_dir = str(data.get('linked_audit_real_poc_solution_dir') or '')
    linked_validation_dir = str(data.get('linked_audit_real_poc_validation_dir') or '')
    over_limit_solution_dirs = list((audit_run_dir / 'real_pocs').glob(f'real_poc_solution_v{max_iterations + 1}*'))
    over_limit_validation_dirs = list((audit_run_dir / 'real_pocs').glob(f'real_poc_validation_report_v{max_iterations + 1}*'))
    terminal = (
        data.get('workflow_completion') == 'passed'
        and manifest.get('all_findings_frozen')
        and manifest.get('all_findings_mapped')
        and manifest.get('all_findings_accepted_or_frozen')
        and linked_solution_dir.endswith(f'real_poc_solution_v{max_iterations}')
        and linked_validation_dir.endswith(f'real_poc_validation_report_v{max_iterations}')
        and not over_limit_solution_dirs
        and not over_limit_validation_dirs
    )
    return terminal, data


def build_prompt(
    template_text: str,
    audit_run_dir: Path,
    shared_poc_dir: Path,
    min_iterations: int,
    max_iterations: int,
    real_poc_solution_prefix: Path,
    real_poc_validation_prefix: Path,
    real_poc_manifest_path: Path,
    real_poc_final_status_path: Path,
) -> str:
    rendered = (
        template_text
        .replace('{{AUDIT_RUN_DIR}}', str(audit_run_dir))
        .replace('{{SHARED_POC_DIR}}', str(shared_poc_dir))
        .replace('{{POC_TEMPLATE_PATH}}', str(POC_TEMPLATE))
        .replace('{{MIN_ITERATIONS}}', str(min_iterations))
        .replace('{{MAX_ITERATIONS}}', str(max_iterations))
        .replace('{{REAL_POC_SOLUTION_PREFIX}}', str(real_poc_solution_prefix))
        .replace('{{REAL_POC_VALIDATION_PREFIX}}', str(real_poc_validation_prefix))
        .replace('{{REAL_POC_MANIFEST_PATH}}', str(real_poc_manifest_path))
        .replace('{{REAL_POC_FINAL_STATUS_PATH}}', str(real_poc_final_status_path))
    )
    run_identity_header = (
        '# Outer launcher injected run identity (high priority)\n\n'
        '- run_kind: `real-poc-iteration`\n'
        f'- root_audit_run_dir: `{audit_run_dir}`\n'
        f'- shared_poc_dir: `{shared_poc_dir}`\n\n'
        '---\n\n'
    )
    return run_identity_header + rendered


def main() -> None:
    ns = parse_args(sys.argv[1:])

    if not PROMPT_TEMPLATE.exists():
        raise SystemExit(f'Missing prompt template: {PROMPT_TEMPLATE}')
    if not POC_TEMPLATE.exists():
        raise SystemExit(f'Missing PoC template: {POC_TEMPLATE}')
    if not SUPER8_ROOT.exists():
        raise SystemExit(f'Missing Super8 root: {SUPER8_ROOT}')

    audit_run_dir = normalize_run_dir(ns.input_path)
    shared_poc_dir = Path(ns.poc_dir).expanduser().resolve() if ns.poc_dir else audit_run_dir / 'real_pocs'
    shared_poc_dir.mkdir(parents=True, exist_ok=True)
    real_poc_solution_prefix = shared_poc_dir / 'real_poc_solution_v'
    real_poc_validation_prefix = shared_poc_dir / 'real_poc_validation_report_v'
    real_poc_manifest_path = shared_poc_dir / 'manifest.json'
    real_poc_final_status_path = shared_poc_dir / 'real_poc_final_status.json'

    terminal, terminal_status = shared_workspace_is_terminal(audit_run_dir)
    if terminal and not ns.dry_run:
        print(f'audit_run_dir={audit_run_dir}')
        print(f'shared_poc_dir={shared_poc_dir}')
        print(f'real_poc_manifest_path={real_poc_manifest_path}')
        print(f'real_poc_final_status_path={real_poc_final_status_path}')
        print(f'max_iterations={DEFAULT_MAX_ITERATIONS}')
        print('status=already-complete')
        print('reason=shared-workspace-terminal-and-capped')
        if terminal_status:
            print(f'workflow_completion={terminal_status.get("workflow_completion")}')
            print(f'workflow_completion_reason={terminal_status.get("workflow_completion_reason")}')
        return

    if not ns.dry_run:
        guard_result = check_launch_allowed('poc')
        if not guard_result.get('ok'):
            print(format_guard_block(guard_result), file=sys.stderr)
            raise SystemExit(2)

    prompt_content = build_prompt(
        PROMPT_TEMPLATE.read_text(encoding='utf-8'),
        audit_run_dir,
        shared_poc_dir,
        ns.min_iterations,
        DEFAULT_MAX_ITERATIONS,
        real_poc_solution_prefix,
        real_poc_validation_prefix,
        real_poc_manifest_path,
        real_poc_final_status_path,
    )
    prompt_path = Path(ns.prompt_out).expanduser().resolve() if ns.prompt_out else (PROMPT_DIR / f'{audit_run_dir.name}-real-poc.md')

    prompt_text = (
        f'唯一任务文件就是这个绝对路径：{prompt_path}。'
        '现在立刻先读取这个文件正文，并把它当作唯一任务规格。'
        '不要搜索候选任务文件，不要向用户反问任务文件是哪一个，不要停在等待确认。'
        '如果该文件存在，就直接按它进入完整 loop9 迭代。'
        '重点是持续改进共享 PoC 目录里的 Python 文件，但不要绕过每轮 solution/validation 的结构化落盘。'
        '共享 real_pocs 只是工作区，不是唯一过程记录。'
        '并且要严格遵守目录隔离：所有 real_poc_solution、real_poc_validation、real_poc_final_status 产物都只能写在 real_pocs/ 下面，绝不能与审计主目录平级混放。'
        '新增高优先级要求：如果 source evidence 或现有 PoC 显示黑/白名单、过滤、disable_functions、动态配置/数据库驱动策略来源等信号，必须先做防御建模并把不确定性写进 PoC；若没有相关信号，则不要臆造防御机制。'
        '额外硬要求：如果任务文件顶部已经给出 `run_kind:`、`root_audit_run_dir:`、`shared_poc_dir:` 这些机器字段，'
        '则 fresh iteration run 的 original_goal/part01.md 顶部必须原样保留这些 snake_case 字段；'
        '禁止翻译成 `Run kind` 等自然语言标题。'
    )

    result = launch_opencode_run(OpenCodeRunConfig(
        workflow_name='loop9-real-poc',
        repo_root=SUPER8_ROOT,
        observe_root=OBSERVE_ROOT,
        prompt_dir=PROMPT_DIR,
        label=f'{audit_run_dir.name}-real-poc',
        prompt_file_stem=f'{audit_run_dir.name}-real-poc',
        prompt_content=prompt_content,
        prompt_text=prompt_text,
        command_name='loop9',
        prompt_out_override=prompt_path,
        transport=ns.transport,
        print_prefix='[loop9-real-poc]',
        extra_run_meta={
            'audit_run_dir': str(audit_run_dir),
            'root_audit_run_dir': str(audit_run_dir),
            'run_kind': 'real-poc-iteration',
            'shared_poc_dir': str(shared_poc_dir),
            'real_poc_solution_prefix': str(real_poc_solution_prefix),
            'real_poc_validation_prefix': str(real_poc_validation_prefix),
            'real_poc_manifest_path': str(real_poc_manifest_path),
            'real_poc_final_status_path': str(real_poc_final_status_path),
            'min_iterations': str(ns.min_iterations),
            'min_iterations_source_kind': 'default' if ns.min_iterations == DEFAULT_MIN_ITERATIONS else 'explicit',
            'max_iterations': str(DEFAULT_MAX_ITERATIONS),
        },
        launch_summary_extra={
            'audit_run_dir': str(audit_run_dir),
            'root_audit_run_dir': str(audit_run_dir),
            'run_kind': 'real-poc-iteration',
            'shared_poc_dir': str(shared_poc_dir),
            'real_poc_solution_prefix': str(real_poc_solution_prefix),
            'real_poc_validation_prefix': str(real_poc_validation_prefix),
            'real_poc_manifest_path': str(real_poc_manifest_path),
            'real_poc_final_status_path': str(real_poc_final_status_path),
            'min_iterations': str(ns.min_iterations),
            'min_iterations_source_kind': 'default' if ns.min_iterations == DEFAULT_MIN_ITERATIONS else 'explicit',
            'max_iterations': str(DEFAULT_MAX_ITERATIONS),
        },
        tmux_session_prefix='loop9-real-poc',
        fixed_agent=LOOP9_FIXED_AGENT,
        enable_session_export=True,
        dry_run=ns.dry_run,
    ))

    if STATUS_SCRIPT.exists():
        subprocess.run([
            'python3',
            str(STATUS_SCRIPT),
            str(audit_run_dir),
            '--output',
            str(real_poc_final_status_path),
        ], check=False)

    print(f'audit_run_dir={audit_run_dir}')
    print(f'shared_poc_dir={shared_poc_dir}')
    print(f'real_poc_solution_prefix={real_poc_solution_prefix}')
    print(f'real_poc_validation_prefix={real_poc_validation_prefix}')
    print(f'real_poc_manifest_path={real_poc_manifest_path}')
    print(f'real_poc_final_status_path={real_poc_final_status_path}')
    print(f'min_iterations={ns.min_iterations}')
    print(f'max_iterations={DEFAULT_MAX_ITERATIONS}')
    print(f'prompt_out={result["prompt_out"]}')
    print(f'obs_dir={result["obs_dir"]}')
    if 'tmux_session' in result:
        print(f'tmux_session={result["tmux_session"]}')
    print(f'status={result["status"]}')


if __name__ == '__main__':
    main()
