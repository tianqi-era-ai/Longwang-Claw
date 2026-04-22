#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path


def fence_for(path: Path) -> str:
    suffix = path.suffix.lower()
    if suffix == ".py":
        return "python"
    if suffix == ".json":
        return "json"
    if suffix in {".md", ".markdown"}:
        return "markdown"
    if suffix in {".sh", ".bash", ".zsh"}:
        return "bash"
    return "text"


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return path.read_text(encoding="utf-8", errors="replace")


def render(path: Path, title: str | None = None) -> str:
    text = read_text(path)
    lang = fence_for(path)
    heading = title or path.name
    lines = [
        f"# {heading}",
        "",
        "## 文件信息",
        f"- 文件名：`{path.name}`",
        f"- 本地路径：`{path}`",
        f"- 扩展名：`{path.suffix or '(none)'}`",
        "",
        "## 文件正文",
        f"```{lang}",
        text.rstrip("\n"),
        "```",
        "",
    ]
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Render a local source file as Feishu-friendly markdown.")
    parser.add_argument("path")
    parser.add_argument("--title")
    parser.add_argument("--json", action="store_true", help="Wrap the markdown in a JSON object")
    args = parser.parse_args()

    path = Path(args.path).expanduser().resolve()
    markdown = render(path, title=args.title)
    if args.json:
        print(json.dumps({"path": str(path), "markdown": markdown}, ensure_ascii=False, indent=2))
    else:
        print(markdown)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
