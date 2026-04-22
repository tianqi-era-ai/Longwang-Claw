# HEARTBEAT.md

# Heartbeat coordinator

This file is the top-level heartbeat index and scheduler entry.

## General rule

- Heartbeat is primarily a **scheduler / coordinator**, not the place to define every skill's user-facing output format.
- When a check belongs to a dedicated skill, prefer dispatching that skill (ideally via isolated subtask / SubAgent-style execution) instead of re-implementing its interpretation inline.
- If a skill owns a display style, keep that display style inside the skill.

## Current checks

### 1) Loop9 long-task monitor

- Use: `workspace/heartbeat/loop9-status-dispatch.md`
- That file defines:
  - when heartbeat should dispatch `loop9-status`
  - the 10-minute anti-spam rule for heartbeat-triggered `loop9-status`
  - the `heartbeat-state.json` fields used by the coordinator
  - the preferred SubAgent dispatch path
  - fallback behavior if the skill path is unavailable

## Proactive sync rule

- Always check timestamps, not just file existence.
- Compare the current time against:
  - the last message I sent 大黑客 about this tracked task,
  - the last meaningful filesystem/log activity,
  - and the expected heartbeat cadence.
- If there has been a large silence gap, I must notice it explicitly and mention it in the next heartbeat reasoning.
- Hard rule: if more than 90 minutes have passed without me sending 大黑客 any update on this tracked long task, send a short sync even if the stage has not changed much yet.
- Hard rule: if more than 2 scheduled heartbeat windows appear to have passed without any user-visible sync from me, treat that itself as a reportable condition.
- If I have been busy for a long time and have not sent 大黑客 an update, send a short heartbeat-based sync when there is a meaningful stage change.
- If things have been quiet for a long time and 大黑客 has not messaged, I may still send a brief heartbeat-based sync if there is useful status to report.
- Prefer short, stage-level updates over chatter.
- Do not spam; but do not ignore obvious time gaps.
- Good sync examples:
  - task has started and is now clearly in long-running background mode
  - a report/shared-context file has appeared
  - a task is likely stalled or exited
  - a new usable result is ready
  - there has been an unusually long silence gap and the task still appears to be running / unchanged
