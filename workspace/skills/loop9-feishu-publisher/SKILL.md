---
name: loop9-feishu-publisher
description: Publish and incrementally sync internal Loop9 audit artifacts into a dedicated Feishu knowledge base. Use when the user wants to initialize/manage the internal Loop9 wiki space, create project/stage structure automatically, sync `loop9_wrapped_audit` outputs, sync `loop9_poc_builder` bundles, rebuild catalog/index docs, or add/update a source-code project's internal documentation tree in Feishu.
user-invocable: true
---

# Loop9 Feishu Publisher

Use this skill to maintain the **internal main Feishu knowledge base** for Loop9.

Important real-usage note:
- In the user's common manual prompt style, this skill is often used as a selector over `~/.openclaw/workspace/Super8/temp/loop9`: choose **one project that has already completed both the code-audit flow and the PoC flow, but has not yet been uploaded to the Feishu knowledge base**, then sync that one project to the corresponding Feishu location.
- So this skill should not be mentally reduced to “publish any arbitrary path”; in the user's real workflow it often includes the pre-step of scanning the Loop9 run pool, deciding what is already fully ready, and only then performing the Feishu sync.

Read these references when needed:
- `references/layout-and-state.md` — hierarchy, state file, idempotency rules
- `references/content-selection.md` — what to publish from Loop9 runs vs PoC bundles
- `references/canonical-project-registry.json` — manual alias -> canonical project mapping used to stop known split-project cases from continuing to fork Feishu project nodes
- `references/hash-semantics-anomaly-cases.md` — how to interpret `hash-semantics-anomaly:*` cases without blindly republishing or hardcoding every exception

Use these scripts first:

```bash
python3 {baseDir}/scripts/build_publish_plan.py <path> --pretty
python3 {baseDir}/scripts/render_local_file_doc.py <local-file> --title "<doc-title>"
python3 {baseDir}/scripts/render_catalog_from_state.py ~/.openclaw/workspace/memory/loop9-feishu-publisher-state.json
```

## Operating model

Target only the **internal** knowledge base layer:
- full materials
- raw analysis
- PoC details
- process notes
- sensitive remarks

Do **not** auto-build the external/client delivery layer in this skill.

## Local state file

Persist and reuse ids here:

```text
~/.openclaw/workspace/memory/loop9-feishu-publisher-state.json
```

If it does not exist, create it.
If it exists, treat it as the source of truth for already-created docs and nodes.

## Canonical workflow

### 1. Build a publish plan

Run the planner on the user-provided source path.

Accepted inputs:
- a Loop9 run dir
- a file or subdir inside a Loop9 run
- a PoC bundle dir
- a file inside a PoC bundle

If project inference confidence is low, ask for a project title before publishing broadly.

### 2. Ensure the Feishu root exists

Preferred root space:
- name: `Loop9 审计交付中心（内部）`
- visibility: `private`

Ensure, in order:
1. wiki space
2. root overview doc
3. root catalog doc

Use state ids if already known.
If missing, create them and immediately write back the ids to the state file.

### 3. Ensure the project subtree exists

For each project, ensure these nested docs exist under `项目 - <项目名>`:
- `00-项目总览`
- `01-原始输入`
- `02-审计过程`
- `03-审计结论`
- `04-验证报告`
- `05-PoC与验证`
- `90-同步记录`

Use docs as stable folder-surrogate nodes.

### 4. Publish planned artifact docs

For each planned item from `build_publish_plan.py`:
- create a child doc under the correct phase node if the artifact key is new
- overwrite/update the existing doc if the exact artifact key is already recorded in state
- for sharded artifact directories, concatenate all `partNN.md` files in numeric order and publish that exact combined body
- do not fall back to `part01.md` alone when later parts exist
- when the source is a real PoC `*.py` file, publish the **full file body** as a dedicated doc page under `05-PoC与验证`
- do not manually compress, summarize, or rewrite `.py` bodies during sync
- for `real_pocs/manifest.json`, publish a rendered summary page and keep the raw manifest content visible inside that page
- keep side files as attachments only when they help future internal review
- if the planner/detector layer reports `hash-semantics-anomaly:*`, do **not** blindly republish that artifact as if it were an ordinary content change; first read `references/hash-semantics-anomaly-cases.md` and classify whether it is a stale historical raw hash, a multipart legacy state, or a genuinely unresolved anomaly

### 5. Rebuild indexes

After each successful sync:
- overwrite `00-项目总览` using the planner-provided `project_overview` markdown
- update `90-同步记录`
- rebuild `00-总览与目录` from the local state file
- if real PoC `.py` files were synced, mention that they are maintained as overwriteable full-body docs rather than one-off attachments
- if a multi-part artifact was synced, mention that the page now reflects all `partNN.md` content in order

Important implementation rule for root catalog rebuild:
- Prefer **Scheme A**: run `render_catalog_from_state.py` and consume its **stdout directly** as the markdown source for the root catalog update.
- Do **not** use the fragile pattern "`exec` writes a temp catalog file and then a separate `read` immediately tries to read that file" in the same burst of tool calls; that can race and produce false `ENOENT` noise even when the render succeeded.
- If a file-based path is truly necessary, split it into two clearly separated steps: first finish the write, then issue a later read after the write result has returned.

## Tool usage rules

### Feishu structure
Use these tools directly:
- `feishu_wiki_space` — create/get/list the internal wiki space
- `feishu_create_doc` — create docs under a wiki space or parent wiki node
- `feishu_update_doc` — overwrite/append existing docs
- `feishu_wiki_space_node` — inspect wiki node metadata when needed
- `feishu_drive_file` — upload local attachments when raw files are worth preserving in the internal archive

### File/state handling
Use workspace files for durable control:
- read/write the local state JSON
- store no hidden state outside the workspace

## Caution rules

- Do not guess old node bindings when state is ambiguous; controlled re-creation is safer.
- Do not silently publish to the wrong project because of weak name inference.
- Do not delete existing docs just to “clean up” structure unless the user explicitly asks.
- Prefer fewer larger writes over noisy one-item update bursts.
- Do not let a `hash-semantics-anomaly:*` candidate repeatedly consume the publish queue; anomaly items are for AI/human interpretation, not for automatic blind overwrite.
- When shell commands need to search for literal text containing backticks, do **not** place raw backticks inside double-quoted shell strings. Use single quotes or proper escaping so the shell does not treat the backticks as command substitution.

## Response style

Be operational.
When syncing, report:
- target project
- source path
- whether this was initialization or incremental update
- created vs updated docs
- the key Feishu doc/wiki URLs when useful
