#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

PHASES = {
    "project_overview": "00-项目总览",
    "original_input": "01-原始输入",
    "audit_process": "02-审计过程",
    "findings": "03-审计结论",
    "validation": "04-验证报告",
    "poc": "05-PoC与验证",
    "sync_log": "90-同步记录",
}

GENERIC_PROJECT_HINTS = {"super8", "wgat", "0001", "0428", "dc01", "9f4c", "fc31", "a74f", "785a", "g3y6"}
CANONICAL_PROJECT_REGISTRY_PATH = Path(__file__).resolve().parent.parent / "references" / "canonical-project-registry.json"


def slugify(text: str) -> str:
    text = text.strip()
    text = re.sub(r"[^0-9A-Za-z\u4e00-\u9fff]+", "-", text)
    text = re.sub(r"-+", "-", text).strip("-")
    return text.lower() or "unnamed-project"


def detect_kind(path: Path) -> str:
    if not path.exists():
        raise FileNotFoundError(f"Path not found: {path}")
    if path.is_file():
        if path.name in {"brief.md", "solution.md", "validation_report.md", "shared_context.md"}:
            return "poc-bundle"
        if path.name in {"index.md", "part01.md", "manifest.json", "medium_risks.md"}:
            return "loop9-run-artifact"
    if path.is_dir():
        child_names = {p.name for p in path.iterdir()}
        if {"manifest.json", "brief.md"}.issubset(child_names) and (
            "poc-drafts" in child_names or "verification-pack" in child_names
        ):
            return "poc-bundle"
        if "original_goal" in child_names or "shared_context" in child_names or any(
            name.startswith("solution_v") for name in child_names
        ):
            return "loop9-run"
    parent = path.parent
    if parent.is_dir():
        child_names = {p.name for p in parent.iterdir()}
        if {"manifest.json", "brief.md"}.issubset(child_names):
            return "poc-bundle"
        if "original_goal" in child_names or "shared_context" in child_names or any(
            name.startswith("solution_v") for name in child_names
        ):
            return "loop9-run"
    raise ValueError(f"Unrecognized Loop9/PoC artifact shape: {path}")


def find_root(path: Path, kind: str) -> Path:
    if kind == "poc-bundle":
        return path if path.is_dir() else path.parent
    if kind == "loop9-run":
        return path if path.is_dir() else path.parent
    if kind == "loop9-run-artifact":
        if path.is_dir():
            return path.parent
        if path.parent.name.startswith(("solution_v", "validation_report_v")) or path.parent.name in {"original_goal", "shared_context"}:
            return path.parent.parent
        return path.parent
    raise ValueError(f"Unsupported kind: {kind}")


def highest_version(entries: list[Path], prefix: str) -> Path | None:
    best: tuple[int, Path] | None = None
    for entry in entries:
        m = re.fullmatch(rf"{re.escape(prefix)}(\d+)", entry.name)
        if not m:
            continue
        version = int(m.group(1))
        if best is None or version > best[0]:
            best = (version, entry)
    return best[1] if best else None


def read_text_if_exists(path: Path) -> str | None:
    if not path.exists() or not path.is_file():
        return None
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return path.read_text(encoding="utf-8", errors="replace")


def normalize_candidate(candidate: str) -> str:
    candidate = candidate.strip().rstrip("`.,)")
    candidate = candidate.split("/")[-1]

    run_like = re.fullmatch(r"\d{8}-\d{6}-(.+)", candidate)
    if run_like:
        candidate = run_like.group(1)
        parts = candidate.split("-")
        if len(parts) >= 2 and re.fullmatch(r"[A-Za-z0-9]{4}", parts[-1]):
            candidate = "-".join(parts[:-1])

    return candidate


def load_canonical_project_registry(registry_path: Path = CANONICAL_PROJECT_REGISTRY_PATH) -> dict[str, Any]:
    if not registry_path.exists():
        return {"projects": {}}
    text = read_text_if_exists(registry_path)
    if not text:
        return {"projects": {}}
    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid canonical project registry JSON: {registry_path}") from exc
    if not isinstance(data, dict):
        raise ValueError(f"Canonical project registry must be a JSON object: {registry_path}")
    projects = data.get("projects")
    if projects is None:
        data["projects"] = {}
        return data
    if not isinstance(projects, dict):
        raise ValueError(f"Canonical project registry 'projects' must be an object: {registry_path}")
    return data


def normalize_project_identity(
    slug: str,
    title: str,
    *,
    registry_path: Path = CANONICAL_PROJECT_REGISTRY_PATH,
) -> tuple[str, str, dict[str, Any]]:
    registry = load_canonical_project_registry(registry_path)
    projects = registry.get("projects", {})
    lookup_keys = {slugify(slug), slugify(title), slugify(normalize_candidate(slug)), slugify(normalize_candidate(title))}

    for canonical_slug_raw, entry in projects.items():
        if not isinstance(entry, dict):
            continue
        canonical_slug = slugify(canonical_slug_raw)
        canonical_title = str(entry.get("title") or canonical_slug_raw).strip() or canonical_slug_raw
        aliases = entry.get("aliases", [])
        alias_keys = {canonical_slug, slugify(canonical_title)}
        if isinstance(aliases, list):
            alias_keys.update(slugify(str(alias)) for alias in aliases)
        if lookup_keys & alias_keys:
            changed = canonical_slug != slug or canonical_title != title
            return canonical_slug, canonical_title, {
                "applied": changed,
                "reason": "canonical-project-registry",
                "matched_on": sorted(lookup_keys & alias_keys),
                "registry_path": str(registry_path),
                "canonical_slug": canonical_slug,
                "canonical_title": canonical_title,
            }

    return slug, title, {
        "applied": False,
        "reason": "no-registry-match",
        "registry_path": str(registry_path),
        "canonical_slug": slug,
        "canonical_title": title,
    }


def infer_project(root: Path, explicit_title: str | None = None) -> tuple[str, str, str, list[str]]:
    reasons: list[str] = []
    if explicit_title:
        title = explicit_title.strip()
        slug = slugify(title)
        return slug, title, "explicit", ["--project-title"]

    name = root.name
    text_parts = [
        read_text_if_exists(root / "original_goal" / "part01.md") or "",
        read_text_if_exists(root / "original_goal" / "index.md") or "",
        read_text_if_exists(root / "shared_context" / "part01.md") or "",
        read_text_if_exists(root / "shared_context" / "index.md") or "",
        read_text_if_exists(root / "shared_context.md") or "",
        read_text_if_exists(root / "brief.md") or "",
        read_text_if_exists(root / "manifest.json") or "",
        read_text_if_exists(root / "real_pocs" / "manifest.json") or "",
        read_text_if_exists(root / "real_pocs" / "real_poc_final_status.json") or "",
    ]
    text = "\n".join(part for part in text_parts if part)

    authority_patterns = [
        r"审计目标源码项目名[：:]\s*`?([A-Za-z0-9_.-]{3,})`?",
        r"target_repo_name[：:]\s*([A-Za-z0-9_.-]{3,})",
        r"target_repo_path[：:]\s*([A-Za-z0-9_./-]+/([A-Za-z0-9_.-]{3,}))",
        r"/targets/([A-Za-z0-9_.-]{3,})",
        r"audit target is\s+([A-Za-z0-9_.-]{3,})",
        r"Audit the full\s+([A-Za-z0-9_.-]{3,})\s+Git repository",
        r"Product:\s*.*?\(([A-Za-z0-9_.-]{3,})\)",
    ]
    for pattern in authority_patterns:
        for m in re.finditer(pattern, text, flags=re.IGNORECASE):
            candidate = normalize_candidate(m.group(m.lastindex or 1))
            if candidate.lower() in GENERIC_PROJECT_HINTS:
                continue
            if candidate.lower().startswith(("solution_v", "validation_report_v")):
                continue
            return slugify(candidate), candidate, "high", ["authority-metadata"]

    patterns = [
        r"(?:目标|仓库|项目|源码|Repo root|Requested path)[：:]\s*([A-Za-z0-9_./-]{3,})",
        r"github\.com/[^/]+/([A-Za-z0-9_.-]{3,})",
        r"/loop9/(\d{8}-\d{6}-[A-Za-z0-9_.-]{3,})",
    ]
    for pattern in patterns:
        for m in re.finditer(pattern, text, flags=re.IGNORECASE):
            candidate = normalize_candidate(m.group(1))
            if candidate.lower() in GENERIC_PROJECT_HINTS:
                continue
            if candidate.lower().startswith(("solution_v", "validation_report_v")):
                continue
            return slugify(candidate), candidate, "medium", ["artifact-content"]

    parts = name.split("-")
    candidate_tails = []
    if parts:
        candidate_tails.extend(parts[-3:])
    for tail in candidate_tails:
        tail = tail.strip()
        if not tail:
            continue
        if tail.lower() in GENERIC_PROJECT_HINTS:
            continue
        if tail.lower().startswith(("solution_v", "validation_report_v")):
            continue
        if re.fullmatch(r"[0-9a-f]{4}", tail.lower()):
            continue
        if re.fullmatch(r"\d{8}", tail) or re.fullmatch(r"\d{6}", tail):
            continue
        if tail.lower() == "super8":
            continue
        title = tail
        return slugify(title), title, "low", ["dirname-tail"]

    title = name
    return slugify(title), title, "low", ["fallback-root-name"]


def collect_loop9_run(root: Path, project_slug: str, project_title: str, confidence: str, reasons: list[str]) -> dict[str, Any]:
    entries = [p for p in root.iterdir()]
    latest_solution = highest_version([p for p in entries if p.is_dir()], "solution_v")
    latest_validation = highest_version([p for p in entries if p.is_dir()], "validation_report_v")
    original_goal = root / "original_goal"
    shared_context = root / "shared_context"
    medium_risks = root / "medium_risks.md"

    docs: list[dict[str, Any]] = []

    def add_doc(phase_key: str, title: str, markdown_path: Path | None, extra: dict[str, Any] | None = None):
        if markdown_path is None or not markdown_path.exists():
            return
        item = {
            "phase_key": phase_key,
            "phase_title": PHASES[phase_key],
            "doc_key": f"loop9::{root.name}::{phase_key}::{markdown_path.parent.name if markdown_path.parent != root else markdown_path.name}",
            "title": title,
            "source_markdown": str(markdown_path),
            "source_dir": str(markdown_path.parent),
            "mode": "overwrite",
        }
        if extra:
            item.update(extra)
        docs.append(item)

    original_goal_parts = collect_part_files(original_goal)
    shared_context_parts = collect_part_files(shared_context)
    add_doc(
        "original_input",
        f"{root.name} · 原始目标",
        original_goal_parts[0] if original_goal_parts else None,
        {
            "rendered_markdown": render_part_directory_markdown(original_goal) if original_goal_parts else None,
            "attachments": collect_side_files(original_goal, skip={p.name for p in original_goal_parts}),
            "source_parts": [str(p) for p in original_goal_parts],
        },
    )
    add_doc(
        "audit_process",
        f"{root.name} · 共享上下文",
        shared_context_parts[0] if shared_context_parts else None,
        {
            "rendered_markdown": render_part_directory_markdown(shared_context) if shared_context_parts else None,
            "attachments": collect_side_files(shared_context, skip={p.name for p in shared_context_parts}),
            "source_parts": [str(p) for p in shared_context_parts],
        },
    )
    if latest_solution:
        solution_parts = collect_part_files(latest_solution)
        add_doc(
            "findings",
            f"{root.name} · {latest_solution.name}",
            solution_parts[0] if solution_parts else None,
            {
                "artifact_version": latest_solution.name,
                "rendered_markdown": render_part_directory_markdown(latest_solution) if solution_parts else None,
                "attachments": collect_side_files(latest_solution, skip={p.name for p in solution_parts}),
                "source_parts": [str(p) for p in solution_parts],
            },
        )
    if latest_validation:
        validation_parts = collect_part_files(latest_validation)
        add_doc(
            "validation",
            f"{root.name} · {latest_validation.name}",
            validation_parts[0] if validation_parts else None,
            {
                "artifact_version": latest_validation.name,
                "rendered_markdown": render_part_directory_markdown(latest_validation) if validation_parts else None,
                "attachments": collect_side_files(latest_validation, skip={p.name for p in validation_parts}),
                "source_parts": [str(p) for p in validation_parts],
            },
        )
    if medium_risks.exists():
        add_doc(
            "findings",
            f"{root.name} · medium_risks",
            medium_risks,
            {"artifact_version": "medium_risks"},
        )

    real_pocs_dir = root / "real_pocs"
    real_pocs_entries = [p for p in real_pocs_dir.iterdir()] if real_pocs_dir.is_dir() else []
    latest_real_poc_solution = highest_version([p for p in real_pocs_entries if p.is_dir()], "real_poc_solution_v")
    latest_real_poc_validation = highest_version([p for p in real_pocs_entries if p.is_dir()], "real_poc_validation_report_v")
    real_pocs_manifest = real_pocs_dir / "manifest.json"
    real_poc_final_status = real_pocs_dir / "real_poc_final_status.json"
    real_poc_scripts = sorted([p for p in real_pocs_dir.glob("*.py") if p.is_file()]) if real_pocs_dir.is_dir() else []

    if latest_real_poc_solution:
        real_poc_solution_parts = collect_part_files(latest_real_poc_solution)
        add_doc(
            "poc",
            f"{root.name} · {latest_real_poc_solution.name}",
            real_poc_solution_parts[0] if real_poc_solution_parts else None,
            {
                "artifact_version": latest_real_poc_solution.name,
                "rendered_markdown": render_part_directory_markdown(latest_real_poc_solution) if real_poc_solution_parts else None,
                "attachments": collect_side_files(latest_real_poc_solution, skip={p.name for p in real_poc_solution_parts}),
                "source_parts": [str(p) for p in real_poc_solution_parts],
            },
        )
    if latest_real_poc_validation:
        real_poc_validation_parts = collect_part_files(latest_real_poc_validation)
        add_doc(
            "poc",
            f"{root.name} · {latest_real_poc_validation.name}",
            real_poc_validation_parts[0] if real_poc_validation_parts else None,
            {
                "artifact_version": latest_real_poc_validation.name,
                "rendered_markdown": render_part_directory_markdown(latest_real_poc_validation) if real_poc_validation_parts else None,
                "attachments": collect_side_files(latest_real_poc_validation, skip={p.name for p in real_poc_validation_parts}),
                "source_parts": [str(p) for p in real_poc_validation_parts],
            },
        )
    if real_pocs_manifest.exists():
        add_doc(
            "poc",
            f"{root.name} · real_pocs 清单",
            real_pocs_manifest,
            {
                "doc_key": f"realpoc::{root.name}::manifest::real_pocs",
                "rendered_markdown": render_real_poc_manifest_markdown(real_pocs_manifest, real_poc_scripts, root),
                "attachments": collect_side_files(real_pocs_dir, skip={'__pycache__'}),
            },
        )
    if real_poc_final_status.exists():
        add_doc(
            "poc",
            f"{root.name} · real_poc_final_status",
            real_poc_final_status,
            {
                "doc_key": f"realpoc::{root.name}::status::real_poc_final_status",
                "rendered_markdown": render_code_file_markdown(real_poc_final_status, title=f"{root.name} · real_poc_final_status"),
            },
        )
    for script_path in real_poc_scripts:
        add_doc(
            "poc",
            f"{root.name} · py · {script_path.name}",
            script_path,
            {
                "doc_key": f"realpoc::{root.name}::py::{script_path.name}",
                "rendered_markdown": render_code_file_markdown(script_path, title=f"{root.name} · py · {script_path.name}"),
            },
        )

    project_overview = render_project_overview_markdown(
        project_title=project_title,
        project_slug=project_slug,
        source_kind="loop9-run",
        root=root,
        docs=docs,
        confidence=confidence,
        reasons=reasons,
    )
    sync_log = render_sync_log_markdown(source_kind="loop9-run", root=root, docs=docs)
    catalog_entry = render_catalog_entry_markdown(project_title=project_title, project_slug=project_slug, root=root, docs=docs)

    return {
        "source_kind": "loop9-run",
        "run_id": root.name,
        "project": {
            "slug": project_slug,
            "title": project_title,
            "confidence": confidence,
            "reasons": reasons,
        },
        "project_layout": phase_layout(project_title),
        "docs": docs,
        "markdown_templates": {
            "project_overview": project_overview,
            "sync_log": sync_log,
            "catalog_entry": catalog_entry,
        },
    }


def collect_poc_bundle(root: Path, project_slug: str, project_title: str, confidence: str, reasons: list[str]) -> dict[str, Any]:
    docs: list[dict[str, Any]] = []
    file_mapping = [
        ("poc", f"{root.name} · brief", root / "brief.md"),
        ("findings", f"{root.name} · solution", root / "solution.md"),
        ("validation", f"{root.name} · validation_report", root / "validation_report.md"),
        ("audit_process", f"{root.name} · shared_context", root / "shared_context.md"),
        ("poc", f"{root.name} · poc overview", root / "poc-drafts" / "overview.md"),
        ("validation", f"{root.name} · verification overview", root / "verification-pack" / "verification-overview.md"),
        ("validation", f"{root.name} · verification matrix", root / "verification-pack" / "verification-matrix.md"),
    ]
    for phase_key, title, path in file_mapping:
        if path.exists():
            docs.append(
                {
                    "phase_key": phase_key,
                    "phase_title": PHASES[phase_key],
                    "doc_key": f"poc::{root.name}::{phase_key}::{path.name}",
                    "title": title,
                    "source_markdown": str(path),
                    "source_dir": str(path.parent),
                    "mode": "overwrite",
                    "attachments": collect_side_files(path.parent, skip={path.name}) if path.parent != root else [],
                }
            )

    project_overview = render_project_overview_markdown(
        project_title=project_title,
        project_slug=project_slug,
        source_kind="poc-bundle",
        root=root,
        docs=docs,
        confidence=confidence,
        reasons=reasons,
    )
    sync_log = render_sync_log_markdown(source_kind="poc-bundle", root=root, docs=docs)
    catalog_entry = render_catalog_entry_markdown(project_title=project_title, project_slug=project_slug, root=root, docs=docs)

    return {
        "source_kind": "poc-bundle",
        "bundle_id": root.name,
        "project": {
            "slug": project_slug,
            "title": project_title,
            "confidence": confidence,
            "reasons": reasons,
        },
        "project_layout": phase_layout(project_title),
        "docs": docs,
        "markdown_templates": {
            "project_overview": project_overview,
            "sync_log": sync_log,
            "catalog_entry": catalog_entry,
        },
    }


def collect_side_files(directory: Path, skip: set[str] | None = None) -> list[str]:
    skip = skip or set()
    files: list[str] = []
    if not directory.exists() or not directory.is_dir():
        return files
    for child in sorted(directory.iterdir()):
        if child.name in skip:
            continue
        if child.is_file():
            files.append(str(child))
    return files


def collect_part_files(directory: Path) -> list[Path]:
    if not directory.exists() or not directory.is_dir():
        return []
    def part_key(path: Path) -> tuple[int, str]:
        m = re.fullmatch(r"part(\d+)\.md", path.name)
        return (int(m.group(1)) if m else 10**9, path.name)
    return sorted([p for p in directory.iterdir() if p.is_file() and re.fullmatch(r"part\d+\.md", p.name)], key=part_key)


def render_part_directory_markdown(directory: Path) -> str:
    part_files = collect_part_files(directory)
    texts = [read_text_if_exists(path) or "" for path in part_files]
    return "\n\n".join(text.rstrip("\n") for text in texts if text is not None).rstrip() + "\n"


def render_code_file_markdown(path: Path, title: str | None = None) -> str:
    suffix = path.suffix.lower()
    lang = {
        ".py": "python",
        ".json": "json",
        ".md": "markdown",
        ".sh": "bash",
        ".bash": "bash",
        ".zsh": "bash",
    }.get(suffix, "text")
    text = read_text_if_exists(path) or ""
    heading = title or path.name
    return (
        f"# {heading}\n\n"
        f"## 文件信息\n"
        f"- 文件名：`{path.name}`\n"
        f"- 本地路径：`{path}`\n"
        f"- 扩展名：`{path.suffix or '(none)'}`\n\n"
        f"## 文件正文\n"
        f"```{lang}\n{text.rstrip()}\n```\n"
    )


def render_real_poc_manifest_markdown(manifest_path: Path, script_paths: list[Path], run_root: Path) -> str:
    manifest_text = read_text_if_exists(manifest_path) or "{}"
    try:
        manifest = json.loads(manifest_text)
    except json.JSONDecodeError:
        manifest = {}
    findings = manifest.get("findings", []) if isinstance(manifest, dict) else []
    lines = [
        "# real_pocs 清单",
        "",
        "## 目录",
        f"- `{manifest.get('shared_poc_dir', str(manifest_path.parent))}`",
        "",
        "## 当前脚本文件",
    ]
    for script_path in script_paths:
        lines.append(f"- `{script_path.name}`")
    lines += ["", "## 当前映射"]
    for finding in findings:
        lines.append(f"- `{finding.get('finding_id', '')}` -> `{finding.get('mapped_file', '')}`")
    lines += [
        "",
        "## 当前状态",
        f"- generated_by: `{manifest.get('generated_by', '')}`",
        f"- 共享 PoC 当前 last_round: `{max((f.get('last_round', 0) for f in findings), default=0)}`",
        f"- run_dir: `{run_root}`",
        "- 适合作为后续增量更新测试页：如果脚本集合、映射、轮次继续变化，这一页应被覆盖更新。",
        "",
        "## manifest 原文",
        "```json",
        manifest_text.strip(),
        "```",
        "",
    ]
    return "\n".join(lines)


def phase_layout(project_title: str) -> dict[str, Any]:
    return {
        "project_title": project_title,
        "project_index_title": f"项目 - {project_title}",
        "phases": [{"key": key, "title": title} for key, title in PHASES.items()],
    }


def render_project_overview_markdown(
    *,
    project_title: str,
    project_slug: str,
    source_kind: str,
    root: Path,
    docs: list[dict[str, Any]],
    confidence: str,
    reasons: list[str],
) -> str:
    lines = [
        f"# {project_title} - 项目总览",
        "",
        "## 项目标识",
        f"- 项目标题：{project_title}",
        f"- 项目标识：`{project_slug}`",
        f"- 最近同步源类型：`{source_kind}`",
        f"- 最近同步根路径：`{root}`",
        f"- 项目识别置信度：`{confidence}`",
        f"- 识别依据：{', '.join(reasons) if reasons else 'unknown'}",
        "",
        "## 阶段目录",
    ]
    for key, title in PHASES.items():
        lines.append(f"- {title}")
    lines += ["", "## 当前已规划同步的文档", ""]
    for doc in docs:
        lines.append(f"- [{doc['phase_title']}] {doc['title']}  ")
        lines.append(f"  源：`{doc['source_markdown']}`")
    return "\n".join(lines).rstrip() + "\n"


def render_sync_log_markdown(*, source_kind: str, root: Path, docs: list[dict[str, Any]]) -> str:
    lines = [
        "# 同步记录",
        "",
        "## 最近一次规划",
        f"- 来源类型：`{source_kind}`",
        f"- 来源根路径：`{root}`",
        f"- 文档数：{len(docs)}",
        "",
        "## 计划覆盖的文档",
    ]
    for doc in docs:
        lines.append(f"- {doc['title']} -> {doc['phase_title']}")
    lines.append("")
    lines.append("后续同步时，追加新的时间戳记录到本页底部。")
    return "\n".join(lines).rstrip() + "\n"


def render_catalog_entry_markdown(*, project_title: str, project_slug: str, root: Path, docs: list[dict[str, Any]]) -> str:
    lines = [
        f"## {project_title}",
        "",
        f"- 项目标识：`{project_slug}`",
        f"- 最近来源：`{root}`",
        f"- 当前规划文档数：{len(docs)}",
        "",
        "阶段：",
    ]
    for key, title in PHASES.items():
        count = sum(1 for doc in docs if doc["phase_key"] == key)
        lines.append(f"- {title}（{count}）")
    return "\n".join(lines).rstrip() + "\n"


def build_plan(path: Path, project_title: str | None = None) -> dict[str, Any]:
    kind = detect_kind(path)
    root = find_root(path, kind)
    raw_project_slug, raw_project_title, confidence, reasons = infer_project(root, explicit_title=project_title)
    project_slug, inferred_title, normalization = normalize_project_identity(raw_project_slug, raw_project_title)
    if kind in {"loop9-run", "loop9-run-artifact"}:
        payload = collect_loop9_run(root, project_slug, inferred_title, confidence, reasons)
    elif kind == "poc-bundle":
        payload = collect_poc_bundle(root, project_slug, inferred_title, confidence, reasons)
    else:
        raise ValueError(f"Unsupported kind for planning: {kind}")

    payload["project"] = {
        **payload["project"],
        "raw_slug": raw_project_slug,
        "raw_title": raw_project_title,
        "normalization": normalization,
    }

    return {
        "schema_version": 1,
        "requested_path": str(path),
        "resolved_root": str(root),
        "detected_kind": kind,
        **payload,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Build a publish plan for Loop9 / PoC artifacts.")
    parser.add_argument("path", help="Loop9 run dir, artifact path, or PoC bundle path")
    parser.add_argument("--project-title", help="Override project title when auto inference is weak")
    parser.add_argument("--pretty", action="store_true", help="Pretty-print JSON output")
    args = parser.parse_args()

    plan = build_plan(Path(args.path).expanduser().resolve(), project_title=args.project_title)
    if args.pretty:
        json.dump(plan, sys.stdout, ensure_ascii=False, indent=2)
    else:
        json.dump(plan, sys.stdout, ensure_ascii=False)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
