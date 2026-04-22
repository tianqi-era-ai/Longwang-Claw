# Feishu delivery-report publishing layout

This publisher targets an already-generated local report tree:

```text
workspace/reports/<repo>/
```

## Publishing target

Prefer reusing the existing Loop9 internal wiki subtree from `memory/loop9-feishu-publisher-state.json`.

If the project already exists:
- reuse `项目 - <项目名>`
- create/reuse one extra stable child container:
  - `06-标准交付报告`

If the project does not exist:
- create/reuse the normal project subtree first
- then create `06-标准交付报告`

Canonical local eligibility marker:

- `98-delivery-bundle.manifest.json`
- `99-最终本地复盘.md/json` with `final_local_review.status = complete`

Control stance:

- AI owns candidate selection, issue interpretation, runtime/repro truth judgment, and final publish acceptance
- code only owns deterministic plan rendering, state writeback, and transport-level document creation/update
- if the rendered plan disagrees with the live local bundle, AI must inspect the live bundle rather than trusting the renderer by default

## Docs published under `06-标准交付报告`

- `00-索引`
- `01-仓库级中文交付报告`
- `02-仓库级技术汇总`
- `02-仓库级技术汇总（JSON）`
- optional: `03-复现实验信息`
- one doc per finding markdown file
- one doc per effective PoC file (`poc/*`)
- one doc per HTTP evidence directory (`http/<finding_id>/` rendered into markdown)
- optional: `99-最终本地复盘`

`03-复现实验信息.md` is the preferred root doc for runtime/reproducibility facts when they exist.

- If the bundle has Tencent CVM / public replay facts, centralize the public IP, entry URLs, manual login path, demo creds, token acquisition path, and runtime caveats there.
- If the bundle is only local/temporary, the doc should say so explicitly instead of implying a公网复验入口.

## State model extension

This publisher is allowed to extend the existing project state with:

```json
{
  "phases": {
    "delivery_reports": {
      "doc_id": "...",
      "node_token": "...",
      "title": "06-标准交付报告"
    }
  },
  "delivery_reports": {
    "report::<slug>::root::00-索引.md": {"doc_id": "...", "node_token": "...", "title": "00-索引"}
  }
}
```

The goal is to stay compatible with the existing `loop9-feishu-publisher` state file instead of creating a second parallel state store.
