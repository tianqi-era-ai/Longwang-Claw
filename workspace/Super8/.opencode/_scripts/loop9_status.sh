#!/usr/bin/env bash
set -euo pipefail

ROOT="$HOME/.openclaw/workspace/Super8"
OBS_DIR="$ROOT/temp/loop9-observe"
REAL_POC_OBS_DIR="$ROOT/temp/loop9-real-poc-observe"
REAL_POC_STATUS_HELPER="$HOME/.openclaw/workspace/skills/loop9-real-poc/scripts/refresh_real_poc_status.py"
LOOP9_DIR="$ROOT/temp/loop9"

latest_observe() {
  ls -1dt "$OBS_DIR"/* 2>/dev/null | head -1 || true
}

latest_real_poc_observe() {
  ls -1dt "$REAL_POC_OBS_DIR"/* 2>/dev/null | head -1 || true
}

latest_loop9_dir() {
  ls -1dt "$LOOP9_DIR"/* 2>/dev/null | head -1 || true
}

latest_reports() {
  find "$ROOT/temp" -maxdepth 1 -type f \( -name '*audit-report*.md' -o -name '*audit-medium-notes*.md' -o -name '*audit-shared-context*.md' \) 2>/dev/null | sort || true
}

read_meta_value() {
  local file="$1"
  local key="$2"
  [[ -f "$file" ]] || return 0
  awk -F= -v k="$key" '$1==k {sub($1 FS,""); print; exit}' "$file"
}

print_fleet_overview() {
  local active_count=0
  local -a active_rows=()
  local -a active_targets=()

  [[ -d "$OBS_DIR" ]] || return 0

  while IFS= read -r obs; do
    [[ -n "$obs" ]] || continue
    local meta="$obs/run.meta"
    local tmux_file="$obs/tmux.session.txt"
    local tmux_name=""
    local target_name=""
    local target_path=""
    local started_at=""
    local policy=""

    [[ -f "$tmux_file" ]] || continue
    tmux_name="$(tr -d '\n' < "$tmux_file")"
    [[ -n "$tmux_name" ]] || continue

    if ! command -v tmux >/dev/null 2>&1 || ! tmux has-session -t "$tmux_name" 2>/dev/null; then
      continue
    fi

    active_count=$((active_count + 1))
    target_name="$(read_meta_value "$meta" target_name)"
    target_path="$(read_meta_value "$meta" target_path)"
    policy="$(read_meta_value "$meta" policy)"
    [[ -f "$obs/started_at.txt" ]] && started_at="$(cat "$obs/started_at.txt")"

    [[ -n "$target_path" ]] && active_targets+=("$target_path")
    active_rows+=("obs=$obs | target=${target_name:-unknown} | policy=${policy:-default} | started_at=${started_at:-unknown} | tmux=$tmux_name")
  done < <(find "$OBS_DIR" -maxdepth 1 -mindepth 1 -type d | sort)

  printf '\n[fleet]\n'
  printf 'active_waves: %s\n' "$active_count"

  if (( ${#active_targets[@]} > 0 )); then
    local unique_targets
    unique_targets="$(printf '%s\n' "${active_targets[@]}" | awk 'NF && !seen[$0]++' | wc -l | tr -d ' ')"
    printf 'active_unique_targets: %s\n' "$unique_targets"
    printf 'active_target_paths:\n'
    printf '%s\n' "${active_targets[@]}" | awk 'NF && !seen[$0]++'
  else
    printf 'active_unique_targets: 0\n'
  fi

  if (( ${#active_rows[@]} > 0 )); then
    printf 'active_wave_rows:\n'
    printf '%s\n' "${active_rows[@]}"
  fi
}

print_heartbeat_context() {
  local obs="$1"
  local run_dir="$2"
  local target_name="$3"
  python3 - "$obs" "$run_dir" "$target_name" <<'PY'
import json, os, sys
from pathlib import Path
from datetime import datetime, timezone

obs = Path(sys.argv[1]) if sys.argv[1] else None
run_dir = Path(sys.argv[2]) if sys.argv[2] else None
target_name = (sys.argv[3] or '').strip()

candidates = []
for base in [obs, run_dir]:
    if base and base.exists():
        for p in [base, *base.rglob('*')]:
            try:
                st = p.stat()
            except Exception:
                continue
            candidates.append((st.st_mtime, str(p)))

latest_activity = max(candidates, default=None, key=lambda x: x[0])

# Try to find the most recent user-visible sync from the main Telegram direct transcript.
sessions_path = Path('~/.openclaw/agents/main/sessions/sessions.json')
last_sync = None
last_sync_text = None
try:
    data = json.loads(sessions_path.read_text())
except Exception:
    data = None

if isinstance(data, dict):
    direct_keys = [k for k in data.keys() if k.startswith('agent:main:telegram:direct:')]
    # Prefer the freshest direct session if multiple exist.
    def sort_key(k):
        v = data.get(k) or {}
        return v.get('updatedAt', 0)
    for key in sorted(direct_keys, key=sort_key, reverse=True):
        entry = data.get(key) or {}
        sid = entry.get('id') or entry.get('sessionId')
        if not sid:
            continue
        transcript = Path('~/.openclaw/agents/main/sessions') / f'{sid}.jsonl'
        if not transcript.exists():
            continue
        try:
            lines = transcript.read_text(encoding='utf-8', errors='ignore').splitlines()
        except Exception:
            continue
        for line in reversed(lines):
            try:
                obj = json.loads(line)
            except Exception:
                continue
            msg = obj.get('message') or {}
            if msg.get('role') != 'assistant':
                continue
            content = msg.get('content') or []
            text_parts = []
            for part in content:
                if isinstance(part, dict) and part.get('type') == 'text':
                    text_parts.append(part.get('text') or '')
            text = '\n'.join(text_parts)
            if not text:
                continue
            low = text.lower()
            if target_name and target_name.lower() in low or 'loop9' in low or '审计' in text:
                last_sync = msg.get('timestamp') or obj.get('timestamp')
                last_sync_text = text.replace('\n', ' ')[:160]
                break
        if last_sync:
            break

now = datetime.now(timezone.utc)
print('\n[heartbeat_context]')
if latest_activity:
    ts = datetime.fromtimestamp(latest_activity[0], tz=timezone.utc)
    age_min = int((now - ts).total_seconds() // 60)
    print(f'latest_activity_at: {ts.isoformat()}')
    print(f'latest_activity_age_min: {age_min}')
    print(f'latest_activity_path: {latest_activity[1]}')
else:
    print('latest_activity_at: unknown')

parsed_sync_dt = None
if last_sync:
    try:
        if isinstance(last_sync, (int, float)) or (isinstance(last_sync, str) and last_sync.isdigit()):
            value = int(last_sync)
            if value > 10**12:
                parsed_sync_dt = datetime.fromtimestamp(value / 1000, tz=timezone.utc)
            else:
                parsed_sync_dt = datetime.fromtimestamp(value, tz=timezone.utc)
        else:
            parsed_sync_dt = datetime.fromisoformat(str(last_sync).replace('Z', '+00:00')).astimezone(timezone.utc)
        age_min = int((now - parsed_sync_dt).total_seconds() // 60)
        print(f'last_user_sync_at: {parsed_sync_dt.isoformat()}')
        print(f'last_user_sync_age_min: {age_min}')
    except Exception:
        print(f'last_user_sync_at: {last_sync}')
    if last_sync_text:
        print(f'last_user_sync_excerpt: {last_sync_text}')
else:
    print('last_user_sync_at: unknown')

sync_due = 'unknown'
if latest_activity and parsed_sync_dt:
    try:
        age_min = int((now - parsed_sync_dt).total_seconds() // 60)
        has_newer_activity = latest_activity[0] > parsed_sync_dt.timestamp() + 60
        sync_due = 'yes' if age_min >= 90 or has_newer_activity else 'no'
        print(f'new_activity_since_last_user_sync: {"yes" if has_newer_activity else "no"}')
        print(f'heartbeat_sync_due: {sync_due}')
    except Exception:
        pass
elif latest_activity and not last_sync:
    print('new_activity_since_last_user_sync: yes')
    print('heartbeat_sync_due: yes')
PY
}

latest_version_dir() {
  local base="$1"
  local prefix="$2"
  find "$base" -maxdepth 1 -mindepth 1 -type d -name "${prefix}_v*" 2>/dev/null | sort -V | tail -1 || true
}

latest_real_poc_iteration_run() {
  python3 - "$LOOP9_DIR" <<'PY'
from pathlib import Path
import sys
base = Path(sys.argv[1])
rows = []
if base.exists():
    for d in base.iterdir():
        if not d.is_dir():
            continue
        part = d / 'original_goal' / 'part01.md'
        if not part.exists():
            continue
        try:
            text = part.read_text(encoding='utf-8', errors='ignore')
        except Exception:
            continue
        low = text.lower()
        if 'loop9-real-poc-prompts' in low or 'real_poc_solution_v' in low or 'shared poc workspace' in low:
            try:
                mt = d.stat().st_mtime
            except Exception:
                mt = 0
            rows.append((mt, str(d)))
if rows:
    rows.sort()
    print(rows[-1][1])
PY
}

count_real_poc_scripts() {
  local dir="$1"
  [[ -d "$dir" ]] || { printf '0\n'; return 0; }
  find "$dir" -maxdepth 1 -type f -name '*.py' | wc -l | tr -d ' '
}

extract_validation_status() {
  local part="$1"
  [[ -f "$part" ]] || return 0
  sed -n 's/^- Status: //p' "$part" | head -1
}

extract_stop_decision() {
  local part="$1"
  [[ -f "$part" ]] || return 0
  sed -n 's/^- Stop-workflow decision: //p' "$part" | head -1
}

# 从日志里抓“后台任务容易漏看”的异常。
# 重点不是泛抓所有 ERROR，而是优先抓：
# - provider / model / auth / API key 相关错误
# - session.processor / llm 报错
# 这样能更快发现“某个模型配错了”或者“某个 provider 调不通”。
extract_runtime_issues() {
  local obs="$1"
  local src=""
  if [[ -f "$obs/opencode.clean.log" ]]; then
    src="$obs/opencode.clean.log"
  elif [[ -f "$obs/tmux.pipe.log" ]]; then
    src="$obs/tmux.pipe.log"
  else
    return 0
  fi

  awk '
    BEGIN { count = 0 }
    /ERROR/ || /ProviderAuthError/ || /AI_LoadAPIKeyError/ || /API key is missing/ || /providerID=/ || /modelID=/ || /statusCode/ || /rate limit/ || /timeout/ || /certificate/ || /TLS/ {
      line = $0
      if (line ~ /service=llm/ || line ~ /service=session\.processor/ || line ~ /ProviderAuthError/ || line ~ /AI_LoadAPIKeyError/ || line ~ /API key is missing/ || line ~ /providerID=/ || line ~ /statusCode/ || line ~ /rate limit/ || line ~ /timeout/ || line ~ /certificate/ || line ~ /TLS/) {
        print line
        count++
        if (count >= 40) exit
      }
    }
  ' "$src"
}

extract_runtime_issue_summary() {
  local obs="$1"
  local src=""
  if [[ -f "$obs/opencode.clean.log" ]]; then
    src="$obs/opencode.clean.log"
  elif [[ -f "$obs/tmux.pipe.log" ]]; then
    src="$obs/tmux.pipe.log"
  else
    return 0
  fi

  python3 - "$src" <<'PY'
import re, sys
from pathlib import Path

text = Path(sys.argv[1]).read_text(encoding='utf-8', errors='ignore')
lines = text.splitlines()[-1200:]
blob = "\n".join(lines)

patterns = [
    ("provider_cert", r"UNKNOWN_CERTIFICATE_VERIFICATION_ERROR|certificate verification error|CERTIFICATE_VERIFY_FAILED|certificate verify failed|TLS|x509|self signed certificate"),
    ("provider_auth", r"ProviderAuthError|AI_LoadAPIKeyError|API key is missing|no available plan|无可用套餐|invalid api key|unauthorized|forbidden|statusCode\":401|statusCode\":403|statusCode=401|statusCode=403"),
    ("provider_rate_limit", r"rate limit|too many requests|statusCode\":429|statusCode=429|retry-after"),
    ("provider_timeout", r"timeout|timed out|ETIMEDOUT|ECONNRESET|socket hang up|network error|fetch failed|stream error"),
    ("provider_server", r"statusCode\":500|statusCode\":502|statusCode\":503|statusCode\":504|statusCode=500|statusCode=502|statusCode=503|statusCode=504"),
]

matches = []
for code, pat in patterns:
    m = re.search(pat, blob, re.I)
    if m:
        matches.append(code)

if not matches:
    sys.exit(0)

primary = matches[0]
labels = {
    "provider_cert": "external_provider_tls_or_certificate_error",
    "provider_auth": "external_provider_auth_or_plan_error",
    "provider_rate_limit": "external_provider_rate_limit",
    "provider_timeout": "external_provider_network_or_timeout_error",
    "provider_server": "external_provider_server_error",
}

hints = {
    "provider_cert": "More likely provider/network/certificate chain issue than a Loop9 workflow logic bug.",
    "provider_auth": "More likely API key / auth / quota / plan configuration issue than a Loop9 workflow logic bug.",
    "provider_rate_limit": "More likely provider throttling than a Loop9 workflow logic bug.",
    "provider_timeout": "More likely transient provider/network instability than a Loop9 workflow logic bug.",
    "provider_server": "More likely upstream provider service failure than a Loop9 workflow logic bug.",
}

print(f"runtime_issue_kind: {labels[primary]}")
print(f"runtime_issue_judgement: {hints[primary]}")

for line in reversed(lines):
    if re.search(r"ERROR|ProviderAuthError|AI_LoadAPIKeyError|API key is missing|statusCode|rate limit|timeout|certificate|TLS|stream error", line, re.I):
        print(f"runtime_issue_last_error: {line[:1200]}")
        break
PY
}

printf '== Loop9 Status ==\n'
printf 'root: %s\n' "$ROOT"

print_fleet_overview

LATEST_RUN="$(latest_loop9_dir)"
REAL_POC_ITER_RUN="$(latest_real_poc_iteration_run)"
OBS="$(latest_observe)"
REAL_POC_OBS="$(latest_real_poc_observe)"
if [[ -n "$OBS" ]]; then
  printf '\n[observe]\n'
  printf 'latest_observe: %s\n' "$OBS"
  [[ -f "$OBS/run.meta" ]] && {
    printf 'target_name: %s\n' "$(read_meta_value "$OBS/run.meta" target_name)"
    printf 'target_path: %s\n' "$(read_meta_value "$OBS/run.meta" target_path)"
    printf 'mode: %s\n' "$(read_meta_value "$OBS/run.meta" mode)"
    printf 'transport: %s\n' "$(read_meta_value "$OBS/run.meta" transport)"
    printf 'tmux_session: %s\n' "$(read_meta_value "$OBS/run.meta" tmux_session)"
  }
  [[ -f "$OBS/started_at.txt" ]] && printf 'started_at: %s\n' "$(cat "$OBS/started_at.txt")"
  [[ -f "$OBS/finished_at.txt" ]] && printf 'finished_at: %s\n' "$(cat "$OBS/finished_at.txt")"
  [[ -f "$OBS/opencode.exit_code" ]] && printf 'exit_code: %s\n' "$(cat "$OBS/opencode.exit_code")"
  [[ -f "$OBS/session.id" ]] && printf 'session_id: %s\n' "$(cat "$OBS/session.id")"
  [[ -f "$OBS/session.title.txt" ]] && printf 'session_title: %s\n' "$(cat "$OBS/session.title.txt")"
  [[ -f "$OBS/tmux.attach.txt" ]] && printf 'tmux_attach: %s\n' "$(cat "$OBS/tmux.attach.txt")"

  if [[ -f "$OBS/session.id" ]]; then
    SESSION_ID="$(cat "$OBS/session.id")"
    SESSION_ROW="$(cd "$ROOT" && opencode session list 2>/dev/null | grep -F "$SESSION_ID" | head -1 || true)"
    [[ -n "$SESSION_ROW" ]] && printf 'session_list_row: %s\n' "$SESSION_ROW"
  fi
  if [[ -f "$OBS/tmux.session.txt" ]]; then
    TMUX_NAME="$(cat "$OBS/tmux.session.txt")"
    if command -v tmux >/dev/null 2>&1 && tmux has-session -t "$TMUX_NAME" 2>/dev/null; then
      printf 'tmux_status: running\n'
      tmux capture-pane -p -t "$TMUX_NAME":0.0 | tail -n 30 > "$OBS/tmux.capture.latest.log" || true
      printf 'tmux_tail:\n'
      sed -n '1,30p' "$OBS/tmux.capture.latest.log" || true
    else
      printf 'tmux_status: not-running\n'
    fi
  fi
  if [[ -f "$OBS/opencode.clean.log" ]]; then
    printf '\nopencode_clean_tail:\n'
    tail -n 30 "$OBS/opencode.clean.log" || true
  elif [[ -f "$OBS/tmux.pipe.log" ]]; then
    printf '\ntmux_pipe_tail:\n'
    tail -n 30 "$OBS/tmux.pipe.log" || true
  fi

  print_heartbeat_context "$OBS" "${LATEST_RUN:-}" "$(read_meta_value "$OBS/run.meta" target_name)"

  RUNTIME_ISSUES="$(extract_runtime_issues "$OBS" || true)"
  if [[ -n "$RUNTIME_ISSUES" ]]; then
    printf '\n[runtime_issues]\n'
    printf '%s\n' "$RUNTIME_ISSUES"
  fi

  RUNTIME_ISSUE_SUMMARY="$(extract_runtime_issue_summary "$OBS" || true)"
  if [[ -n "$RUNTIME_ISSUE_SUMMARY" ]]; then
    printf '\n[runtime_issue_summary]\n'
    printf '%s\n' "$RUNTIME_ISSUE_SUMMARY"
  fi
fi

if [[ -n "$REAL_POC_OBS" ]]; then
  printf '\n[real-poc-observe]\n'
  printf 'latest_real_poc_observe: %s\n' "$REAL_POC_OBS"
  [[ -f "$REAL_POC_OBS/run.meta" ]] && {
    printf 'workflow_name: %s\n' "$(read_meta_value "$REAL_POC_OBS/run.meta" workflow_name)"
    printf 'audit_run_dir: %s\n' "$(read_meta_value "$REAL_POC_OBS/run.meta" audit_run_dir)"
    printf 'shared_poc_dir: %s\n' "$(read_meta_value "$REAL_POC_OBS/run.meta" shared_poc_dir)"
    printf 'real_poc_solution_prefix: %s\n' "$(read_meta_value "$REAL_POC_OBS/run.meta" real_poc_solution_prefix)"
    printf 'real_poc_validation_prefix: %s\n' "$(read_meta_value "$REAL_POC_OBS/run.meta" real_poc_validation_prefix)"
    printf 'real_poc_manifest_path: %s\n' "$(read_meta_value "$REAL_POC_OBS/run.meta" real_poc_manifest_path)"
    printf 'tmux_session: %s\n' "$(read_meta_value "$REAL_POC_OBS/run.meta" tmux_session)"
  }
  [[ -f "$REAL_POC_OBS/started_at.txt" ]] && printf 'started_at: %s\n' "$(cat "$REAL_POC_OBS/started_at.txt")"
  [[ -f "$REAL_POC_OBS/finished_at.txt" ]] && printf 'finished_at: %s\n' "$(cat "$REAL_POC_OBS/finished_at.txt")"
  [[ -f "$REAL_POC_OBS/opencode.exit_code" ]] && printf 'exit_code: %s\n' "$(cat "$REAL_POC_OBS/opencode.exit_code")"
  [[ -f "$REAL_POC_OBS/tmux.attach.txt" ]] && printf 'tmux_attach: %s\n' "$(cat "$REAL_POC_OBS/tmux.attach.txt")"

  if [[ -f "$REAL_POC_OBS/tmux.session.txt" ]]; then
    TMUX_NAME="$(cat "$REAL_POC_OBS/tmux.session.txt")"
    if command -v tmux >/dev/null 2>&1 && tmux has-session -t "$TMUX_NAME" 2>/dev/null; then
      printf 'tmux_status: running\n'
      tmux capture-pane -p -t "$TMUX_NAME":0.0 | tail -n 30 > "$REAL_POC_OBS/tmux.capture.latest.log" || true
      printf 'tmux_tail:\n'
      sed -n '1,30p' "$REAL_POC_OBS/tmux.capture.latest.log" || true
    else
      printf 'tmux_status: not-running\n'
    fi
  fi

  REAL_POC_AUDIT_RUN="$(read_meta_value "$REAL_POC_OBS/run.meta" audit_run_dir)"
  REAL_POC_SHARED_DIR="$(read_meta_value "$REAL_POC_OBS/run.meta" shared_poc_dir)"
  REAL_POC_MANIFEST="$(read_meta_value "$REAL_POC_OBS/run.meta" real_poc_manifest_path)"
  if [[ -n "$REAL_POC_AUDIT_RUN" ]]; then
    printf '\n[real-poc-linked-audit-run]\n'
    printf 'audit_run_dir: %s\n' "$REAL_POC_AUDIT_RUN"
    REAL_POC_SOLUTION_DIR=""
    REAL_POC_VALIDATION_DIR=""
    if [[ -n "$REAL_POC_SHARED_DIR" && -d "$REAL_POC_SHARED_DIR" ]]; then
      REAL_POC_SOLUTION_DIR="$(latest_version_dir "$REAL_POC_SHARED_DIR" real_poc_solution)"
      REAL_POC_VALIDATION_DIR="$(latest_version_dir "$REAL_POC_SHARED_DIR" real_poc_validation_report)"
    fi
    [[ -n "$REAL_POC_SOLUTION_DIR" ]] && printf 'latest_real_poc_solution_dir: %s\n' "$REAL_POC_SOLUTION_DIR"
    [[ -n "$REAL_POC_VALIDATION_DIR" ]] && printf 'latest_real_poc_validation_dir: %s\n' "$REAL_POC_VALIDATION_DIR"
    [[ -n "$REAL_POC_SHARED_DIR" ]] && printf 'shared_poc_py_count: %s\n' "$(count_real_poc_scripts "$REAL_POC_SHARED_DIR")"
    if [[ -n "$REAL_POC_SHARED_DIR" && -d "$REAL_POC_SHARED_DIR" ]]; then
      printf 'shared_poc_py_files:\n'
      find "$REAL_POC_SHARED_DIR" -maxdepth 1 -type f -name '*.py' | sort || true
    fi
    [[ -n "$REAL_POC_MANIFEST" && -f "$REAL_POC_MANIFEST" ]] && printf 'real_poc_manifest_path: %s\n' "$REAL_POC_MANIFEST"
    if [[ -n "$REAL_POC_VALIDATION_DIR" && -f "$REAL_POC_VALIDATION_DIR/part01.md" ]]; then
      REAL_POC_VALIDATION_STATUS="$(extract_validation_status "$REAL_POC_VALIDATION_DIR/part01.md")"
      [[ -n "$REAL_POC_VALIDATION_STATUS" ]] && printf 'validation_status: %s\n' "$REAL_POC_VALIDATION_STATUS"
      printf '\nreal_poc_validation_excerpt:\n'
      sed -n '1,40p' "$REAL_POC_VALIDATION_DIR/part01.md" || true
    fi
    if [[ -f "$REAL_POC_STATUS_HELPER" ]]; then
      printf '\n[real-poc-final-status]\n'
      python3 "$REAL_POC_STATUS_HELPER" "$REAL_POC_AUDIT_RUN" --kv || true
      printf '\n[real-poc-final-summary]\n'
      REAL_POC_STATUS_JSON_FILE="$REAL_POC_OBS/real_poc_status_snapshot.json"
      python3 "$REAL_POC_STATUS_HELPER" "$REAL_POC_AUDIT_RUN" --no-write > "$REAL_POC_STATUS_JSON_FILE" 2>/dev/null || true
      if [[ -s "$REAL_POC_STATUS_JSON_FILE" ]]; then
        python3 - "$REAL_POC_STATUS_JSON_FILE" <<'PY' || true
import json, sys
obj = json.loads(open(sys.argv[1], 'r', encoding='utf-8').read())
round_status = obj.get('latest_round_validation_status') or 'unknown'
workflow = obj.get('workflow_completion') or 'unknown'
reason = obj.get('workflow_completion_reason') or 'unknown'
latest_round = obj.get('latest_round')
latest_round_src = obj.get('latest_round_source') or 'unknown'
min_it = obj.get('min_iterations')
max_it = obj.get('max_iterations')
recorded_min = obj.get('recorded_min_iterations')
min_norm = obj.get('min_iterations_normalization') or 'none'
print(f"real_poc_round_status: {round_status}")
print(f"real_poc_workflow_completion: {workflow}")
print(f"real_poc_workflow_reason: {reason}")
print(f"real_poc_latest_round: {latest_round if latest_round is not None else 'unknown'}")
print(f"real_poc_latest_round_source: {latest_round_src}")
print(f"real_poc_effective_min_max: {min_it}/{max_it}")
print(f"real_poc_recorded_min_iterations: {recorded_min if recorded_min is not None else 'unknown'}")
print(f"real_poc_legacy_normalization: {min_norm}")
PY
      fi
    fi
  fi
fi

if [[ -n "$REAL_POC_ITER_RUN" ]]; then
  printf '\n[real-poc-iteration-run]\n'
  printf 'latest_real_poc_iteration_run_dir: %s\n' "$REAL_POC_ITER_RUN"
  ITER_SOL="$(latest_version_dir "$REAL_POC_ITER_RUN" solution)"
  ITER_VAL="$(latest_version_dir "$REAL_POC_ITER_RUN" validation_report)"
  [[ -n "$ITER_SOL" ]] && printf 'latest_solution_dir: %s\n' "$ITER_SOL"
  [[ -n "$ITER_VAL" ]] && printf 'latest_validation_dir: %s\n' "$ITER_VAL"
  if [[ -f "$REAL_POC_ITER_RUN/original_goal/part01.md" ]]; then
    printf 'source_task_file: %s\n' "$(sed -n 's/^- \(`\)\{0,1\}\(\/.*loop9-real-poc-prompts\/[^`]*\)\(`\)\{0,1\}$/\2/p' "$REAL_POC_ITER_RUN/original_goal/part01.md" | head -1)"
  fi
  if [[ -n "$ITER_VAL" && -f "$ITER_VAL/part01.md" ]]; then
    ITER_STATUS="$(sed -n 's/^- Overall status: //p' "$ITER_VAL/part01.md" | head -1)"
    [[ -z "$ITER_STATUS" ]] && ITER_STATUS="$(extract_validation_status "$ITER_VAL/part01.md")"
    [[ -n "$ITER_STATUS" ]] && printf 'validation_status: %s\n' "$ITER_STATUS"
    printf '\niteration_validation_excerpt:\n'
    sed -n '1,40p' "$ITER_VAL/part01.md" || true
  fi
fi

if [[ -n "$LATEST_RUN" ]]; then
  printf '\n[loop9-run-dir]\n'
  printf 'latest_run_dir: %s\n' "$LATEST_RUN"

  LATEST_SOLUTION="$(latest_version_dir "$LATEST_RUN" solution)"
  LATEST_VALIDATION="$(latest_version_dir "$LATEST_RUN" validation_report)"
  [[ -n "$LATEST_SOLUTION" ]] && printf 'latest_solution_dir: %s\n' "$LATEST_SOLUTION"
  [[ -n "$LATEST_VALIDATION" ]] && printf 'latest_validation_dir: %s\n' "$LATEST_VALIDATION"

  if [[ -n "$LATEST_VALIDATION" && -f "$LATEST_VALIDATION/part01.md" ]]; then
    VALIDATION_STATUS="$(extract_validation_status "$LATEST_VALIDATION/part01.md")"
    STOP_DECISION="$(extract_stop_decision "$LATEST_VALIDATION/part01.md")"
    [[ -n "$VALIDATION_STATUS" ]] && printf 'validation_status: %s\n' "$VALIDATION_STATUS"
    [[ -n "$STOP_DECISION" ]] && printf 'stop_workflow_decision: %s\n' "$STOP_DECISION"
  fi

  if [[ -n "$LATEST_VALIDATION" && -f "$LATEST_VALIDATION/part01.md" ]]; then
    printf '\nvalidation_excerpt:\n'
    sed -n '1,40p' "$LATEST_VALIDATION/part01.md" || true
  fi

  find "$LATEST_RUN" -maxdepth 2 -type f 2>/dev/null | sort | tail -20 || true
fi

printf '\n[reports]\n'
latest_reports || true

printf '\n[sessions]\n'
cd "$ROOT"
opencode session list | sed -n '1,12p' || true
