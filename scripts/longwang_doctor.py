#!/usr/bin/env python3
"""End-to-end readiness doctor for the public LongWangClaw workspace repo."""

from __future__ import annotations

import argparse
import json
import os
import py_compile
import re
import shutil
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

try:
    import tomllib
except ModuleNotFoundError:  # Python < 3.11 can still run the rest of doctor.
    tomllib = None


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from render_longwang_config import (  # noqa: E402
    EXAMPLE_PROFILE,
    DEFAULT_PROFILE,
    ProfileError,
    collect_profile_placeholders,
    get_path,
    load_json,
    render_all,
)


LANES = (
    "audit",
    "real_poc_static",
    "static_feishu_publish",
    "dynamic_verify",
    "delivery_report",
    "delivery_feishu_publish",
    "cron",
)

EXPECTED_CRON = {
    "Loop9 Publish Dispatcher": "15,50 * * * *",
    "Loop9 Audit Dispatcher": "0,30 * * * *",
    "Loop9 Real-PoC Dispatcher": "5,25,45 * * * *",
    "Loop9 Delivery Report Publisher": "35 * * * *",
    "Loop9 Verify V4 Auto Runner": "55 * * * *",
}

EXCLUDED_TRACKED_ROOTS = {
    "reports",
    "runs",
    "targets",
    "logs",
    "memory",
    "node_modules",
    "__pycache__",
}

SECRET_ASSIGN_RE = re.compile(
    r"(?i)(api[_-]?key|appsecret|secret|token|password|bottoken|authToken)\s*[:=]\s*[\"']([^\"'\n]{12,})[\"']"
)
LONG_HEX_RE = re.compile(r"\b[a-fA-F0-9]{48,}\b")
LOCAL_MODEL_MARKERS = (
    "xiao" "hongshu_codexfor",
    "custom" "-right-codes",
)
DEFAULT_ASSET_KEY_MARKERS = (
    "DEFAULT_" "FOFA_KEY",
    "DEFAULT_" "HUNTER_API_KEY",
    "DEFAULT_" "SHODAN_KEY",
)
LOCAL_USER_PATH_MARKER = "/Users/" "xlx"
PASSWORD_LITERAL_MARKER = "DXZN" "@"
PRIVATE_BEGIN_MARKER = "-----BEGIN "
PRIVATE_KEY_END_MARKER = "PRIVATE " "KEY-----"


@dataclass
class Check:
    status: str
    category: str
    name: str
    message: str
    lanes: list[str] = field(default_factory=list)
    detail: dict[str, Any] = field(default_factory=dict)


class Doctor:
    def __init__(self, repo_root: Path, profile_path: Path, *, skip_syntax: bool = False) -> None:
        self.repo_root = repo_root
        self.profile_path = profile_path
        self.skip_syntax = skip_syntax
        self.checks: list[Check] = []
        self.lane_issues: dict[str, list[Check]] = {lane: [] for lane in LANES}
        self.profile: dict[str, Any] = {}

    def add(self, status: str, category: str, name: str, message: str, *, lanes: list[str] | None = None, detail: dict[str, Any] | None = None) -> None:
        check = Check(status=status, category=category, name=name, message=message, lanes=lanes or [], detail=detail or {})
        self.checks.append(check)
        if status != "ok":
            for lane in check.lanes:
                self.lane_issues.setdefault(lane, []).append(check)

    def path(self, rel: str) -> Path:
        return self.repo_root / rel

    def rel(self, path: Path) -> str:
        try:
            return str(path.relative_to(self.repo_root))
        except ValueError:
            return str(path)

    def run(self) -> dict[str, Any]:
        self.check_profile()
        self.check_layout()
        self.check_commands()
        self.check_templates()
        self.check_cron_examples()
        self.check_opencode_assets()
        if not self.skip_syntax:
            self.check_syntax()
        self.check_repo_boundary_and_secrets()
        return self.result()

    def check_profile(self) -> None:
        try:
            self.profile = load_json(self.profile_path)
        except ProfileError as exc:
            self.add("blocked", "profile", "load", str(exc), lanes=list(LANES))
            self.profile = {}
            return

        self.add("ok", "profile", "load", f"profile loaded: {self.profile_path}")
        if self.profile.get("schema") != "longwang.config.v1":
            self.add("warn", "profile", "schema", "profile schema is not longwang.config.v1", lanes=list(LANES))

        placeholder_fields = collect_profile_placeholders(self.profile)
        if placeholder_fields:
            self.add(
                "warn",
                "profile",
                "placeholders",
                f"profile still contains {len(placeholder_fields)} CHANGE_ME/TODO values",
                lanes=["static_feishu_publish", "dynamic_verify", "delivery_feishu_publish", "cron"],
                detail={"fields": placeholder_fields[:80]},
            )

        self._require_fields(
            "audit",
            [
                "paths.workspaceRoot",
                "paths.super8Root",
                "commands.opencode",
                "models.opencode.agentModel",
            ],
        )
        self._require_fields(
            "real_poc_static",
            [
                "paths.workspaceRoot",
                "paths.super8Root",
                "commands.opencode",
                "models.opencode.agentModel",
            ],
        )
        self._require_fields(
            "static_feishu_publish",
            [
                "feishu.appId",
                "feishu.appSecret",
                "feishu.wiki.internalSpaceName",
                "paths.memoryRoot",
            ],
        )
        self._require_fields(
            "dynamic_verify",
            [
                "commands.codex",
                "remoteRuntime.kind",
                "remoteRuntime.label",
                "remoteRuntime.runtimeRoot",
            ],
        )
        self._require_fields(
            "delivery_report",
            [
                "paths.reportsRoot",
                "paths.runsRoot",
            ],
        )
        self._require_fields(
            "delivery_feishu_publish",
            [
                "feishu.appId",
                "feishu.appSecret",
                "feishu.wiki.deliveryReportNodeTitle",
                "paths.memoryRoot",
            ],
        )
        self._require_fields(
            "cron",
            [
                "paths.cronJobs",
                "cron.timezone",
                "cron.defaultAgentId",
                "cron.feishuAgentId",
            ],
        )

        if not self._bool_path("feishu.enabled"):
            self.add(
                "blocked",
                "profile",
                "feishu.enabled",
                "Feishu upload lanes are disabled in the profile",
                lanes=["static_feishu_publish", "delivery_feishu_publish"],
            )
        if not self._bool_path("remoteRuntime.enabled"):
            self.add(
                "blocked",
                "profile",
                "remoteRuntime.enabled",
                "dynamic verification remote runtime is disabled in the profile",
                lanes=["dynamic_verify"],
            )
        if not self._bool_path("cron.enabled"):
            self.add("warn", "profile", "cron.enabled", "cron rendering is configured disabled", lanes=["cron"])

    def _bool_path(self, field: str) -> bool:
        try:
            return bool(get_path(self.profile, field))
        except Exception:
            return False

    def _value_missing(self, value: Any) -> bool:
        if value is None:
            return True
        if isinstance(value, str):
            stripped = value.strip()
            return not stripped or stripped.startswith("CHANGE_ME") or stripped in {"TODO", "REPLACE_ME"}
        return False

    def _require_fields(self, lane: str, fields: list[str]) -> None:
        for field_name in fields:
            try:
                value = get_path(self.profile, field_name)
            except Exception:
                self.add("blocked", "profile", field_name, "missing required profile field", lanes=[lane])
                continue
            if self._value_missing(value):
                self.add("blocked", "profile", field_name, "required profile field is empty or still a placeholder", lanes=[lane])

    def check_layout(self) -> None:
        required = {
            "workspace/bin/loop9-dispatch": ["audit", "real_poc_static", "static_feishu_publish"],
            "workspace/bin/loop9-launch-guard": ["audit", "real_poc_static"],
            "workspace/bin/loop9-cron-install": ["cron"],
            "workspace/bin/loop9-verify-v4-auto-run.sh": ["dynamic_verify", "cron"],
            "workspace/lib/loop9_automation/config.py": ["audit", "real_poc_static", "cron"],
            "workspace/Super8/.opencode/command/loop9.md": ["audit", "real_poc_static"],
            "workspace/Super8/.opencode/agents/loop9-controller.md": ["audit", "real_poc_static"],
            "workspace/Super8/.opencode/_scripts/loop9_authorized_review.py": ["audit"],
            "workspace/Super8/工作流_提示词工程/case10_比较简单的Math9/loop9____第二版/案例/3_0day挖掘_1/red队/DotNet项目/【模板（更新版）】提示词.md": ["audit"],
            "workspace/Super8/工作流_提示词工程/case10_比较简单的Math9/loop9____第二版/案例/3_0day挖掘_1/red队/DotNet项目/【模板（微步在线收录版）】提示词.md": ["audit"],
            "workspace/skills/loop9-wrapped-audit/SKILL.md": ["audit"],
            "workspace/skills/loop9-real-poc/SKILL.md": ["real_poc_static"],
            "workspace/skills/loop9-feishu-publisher/SKILL.md": ["static_feishu_publish"],
            "workspace/skills/loop9-verify-v4/SKILL.md": ["dynamic_verify"],
            "workspace/skills/loop9-verify-v4-env-bootstrap/SKILL.md": ["dynamic_verify"],
            "workspace/skills/loop9-verify-v4-finding-replay/SKILL.md": ["dynamic_verify"],
            "workspace/skills/loop9-delivery-reports/SKILL.md": ["delivery_report"],
            "workspace/skills/loop9-feishu-delivery-publisher/SKILL.md": ["delivery_feishu_publish"],
            "extensions/openclaw-lark/package.json": ["static_feishu_publish", "delivery_feishu_publish"],
            "extensions/openclaw-lark/openclaw.plugin.json": ["static_feishu_publish", "delivery_feishu_publish"],
            "scripts/bootstrap_openclaw_layout.py": list(LANES),
            "scripts/render_longwang_config.py": list(LANES),
            "scripts/longwang_doctor.py": list(LANES),
            "workspace/config/longwang.example.json": list(LANES),
        }
        for rel, lanes in required.items():
            if self.path(rel).exists():
                self.add("ok", "layout", rel, "present")
            else:
                self.add("blocked", "layout", rel, "missing required public asset", lanes=lanes)

        for rel in ("reports", "runs", "targets", "logs", "memory", "node_modules"):
            if self.path(rel).exists():
                self.add("blocked", "layout", rel, "excluded runtime directory exists at repo root", lanes=list(LANES))

    def check_commands(self) -> None:
        command_lanes = {
            "python": list(LANES),
            "bash": list(LANES),
            "git": list(LANES),
            "node": ["static_feishu_publish", "delivery_feishu_publish"],
            "npm": ["static_feishu_publish", "delivery_feishu_publish"],
            "opencode": ["audit", "real_poc_static"],
            "codex": ["dynamic_verify"],
            "tmux": ["audit", "real_poc_static", "cron"],
            "docker": ["dynamic_verify"],
        }
        for key, lanes in command_lanes.items():
            try:
                command = str(get_path(self.profile, f"commands.{key}"))
            except Exception:
                self.add("blocked", "command", key, "command missing from profile", lanes=lanes)
                continue
            found = shutil.which(command)
            if found:
                self.add("ok", "command", key, f"{command} -> {found}")
            else:
                self.add("blocked", "command", key, f"command not found on PATH: {command}", lanes=lanes)

    def check_templates(self) -> None:
        if not self.profile:
            return
        try:
            items = render_all(self.profile, repo_root=self.repo_root)
        except Exception as exc:
            self.add("blocked", "templates", "render", f"render failed: {exc}", lanes=list(LANES))
            return
        for item in items:
            if item.unresolved:
                self.add("blocked", "templates", item.name, f"unresolved placeholders: {', '.join(item.unresolved)}", lanes=list(LANES))
                continue
            try:
                if item.name in {"openclaw", "opencode", "cron"}:
                    json.loads(item.content)
                elif item.name == "codex" and tomllib is not None:
                    tomllib.loads(item.content)
            except Exception as exc:
                self.add("blocked", "templates", item.name, f"rendered template syntax error: {exc}", lanes=list(LANES))
                continue
            self.add("ok", "templates", item.name, f"renders to {item.target_path}")

    def check_cron_examples(self) -> None:
        paths = [
            self.path("workspace/plans/loop9-hourly-cron-jobs.example.json"),
        ]
        for path in paths:
            if not path.exists():
                self.add("blocked", "cron", self.rel(path), "cron example missing", lanes=["cron"])
                continue
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
            except Exception as exc:
                self.add("blocked", "cron", self.rel(path), f"cron example is not valid JSON: {exc}", lanes=["cron"])
                continue
            jobs = data.get("jobs") if isinstance(data, dict) else None
            if not isinstance(jobs, list):
                self.add("blocked", "cron", self.rel(path), "cron example does not contain jobs[]", lanes=["cron"])
                continue
            by_name = {str(job.get("name")): job for job in jobs if isinstance(job, dict)}
            missing = [name for name in EXPECTED_CRON if name not in by_name]
            wrong_expr = []
            for name, expr in EXPECTED_CRON.items():
                got = (((by_name.get(name) or {}).get("schedule") or {}).get("expr"))
                if name in by_name and got != expr:
                    wrong_expr.append({"name": name, "expected": expr, "actual": got})
            if missing or wrong_expr:
                self.add("blocked", "cron", self.rel(path), "cron example does not match the five public lanes", lanes=["cron"], detail={"missing": missing, "wrongExpr": wrong_expr})
            else:
                self.add("ok", "cron", self.rel(path), "five lanes present")

    def check_opencode_assets(self) -> None:
        opencode_root = self.path("workspace/Super8/.opencode")
        agent_files = sorted((opencode_root / "agents").glob("*.md"))
        if len(agent_files) < 4:
            self.add("blocked", "opencode", "agents", "expected controller/solver/validator/refiner agent files", lanes=["audit", "real_poc_static"])
        for path in agent_files:
            text = path.read_text(encoding="utf-8", errors="ignore")
            if any(marker in text for marker in LOCAL_MODEL_MARKERS):
                self.add("blocked", "opencode", self.rel(path), "local/private model provider remains in OpenCode agent frontmatter", lanes=["audit", "real_poc_static"])
            elif re.search(r"^model:\s*\"?[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+\"?", text, re.MULTILINE):
                self.add("ok", "opencode", self.rel(path), "agent has qualified model")
            else:
                self.add("warn", "opencode", self.rel(path), "agent model not found in frontmatter", lanes=["audit", "real_poc_static"])

        master = opencode_root / "_xml" / "loop9.master.xml"
        if master.exists():
            text = master.read_text(encoding="utf-8", errors="ignore")
            if any(marker in text for marker in LOCAL_MODEL_MARKERS):
                self.add("blocked", "opencode", self.rel(master), "local/private model provider remains in master XML", lanes=["audit", "real_poc_static"])

    def check_syntax(self) -> None:
        self._check_python_syntax()
        self._check_bash_syntax()
        self._check_node_syntax()

    def _check_python_syntax(self) -> None:
        roots = [
            self.path("scripts"),
            self.path("workspace/bin"),
            self.path("workspace/lib"),
            self.path("workspace/skills"),
            self.path("workspace/Super8/.opencode/_scripts"),
        ]
        files: list[Path] = []
        for root in roots:
            if root.exists():
                files.extend(sorted(root.rglob("*.py")))
        failures = []
        for path in files:
            try:
                py_compile.compile(str(path), doraise=True)
            except Exception as exc:
                failures.append({"path": self.rel(path), "error": str(exc)})
        if failures:
            self.add("blocked", "syntax", "python", f"python syntax failures: {len(failures)}", lanes=list(LANES), detail={"failures": failures[:30]})
        else:
            self.add("ok", "syntax", "python", f"py_compile passed for {len(files)} files")

    def _is_shell_file(self, path: Path) -> bool:
        if path.suffix == ".sh":
            return True
        try:
            first = path.read_text(encoding="utf-8", errors="ignore").splitlines()[0]
        except Exception:
            return False
        return "bash" in first or first.endswith("/sh")

    def _check_bash_syntax(self) -> None:
        bash = shutil.which(str((self.profile.get("commands") or {}).get("bash") or "bash"))
        if not bash:
            return
        roots = [self.path("workspace/bin"), self.path("workspace/Super8/.opencode/_scripts")]
        files: list[Path] = []
        for root in roots:
            if root.exists():
                for path in sorted(root.rglob("*")):
                    if path.is_file() and self._is_shell_file(path):
                        files.append(path)
        failures = []
        for path in files:
            result = subprocess.run([bash, "-n", str(path)], capture_output=True, text=True, check=False)
            if result.returncode != 0:
                failures.append({"path": self.rel(path), "stderr": result.stderr.strip()})
        if failures:
            self.add("blocked", "syntax", "bash", f"bash -n failures: {len(failures)}", lanes=["audit", "dynamic_verify", "cron"], detail={"failures": failures[:30]})
        else:
            self.add("ok", "syntax", "bash", f"bash -n passed for {len(files)} files")

    def _check_node_syntax(self) -> None:
        node = shutil.which(str((self.profile.get("commands") or {}).get("node") or "node"))
        if not node:
            return
        roots = [self.path("extensions/openclaw-lark"), self.path("workspace/hooks")]
        files: list[Path] = []
        for root in roots:
            if root.exists():
                files.extend(sorted(root.rglob("*.js")))
        failures = []
        for path in files:
            result = subprocess.run([node, "--check", str(path)], capture_output=True, text=True, check=False)
            if result.returncode != 0:
                failures.append({"path": self.rel(path), "stderr": result.stderr.strip()})
        if failures:
            self.add("blocked", "syntax", "node", f"node --check failures: {len(failures)}", lanes=["static_feishu_publish", "delivery_feishu_publish"], detail={"failures": failures[:30]})
        else:
            self.add("ok", "syntax", "node", f"node --check passed for {len(files)} files")

    def _tracked_files(self) -> list[Path]:
        result = subprocess.run(["git", "ls-files", "-z"], cwd=self.repo_root, capture_output=True, check=False)
        if result.returncode != 0:
            return [path for path in self.repo_root.rglob("*") if path.is_file() and ".git" not in path.parts]
        return [self.repo_root / raw.decode("utf-8") for raw in result.stdout.split(b"\0") if raw]

    def check_repo_boundary_and_secrets(self) -> None:
        files = self._tracked_files()
        blocked_paths = []
        secret_hits = []
        for path in files:
            rel = self.rel(path)
            parts = Path(rel).parts
            if parts and parts[0] in EXCLUDED_TRACKED_ROOTS:
                blocked_paths.append(rel)
            if len(parts) >= 2 and parts[0] == "workspace" and parts[1] in EXCLUDED_TRACKED_ROOTS:
                blocked_paths.append(rel)
            if path.name in {".env", ".env.local", "openclaw.json", "opencode.json", "config.toml"} and not rel.startswith("templates/"):
                blocked_paths.append(rel)
            if path.name in {"package-lock.json", "LICENSE", "LICENSE.md"}:
                continue
            text = path.read_text(encoding="utf-8", errors="ignore")
            if rel == "scripts/longwang_doctor.py":
                continue
            if PRIVATE_BEGIN_MARKER in text and PRIVATE_KEY_END_MARKER in text:
                secret_hits.append({"path": rel, "kind": "private-key"})
            if any(marker in text for marker in DEFAULT_ASSET_KEY_MARKERS):
                secret_hits.append({"path": rel, "kind": "default-asset-search-key"})
            if PASSWORD_LITERAL_MARKER in text:
                secret_hits.append({"path": rel, "kind": "password-like-literal"})
            if LOCAL_USER_PATH_MARKER in text:
                secret_hits.append({"path": rel, "kind": "local-user-path"})
            if LOCAL_MODEL_MARKERS[0] in text:
                secret_hits.append({"path": rel, "kind": "local-model-provider"})
            if path.suffix.lower() not in {".py", ".js", ".ts"}:
                for match in SECRET_ASSIGN_RE.finditer(text):
                    value = match.group(2).strip()
                    value_lower = value.lower()
                    if "{{" in value or "CHANGE_ME" in value or "REPLACE_ME" in value or "placeholder" in value_lower or "xxx" in value_lower:
                        continue
                    if value in {"appSecret", "apiKey", "secret", "token", "password"}:
                        continue
                    secret_hits.append({"path": rel, "kind": "secret-assignment", "field": match.group(1)})
                    break
            if LONG_HEX_RE.search(text) and "sha256" not in text.lower() and "integrity" not in text.lower():
                if rel.endswith((".md", ".json", ".py", ".js", ".sh", ".toml", ".tpl")):
                    secret_hits.append({"path": rel, "kind": "long-hex-token"})

        if blocked_paths:
            self.add("blocked", "boundary", "excluded-paths", f"tracked excluded paths: {len(blocked_paths)}", lanes=list(LANES), detail={"paths": sorted(set(blocked_paths))[:80]})
        else:
            self.add("ok", "boundary", "excluded-paths", "no tracked runtime/excluded paths")
        if secret_hits:
            self.add("blocked", "security", "secret-scan", f"high-confidence secret/locality hits: {len(secret_hits)}", lanes=list(LANES), detail={"hits": secret_hits[:80]})
        else:
            self.add("ok", "security", "secret-scan", "no high-confidence secret hits")

    def result(self) -> dict[str, Any]:
        lanes = {}
        for lane, issues in self.lane_issues.items():
            if any(item.status == "blocked" for item in issues):
                status = "blocked"
            elif any(item.status == "warn" for item in issues):
                status = "partial"
            else:
                status = "ready"
            lanes[lane] = {
                "status": status,
                "issues": [
                    {
                        "status": item.status,
                        "category": item.category,
                        "name": item.name,
                        "message": item.message,
                    }
                    for item in issues
                ],
            }
        return {
            "schema": "longwang.doctor.v1",
            "repoRoot": str(self.repo_root),
            "profile": str(self.profile_path),
            "lanes": lanes,
            "checks": [
                {
                    "status": item.status,
                    "category": item.category,
                    "name": item.name,
                    "message": item.message,
                    "lanes": item.lanes,
                    "detail": item.detail,
                }
                for item in self.checks
            ],
        }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Check LongWangClaw end-to-end assembly readiness.")
    parser.add_argument(
        "--profile",
        default=str(DEFAULT_PROFILE if DEFAULT_PROFILE.exists() else EXAMPLE_PROFILE),
        help="Path to longwang.local.json. Defaults to local profile, then example profile.",
    )
    parser.add_argument("--repo-root", default=str(REPO_ROOT), help="LongWangClaw repo root.")
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON.")
    parser.add_argument("--skip-syntax", action="store_true", help="Skip py_compile/bash/node syntax checks.")
    return parser.parse_args()


def print_human(result: dict[str, Any]) -> None:
    print("LongWangClaw doctor")
    print(f"repo={result['repoRoot']}")
    print(f"profile={result['profile']}")
    print("")
    print("Lane readiness:")
    for lane, info in result["lanes"].items():
        print(f"- {lane}: {info['status']} ({len(info['issues'])} issue(s))")
    print("")
    visible = [check for check in result["checks"] if check["status"] != "ok"]
    if not visible:
        print("No blocking or warning checks.")
        return
    print("Issues:")
    for check in visible[:120]:
        print(f"- [{check['status']}] {check['category']}.{check['name']}: {check['message']}")
    if len(visible) > 120:
        print(f"... {len(visible) - 120} more issue(s). Use --json for full detail.")


def main() -> int:
    args = parse_args()
    repo_root = Path(args.repo_root).expanduser().resolve()
    profile_path = Path(args.profile).expanduser().resolve()
    result = Doctor(repo_root, profile_path, skip_syntax=args.skip_syntax).run()
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print_human(result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
