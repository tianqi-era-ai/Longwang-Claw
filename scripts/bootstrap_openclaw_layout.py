#!/usr/bin/env python3
"""Copy this repo's public workflow assets back into ~/.openclaw/workspace."""

from __future__ import annotations

import argparse
import shutil
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]

COPY_DIRS = (
    ("workspace/bin", "bin"),
    ("workspace/lib", "lib"),
    ("workspace/config", "config"),
    ("workspace/plans", "plans"),
    ("workspace/skills", "skills"),
    ("workspace/Super8/.opencode", "Super8/.opencode"),
)

COPY_FILES = (
    ("workspace/Super8/START_HERE_Loop9.md", "Super8/START_HERE_Loop9.md"),
    ("workspace/Super8/README.loop9-local.md", "Super8/README.loop9-local.md"),
    ("workspace/Super8/LOOP9_问题地图.md", "Super8/LOOP9_问题地图.md"),
    ("workspace/Super8/LOOP9_封装计划.md", "Super8/LOOP9_封装计划.md"),
    ("workspace/Super8/下一步计划.md", "Super8/下一步计划.md"),
    ("workspace/Super8/TELEGRAM_默认行为规范.md", "Super8/TELEGRAM_默认行为规范.md"),
    ("workspace/Super8/TELEGRAM_通知模板.md", "Super8/TELEGRAM_通知模板.md"),
)


def copy_dir(src: Path, dst: Path, dry_run: bool) -> int:
    if not src.exists():
        return 0
    if dry_run:
        return sum(1 for path in src.rglob("*") if path.is_file())
    shutil.copytree(src, dst, dirs_exist_ok=True)
    return sum(1 for path in src.rglob("*") if path.is_file())


def copy_file(src: Path, dst: Path, dry_run: bool) -> int:
    if not src.exists():
        return 0
    if not dry_run:
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
    return 1


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
        "--workspace-root",
        default=str(Path.home() / ".openclaw" / "workspace"),
        help="Target OpenClaw workspace root",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print what would be copied without writing files",
    )
    args = parser.parse_args()

    repo_root = Path(args.repo_root).expanduser().resolve()
    workspace_root = Path(args.workspace_root).expanduser()

    copied = 0
    print(f"repo_root={repo_root}")
    print(f"workspace_root={workspace_root}")
    print(f"mode={'dry-run' if args.dry_run else 'copy'}")

    for src_rel, dst_rel in COPY_DIRS:
        src = repo_root / src_rel
        dst = workspace_root / dst_rel
        count = copy_dir(src, dst, args.dry_run)
        copied += count
        print(f"[dir] {src_rel} -> {dst_rel} ({count} files)")

    for src_rel, dst_rel in COPY_FILES:
        src = repo_root / src_rel
        dst = workspace_root / dst_rel
        count = copy_file(src, dst, args.dry_run)
        copied += count
        print(f"[file] {src_rel} -> {dst_rel} ({count} file)")

    print(f"total_files={copied}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
