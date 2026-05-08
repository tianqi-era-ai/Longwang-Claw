#!/usr/bin/env bash
set -euo pipefail

umask 077

WORKSPACE="${WORKSPACE:-${LONGWANG_WORKSPACE:-$HOME/.openclaw/workspace}}"
LONGWANG_ENV_FILE="${LONGWANG_ENV_FILE:-$WORKSPACE/config/longwang.env}"
if [ -f "$LONGWANG_ENV_FILE" ]; then
  # shellcheck disable=SC1090
  . "$LONGWANG_ENV_FILE"
fi

WORKSPACE="${WORKSPACE:-${LONGWANG_WORKSPACE:-$HOME/.openclaw/workspace}}"
CODEX_BIN="${CODEX_BIN:-${LONGWANG_CODEX_BIN:-codex}}"
REMOTE_RUNTIME_LABEL="${LONGWANG_REMOTE_RUNTIME_LABEL:-remote Docker/CVM}"
REMOTE_RUNTIME_PROMPT="${LONGWANG_REMOTE_RUNTIME_PROMPT:-$REMOTE_RUNTIME_LABEL}"
RUN_ROOT="$WORKSPACE/runs/loop9-verify-v4-auto"
LOCK_DIR="$WORKSPACE/tmp/loop9-verify-v4-auto.lock"
PID_FILE="$LOCK_DIR/pid"
CURRENT_TASK_FILE="$RUN_ROOT/00-current-task.md"
RUN_STATE_NAME="run-state.md"
RECOVERY_NOTE_NAME="01-recovery-note.md"

DEFAULT_PROMPT="$(cat <<EOF
请使用【$WORKSPACE/skills/loop9-verify-v4/SKILL.md】和【$WORKSPACE/skills/ai-native-development/SKILL.md】skill。自己选择 Repo，采用 ${REMOTE_RUNTIME_PROMPT} 搭建环境，完成完整的 repo-complete 流程。
硬约束：
1. 某个 repo 一旦已经 truthfully 达到 \`repo-mainline-done\`，并且已有 \`98-delivery-bundle.manifest.json\`、\`99-最终本地复盘.*\`、以及显式 sedimentation 结果，后续 auto-run 默认必须切到下一个未完成 repo；不要把新的整点机会继续花在这个已完成 repo 的 live 复核、状态同步、验活上。
2. 已完成 repo 默认最多只允许一次轻量 post-closure 验活，而且应尽量放在同一次 repo mainline run 内完成；后续周期性状态检查属于 monitor/heartbeat/status 工作，不属于新的 repo-complete 主线。
3. 在共享 ${REMOTE_RUNTIME_LABEL} 上，默认只保留当前决定性 runtime 为热态；与当前主线无关的旧容器/旧运行态要及时释放。需要保留的旧结果优先保留为冷快照，不要长期维持为运行中容器占用内存。
4. 不要把已完成 repo 叙述成“这轮又自动选择了它”，除非这次是显式 reopen。
5. 如果【${CURRENT_TASK_FILE}】显示已有同一未完成 auto task，则必须优先继续该任务，不得借 fresh auto-select 绕开它。
EOF
)"
PROMPT="${LOOP9_VERIFY_V4_PROMPT:-$DEFAULT_PROMPT}"

CURRENT_TASK_ID=""
CURRENT_TASK_STATE=""
CURRENT_TASK_ORIGIN_RUN=""
CURRENT_TASK_OPENED_AT=""
CURRENT_TASK_LAST_ATTEMPT_AT=""
CURRENT_TASK_LAST_RUN_DIR=""
CURRENT_TASK_LAST_SESSION_ID=""
CURRENT_TASK_LAST_RESULT_CLASS=""
CURRENT_TASK_LAST_FAILURE_KIND=""
CURRENT_TASK_NEXT_MODE=""
CURRENT_TASK_LAST_FINAL_MESSAGE=""
CURRENT_TASK_LAST_LAUNCH_MODE=""

cleanup() {
  if [ -f "$PID_FILE" ] && [ "$(cat "$PID_FILE" 2>/dev/null || true)" = "$$" ]; then
    rm -rf "$LOCK_DIR"
  fi
}

acquire_lock() {
  mkdir -p "$WORKSPACE/tmp" "$RUN_ROOT"

  if mkdir "$LOCK_DIR" 2>/dev/null; then
    printf '%s\n' "$$" >"$PID_FILE"
    return 0
  fi

  local current_pid=""
  if [ -f "$PID_FILE" ]; then
    current_pid="$(cat "$PID_FILE" 2>/dev/null || true)"
  fi

  if [ -n "$current_pid" ] && kill -0 "$current_pid" 2>/dev/null; then
    printf '[skip] existing run is still active (pid=%s)\n' "$current_pid"
    return 1
  fi

  rm -rf "$LOCK_DIR"
  mkdir "$LOCK_DIR"
  printf '%s\n' "$$" >"$PID_FILE"
}

md_get_value() {
  local file="$1"
  local key="$2"

  [ -f "$file" ] || return 0

  awk -v key="$key" '
    index($0, "- " key ": ") == 1 {
      value = substr($0, length("- " key ": ") + 1)
      sub(/^`/, "", value)
      sub(/`$/, "", value)
      print value
      exit
    }
  ' "$file"
}

extract_session_id_from_log() {
  local log_file="$1"

  [ -f "$log_file" ] || return 0

  awk '
    NR <= 120 {
      lower = tolower($0)
      if (index(lower, "session id: ") == 1) {
        sub(/^[^:]+: /, "", $0)
        print $0
        exit
      }
    }
  ' "$log_file"
}

session_file_for_id() {
  local session_id="$1"

  [ -n "$session_id" ] || return 0
  [ -d "$HOME/.codex/sessions" ] || return 0

  find "$HOME/.codex/sessions" -type f -name "rollout-*${session_id}.jsonl" -print -quit 2>/dev/null || true
}

classify_failure_kind() {
  local log_file="$1"
  local excerpt=""

  if [ -f "$log_file" ]; then
    excerpt="$(tail -n 200 "$log_file" 2>/dev/null || true)"
  fi

  if printf '%s\n' "$excerpt" | grep -Eiq 'Too Many Requests|429'; then
    printf '%s\n' 'provider-429'
  elif printf '%s\n' "$excerpt" | grep -Eiq '403 Forbidden|(^|[^0-9])403([^0-9]|$)'; then
    printf '%s\n' 'provider-403'
  elif printf '%s\n' "$excerpt" | grep -Eiq 'stream disconnected before completion|Transport error|network error|error decoding response body'; then
    printf '%s\n' 'transport-stream-disconnect'
  elif printf '%s\n' "$excerpt" | grep -Eiq 'ERROR: Reconnecting'; then
    printf '%s\n' 'transport-reconnect'
  elif printf '%s\n' "$excerpt" | grep -Eiq 'timed out|timeout'; then
    printf '%s\n' 'timeout-or-budget'
  else
    printf '%s\n' 'nonzero-unknown'
  fi
}

result_class_for_failure() {
  local failure_kind="$1"

  case "$failure_kind" in
    provider-429|provider-403|transport-*)
      printf '%s\n' 'interrupted-transport'
      ;;
    timeout-or-budget)
      printf '%s\n' 'interrupted-timeout'
      ;;
    *)
      printf '%s\n' 'interrupted-nonzero'
      ;;
  esac
}

load_current_task() {
  CURRENT_TASK_ID="$(md_get_value "$CURRENT_TASK_FILE" task_id)"
  CURRENT_TASK_STATE="$(md_get_value "$CURRENT_TASK_FILE" task_state)"
  CURRENT_TASK_ORIGIN_RUN="$(md_get_value "$CURRENT_TASK_FILE" task_origin_run)"
  CURRENT_TASK_OPENED_AT="$(md_get_value "$CURRENT_TASK_FILE" opened_at)"
  CURRENT_TASK_LAST_ATTEMPT_AT="$(md_get_value "$CURRENT_TASK_FILE" last_attempt_at)"
  CURRENT_TASK_LAST_RUN_DIR="$(md_get_value "$CURRENT_TASK_FILE" last_run_dir)"
  CURRENT_TASK_LAST_SESSION_ID="$(md_get_value "$CURRENT_TASK_FILE" last_session_id)"
  CURRENT_TASK_LAST_RESULT_CLASS="$(md_get_value "$CURRENT_TASK_FILE" last_result_class)"
  CURRENT_TASK_LAST_FAILURE_KIND="$(md_get_value "$CURRENT_TASK_FILE" last_failure_kind)"
  CURRENT_TASK_NEXT_MODE="$(md_get_value "$CURRENT_TASK_FILE" next_mode)"
  CURRENT_TASK_LAST_FINAL_MESSAGE="$(md_get_value "$CURRENT_TASK_FILE" last_final_message)"
  CURRENT_TASK_LAST_LAUNCH_MODE="$(md_get_value "$CURRENT_TASK_FILE" last_launch_mode)"

  if [ -z "$CURRENT_TASK_LAST_SESSION_ID" ] && [ -n "$CURRENT_TASK_LAST_RUN_DIR" ]; then
    CURRENT_TASK_LAST_SESSION_ID="$(extract_session_id_from_log "$CURRENT_TASK_LAST_RUN_DIR/codex.log")"
  fi
}

build_resume_prompt() {
  local previous_run_dir="$1"
  local previous_run_state="${previous_run_dir:+$previous_run_dir/$RUN_STATE_NAME}"
  local previous_recovery_note="${previous_run_dir:+$previous_run_dir/$RECOVERY_NOTE_NAME}"

  cat <<EOF
请继续同一个未完成的【loop9-verify-v4-auto】任务。这不是 fresh auto-select 重开。
先读取：
- $CURRENT_TASK_FILE
- ${previous_run_state:-$RUN_ROOT/<previous-run-missing>/$RUN_STATE_NAME}
- ${previous_recovery_note:-$RUN_ROOT/<previous-run-missing>/$RECOVERY_NOTE_NAME}
- $WORKSPACE/skills/loop9-verify-v4/SKILL.md
- $WORKSPACE/skills/ai-native-development/SKILL.md
恢复硬约束：
1. 先以当前 workspace 里的 canonical artifacts、accepted current-round anchors、round root、delivery tail frontier 为准，判断上一条 mainline 目前停在何处。
2. 优先继续同一未完成 repo mainline；不要重新 auto-select 新 repo，不要重复已经 truthfully 完成的 stage。
3. 如果 session 内历史叙述与当前 workspace truth 冲突，以当前 workspace canonical artifacts 为准。
4. 只有在你先 truthfully 证明上一任务已经完成、或 truthfully 不再能作为同一 mainline 继续时，才允许释放这个 current task 并回到 fresh auto-select。
5. 429 / reconnect / stream disconnect / provider-side interruption 属于 transport/provider 失败，不是 repo semantic closure。
EOF
}

build_cold_recovery_prompt() {
  local previous_run_dir="$1"
  local previous_run_state="${previous_run_dir:+$previous_run_dir/$RUN_STATE_NAME}"
  local previous_recovery_note="${previous_run_dir:+$previous_run_dir/$RECOVERY_NOTE_NAME}"

  cat <<EOF
请使用【$WORKSPACE/skills/loop9-verify-v4/SKILL.md】和【$WORKSPACE/skills/ai-native-development/SKILL.md】skill。
这是【loop9-verify-v4-auto】对同一未完成任务的冷恢复，不是 fresh auto-select 重开。
先读取：
- $CURRENT_TASK_FILE
- ${previous_run_state:-$RUN_ROOT/<previous-run-missing>/$RUN_STATE_NAME}
- ${previous_recovery_note:-$RUN_ROOT/<previous-run-missing>/$RECOVERY_NOTE_NAME}
冷恢复硬约束：
1. 先根据 current task pointer + 当前 workspace 的 canonical artifacts / accepted current-round anchors / round root / delivery tail，重建上一条 mainline 现在的真实 frontier。
2. 优先继续同一未完成 repo mainline，不要重做已经 truthfully 完成的 stage，不要重新 auto-select 新 repo。
3. 只有在你先根据 workspace truth 证明上一任务已经 truthfully 完成、或 truthfully 无法再作为同一 mainline 继续时，才允许结束这条 current task 并回到 fresh auto-select。
4. transport/provider failure 不是 repo semantic failure；不要因为上一轮 429 / reconnect / stream disconnect 就把 repo 误读成已关闭或释放到新 repo。
5. 这次冷恢复的 transport 是新的，但语义任务仍是同一个未完成任务。
EOF
}

write_current_task_file() {
  local task_id="$1"
  local task_state="$2"
  local task_origin_run="$3"
  local opened_at="$4"
  local last_attempt_at="$5"
  local last_run_dir="$6"
  local last_session_id="$7"
  local last_result_class="$8"
  local last_failure_kind="$9"
  local next_mode="${10}"
  local last_final_message="${11}"
  local last_launch_mode="${12}"

  cat >"$CURRENT_TASK_FILE" <<EOF
# current-task — loop9-verify-v4-auto

## task identity
- task_id: \`$task_id\`
- task_state: \`$task_state\`
- task_origin_run: \`${task_origin_run:-none}\`
- opened_at: \`$opened_at\`
- last_attempt_at: \`$last_attempt_at\`

## bridge posture
- last_run_dir: \`${last_run_dir:-none}\`
- last_session_id: \`${last_session_id:-none}\`
- last_result_class: \`$last_result_class\`
- last_failure_kind: \`$last_failure_kind\`
- next_mode: \`$next_mode\`
- last_final_message: \`${last_final_message:-none}\`
- last_launch_mode: \`$last_launch_mode\`

## control reading
- continuation_rule: \`same unfinished task must be recovered before fresh auto-select\`
- state_owner: \`workspace canonical artifacts + accepted current-round anchors\`
EOF
}

write_run_state_file() {
  local file="$1"
  local stamp="$2"
  local task_id="$3"
  local attempt_state="$4"
  local launch_mode="$5"
  local result_class="$6"
  local failure_kind="$7"
  local session_id="$8"
  local session_file="$9"
  local next_mode="${10}"
  local exit_code="${11}"
  local final_message="${12}"
  local previous_run_dir="${13}"

  cat >"$file" <<EOF
# run-state — $stamp

## attempt identity
- run_dir: \`$RUN_ROOT/$stamp\`
- task_id: \`$task_id\`
- attempt_state: \`$attempt_state\`
- launch_mode: \`$launch_mode\`
- previous_run_dir: \`${previous_run_dir:-none}\`

## transport receipt
- result_class: \`$result_class\`
- failure_kind: \`$failure_kind\`
- session_id: \`${session_id:-none}\`
- session_file: \`${session_file:-none}\`
- exit_code: \`$exit_code\`
- final_message: \`${final_message:-none}\`
- next_mode: \`$next_mode\`

## control reading
- workspace_truth_owner: \`repo round roots / boards / objects / artifacts / delivery tail\`
- recurring_rule: \`same unfinished task before fresh auto-select\`
EOF
}

write_recovery_note_file() {
  local file="$1"
  local task_state="$2"
  local result_class="$3"
  local failure_kind="$4"
  local launch_mode="$5"
  local next_mode="$6"
  local session_id="$7"

  if [ "$task_state" = "completed" ]; then
    cat >"$file" <<EOF
# recovery-note

## current reading

- task_state: \`completed\`
- launch_mode: \`$launch_mode\`
- result_class: \`$result_class\`
- next_mode: \`fresh-auto-select\`

## scheduler note

- the current task pointer is closed
- the next recurring slot may perform a fresh auto-select
- later live/status checks of this delivered repo do not belong to repo-complete auto-run by default
EOF
    return 0
  fi

  cat >"$file" <<EOF
# recovery-note

## current reading

- task_state: \`active\`
- launch_mode: \`$launch_mode\`
- result_class: \`$result_class\`
- failure_kind: \`$failure_kind\`
- preferred_next_mode: \`$next_mode\`
- session_id: \`${session_id:-none}\`

## next-slot contract

- recover the same unfinished task before any fresh auto-select
- if \`preferred_next_mode = resume\`, use the recorded session first
- if \`preferred_next_mode = cold-recovery\`, start a fresh carrier but reconstruct frontier from workspace truth before any repo reselection
- do not treat transport/provider failure as repo closure
- do not release the slot to a different repo until the current task is truthfully closed or truthfully unrecoverable as the same mainline
EOF
}

run_codex_attempt() {
  local launch_mode="$1"
  local session_id="$2"
  local final_message="$3"
  local prompt="$4"
  local log_file="$5"

  local exit_code=0

  set +e
  if [ "$launch_mode" = "resume" ]; then
    "$CODEX_BIN" exec \
      --color never \
      -C "$WORKSPACE" \
      resume \
      --skip-git-repo-check \
      --dangerously-bypass-approvals-and-sandbox \
      -o "$final_message" \
      "$session_id" \
      "$prompt" \
      2>&1 | tee -a "$log_file"
    exit_code=${PIPESTATUS[0]}
  else
    "$CODEX_BIN" exec \
      --skip-git-repo-check \
      --color never \
      --dangerously-bypass-approvals-and-sandbox \
      -C "$WORKSPACE" \
      -o "$final_message" \
      "$prompt" \
      2>&1 | tee -a "$log_file"
    exit_code=${PIPESTATUS[0]}
  fi
  set -e

  return "$exit_code"
}

resolve_codex_bin() {
  if [ -x "$CODEX_BIN" ]; then
    return 0
  fi

  local resolved=""
  resolved="$(command -v "$CODEX_BIN" 2>/dev/null || true)"
  if [ -n "$resolved" ] && [ -x "$resolved" ]; then
    CODEX_BIN="$resolved"
    return 0
  fi

  printf '[error] codex binary not found or not executable: %s\n' "$CODEX_BIN" >&2
  return 1
}

main() {
  if ! resolve_codex_bin; then
    return 127
  fi

  if ! acquire_lock; then
    return 0
  fi
  trap cleanup EXIT INT TERM

  load_current_task

  local stamp run_dir log_file final_message run_state_file recovery_note_file
  local task_id task_origin_run opened_at last_attempt_at
  local launch_mode prompt_for_attempt resume_session_id session_file previous_run_dir
  local exit_code captured_session_id failure_kind result_class next_mode
  local attempt_state last_final_message started_at finished_at

  stamp="$(date '+%Y%m%d-%H%M%S')-$$"
  run_dir="$RUN_ROOT/$stamp"
  mkdir -p "$run_dir"
  log_file="$run_dir/codex.log"
  final_message="$run_dir/final-message.txt"
  run_state_file="$run_dir/$RUN_STATE_NAME"
  recovery_note_file="$run_dir/$RECOVERY_NOTE_NAME"
  started_at="$(date '+%Y-%m-%d %H:%M:%S %z')"

  if [ "$CURRENT_TASK_STATE" = "active" ] && [ -n "$CURRENT_TASK_ID" ]; then
    task_id="$CURRENT_TASK_ID"
    task_origin_run="${CURRENT_TASK_ORIGIN_RUN:-$CURRENT_TASK_LAST_RUN_DIR}"
    opened_at="${CURRENT_TASK_OPENED_AT:-$started_at}"
    previous_run_dir="$CURRENT_TASK_LAST_RUN_DIR"
    resume_session_id="$CURRENT_TASK_LAST_SESSION_ID"
    session_file="$(session_file_for_id "$resume_session_id")"

    case "${CURRENT_TASK_NEXT_MODE:-resume}" in
      cold-recovery)
        launch_mode="cold-recovery"
        ;;
      resume)
        if [ -n "$resume_session_id" ] && [ -n "$session_file" ]; then
          launch_mode="resume"
        else
          launch_mode="cold-recovery"
        fi
        ;;
      *)
        if [ -n "$resume_session_id" ] && [ -n "$session_file" ]; then
          launch_mode="resume"
        else
          launch_mode="cold-recovery"
        fi
        ;;
    esac
  else
    task_id="$stamp"
    task_origin_run="$run_dir"
    opened_at="$started_at"
    previous_run_dir=""
    resume_session_id=""
    session_file=""
    launch_mode="fresh-exec"
  fi

  case "$launch_mode" in
    resume)
      prompt_for_attempt="$(build_resume_prompt "$previous_run_dir")"
      ;;
    cold-recovery)
      prompt_for_attempt="$(build_cold_recovery_prompt "$previous_run_dir")"
      ;;
    *)
      prompt_for_attempt="$PROMPT"
      ;;
  esac

  write_current_task_file \
    "$task_id" \
    "active" \
    "$task_origin_run" \
    "$opened_at" \
    "$started_at" \
    "$run_dir" \
    "${resume_session_id:-$CURRENT_TASK_LAST_SESSION_ID}" \
    "running" \
    "in-progress" \
    "$launch_mode" \
    "$final_message" \
    "$launch_mode"

  write_run_state_file \
    "$run_state_file" \
    "$stamp" \
    "$task_id" \
    "running" \
    "$launch_mode" \
    "running" \
    "in-progress" \
    "${resume_session_id:-$CURRENT_TASK_LAST_SESSION_ID}" \
    "$session_file" \
    "$launch_mode" \
    "running" \
    "$final_message" \
    "$previous_run_dir"

  {
    printf '[start] %s\n' "$started_at"
    printf '[workspace] %s\n' "$WORKSPACE"
    printf '[run_dir] %s\n' "$run_dir"
    printf '[codex] %s\n' "$CODEX_BIN"
    printf '[task_id] %s\n' "$task_id"
    printf '[launch_mode] %s\n' "$launch_mode"
    printf '[previous_run_dir] %s\n' "${previous_run_dir:-none}"
    printf '[resume_session_id] %s\n' "${resume_session_id:-none}"
    printf '[current_task_file] %s\n' "$CURRENT_TASK_FILE"
  } | tee -a "$log_file"

  if run_codex_attempt "$launch_mode" "$resume_session_id" "$final_message" "$prompt_for_attempt" "$log_file"; then
    exit_code=0
  else
    exit_code=$?
  fi

  captured_session_id="$(extract_session_id_from_log "$log_file")"
  if [ -z "$captured_session_id" ]; then
    captured_session_id="$resume_session_id"
  fi
  session_file="$(session_file_for_id "$captured_session_id")"

  finished_at="$(date '+%Y-%m-%d %H:%M:%S %z')"
  last_attempt_at="$finished_at"
  last_final_message="$final_message"

  if [ "$exit_code" -eq 0 ]; then
    attempt_state="finished"
    result_class="completed"
    failure_kind="none"
    next_mode="fresh-auto-select"
    write_current_task_file \
      "$task_id" \
      "completed" \
      "$task_origin_run" \
      "$opened_at" \
      "$last_attempt_at" \
      "$run_dir" \
      "$captured_session_id" \
      "$result_class" \
      "$failure_kind" \
      "$next_mode" \
      "$last_final_message" \
      "$launch_mode"
    write_run_state_file \
      "$run_state_file" \
      "$stamp" \
      "$task_id" \
      "$attempt_state" \
      "$launch_mode" \
      "$result_class" \
      "$failure_kind" \
      "$captured_session_id" \
      "$session_file" \
      "$next_mode" \
      "$exit_code" \
      "$final_message" \
      "$previous_run_dir"
    write_recovery_note_file \
      "$recovery_note_file" \
      "completed" \
      "$result_class" \
      "$failure_kind" \
      "$launch_mode" \
      "$next_mode" \
      "$captured_session_id"
  else
    attempt_state="finished"
    failure_kind="$(classify_failure_kind "$log_file")"
    result_class="$(result_class_for_failure "$failure_kind")"
    if [ -n "$captured_session_id" ] && [ -n "$session_file" ]; then
      next_mode="resume"
    else
      next_mode="cold-recovery"
    fi

    write_current_task_file \
      "$task_id" \
      "active" \
      "$task_origin_run" \
      "$opened_at" \
      "$last_attempt_at" \
      "$run_dir" \
      "$captured_session_id" \
      "$result_class" \
      "$failure_kind" \
      "$next_mode" \
      "$last_final_message" \
      "$launch_mode"
    write_run_state_file \
      "$run_state_file" \
      "$stamp" \
      "$task_id" \
      "$attempt_state" \
      "$launch_mode" \
      "$result_class" \
      "$failure_kind" \
      "$captured_session_id" \
      "$session_file" \
      "$next_mode" \
      "$exit_code" \
      "$final_message" \
      "$previous_run_dir"
    write_recovery_note_file \
      "$recovery_note_file" \
      "active" \
      "$result_class" \
      "$failure_kind" \
      "$launch_mode" \
      "$next_mode" \
      "$captured_session_id"
  fi

  {
    printf '[exit_code] %s\n' "$exit_code"
    printf '[captured_session_id] %s\n' "${captured_session_id:-none}"
    printf '[result_class] %s\n' "$result_class"
    printf '[failure_kind] %s\n' "$failure_kind"
    printf '[next_mode] %s\n' "$next_mode"
    printf '[finished] %s\n' "$finished_at"
    printf '[final_message] %s\n' "$final_message"
  } | tee -a "$log_file"

  return "$exit_code"
}

if [ "${BASH_SOURCE[0]}" = "$0" ]; then
  main "$@"
fi
