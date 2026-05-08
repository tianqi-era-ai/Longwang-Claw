---
name: loop9-wrapped-audit
description: Launch the Super8 Loop9 wrapper for a local target path from chat. In the user's real usage, this skill may be used in two ways: (1) launch the standardized audit directly for an already-materialized local target path, or (2) under `weibu-submission`, first read the provided scope/reference materials, proactively discover a suitable target with a mainland-China usage bias (Gitee first, GitCode second, GitHub only as a narrow exception lane), materialize it locally under `targets/`, and then launch the standardized audit. Use when the user wants the full standardized Loop9 audit entry workflow rather than ad-hoc manual commands.
user-invocable: true
metadata: {"openclaw":{"emoji":"🦞","os":["darwin","linux"],"requires":{"bins":["python3","bash"]}}}
---

Start the Super8 Loop9 workflow only through the wrapper script below.

## Canonical entrypoint

```bash
cd ~/.openclaw/workspace/Super8
./.opencode/_scripts/loop9_authorized_review.py [--policy internal-full-audit|weibu-submission] <local-target-path>
```

Use `exec` to run it on the host.

## Arguments

Pass either:
- a raw local target path, or
- an optional policy flag followed by the local target path.

Important real-usage note:
- In the user's common manual prompt style, this skill is also used as a **full business workflow entrypoint** for `weibu-submission`: read range/reference materials, proactively discover a suitable target (mainland-China usage bias; Gitee first, GitCode second, GitHub only as a narrow exception lane), materialize it locally, then launch the wrapper.
- So this skill should not be mentally reduced to “only a path launcher”; that is too narrow for the user's actual established usage.

Supported policies:
- `--policy internal-full-audit` — default internal full-audit mode; suitable for internal code-security review of legitimate product/source targets
- `--policy weibu-submission` — 微步在线收录口径模式; target choice should be narrower and aligned with 微步-style collection/submission fit rather than broad internal audit coverage

Examples of valid inputs:
- `~/.openclaw/workspace/targets/apache-shiro`
- `--policy internal-full-audit ~/.openclaw/workspace/targets/apache-shiro`
- `--policy weibu-submission ~/.openclaw/workspace/targets/maccms10`
- `/absolute/path/to/local/repo`

If the user gives a GitHub URL instead of a local path, stop and ask whether they want you to first materialize it locally.

## Target-boundary reminder

This skill must respect the user's real business modes.

Important distinctions:
- `internal-full-audit` and `weibu-submission` are **different business modes** with different project/vulnerability collection ranges.
- In the user's real usage, `weibu-submission` is not merely “run wrapper on an existing local path”; it often means:
  - read 微步范围与参照材料
  - proactively discover a suitable target with a **mainland-China usage bias**
  - default source priority: `gitee` first, `gitcode` second, `github` only as a narrow exception lane
  - skip already-processed local targets
  - use `loop9-asset-evidence` as a default value-gate before launch once a repo-side candidate looks plausibly usable
  - when that formal asset-evidence judgment is performed, update `skills/loop9-asset-evidence/references/history-cases.md` in the compact index format instead of leaving history sync as a manual follow-up
  - if one candidate already passes the launch-value floor, it may be chosen directly; do not artificially keep collecting 1-3 candidates just to compare them
  - only when multiple candidates all pass the floor and still remain ambiguous should `loop9-asset-evidence` act as a thin comparison layer
  - materialize one chosen target locally
  - then call the standard wrapper
- For proactive `weibu-submission` discovery, treat these as **hard gates**, not soft preferences:
  - target fits the default business meaning of “中国大陆正在使用的 CMS / OA / 常见 WEB 应用 / 相关通用软件”
  - if the target is from overseas / GitHub, it must clearly fall into a narrow exception lane:
    - explicitly named by 微步 / range materials, or
    - a foundational component widely used by Chinese products/frameworks (for example Apache / Shiro), or
    - a foreign product with strong real-world China gov/SOE/enterprise usage
  - company/vendor projects are preferred; personal projects only remain when their impact surface is clearly broad enough
  - star thresholds apply uniformly across GitHub / Gitee / GitCode:
    - company/vendor project: `stars >= 1000`
    - personal project: `stars >= 1500`
  - repo/project is not already processed / already running locally
  - repo/project is not a deliberately insecure training ground / 靶场 / educational vulnerable app
  - for platforms exposing those fields: repo is not archived and not a fork
  - for GitHub: `pushedAt >= 当前执行时间 - 6个月`
  - for GitCode: watch for mirror risk; a likely GitHub mirror should not be promoted by default
- About recency:
  - use `pushedAt` as the primary maintenance signal on GitHub; do **not** substitute `updatedAt`, because it can be polluted by issue / release / metadata activity
  - on Gitee / GitCode, prefer visible code-maintenance signals from the project page rather than vague popularity impressions
- Deliberately insecure training grounds / 靶场 / educational vulnerable apps (for example `pikachu`, `WebGoat`) may still be launched manually when the human explicitly wants that, but they must **not** be treated as default automatic choices for this proactive `weibu-submission` path.
- Ranking among already-eligible candidates should also consider **audit ROI / 性价比**:
  - star count is not the only ranking signal
  - under the same business fit, do not blindly prefer the hardest, most battle-tested industry head just because it is bigger
- Important correction: do **not** hardcode the fuzzy discovery / suitability brain into local Python scripts. Prefer dynamic skill orchestration for the discovery step. If a script is used at all, keep it limited to strong-precision chores after discovery is already done.

Read these references when needed:
- `references/proactive-discovery-mode.md`
- `references/query-source-format.md`
- `references/candidate-source-format.md`
- `references/candidate-discovery-queries.md`

Important clarification rule:
- If the user later explicitly says to first download/clone/materialize the repo locally and then launch the audit, treat that as sufficient authorization and proceed.
- Do not ask the same local-materialization question again within the same request flow after the user has already clearly confirmed it.
- After explicit confirmation, choose a sensible local target path under `~/.openclaw/workspace/targets/` (for example `~/.openclaw/workspace/targets/<repo-name>`) and continue directly.

Robust execution rule for remote repositories:
- Do **not** combine `git clone ... && wrapper-launch` into one long foreground shell chain.
- First materialize the repository as its **own step**.
- Then verify the local repo exists (for example `.git` exists or `git rev-parse --is-inside-work-tree` succeeds).
- Only after that, launch the Super8 wrapper as a **second separate step**.
- Reason: if the first foreground exec is interrupted/killed (for example heartbeat preemption, runtime interruption, or outer session cancellation), a one-shot chained command can leave the repo cloned but skip the wrapper launch entirely.
- Prefer a stability-first clone strategy when appropriate (for ordinary source audit setup, shallow clone is acceptable unless full history is specifically needed).

## Required execution behavior

- Always use the wrapper script as the single blessed entrypoint.
- Do not manually reconstruct the OpenCode command unless debugging the wrapper itself.
- Prefer the wrapper default behavior rather than adding extra flags.
- Treat this as a long-running background workflow.
- Do not manually kill the process just because it appears slow.

## Long-running task policy

This workflow is expected to be slow.

Operational guidance:
- 1-2 hours is normal.
- 3-5 hours is possible.
- Early stages may only show file reads, glob searches, todo creation, or partial output.
- Lack of a full Loop9 artifact tree in the first minute does not mean failure.
- Prefer launching, confirming, then checking progress later.

## Progress checks

When the user asks for progress, inspect in this order:

1. `~/.openclaw/workspace/Super8/temp/loop9-observe/`
2. `~/.openclaw/workspace/Super8/temp/loop9/`
3. latest OpenCode session for `Super8`
4. report files in `~/.openclaw/workspace/Super8/temp/`

Notify the user when there is meaningful progress or a usable report.

## Known pitfalls

- Use the wrapper, not ad-hoc hand-built command strings.
- Command mode has shown the best real progress in this environment, but it can still be noisy or slow.
- Runtime references to `skill(name="loop9")` do not necessarily mean an old leftover Loop9 skill; command and skill resolution may share an entry surface.
- The workflow may produce useful audit files before it perfectly matches the ideal `temp/loop9/<run_id>/...` shape.
- This skill is an outer OpenClaw/Telegram entrypoint only; it must not become part of local Loop9 recursion.

## Response style after launch

After starting the workflow, reply briefly with:
- the target path
- that the standardized Super8 wrapper has been launched
- that this is a long-running background task
- that updates will be sent when meaningful progress appears
