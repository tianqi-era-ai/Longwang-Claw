#!/usr/bin/env python3
"""
loop9_authorized_review.py

Canonical Python entrypoint for the Super8 Loop9 wrapper.

Design goals:
- Keep the external interface stable (`--mode`, `--transport`, target path, optional output path)
- Keep the same prompt/output/observe directory conventions
- Keep the same tmux-centric long-task workflow
- Keep the same helper artifacts (`run.meta`, `prompt.txt`, `command.txt`, etc.)
- Avoid surprising behavior changes while making the implementation easier to read
"""

import argparse
import json
import os
import subprocess
import sys
import textwrap
from pathlib import Path
from datetime import datetime
from typing import Literal, Optional

WORKSPACE = Path('~/.openclaw/workspace').expanduser()
if str(WORKSPACE) not in sys.path:
    sys.path.insert(0, str(WORKSPACE))

from lib.loop9_automation.launch_guard import check_launch_allowed, format_guard_block
from lib.loop9_automation.target_gate import check_target_policy, format_target_gate_block
from lib.opencode_runner import OpenCodeRunConfig, launch_opencode_run

# Critical maintenance note:
# For the Loop9 command path in this environment, `--command loop9` must keep
# being paired with `--agent loop9-controller`.
# Do NOT casually change/remove this agent value just because it looks
# redundant. This pairing is an experience-backed stability guardrail for the
# multi-SubAgent / recursive Loop9 workflow.
# If you think this should change, first re-read:
#   - plans/loop9-authorized-review-must-keep.md
# and re-validate against real long-running runs before touching it.
LOOP9_FIXED_AGENT = 'loop9-controller'
SKIP_TARGET_GATE_CONFIRM_TOKEN = 'I-understand-and-confirm-target-gate-bypass'

PROMPT_MODULE_SPECS = {
    'weibu-submission': [
        {
            'path': WORKSPACE / 'skills/loop9-rce-audit-focus/prompt-modules/weibu-rce-stage-a.md',
            'anchor': '# 我的重要关注点',
            'mode': 'before',
            'label': 'loop9-rce-audit-focus-stage-a',
        },
        {
            'path': WORKSPACE / 'skills/loop9-rce-audit-focus/prompt-modules/weibu-rce-stage-b.md',
            'anchor': '5、如果中间发现可疑的中危或不满足收录条件、但对内部安全仍有价值的问题，可以另开文件记录。',
            'mode': 'after',
            'label': 'loop9-rce-audit-focus-stage-b',
        },
    ],
}

RCE_REGEX_SCAN_SCRIPT = WORKSPACE / 'skills/loop9-rce-audit-focus/scripts/rce_regex_scan.py'
RCE_PRE_SCAN_POLICIES = {'weibu-submission'}
RCE_LANGUAGE_SIGNALS = {
    'java': {
        'suffixes': {'.java', '.jsp', '.jspx', '.tag', '.tagx', '.kt', '.kts', '.groovy'},
        'exact_names': {'pom.xml', 'build.gradle', 'build.gradle.kts', 'settings.gradle', 'settings.gradle.kts', 'gradlew', 'mvnw'},
    },
    'php': {
        'suffixes': {'.php', '.phtml', '.php3', '.php4', '.php5', '.php7', '.php8', '.phps', '.inc', '.module', '.install', '.theme', '.ctp'},
        'exact_names': {'composer.json', 'composer.lock', 'index.php', 'wp-config.php', 'artisan'},
    },
}
RCE_LANGUAGE_EXCLUDE_DIRS = {
    '.git', '.idea', '.vscode', '.gradle', '.mvn', '.svn', '.hg',
    'node_modules', 'vendor', 'dist', 'build', 'target', 'out', 'coverage',
    '__pycache__', 'tmp', 'temp', 'logs', 'cache', 'storage'
}

# -----------------------------------------------------------------------------
# Prompt-module injection helpers
# -----------------------------------------------------------------------------


def inject_prompt_module(template_text: str, *, module_text: str, anchor: str, mode: Literal['before', 'after']) -> tuple[str, bool]:
    """Insert one module block relative to a stable anchor.

    Preferred behavior is anchored insertion so the module stays close to the
    matching workflow section. The caller may choose a fallback if no anchor is
    found.
    """
    idx = template_text.find(anchor)
    if idx == -1:
        return template_text, False

    cleaned = module_text.strip()
    if not cleaned:
        return template_text, True

    if mode == 'before':
        injected = f"{cleaned}\n\n{anchor}"
        return template_text[:idx] + injected + template_text[idx + len(anchor):], True

    insert_at = idx + len(anchor)
    injected = f"{anchor}\n\n{cleaned}"
    return template_text[:idx] + injected + template_text[insert_at:], True



def apply_prompt_modules(template_text: str, policy: str) -> tuple[str, list[dict[str, str]]]:
    """Apply thin policy-specific prompt modules with anchor-first insertion.

    First version intentionally keeps this small:
    - only modules listed for the selected policy are considered
    - anchored insertion is preferred
    - append-at-end is used only as a fallback
    """
    result = template_text
    applied: list[dict[str, str]] = []

    for spec in PROMPT_MODULE_SPECS.get(policy, []):
        path = Path(spec['path'])
        if not path.exists():
            continue

        module_text = path.read_text(encoding='utf-8').strip()
        if not module_text:
            continue

        result, matched = inject_prompt_module(
            result,
            module_text=module_text,
            anchor=spec['anchor'],
            mode=spec['mode'],
        )
        if matched:
            applied.append({
                'label': spec['label'],
                'path': str(path),
                'placement': f"anchor:{spec['mode']}",
            })
            continue

        result = result.rstrip() + "\n\n" + module_text + "\n"
        applied.append({
            'label': spec['label'],
            'path': str(path),
            'placement': 'append-fallback',
        })

    return result, applied


def detect_rce_scan_language(target_path: Path) -> tuple[Optional[str], dict[str, int]]:
    """Best-effort language detection for stable outer-layer pre-scan gating.

    We intentionally keep this simple and auditable: count strong Java/PHP
    signals from filenames/suffixes while pruning obviously irrelevant dirs.
    """
    scores = {name: 0 for name in RCE_LANGUAGE_SIGNALS}
    seen_files = 0

    for current_root, dirnames, filenames in os.walk(target_path):
        dirnames[:] = [d for d in dirnames if d not in RCE_LANGUAGE_EXCLUDE_DIRS]
        for filename in filenames:
            seen_files += 1
            lower_name = filename.lower()
            suffix = Path(lower_name).suffix
            for language, signals in RCE_LANGUAGE_SIGNALS.items():
                if lower_name in signals['exact_names']:
                    scores[language] += 4
                elif suffix in signals['suffixes']:
                    scores[language] += 1
            if seen_files >= 12000:
                break
        if seen_files >= 12000:
            break

    best_language = max(scores, key=scores.get)
    best_score = scores[best_language]
    second_score = max(score for name, score in scores.items() if name != best_language)
    if best_score == 0:
        return None, scores
    if best_score < 3 and second_score > 0:
        return None, scores
    if second_score > 0 and best_score < second_score * 2:
        return None, scores
    return best_language, scores


def run_rce_pre_scan(target_path: Path, policy: str) -> dict[str, object]:
    """Run the regex pre-scan from the wrapper layer when language is clear.

    This turns the RCE regex scan from a soft prompt suggestion into an
    observable wrapper-side step. The audit still continues if pre-scan is
    skipped or fails, but the reason becomes explicit in run metadata.
    """
    state: dict[str, object] = {
        'status': 'not-requested',
        'policy': policy,
        'language': None,
        'scores': {},
        'output_path': None,
        'scanned_file_count': None,
        'matched_file_count': None,
        'reason': None,
        'command': None,
        'stdout': None,
        'stderr': None,
        'returncode': None,
    }

    if policy not in RCE_PRE_SCAN_POLICIES:
        state['reason'] = 'policy-disabled'
        return state

    if not RCE_REGEX_SCAN_SCRIPT.exists():
        state['status'] = 'failed'
        state['reason'] = 'scan-script-missing'
        return state

    language, scores = detect_rce_scan_language(target_path)
    state['scores'] = scores
    if language is None:
        state['status'] = 'skipped'
        state['reason'] = 'language-unclear-or-unsupported'
        return state

    state['language'] = language
    command = [
        sys.executable,
        str(RCE_REGEX_SCAN_SCRIPT),
        str(target_path),
        '--language', language,
        '--output-format', 'json',
    ]
    state['command'] = command

    try:
        completed = subprocess.run(
            command,
            cwd=str(WORKSPACE),
            capture_output=True,
            text=True,
            timeout=1800,
            check=False,
        )
    except subprocess.TimeoutExpired as exc:
        state['status'] = 'failed'
        state['reason'] = 'timeout'
        state['stderr'] = str(exc)
        return state

    state['stdout'] = completed.stdout.strip() or None
    state['stderr'] = completed.stderr.strip() or None
    state['returncode'] = completed.returncode

    if completed.returncode != 0:
        state['status'] = 'failed'
        state['reason'] = 'scanner-nonzero-exit'
        return state

    try:
        summary = json.loads(completed.stdout)
    except json.JSONDecodeError:
        state['status'] = 'failed'
        state['reason'] = 'scanner-summary-not-json'
        return state

    state['status'] = 'executed'
    state['reason'] = 'executed'
    state['output_path'] = summary.get('output_path')
    state['scanned_file_count'] = summary.get('scanned_file_count')
    state['matched_file_count'] = summary.get('matched_file_count')
    return state


def build_rce_pre_scan_header(pre_scan: dict[str, object]) -> str:
    """Render wrapper-authoritative pre-scan metadata into the prompt."""
    lines = [
        '# RCE 正则预扫状态（由外层包装器判定/执行，优先级高于正文推测）',
        '',
        f"- rce_regex_scan_status: `{pre_scan.get('status')}`",
        f"- rce_regex_scan_policy: `{pre_scan.get('policy')}`",
    ]

    language = pre_scan.get('language')
    if language:
        lines.append(f"- rce_regex_scan_language: `{language}`")

    output_path = pre_scan.get('output_path')
    if output_path:
        lines.append(f"- rce_regex_scan_output_path: `{output_path}`")

    scanned = pre_scan.get('scanned_file_count')
    matched = pre_scan.get('matched_file_count')
    if scanned is not None:
        lines.append(f"- rce_regex_scan_scanned_file_count: `{scanned}`")
    if matched is not None:
        lines.append(f"- rce_regex_scan_matched_file_count: `{matched}`")

    reason = pre_scan.get('reason')
    if reason:
        lines.append(f"- rce_regex_scan_reason: `{reason}`")

    scores = pre_scan.get('scores')
    if isinstance(scores, dict) and scores:
        score_text = ', '.join(f'{k}={v}' for k, v in sorted(scores.items()))
        lines.append(f"- rce_regex_scan_language_scores: `{score_text}`")

    lines.extend([
        '',
        '- 若 `rce_regex_scan_status=executed`，必须先读取该 JSON 结果文件，并把它当作**高召回辅助输入**，不能把命中当结论。',
        '- 若 `rce_regex_scan_status=skipped` 或 `failed`，必须把这个状态视为外层约束事实，而不是假装已经做过预扫。',
        '',
        '---',
        '',
    ])
    return '\n'.join(lines)


# -----------------------------------------------------------------------------
# User-facing help text
# -----------------------------------------------------------------------------


USAGE_TEXT = """\
Usage:
  loop9_authorized_review.py [--mode command|agent] [--transport tmux|direct] [--policy internal-full-audit|weibu-submission] <LOCAL_TARGET_PATH> [PROMPT_OUT_PATH]

What it does:
  1. Creates a prompt file from the project template.
  2. Fills the target repo name + absolute local path.
  3. Launches OpenCode in the Super8 project.

Modes:
  --mode command  Default/recommended path: use OpenCode command mode for loop9 .
  --mode agent    path: start OpenCode with --agent loop9-controller.

Transport:
  --transport tmux    Default. Start the long-running workflow inside a named tmux session.
  --transport direct  Run directly in the current shell process.

Policy:
  --policy internal-full-audit  Default. Use the original internal full-audit prompt template.
  --policy weibu-submission     Use the 微步在线收录-oriented prompt template.

Target gate:
  --skip-target-gate            Request bypass of local target eligibility checks for an explicit manual launch.
  --skip-target-gate-confirm    Required confirmation token for the bypass request.
                                Value must be: I-understand-and-confirm-target-gate-bypass

Notes:
  - Intended for authorized/local security review workflows only.
  - Run this script from anywhere; it resolves paths itself.
  - If PROMPT_OUT_PATH is omitted, it writes to:
      Super8/temp/loop9-prompts/<target>-<timestamp>.md
"""


def usage(exit_code: int = 0) -> None:
    """Print the historical usage text and exit.

    We intentionally keep the old hand-written help text instead of relying on
    argparse's default formatting, so existing users see the same output style.
    """
    print(USAGE_TEXT, end="")
    raise SystemExit(exit_code)



def parse_args(argv: list[str]) -> argparse.Namespace:
    """Parse CLI arguments while preserving the old script contract.

    We keep parsing intentionally simple:
    - `--mode` controls command-vs-agent path
    - `--transport` controls tmux-vs-direct launching
    - positional #1 is the local target repo/path to audit
    - positional #2 optionally overrides the generated prompt path
    """
    if not argv:
        usage(0)
    if argv and argv[0] in {"-h", "--help"}:
        usage(0)

    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--mode", choices=["command", "agent"], default="command")
    parser.add_argument("--transport", choices=["tmux", "direct"], default="tmux")
    parser.add_argument("--policy", choices=["internal-full-audit", "weibu-submission"], default="internal-full-audit")
    parser.add_argument("--skip-target-gate", action="store_true")
    parser.add_argument("--skip-target-gate-confirm", default="")
    parser.add_argument("target_input", nargs="?")
    parser.add_argument("prompt_out", nargs="?")
    parser.add_argument("-h", "--help", action="store_true")
    ns = parser.parse_args(argv)

    if ns.help:
        usage(0)
    if not ns.target_input:
        usage(0)
    return ns



def resolve_target_path(target_input: str) -> Path:
    """Resolve the user-supplied target path to an absolute local directory.

    The old shell wrapper first changed into the provided directory and then
    resolved the absolute path, which effectively required the input to already
    exist and be a directory. We preserve that behavior here.
    """
    target = Path(target_input).expanduser()
    if not target.exists() or not target.is_dir():
        print(f"Target path is not a directory: {target_input}", file=sys.stderr)
        raise SystemExit(1)
    return target.resolve()



def main() -> None:
    """Main orchestration entrypoint.

    High-level flow:
    1. Resolve target + repository-relative paths
    2. Fill prompt template and create observe directory
    3. Write helper artifacts (`run.meta`, `prompt.txt`, helpers)
    4. Either:
       - exit early in agent mode (preserving the old behavior), or
       - launch command mode via tmux/direct transport
    """
    ns = parse_args(sys.argv[1:])

    target_path = resolve_target_path(ns.target_input)
    target_name = target_path.name

    if ns.skip_target_gate:
        if ns.skip_target_gate_confirm != SKIP_TARGET_GATE_CONFIRM_TOKEN:
            print('[loop9-target-gate] Bypass requested but not confirmed.', file=sys.stderr)
            print(f'[loop9-target-gate] Re-run only after explicit human approval with: --skip-target-gate --skip-target-gate-confirm {SKIP_TARGET_GATE_CONFIRM_TOKEN}', file=sys.stderr)
            raise SystemExit(2)
    else:
        target_gate = check_target_policy(target_path, ns.policy)
        if not target_gate.get('ok'):
            print(format_target_gate_block(target_gate), file=sys.stderr)
            raise SystemExit(2)

    guard_result = check_launch_allowed('audit')
    if not guard_result.get('ok'):
        print(format_guard_block(guard_result), file=sys.stderr)
        raise SystemExit(2)

    script_dir = Path(__file__).resolve().parent
    repo_root = script_dir.parent.parent
    template_map = {
        "internal-full-audit": repo_root / "工作流_提示词工程/case10_比较简单的Math9/loop9____第二版/案例/3_0day挖掘_1/red队/DotNet项目/【模板（更新版）】提示词.md",
        "weibu-submission": repo_root / "工作流_提示词工程/case10_比较简单的Math9/loop9____第二版/案例/3_0day挖掘_1/red队/DotNet项目/【模板（微步在线收录版）】提示词.md",
    }
    template = template_map[ns.policy]
    prompt_dir = repo_root / "temp/loop9-prompts"
    observe_root = repo_root / "temp/loop9-observe"
    prompt_dir.mkdir(parents=True, exist_ok=True)
    observe_root.mkdir(parents=True, exist_ok=True)

    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    policy_suffix = "" if ns.policy == "internal-full-audit" else f"-{ns.policy}"
    default_out = prompt_dir / f"{target_name}{policy_suffix}-{stamp}.md"
    prompt_out = Path(ns.prompt_out).expanduser() if ns.prompt_out else default_out
    prompt_out.parent.mkdir(parents=True, exist_ok=True)

    # Fill the historical prompt template exactly once for repo name/path.
    # We intentionally preserve the old placeholder replacement strategy rather
    # than redesigning the template format right now.
    template_text = template.read_text(encoding="utf-8")
    filled = template_text.replace("【_______________________________】", f"【{target_name}】", 1)
    filled = filled.replace("【./_______________________________  _bin】", f"【{target_path}】", 1)
    filled, applied_prompt_modules = apply_prompt_modules(filled, ns.policy)
    rce_pre_scan = run_rce_pre_scan(target_path, ns.policy)

    # Inject explicit authoritative target metadata into the task file itself.
    # This prevents the inner Loop9 controller from accidentally treating the
    # orchestration repo (`Super8`) as the audit target name when it later
    # derives run_id / run_dir naming.
    authoritative_header = textwrap.dedent(
        f"""\
        # 外层包装器注入的权威元信息（高优先级，必须遵守）

        - 审计目标源码项目名：`{target_name}`
        - 审计目标源码根目录：`{target_path}`
        - run_kind: `audit-root`
        - run_id 命名规则：`YYYYMMDD-HHMMSS-{target_name}-XXXX`
        - 目录命名强制要求：`temp/loop9/<run_id>/` 中的 `<target_name>` 必须使用上面的审计目标源码项目名。
        - `Super8` 只是工作流/编排仓库名，不是本次审计目标名；除非本次被审计路径本身就是 `Super8`，否则禁止把 `Super8` 用作 run_id 中的目标名。

        ---

        """
    )
    rce_pre_scan_header = build_rce_pre_scan_header(rce_pre_scan)
    prompt_out.write_text(authoritative_header + rce_pre_scan_header + filled, encoding="utf-8")

    print(f"————————当前模式：{ns.mode} / transport={ns.transport} / policy={ns.policy}————————")

    prompt_text = (
        f"权威目标元信息：TARGET_REPO_NAME={target_name}；TARGET_REPO_PATH={target_path}；"
        f"run_id 必须使用 {target_name} 作为目标名，绝不能误用当前工作流仓库名 Super8（除非本次审计目标本身就是 Super8）。"
        f"RCE预扫状态：status={rce_pre_scan.get('status')}；language={rce_pre_scan.get('language')}；output={rce_pre_scan.get('output_path')}。"
        f"先读取并严格执行这个任务文件：'{prompt_out}'。"
        "把文件里的内容当作唯一任务规格；不要复述文件正文，不要先总结，不要先反问，直接按其中要求启动完整流程并落盘。"
    )

    if ns.mode == "agent":
        print(textwrap.dedent(
            f"""\
            [loop9] Prompt file created:
            {prompt_out}
            [loop9] Policy:
            {ns.policy}

            [loop9] Starting OpenCode directly with agent: loop9-controller
            [loop9] Prompt:
            {prompt_text}
            """
        ).rstrip())
        print(
            "第1次尝试修复、Agent模式存在较多不稳定因素————比如不遵从预先指令，暂时不做采用。  "
            "第2次尝试修复、在努力和command模式贴近后，仍然有【一半概率】会自己去挖洞、而非调用子SubAgent工作流————所以暂时放弃。"
        )
        raise SystemExit(1)

    print(textwrap.dedent(
        f"""\
        [loop9] Prompt file created:
        {prompt_out}
        [loop9] Policy:
        {ns.policy}

        [loop9] Starting OpenCode run in command mode
        [loop9] Command:
        loop9
        [loop9] Arguments:
        {prompt_text}
        """
    ).rstrip())

    result = launch_opencode_run(OpenCodeRunConfig(
        workflow_name='loop9-wrapped-audit',
        repo_root=repo_root,
        observe_root=observe_root,
        prompt_dir=prompt_dir,
        label=f'{target_name}-{ns.mode}',
        prompt_file_stem=f'{target_name}{policy_suffix}',
        prompt_content=authoritative_header + rce_pre_scan_header + filled,
        prompt_text=prompt_text,
        prompt_out_override=prompt_out,
        command_name='loop9',
        transport=ns.transport,
        extra_run_meta={
            'mode': ns.mode,
            'policy': ns.policy,
            'template': str(template),
            'target_name': target_name,
            'target_path': str(target_path),
            'run_kind': 'audit-root',
            'prompt_modules': applied_prompt_modules,
            'rce_pre_scan': rce_pre_scan,
        },
        launch_summary_extra={
            'policy': ns.policy,
        },
        tmux_session_prefix='loop9',
        fixed_agent=LOOP9_FIXED_AGENT,
        enable_session_export=True,
        stamp_override=stamp,
        dry_run=False,
    ))

    if result.get('status') == 'launched-in-tmux':
        print(textwrap.dedent(
            f"""\
            [loop9] tmux session started:
            {result['tmux_session']}
            [loop9] Attach with:
            tmux attach -t {result['tmux_session']}
            [loop9] Observe dir:
            {result['obs_dir']}
            """
        ).rstrip())
        raise SystemExit(0)

    raise SystemExit(0)


if __name__ == "__main__":
    main()
