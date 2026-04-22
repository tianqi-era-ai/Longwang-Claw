# Loop9 heartbeat dispatch

This file defines how heartbeat should dispatch Loop9 status checks.

## Role split

- `HEARTBEAT.md` = top-level heartbeat index / scheduler entry
- `workspace/skills/loop9-status/SKILL.md` = Loop9 status interpretation + user-facing formatting
- This file = heartbeat-side dispatch, throttling, and fallback rules for Loop9

## Canonical skill

- Treat `workspace/skills/loop9-status/SKILL.md` as the canonical Loop9 status-summary skill.
- `loop9-status` is a **general skill**:
  - it may be called manually by a human,
  - and it may also be called by heartbeat.
- Do **not** copy or reimplement the skill's human-readable output format here.
- In particular, red/yellow/green card-style formatting belongs to `loop9-status`, not to heartbeat dispatch docs.

## Preferred execution mode

- When heartbeat needs a Loop9 check, prefer invoking `loop9-status` via an isolated **SubAgent-style** task.
- Goal:
  - keep heartbeat as the scheduler / coordinator,
  - keep `loop9-status` as the Loop9 interpreter / formatter,
  - reduce context pollution and avoid one check blocking unrelated heartbeat work.
- Keep this thin: dispatch the check, collect the result, decide whether to notify. Do not build a heavy framework around it.

## Minimum interval / anti-spam rule

- The 10-minute minimum interval applies **only** to heartbeat-triggered calls of `loop9-status`.
- Use this state file as the coordinator's minimal source of truth:
  - `workspace/memory/heartbeat-state.json`
- For Loop9 checks, read and update only the `loop9Status` section.
- If less than 10 minutes have passed since `loop9Status.lastHeartbeatInvocationAt`, do **not** invoke `loop9-status` again in this heartbeat round.
- This limit does **not** apply to explicit manual / human-triggered `loop9-status` use.
- Purpose: avoid pathological high-frequency repeated status checks under retry / scheduling jitter.

## Coordinator behavior

### Extra guardrail: publish-lock observation (non-intrusive)

Because Loop9 publish runs can terminate after doing real work but before releasing the publish lock, heartbeat should *observe* (not auto-fix) this condition:

- Check `workspace/automation-state/loop9/locks/publish.json` when present.
- If the lock exists but the recorded `pid` is not running anymore, treat it as a **stale-lock suspicion**.
- Do **not** auto-clear the lock by default (user wants to observe first).
- Only surface it in the Loop9 heartbeat summary when either:
  - it persists for >30 minutes, or
  - it blocks publish for 2+ consecutive publish cron rounds.

For Loop9 heartbeat checks:

1. Decide whether Loop9 is a task that should be checked this round.
2. Read `workspace/memory/heartbeat-state.json` and inspect `loop9Status.lastHeartbeatInvocationAt`.
3. If the last heartbeat-triggered invocation was under 10 minutes ago, skip this Loop9 skill dispatch for this round.
4. Otherwise, immediately update `loop9Status.lastHeartbeatInvocationAt` to the current round time and dispatch the check via an isolated subtask.
5. Prefer `sessions_spawn` with:
   - `runtime="subagent"`
   - `mode="run"`
   - `cleanup="delete"`
   - attachment / prompt source: `workspace/prompts/heartbeat-loop9-status-subagent.md`
6. The subtask must read and follow `workspace/skills/loop9-status/SKILL.md` and return either:
   - a final user-facing Loop9 status summary, or
   - exactly `NO_CHANGE`
7. If the subtask returns `NO_CHANGE`, stay quiet unless another heartbeat rule independently requires a user-visible sync.
8. If the subtask returns a real summary, use that result as the canonical user-facing Loop9 update for this round.
9. After a real user-visible Loop9 sync is sent, update `loop9Status.lastHeartbeatSummaryAt`; if practical, also store a lightweight content fingerprint in `loop9Status.lastHeartbeatSummaryHash` to help avoid duplicate summaries.

## Fallback only if the skill path is unavailable or insufficient

- Only if `loop9-status` cannot be used, fall back to the raw canonical status script:
  - `~/.openclaw/workspace/Super8/.opencode/_scripts/loop9_status.sh`
- Treat that script as the primary source of truth for underlying Loop9 state.
- Read and use these sections first when present:
  - `[fleet]` for active waves / unique targets / whether multiple waves are running
  - `[observe]` for latest task identity and tmux state
  - `[heartbeat_context]` for latest activity timestamp, last user-visible sync, and whether sync is due
  - `[loop9-run-dir]` / `[reports]` for deliverables and validation state
- Only if the script output is missing, stale, or obviously insufficient, fall back further to direct inspection of:
  - `~/.openclaw/workspace/Super8/temp/loop9-observe/`
  - `~/.openclaw/workspace/Super8/temp/loop9/`
  - latest OpenCode session in `Super8`
- Determine whether the task is:
  - still progressing,
  - completed with usable output,
  - stalled,
  - or failed.
- If there is meaningful new progress, notify 大黑客 with a short update.
- If a final audit/report file appears, summarize the result and mention the output path.
- Do not kill the long-running task just because it is slow.
- Treat 1-2 hours as normal for this class of task; 3-5 hours is possible.
- If nothing materially changed since the last check, stay quiet.
