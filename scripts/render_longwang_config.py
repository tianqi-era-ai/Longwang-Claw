#!/usr/bin/env python3
"""Render LongWangClaw local/private config files from a single profile."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shlex
from dataclasses import dataclass
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PROFILE = REPO_ROOT / "workspace" / "config" / "longwang.local.json"
EXAMPLE_PROFILE = REPO_ROOT / "workspace" / "config" / "longwang.example.json"

PLACEHOLDER_RE = re.compile(r"\{\{\s*([^{}]+?)\s*\}\}")
SECRET_FIELD_RE = re.compile(
    r"(api[_-]?key|appsecret|secret|token|password|bottoken|authToken|sshKeyPath)",
    re.IGNORECASE,
)
MASK_LINE_RE = re.compile(
    r"(?i)(\"?(?:api[_-]?key|appSecret|secret|token|password|botToken|authToken)\"?\s*[:=]\s*)(\"?)([^\"'\n,]+)(\"?)"
)


@dataclass(frozen=True)
class TemplateSpec:
    name: str
    template: str
    target_profile_key: str
    mode: int = 0o600


@dataclass
class RenderedTemplate:
    name: str
    template_path: Path
    target_path: Path
    content: str
    placeholders: list[str]
    unresolved: list[str]
    sha256: str
    mode: int = 0o600


TEMPLATES: tuple[TemplateSpec, ...] = (
    TemplateSpec("openclaw", "templates/openclaw/openclaw.json.tpl", "paths.openclawConfig"),
    TemplateSpec("opencode", "templates/opencode/opencode.json.tpl", "paths.opencodeConfig"),
    TemplateSpec("codex", "templates/codex/config.toml.tpl", "paths.codexConfig"),
    TemplateSpec("cron", "templates/cron/jobs.json.tpl", "paths.cronJobs"),
    TemplateSpec("env", "templates/env/longwang.env.tpl", "paths.longwangEnvFile"),
)

OPENCODE_AGENT_FILES: tuple[str, ...] = (
    "loop9-controller.md",
    "loop9-refiner.md",
    "loop9-solver.md",
    "loop9-validator.md",
)


class ProfileError(ValueError):
    pass


def load_json(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ProfileError(f"profile not found: {path}") from exc
    except json.JSONDecodeError as exc:
        raise ProfileError(f"profile is not valid JSON: {path}: {exc}") from exc
    if not isinstance(data, dict):
        raise ProfileError(f"profile root must be a JSON object: {path}")
    return data


def _split_expr(expr: str) -> tuple[str, str]:
    expr = expr.strip()
    if ":" not in expr:
        return "raw", expr
    prefix, rest = expr.split(":", 1)
    if prefix in {"raw", "json", "toml", "sh", "env"}:
        return prefix, rest.strip()
    return "raw", expr


def get_path(data: dict[str, Any], path_expr: str) -> Any:
    current: Any = data
    for part in path_expr.split("."):
        part = part.strip()
        if not part:
            continue
        if isinstance(current, dict) and part in current:
            current = current[part]
            continue
        raise KeyError(path_expr)
    return current


def _toml_value(value: Any) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (int, float)):
        return str(value)
    if isinstance(value, (list, tuple)):
        return "[" + ", ".join(_toml_value(item) for item in value) + "]"
    if value is None:
        return '""'
    return json.dumps(str(value), ensure_ascii=False)


def _format_value(data: dict[str, Any], filter_name: str, path_expr: str) -> str:
    optional = path_expr.startswith("?")
    if optional:
        path_expr = path_expr[1:].strip()
    if filter_name == "env":
        value = os.environ.get(path_expr, "")
    else:
        try:
            value = get_path(data, path_expr)
        except KeyError:
            if optional:
                value = ""
            else:
                raise

    if filter_name == "json":
        return json.dumps(value, ensure_ascii=False)
    if filter_name == "toml":
        return _toml_value(value)
    if filter_name == "sh":
        return shlex.quote(str(value))
    if isinstance(value, (dict, list, tuple, bool)):
        return json.dumps(value, ensure_ascii=False)
    if value is None:
        return ""
    return str(value)


def render_text(template: str, profile: dict[str, Any]) -> tuple[str, list[str], list[str]]:
    placeholders: list[str] = []
    unresolved: list[str] = []

    def replace(match: re.Match[str]) -> str:
        expr = match.group(1).strip()
        placeholders.append(expr)
        filter_name, path_expr = _split_expr(expr)
        try:
            return _format_value(profile, filter_name, path_expr)
        except KeyError:
            unresolved.append(expr)
            return match.group(0)

    rendered = PLACEHOLDER_RE.sub(replace, template)
    unresolved.extend(match.group(1).strip() for match in PLACEHOLDER_RE.finditer(rendered))
    return rendered, placeholders, sorted(set(unresolved))


def target_for_profile_key(profile: dict[str, Any], key: str, target_root: Path | None = None) -> Path:
    raw = str(get_path(profile, key))
    path = Path(raw).expanduser()
    if target_root is None:
        return path
    if path.is_absolute():
        return target_root / str(path).lstrip("/")
    return target_root / path


def render_all(
    profile: dict[str, Any],
    *,
    repo_root: Path = REPO_ROOT,
    target_root: Path | None = None,
    names: set[str] | None = None,
) -> list[RenderedTemplate]:
    rendered_items: list[RenderedTemplate] = []
    for spec in TEMPLATES:
        if names and spec.name not in names:
            continue
        template_path = repo_root / spec.template
        template = template_path.read_text(encoding="utf-8")
        content, placeholders, unresolved = render_text(template, profile)
        digest = hashlib.sha256(content.encode("utf-8")).hexdigest()
        target_path = target_for_profile_key(profile, spec.target_profile_key, target_root=target_root)
        rendered_items.append(
            RenderedTemplate(
                name=spec.name,
                template_path=template_path,
                target_path=target_path,
                content=content,
                placeholders=placeholders,
                unresolved=unresolved,
                sha256=digest,
                mode=spec.mode,
            )
        )
    if not names or "opencode-agents" in names:
        rendered_items.extend(render_opencode_agents(profile, repo_root=repo_root, target_root=target_root))
    return rendered_items


def _replace_frontmatter_scalar(text: str, key: str, value: str) -> str:
    lines = text.splitlines(keepends=True)
    if not lines or lines[0].strip() != "---":
        return text

    end_idx = None
    for idx in range(1, len(lines)):
        if lines[idx].strip() == "---":
            end_idx = idx
            break
    if end_idx is None:
        return text

    rendered = json.dumps(str(value), ensure_ascii=False)
    replacement = f"{key}: {rendered}\n"
    for idx in range(1, end_idx):
        if re.match(rf"^\s*{re.escape(key)}\s*:", lines[idx]):
            lines[idx] = replacement
            return "".join(lines)

    lines.insert(end_idx, replacement)
    return "".join(lines)


def render_opencode_agents(
    profile: dict[str, Any],
    *,
    repo_root: Path = REPO_ROOT,
    target_root: Path | None = None,
) -> list[RenderedTemplate]:
    source_root = repo_root / "workspace" / "Super8" / ".opencode" / "agents"
    placeholders = ["models.opencode.agentModel", "models.opencode.variant", "paths.super8Root"]
    unresolved: list[str] = []

    try:
        model = str(get_path(profile, "models.opencode.agentModel"))
    except KeyError:
        model = ""
        unresolved.append("models.opencode.agentModel")
    try:
        variant = str(get_path(profile, "models.opencode.variant"))
    except KeyError:
        variant = ""
        unresolved.append("models.opencode.variant")
    try:
        super8_root = target_for_profile_key(profile, "paths.super8Root", target_root=target_root)
    except KeyError:
        super8_root = Path("{{paths.super8Root}}")
        unresolved.append("paths.super8Root")

    items: list[RenderedTemplate] = []
    for filename in OPENCODE_AGENT_FILES:
        source = source_root / filename
        content = source.read_text(encoding="utf-8")
        if not unresolved:
            content = _replace_frontmatter_scalar(content, "model", model)
            content = _replace_frontmatter_scalar(content, "variant", variant)
        digest = hashlib.sha256(content.encode("utf-8")).hexdigest()
        items.append(
            RenderedTemplate(
                name=f"opencode-agent:{filename}",
                template_path=source,
                target_path=super8_root / ".opencode" / "agents" / filename,
                content=content,
                placeholders=placeholders,
                unresolved=sorted(set(unresolved)),
                sha256=digest,
                mode=0o644,
            )
        )
    return items


def _is_placeholder_value(value: Any) -> bool:
    if not isinstance(value, str):
        return False
    stripped = value.strip()
    if not stripped:
        return True
    return (
        stripped.startswith("CHANGE_ME")
        or stripped.startswith("<")
        or stripped.endswith("_HERE")
        or stripped in {"TODO", "REPLACE_ME", "YOUR_KEY"}
    )


def collect_profile_placeholders(data: Any, prefix: str = "") -> list[str]:
    rows: list[str] = []
    if isinstance(data, dict):
        for key, value in data.items():
            path = f"{prefix}.{key}" if prefix else str(key)
            rows.extend(collect_profile_placeholders(value, path))
    elif isinstance(data, list):
        for idx, value in enumerate(data):
            rows.extend(collect_profile_placeholders(value, f"{prefix}[{idx}]"))
    elif _is_placeholder_value(data):
        rows.append(prefix)
    return rows


def collect_secret_fields(data: Any, prefix: str = "") -> list[str]:
    rows: list[str] = []
    if isinstance(data, dict):
        for key, value in data.items():
            path = f"{prefix}.{key}" if prefix else str(key)
            if SECRET_FIELD_RE.search(str(key)) and isinstance(value, str) and value.strip():
                rows.append(path)
            rows.extend(collect_secret_fields(value, path))
    elif isinstance(data, list):
        for idx, value in enumerate(data):
            rows.extend(collect_secret_fields(value, f"{prefix}[{idx}]"))
    return rows


def mask_sensitive(text: str) -> str:
    def repl(match: re.Match[str]) -> str:
        return f"{match.group(1)}{match.group(2)}***MASKED***{match.group(4)}"

    masked = MASK_LINE_RE.sub(repl, text)
    masked = re.sub(r"(?i)(OPENAI_API_KEY|FOFA_KEY|HUNTER_API_KEY|SHODAN_KEY)=\S+", r"\1=***MASKED***", masked)
    return masked


def write_rendered(items: list[RenderedTemplate]) -> None:
    for item in items:
        item.target_path.parent.mkdir(parents=True, exist_ok=True)
        item.target_path.write_text(item.content, encoding="utf-8")
        item.target_path.chmod(item.mode)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Render LongWangClaw local config templates from one profile.")
    parser.add_argument(
        "--profile",
        default=str(DEFAULT_PROFILE if DEFAULT_PROFILE.exists() else EXAMPLE_PROFILE),
        help="Path to longwang.local.json. Defaults to local profile, then example profile.",
    )
    parser.add_argument("--repo-root", default=str(REPO_ROOT), help="LongWangClaw repo root.")
    parser.add_argument(
        "--only",
        action="append",
        choices=[spec.name for spec in TEMPLATES] + ["opencode-agents"],
        help="Render only one template group. May be repeated.",
    )
    parser.add_argument("--target-root", help="Rewrite absolute target paths under this directory for testing.")
    parser.add_argument("--write", action="store_true", help="Actually write rendered files. Default is dry-run.")
    parser.add_argument("--dry-run", action="store_true", help="Explicit dry-run; kept for readability because dry-run is already the default.")
    parser.add_argument("--show", action="store_true", help="Print masked rendered content.")
    parser.add_argument("--allow-unresolved", action="store_true", help="Do not fail when template placeholders cannot be resolved.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    profile_path = Path(args.profile).expanduser().resolve()
    repo_root = Path(args.repo_root).expanduser().resolve()
    target_root = Path(args.target_root).expanduser().resolve() if args.target_root else None
    profile = load_json(profile_path)
    names = set(args.only or [])
    items = render_all(profile, repo_root=repo_root, target_root=target_root, names=names or None)

    unresolved = [item for item in items if item.unresolved]
    if unresolved and not args.allow_unresolved:
        for item in unresolved:
            print(f"[error] {item.name}: unresolved placeholders: {', '.join(item.unresolved)}")
        return 2

    mode = "write" if args.write else "dry-run"
    print(f"profile={profile_path}")
    print(f"repo_root={repo_root}")
    if target_root:
        print(f"target_root={target_root}")
    print(f"mode={mode}")

    placeholder_fields = collect_profile_placeholders(profile)
    if placeholder_fields:
        print(f"profile_placeholders={len(placeholder_fields)}")
        for field in placeholder_fields[:30]:
            print(f"  - {field}")
        if len(placeholder_fields) > 30:
            print(f"  ... {len(placeholder_fields) - 30} more")

    for item in items:
        print(
            f"[{mode}] {item.name}: {item.template_path.relative_to(repo_root)} -> "
            f"{item.target_path} bytes={len(item.content.encode('utf-8'))} "
            f"sha256={item.sha256[:16]} placeholders={len(item.placeholders)} unresolved={len(item.unresolved)}"
        )
        if args.show:
            print(mask_sensitive(item.content).rstrip())
            print("---")

    if args.write:
        write_rendered(items)
        print(f"written={len(items)}")
    else:
        print("dry_run=true")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
