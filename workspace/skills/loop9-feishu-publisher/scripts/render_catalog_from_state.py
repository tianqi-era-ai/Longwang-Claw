#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

PHASE_ORDER = [
    "project_overview",
    "original_input",
    "audit_process",
    "findings",
    "validation",
    "poc",
    "sync_log",
]


def load_state(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    parser = argparse.ArgumentParser(description="Render the root catalog markdown from publisher state.")
    parser.add_argument("state_path", help="Path to loop9-feishu-publisher state JSON")
    args = parser.parse_args()

    state = load_state(Path(args.state_path).expanduser().resolve())
    space = state.get("space", {})
    projects = state.get("projects", {})

    lines = [
        "# Loop9 审计交付中心（内部）- 目录",
        "",
        "## 根信息",
        f"- 知识空间：{space.get('name', '未初始化')}",
        f"- space_id：`{space.get('space_id', '')}`",
        f"- 可见性：`{space.get('visibility', '')}`",
        "",
        f"## 项目总数\n- {len(projects)}",
        "",
    ]

    if not projects:
        lines += ["目前还没有已登记项目。", ""]
    else:
        for slug, project in sorted(projects.items(), key=lambda item: item[1].get("title", item[0]).lower()):
            lines += [
                f"## {project.get('title', slug)}",
                "",
                f"- slug：`{slug}`",
                f"- 最近同步时间：`{project.get('last_synced_at', '')}`",
                f"- 最近来源：`{project.get('last_source_path', '')}`",
                "",
                "阶段页：",
            ]
            phases = project.get("phases", {})
            for key in PHASE_ORDER:
                phase = phases.get(key, {})
                title = phase.get("title", key)
                doc_id = phase.get("doc_id", "")
                lines.append(f"- {title}：`{doc_id}`")
            lines.append("")

    sys.stdout.write("\n".join(lines).rstrip() + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
