#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

WORKSPACE = Path("~/.openclaw/workspace").expanduser()
STATE_PATH = WORKSPACE / "memory" / "loop9-feishu-publisher-state.json"
DELIVERY_CONTAINER_TITLE = "06-标准交付报告"
MANIFEST_NAME = "98-delivery-bundle.manifest.json"
CANONICAL_REPORT_KIND = "loop9-standard-delivery-report"
HTTP_RENDER_TOTAL_CHAR_LIMIT = 18_000
HTTP_RENDER_FILE_CHAR_LIMIT = 6_000
HTTP_RENDER_SNIPPET_CHAR_LIMIT = 4_000


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build a thin Feishu publish plan from a canonical reports/<repo> directory")
    parser.add_argument("report_dir", help="Path like workspace/reports/<repo>")
    parser.add_argument("--project-title", help="Override project title when state lookup is missing/ambiguous")
    parser.add_argument("--pretty", action="store_true")
    return parser.parse_args()


def load_state() -> dict[str, Any]:
    if not STATE_PATH.exists():
        return {"projects": {}}
    return read_json(STATE_PATH)


def load_manifest(report_dir: Path) -> dict[str, Any]:
    path = report_dir / MANIFEST_NAME
    if not path.exists():
        raise SystemExit(f"canonical manifest not found: {path}")
    manifest = read_json(path)
    if manifest.get("report_kind") != CANONICAL_REPORT_KIND:
        raise SystemExit(f"invalid manifest kind in {path}")
    return manifest


def slug_from_report_dir(report_dir: Path) -> str:
    manifest = load_manifest(report_dir)
    return str(((manifest.get("repo") or {}).get("slug")) or report_dir.name).strip() or "unknown-project"


def fence_for_suffix(path: Path) -> str:
    return {
        ".py": "python",
        ".json": "json",
        ".txt": "text",
        ".md": "markdown",
        ".log": "text",
    }.get(path.suffix.lower(), "")


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def sanitize_http_text(text: str) -> str:
    import re

    text = re.sub(r"(?im)^Authorization:\s*Bearer\s+.+$", "Authorization: Bearer <redacted>", text)
    text = re.sub(r"(?im)^Set-Cookie:\s*([^=;\s]+)=([^;\r\n]*)", r"Set-Cookie: \1=<redacted>", text)
    return text


def strip_leading_h1(markdown: str) -> str:
    lines = markdown.splitlines()
    if lines and lines[0].startswith("# "):
        lines = lines[1:]
        while lines and not lines[0].strip():
            lines = lines[1:]
    return "\n".join(lines).rstrip() + "\n" if lines else ""


def render_file(path: Path) -> str:
    if path.suffix.lower() == ".md":
        return strip_leading_h1(read_text(path))
    lang = fence_for_suffix(path)
    body = read_text(path)
    return f"```{lang}\n{body}\n```\n"


def _truncate_text(text: str, limit: int) -> tuple[str, bool]:
    if len(text) <= limit:
        return text, False
    head_limit = max(1, limit // 2)
    tail_limit = max(1, limit - head_limit)
    return text[:head_limit].rstrip() + "\n\n...[truncated for Feishu delivery size limit]...\n\n" + text[-tail_limit:].lstrip(), True


def condense_http_text(text: str, limit: int) -> tuple[str, bool]:
    if len(text) <= limit:
        return text, False
    marker = "## source:"
    if marker in text:
        raw_sections = [part for part in text.split(marker) if part.strip()]
        section_limit = max(600, min(1200, limit // max(1, len(raw_sections))))
        condensed_sections = []
        for part in raw_sections:
            section = marker + part
            snippet, _ = _truncate_text(section.strip(), section_limit)
            condensed_sections.append(snippet)
        combined = "\n\n".join(condensed_sections)
        final_text, _ = _truncate_text(combined, limit)
        return final_text, True
    return _truncate_text(text, limit)


def render_http_dir(path: Path) -> str:
    files = sorted(child for child in path.iterdir() if child.is_file())
    request_files = [file for file in files if file.name.startswith("request-")]
    response_files = [file for file in files if file.name.startswith("response-")]

    lines = [f"# {path.name} HTTP 证据", ""]
    lines.extend([
        "## 说明",
        "",
        "- 当前页面由本地 `http/<finding_id>/` 目录渲染而来。",
        "- 当原始 HTTP 证据过长时，此页会保留 request / response 双侧的关键片段，并明确标注发生了截断。",
        f"- 完整原始证据目录：`{path}`",
        f"- request 文件数：`{len(request_files)}`；response 文件数：`{len(response_files)}`",
        "",
    ])

    consumed = len("\n".join(lines))
    for file in files:
        raw = sanitize_http_text(read_text(file).rstrip())
        condensed_once, was_truncated = condense_http_text(raw, HTTP_RENDER_FILE_CHAR_LIMIT)
        remaining = max(HTTP_RENDER_SNIPPET_CHAR_LIMIT, HTTP_RENDER_TOTAL_CHAR_LIMIT - consumed)
        snippet, was_truncated_again = condense_http_text(condensed_once, remaining)
        truncated = was_truncated or was_truncated_again

        lines.append(f"## {file.name}")
        lines.append("")
        if truncated:
            lines.append(f"> 原始内容较长；此处仅保留关键片段。完整原始文件：`{file}`")
            lines.append("")
        lines.append(f"```{fence_for_suffix(file)}")
        lines.append(snippet)
        lines.append("```")
        lines.append("")

        consumed = len("\n".join(lines))
        if consumed >= HTTP_RENDER_TOTAL_CHAR_LIMIT:
            lines.extend([
                "## 其余内容",
                "",
                f"> 当前 Feishu 交付页已达到尺寸上限；其余原始 request / response 内容请直接查看本地目录：`{path}`",
                "",
            ])
            break

    return "\n".join(lines).rstrip() + "\n"


def doc_title_from_path(path: Path) -> str:
    if path.name == "00-索引.md":
        return "00-索引"
    if path.name == "01-仓库级中文交付报告.md":
        return "01-仓库级中文交付报告"
    if path.name == "02-仓库级技术汇总.md":
        return "02-仓库级技术汇总"
    if path.name == "02-仓库级技术汇总.json":
        return "02-仓库级技术汇总（JSON）"
    if path.name == "03-复现实验信息.md":
        return "03-复现实验信息"
    if path.name == "99-最终本地复盘.md":
        return "99-最终本地复盘"
    if path.parent.name == "poc":
        return f"PoC · {path.name}"
    if path.parent.name == "http":
        return f"HTTP · {path.name}"
    return path.stem


def doc_key(project_slug: str, path: Path) -> str:
    if path.parent.name == "poc":
        return f"report::{project_slug}::poc::{path.name}"
    if path.parent.name == "http":
        return f"report::{project_slug}::http::{path.name}"
    return f"report::{project_slug}::root::{path.name}"


def collect_docs(report_dir: Path, project_slug: str) -> list[dict[str, Any]]:
    manifest = load_manifest(report_dir)
    docs: list[dict[str, Any]] = []

    root_order = [
        report_dir / "00-索引.md",
        report_dir / "01-仓库级中文交付报告.md",
        report_dir / "02-仓库级技术汇总.md",
        report_dir / "02-仓库级技术汇总.json",
        report_dir / "03-复现实验信息.md",
    ]
    review_md = Path(str(((manifest.get("final_local_review") or {}).get("review_record_md")) or ""))
    if review_md.exists() and review_md.parent.resolve() == report_dir.resolve():
        root_order.append(review_md)

    for path in root_order:
        if path.exists():
            docs.append(
                {
                    "doc_key": doc_key(project_slug, path),
                    "title": doc_title_from_path(path),
                    "source_path": str(path),
                    "rendered_markdown": render_file(path),
                    "mode": "overwrite",
                }
            )

    for finding in manifest.get("delivery_findings") or []:
        report_doc = str(finding.get("report_doc") or "").strip()
        if not report_doc:
            continue
        path = report_dir / report_doc
        if path.exists():
            docs.append(
                {
                    "doc_key": doc_key(project_slug, path),
                    "title": doc_title_from_path(path),
                    "source_path": str(path),
                    "rendered_markdown": render_file(path),
                    "mode": "overwrite",
                }
            )

    for finding in manifest.get("delivery_findings") or []:
        for poc_name in finding.get("poc_files") or []:
            path = report_dir / "poc" / poc_name
            if path.exists():
                docs.append(
                    {
                        "doc_key": doc_key(project_slug, path),
                        "title": doc_title_from_path(path),
                        "source_path": str(path),
                        "rendered_markdown": render_file(path),
                        "mode": "overwrite",
                    }
                )
        http_dir_rel = str(finding.get("http_dir") or "").strip()
        if http_dir_rel:
            path = report_dir / http_dir_rel
            if path.exists() and path.is_dir():
                docs.append(
                    {
                        "doc_key": doc_key(project_slug, path),
                        "title": doc_title_from_path(path),
                        "source_path": str(path),
                        "rendered_markdown": render_http_dir(path),
                        "mode": "overwrite",
                    }
                )

    return docs


def main() -> int:
    ns = parse_args()
    report_dir = Path(ns.report_dir).expanduser().resolve()
    if not report_dir.exists() or not report_dir.is_dir():
        raise SystemExit(f"report dir not found: {report_dir}")

    manifest = load_manifest(report_dir)
    state = load_state()
    project_slug = slug_from_report_dir(report_dir)
    project_state = ((state.get("projects") or {}).get(project_slug) or {})
    project_title = ns.project_title or ((manifest.get("repo") or {}).get("display_name")) or project_state.get("title") or project_slug
    project_node = project_state.get("project_node") or {}
    delivery_node = ((project_state.get("phases") or {}).get("delivery_reports") or {})

    plan = {
        "schema_version": 1,
        "source": {
            "report_dir": str(report_dir),
            "project_slug": project_slug,
            "project_title": project_title,
            "manifest_path": str(report_dir / MANIFEST_NAME),
            "publish_ready": bool(manifest.get("publish_ready")),
        },
        "state_refs": {
            "state_path": str(STATE_PATH),
            "project_node": project_node,
            "delivery_reports": delivery_node,
        },
        "ensure_nodes": {
            "project_node_title": f"项目 - {project_title}",
            "delivery_reports_title": DELIVERY_CONTAINER_TITLE,
        },
        "docs": collect_docs(report_dir, project_slug),
    }
    print(json.dumps(plan, ensure_ascii=False, indent=2 if ns.pretty else None))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
