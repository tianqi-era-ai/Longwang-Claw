---
name: loop9-feishu-delivery-publisher
description: Publish an already-generated local Loop9 delivery report bundle from `workspace/reports/<repo>/` into the internal Feishu wiki. Use when a repo already has the canonical local report tree **with `98-delivery-bundle.manifest.json` + completed `99-最终本地复盘`**, and you want those standard docs synced under the existing project node in the Loop9 internal knowledge base, preferably under a stable `06-标准交付报告` child container.
---

# Loop9 Feishu Delivery Publisher

Use this skill **after** local delivery reports already exist.

AI-native control model:

- AI owns repo choice, issue interpretation, whether to publish/skip/incident, whether runtime/repro facts are materially complete, and whether the final published result is acceptable.
- Code only owns bounded deterministic bridges such as local fact extraction, plan rendering, slot bookkeeping, and doc write transport.

High-severity warning:

- if the active lane starts being narrated as “the publish-plan script decides what is true,” treat that as route drift
- if missing delivery facts are being handled by thickening Python instead of by AI inspecting and repairing the local bundle, stop and correct the control model first

This skill is intentionally separate from `loop9-feishu-publisher`:
- `loop9-feishu-publisher` syncs raw Loop9 run artifacts
- this skill syncs the **standardized local delivery-report tree**

That separation keeps the publisher thin and avoids fighting the existing raw-artifact sync rules.

## When to use

Use this skill when:
- `workspace/reports/<repo>/` already exists
- the user wants the standard delivery docs uploaded into Feishu wiki
- the repo already has a project node and you want to attach delivery docs under it
- you need to publish a repo after PoC automation is complete without rediscovering raw runtime artifacts again

Do **not** use this skill for:
- generating local reports from verifier outputs
- publishing raw Loop9 run artifacts directly from `Super8/temp/loop9/...`
- auto-chaining yourself immediately after report generation unless the user explicitly asks for the publish stage
- skipping the repo's final local review step and treating local report generation as automatic permission to publish

## Control model

This skill must stay **AI-native**:

- AI owns candidate scanning, issue interpretation, publish / skip / incident judgment, and user-visible narration.
- Code is allowed only as thin deterministic bridges for:
  - local fact extraction
  - slot claim / release
  - incident markdown write
  - publish-plan rendering after the AI has already chosen a repo

High-severity warning:

- do **not** grow a new `manage_*`, `runner`, `plan`, or orchestration-heavy script around this skill
- do **not** let a Python CLI become the semantic owner of candidate choice or incident wording
- if a deterministic bridge starts owning publish policy, treat that as AI-native drift and repair by subtraction first

## Canonical workflow

1. Read `../ai-native-development/SKILL.md`
2. Read `references/layout.md`
3. Keep the repo choice and incident choice in the AI lane
4. Before building a publish plan, inspect the chosen `workspace/reports/<repo>/` bundle plus any current-round handoff/verdict objects you already have and decide whether the bundle is missing a stable runtime/repro summary.
5. If the report already contains durable reproducibility facts, materialize or refresh one root doc:
   - `03-复现实验信息.md`
   - keep it truthful: if the runtime is only local/temporary, say so explicitly instead of implying Tencent/public reproducibility
   - if Tencent CVM / public replay facts really exist, centralize the IP, entry URL, manual login path, demo creds, token-acquisition notes, and runtime caveats there instead of scattering them across finding docs
6. Only after the repo is chosen, build a publish plan with the thin renderer bridge:

```bash
python3 {baseDir}/scripts/build_report_publish_plan.py <workspace/reports/repo> --pretty
```

7. AI must inspect the plan output instead of blindly trusting it:
   - expected root docs
   - expected finding docs
   - expected PoC docs
   - expected HTTP evidence docs
   - whether `03-复现实验信息` should exist and whether it is truthful
8. Reuse `memory/loop9-feishu-publisher-state.json` as the source of truth for the existing project subtree
9. Prefer reusing the existing `项目 - <项目名>` node
10. Create/reuse one stable child container under it:
   - `06-标准交付报告`
11. Create/update the planned docs under that container
12. Write the new node/doc bindings back into the same state file instead of inventing a second state store
    - `last_content_hash` must hash the exact markdown payload sent to Feishu, normally `doc["rendered_markdown"]`, not the raw source bytes on disk
13. After the write phase, rerun the same single-report preflight receipt as a post-publish self-check
14. AI must read that self-check receipt directly; do not let a script summarize away the real issue shape
15. Only declare publish success when the post-publish receipt shows all of the following:
   - `issues=[]`
   - `needs_sync=false`
   - `missing_docs=[]`
   - `changed_docs=[]`
   - `invalid_bindings=[]`

## Cron / automation workflow

When this skill is reused by the dedicated delivery-report cron:

1. Read concurrency from `config/loop9-dispatch.json > deliveryReportPublish.maxConcurrent`
2. Read `references/cron-ai-native-bridges.md`
3. Use the thin bridge snippets there to:
   - clean stale delivery-publish slots
   - inspect one canonical `workspace/reports/<repo>/` candidate at a time
   - collect local completeness facts and sync-state facts
   - claim / release a slot only after the AI has decided to publish
   - write incident markdown only after the AI has decided no healthy candidate exists
   - keep each receipt bounded to exactly one `report_dir`; do not expand this into a whole-reports mega-summary helper
4. AI must keep scanning until one of these is true:
   - a healthy `needs_sync=true` repo is found and chosen for publish
   - there is no healthy publishable repo, so an incident is warranted
   - there is no healthy publishable repo and no incident-worthy blocker, so the run is a healthy skip
   - once the highest-priority healthy candidate is found, stop scanning and continue to publish instead of widening context further
5. Before building the publish plan for the selected repo, inspect whether reproducibility/runtime facts should be materialized into `03-复现实验信息.md`
6. Publish the selected repo by reusing this skill's normal plan/build flow
7. Rerun the same single-report preflight receipt as a post-publish self-check; only success if the receipt comes back sync-clean
8. Release the claimed slot after finish/failure
9. When surfacing an incident to the user / cron summary:
   - reuse the chosen receipt's real issue summary verbatim
   - do not infer extra missing artifacts that are not present in the receipt

AI-native repair preference:

- if a publish mismatch is discovered, first fix the local bundle / markdown truth / runtime fact expression
- only patch a bridge script when the fault is clearly a deterministic render or transport edge
- do **not** let `build_report_publish_plan.py` or cron snippets expand into hidden candidate-selection or acceptance-policy owners

## Publishing rules

- Prefer fewer larger writes; do not spam one tiny write per sentence
- Markdown files should usually publish as normal markdown docs
- `.py`, `.json`, and `.txt` local files should publish as readable docs with fenced code blocks
- `http/<finding_id>/` directories should publish as one rendered markdown doc per directory, not as dozens of tiny child docs
- `03-复现实验信息.md` should publish as a normal root markdown doc when present; use it as the canonical place for Tencent/public replay facts or for an explicit "current bundle is local-only" statement
- For a repo-level delivery publish, **PoC docs and HTTP evidence docs are mandatory**, not optional. A publish is not complete if it stops after only the repo/finding markdown layer.
- Publisher / cron selector must treat `98-delivery-bundle.manifest.json` as the canonical local marker. Do not fall back to “looks like a report tree” guessing.
- For HTTP evidence, both request and response sides are mandatory whenever the local `http/<finding_id>/` directory contains both. Do not publish a one-sided HTTP page that only shows requests while silently dropping responses.
- If the project node is missing, create the normal project subtree first, then attach `06-标准交付报告`
- Feishu wiki node creation can hit `CreateWikiNode ... lock contention` when many children are created too quickly under the same parent. In that case, switch to **serialized creates / updates** instead of parallel fan-out; treat serialization as the durable default for the actual write phase of this publisher.
- If a raw HTTP evidence page triggers upstream Feishu/MCP rejection (`MCP HTTP 444` / access denied), do not abandon the HTTP layer. Fallback to a **condensed evidence page** that keeps the critical request/response snippets, redacts sensitive headers/tokens, and explicitly points to the full local capture directory under `reports/<repo>/http/<finding_id>/`.
- If the write phase finishes but the post-publish receipt still reports `needs_sync=true` or any non-empty issue/change/binding list, treat that as a failed publish that needs follow-up instead of announcing success early.
- `scripts/build_report_publish_plan.py` is a bounded content-render bridge, not a candidate-selection owner. Do not thicken it into a policy runner.

## References

- `references/layout.md` — Feishu placement rules and state extension shape
- `references/cron-ai-native-bridges.md` — visible thin bridge snippets for cron usage
