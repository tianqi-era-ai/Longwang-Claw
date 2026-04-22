# Layout and state model

## Root design

This skill targets the **internal main knowledge base** only.

Use one dedicated Feishu wiki space as the root:
- recommended name: `Loop9 审计交付中心（内部）`
- expected visibility: `private`

Inside that space, use docs as stable index/folder-surrogate nodes.

Recommended top-level structure:
- `Loop9 审计交付中心（内部）- 总览`
  - `00-总览与目录`
  - `项目 - <项目名>`
    - `00-项目总览`
    - `01-原始输入`
    - `02-审计过程`
    - `03-审计结论`
    - `04-验证报告`
    - `05-PoC与验证`
    - `90-同步记录`

## Why docs instead of true wiki folders

The Feishu wiki/doc APIs are reliable for creating nested docs under a wiki node, while fully general “folder-like” wiki operations are less ergonomic for long-lived idempotent automation.

Use doc nodes as stable containers and child pages under them.

## Local state file

Persist ids in a local JSON file so the skill can update existing docs instead of creating duplicates every time.

Recommended path:
`~/.openclaw/workspace/memory/loop9-feishu-publisher-state.json`

## Minimal state shape

```json
{
  "schema_version": 1,
  "space": {
    "space_id": "761...",
    "name": "Loop9 审计交付中心（内部）",
    "visibility": "private"
  },
  "root": {
    "overview": {"doc_id": "...", "node_token": "...", "title": "Loop9 审计交付中心（内部）- 总览"},
    "catalog": {"doc_id": "...", "node_token": "...", "title": "00-总览与目录"}
  },
  "projects": {
    "zentaopms": {
      "title": "ZenTaoPMS",
      "last_synced_at": "2026-03-12T14:00:00+08:00",
      "last_source_path": "/Users/.../Super8/temp/loop9/...",
      "project_node": {"doc_id": "...", "node_token": "...", "title": "项目 - ZenTaoPMS"},
      "phases": {
        "project_overview": {"doc_id": "...", "node_token": "...", "title": "00-项目总览"},
        "original_input": {"doc_id": "...", "node_token": "...", "title": "01-原始输入"},
        "audit_process": {"doc_id": "...", "node_token": "...", "title": "02-审计过程"},
        "findings": {"doc_id": "...", "node_token": "...", "title": "03-审计结论"},
        "validation": {"doc_id": "...", "node_token": "...", "title": "04-验证报告"},
        "poc": {"doc_id": "...", "node_token": "...", "title": "05-PoC与验证"},
        "sync_log": {"doc_id": "...", "node_token": "...", "title": "90-同步记录"}
      },
      "artifacts": {
        "loop9::20260309-171458-759c-ZenTaoPMS::findings::solution_v5": {
          "doc_id": "...",
          "node_token": "...",
          "title": "20260309-171458-759c-ZenTaoPMS · solution_v5",
          "source_markdown": "/Users/.../part01.md"
        }
      }
    }
  }
}
```

## Idempotency rule

Creation order:
1. wiki space
2. root overview doc
3. root catalog doc
4. project container doc
5. phase docs
6. run-specific / artifact-specific docs

Always prefer:
- create when missing
- overwrite/update when the state already knows the target doc id
- append only for sync logs

## Recovery rule

If the local state is missing but the space already exists:
- first try to recover the root space by name or stored `space_id`
- if individual docs cannot be safely rediscovered, create a fresh controlled subtree and re-bind the state to that subtree
- avoid guessing mismatched old nodes by fuzzy title alone when there is any ambiguity
