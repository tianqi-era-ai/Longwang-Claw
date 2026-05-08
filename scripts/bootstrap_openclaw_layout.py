#!/usr/bin/env python3
"""Copy this repo's public workflow assets back into ~/.openclaw/workspace."""

from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]

ROOT_COPY_DIRS = (
    ("extensions/openclaw-lark", "extensions/openclaw-lark"),
)

COPY_DIRS = (
    ("workspace/bin", "bin"),
    ("workspace/lib", "lib"),
    ("workspace/config", "config"),
    ("workspace/hooks", "hooks"),
    ("workspace/plans", "plans"),
    ("workspace/plugins", "plugins"),
    ("workspace/skills", "skills"),
    ("workspace/heartbeat", "heartbeat"),
    ("workspace/prompts", "prompts"),
    ("workspace/Super8/.opencode", "Super8/.opencode"),
    ("workspace/Super8/工作流_提示词工程", "Super8/工作流_提示词工程"),
)

COPY_FILES = (
    ("workspace/HEARTBEAT.md", "HEARTBEAT.md"),
    ("workspace/OpenClaw_实装入口设计.md", "OpenClaw_实装入口设计.md"),
    ("workspace/TELEGRAM_小龙虾封装说明.md", "TELEGRAM_小龙虾封装说明.md"),
    ("workspace/REPO-STRUCTURE.md", "REPO-STRUCTURE.md"),
    ("workspace/Super8/START_HERE_Loop9.md", "Super8/START_HERE_Loop9.md"),
    ("workspace/Super8/README.loop9-local.md", "Super8/README.loop9-local.md"),
    ("workspace/Super8/.gitignore", "Super8/.gitignore"),
    ("workspace/Super8/LOOP9_问题地图.md", "Super8/LOOP9_问题地图.md"),
    ("workspace/Super8/LOOP9_封装计划.md", "Super8/LOOP9_封装计划.md"),
    ("workspace/Super8/下一步计划.md", "Super8/下一步计划.md"),
    ("workspace/Super8/TELEGRAM_默认行为规范.md", "Super8/TELEGRAM_默认行为规范.md"),
    ("workspace/Super8/TELEGRAM_通知模板.md", "Super8/TELEGRAM_通知模板.md"),
)


def count_files(path: Path) -> int:
    if not path.exists():
        return 0
    if path.is_file():
        return 1
    return sum(1 for child in path.rglob("*") if child.is_file())


def copy_dir(src: Path, dst: Path, dry_run: bool) -> dict[str, object]:
    if not src.exists():
        return {"source": str(src), "target": str(dst), "files": 0, "target_exists": dst.exists()}
    count = count_files(src)
    exists = dst.exists()
    if dry_run:
        return {"source": str(src), "target": str(dst), "files": count, "target_exists": exists}
    shutil.copytree(src, dst, dirs_exist_ok=True)
    return {"source": str(src), "target": str(dst), "files": count, "target_exists": exists}


def copy_file(src: Path, dst: Path, dry_run: bool) -> dict[str, object]:
    if not src.exists():
        return {"source": str(src), "target": str(dst), "files": 0, "target_exists": dst.exists()}
    exists = dst.exists()
    if not dry_run:
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
    return {"source": str(src), "target": str(dst), "files": 1, "target_exists": exists}


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Directly copy Longwang-Claw public assets into ~/.openclaw/workspace",
    )
    parser.add_argument(
        "--repo-root",
        default=str(REPO_ROOT),
        help="Path to the Longwang-Claw repo root",
    )
    parser.add_argument(
        "--openclaw-root",
        default=None,
        help="Target ~/.openclaw root; defaults to parent of --workspace-root",
    )
    parser.add_argument(
        "--workspace-root",
        default=str(Path.home() / ".openclaw" / "workspace"),
        help="Target OpenClaw workspace root",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print what would be copied without writing files",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit a machine-readable summary.",
    )
    args = parser.parse_args()

    repo_root = Path(args.repo_root).expanduser().resolve()
    workspace_root = Path(args.workspace_root).expanduser()
    openclaw_root = (
        Path(args.openclaw_root).expanduser()
        if args.openclaw_root
        else workspace_root.parent
    )

    copied = 0
    items: list[dict[str, object]] = []
    mode = "dry-run" if args.dry_run else "copy"
    if not args.json:
        print(f"repo_root={repo_root}")
        print(f"openclaw_root={openclaw_root}")
        print(f"workspace_root={workspace_root}")
        print(f"mode={mode}")
        print("copy_policy=thin direct copy; existing target files under the listed public paths may be overwritten")
        print("excluded=harness, fixtures, reports, runs, targets, logs, memory, secrets")

    for src_rel, dst_rel in ROOT_COPY_DIRS:
        src = repo_root / src_rel
        dst = openclaw_root / dst_rel
        result = copy_dir(src, dst, args.dry_run)
        count = int(result["files"])
        copied += count
        items.append({"kind": "root-dir", "source": src_rel, "target": dst_rel, **result})
        if not args.json:
            exists_note = " target-exists" if result["target_exists"] else ""
            print(f"[root-dir] {src_rel} -> {dst_rel} ({count} files){exists_note}")

    for src_rel, dst_rel in COPY_DIRS:
        src = repo_root / src_rel
        dst = workspace_root / dst_rel
        result = copy_dir(src, dst, args.dry_run)
        count = int(result["files"])
        copied += count
        items.append({"kind": "dir", "source": src_rel, "target": dst_rel, **result})
        if not args.json:
            exists_note = " target-exists" if result["target_exists"] else ""
            print(f"[dir] {src_rel} -> {dst_rel} ({count} files){exists_note}")

    for src_rel, dst_rel in COPY_FILES:
        src = repo_root / src_rel
        dst = workspace_root / dst_rel
        result = copy_file(src, dst, args.dry_run)
        count = int(result["files"])
        copied += count
        items.append({"kind": "file", "source": src_rel, "target": dst_rel, **result})
        if not args.json:
            exists_note = " target-exists" if result["target_exists"] else ""
            print(f"[file] {src_rel} -> {dst_rel} ({count} file){exists_note}")

    summary = {
        "schema": "longwang.bootstrap.summary.v1",
        "repoRoot": str(repo_root),
        "openclawRoot": str(openclaw_root),
        "workspaceRoot": str(workspace_root),
        "mode": mode,
        "copyPolicy": "thin direct copy of public workspace assets only",
        "excluded": ["harness", "fixtures", "reports", "runs", "targets", "logs", "memory", "secrets"],
        "totalFiles": copied,
        "items": items,
    }
    if args.json:
        print(json.dumps(summary, ensure_ascii=False, indent=2))
    else:
        print(f"total_files={copied}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
