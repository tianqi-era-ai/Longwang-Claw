---
name: loop9-rce-audit-focus
description: Strengthen Loop9 audit with an RCE-focused review layer for code-security work. Use when an audit needs extra attention on remote code execution, unrestricted/weak file upload, low-privilege-to-RCE chains, template/render/deserialize execution paths, or unauthenticated/weak-auth functionality that may open an execution path. Especially use in two moments: (1) shortly after the repo structure is initially understood, to identify high-value RCE exploitation surfaces and set a Markdown shared-context skeleton; (2) later, when the audit discovers upload, template, preview, integration, plugin, scheduler, webhook, config, JWT/SSO, or suspicious auth-boundary signals and needs chain-oriented deepening rather than plain sink scanning.
---

# Loop9 RCE Audit Focus

Apply this skill as a **topic lens inside an audit**, not as a standalone vulnerability scanner.

The goal is not to dump dangerous keywords. The goal is to:
- identify **high-value exploitation surfaces**
- distinguish **execution surfaces** from **pivot/progression surfaces**
- form **chain hypotheses** that better match 微步偏好的方向：
  - direct RCE
  - file upload → reachable interpreter / render path → RCE
  - unauthenticated / weak-auth / low-privilege capability → config/template/action → RCE
- keep a **Markdown shared context** that later humans/agents can continue directly

## Core stance

Do not reduce this skill to “search Runtime.exec/system and stop”.

Always think in two layers:

1. **Execution surfaces**
   - command execution
   - template execution / expression execution / SSTI / EL / Velocity-like engines
   - deserialization / gadget reachability
   - script runners / scheduled jobs / hooks / plugin execution
   - dynamic loading / interpreter entry points

2. **Progression surfaces**
   - file upload
   - path traversal affecting file location or template location
   - weak auth / auth bypass / low-privilege backend access
   - config mutation
   - JWT / SSO / auth-provider / user-source settings
   - webhook / callback / test connection / import / preview / theme / email-template features

A strong result from this skill is usually a **chainable story**, not a raw sink hit.

## When to use this skill

### Stage A: early lightweight pass after initial repo understanding

Use this skill after:
- the repository is local and readable
- the audit has a basic sense of project structure
- but before the audit has fully locked onto one narrow bug hypothesis

At this stage, do not try to prove a vulnerability yet.

Instead:
- identify the most valuable RCE-related functional areas
- classify the project tendency:
  - direct-execution heavy
  - upload-to-execution heavy
  - low-privilege/config-to-execution heavy
  - middleware/admin-console/template heavy
- start the Markdown shared context document

### Stage B: deeper follow-up when a high-value signal appears

Call this skill again when the audit encounters signals like:
- upload features
- template/theme/email-template/page-builder/design-xml features
- preview/render/compile/evaluate/expression paths
- integrations, plugins, schedulers, hooks, scripts, webhooks, test-connection features
- JWT/SSO/user-source/auth-provider/config management
- self-registration plus reachable backend/API capability
- suspicious guest/editor/marketing/support/low-privilege access to high-value surfaces

At this stage:
- turn vague suspicious points into **chain hypotheses**
- follow strong signals repeatedly when needed; do not assume this stage is single-shot
- decide whether to escalate, park, or downgrade the line
- spend substantial time/token budget when the evidence quality justifies it
- update the shared context Markdown with the newest findings

## What to read

Read these local files when helpful:
- `相关文章和思路、方法论，以及部分实战案例.md`
- `Java的RCE_搜索关键词.md` (verified Java asset; keep it stable and do not casually refactor it)
- `references/RCE专题共享上下文模板.md`
- `references/调用策略与判定原则.md`
- `references/调用示例与期望输出.md`
- `references/语言正则使用边界说明.md`
- `references/真实Java项目观察清单.md`
- `references/真实PHP项目观察清单.md`
- any repo-local files already identified by the main audit as relevant to:
  - uploads
  - templates/themes/rendering
  - integrations/plugins/scripts/jobs
  - auth/config/admin APIs

Do not start by over-consuming keyword material. Start from architecture, capability, and chainability.

When the project is clearly Java/JVM, treat `scripts/rce_regex_scan.py <repo-root> --language java` as part of the normal RCE-focused workflow, not as an unrelated extra.

When the project is clearly PHP, treat `scripts/rce_regex_scan.py <repo-root> --language php` the same way: a normal high-recall workflow step that helps surface command-execution, deserialization/Phar, template, upload, and interpreter-adjacent signals.

### Java/JVM projects: run the regex scanner as a normal workflow step

When Java/JVM project identity is already reasonably established, run:

```bash
python3 scripts/rce_regex_scan.py <repo-root> --language java
```

### PHP projects: run the regex scanner as a normal workflow step

When PHP project identity is already reasonably established, run:

```bash
python3 scripts/rce_regex_scan.py <repo-root> --language php
```

Interpretation rule:
- this scanner is a **high-recall input source**
- do **not** treat hits as conclusions
- use the generated JSON result file as reusable evidence input for the rest of the audit

After the script runs, decide how to read the generated result file based on its size and finding volume:

1. **Small file / small finding count**
   - Prefer reading the whole file.
   - Good default when the JSON is short enough that full reading will not bloat context.

2. **Medium file / moderate finding count**
   - Prefer reading targeted sections or partial slices first.
   - Good patterns:
     - read the header/summary area first
     - then inspect the first few findings
     - then expand only the most suspicious paths

3. **Large file / high finding count**
   - Do not dump the whole file into context.
   - Prefer one of these strategies depending on need:
     - search/retrieval first
     - read by batches
     - sample representative sections
     - random spot-check only when no better prioritization exists
   - In general, prefer **search / retrieval / targeted partial reads** over naive full reads.

4. **When file paths already reveal useful prioritization**
   - Prefer reading the most suspicious files first, for example:
     - source files before tooling/config noise
     - files near known strong signals
     - files whose hits look more execution-adjacent than dependency-only

5. **When the file is obviously noisy**
   - Do not stop using it.
   - Instead, use it as a triage layer:
     - identify clusters
     - separate config/dependency noise from likely execution-relevant paths
     - only then read deeper

The scanner result should usually feed into:
- high-value surface mapping
- chain hypothesis formation
- updates to `RCE专题共享上下文.md`

## Required workflow

### 1) Map high-value functional surfaces

Look for capabilities such as:
- uploads and import/export
- template, theme, rendering, preview, compile, evaluate, expression systems
- schedulers, hooks, plugin systems, installers, package managers
- webhooks, callback URLs, test-connection functions
- auth/configuration surfaces such as JWT, SSO, auth providers, user sources
- admin/debug/integration APIs reachable from weaker roles than expected

Write findings in functional language, not just file-name dumps.

### 2) Check privilege boundaries around those surfaces

Do not write a full auth review here.

Only record auth facts that matter for RCE chaining, for example:
- whether self-registration exists
- what anonymous users can reach
- what low-privilege roles can modify or trigger
- whether configuration/template/upload/preview surfaces are unexpectedly reachable
- whether auth bypass or missing authorization seems plausible

### 3) Analyze upload-to-execution potential carefully

Do not stop at “upload exists”.

Trace:
- frontend restrictions
- backend restrictions
- final storage location
- predictability of file path / filename / extension
- separation or mismatch between extension, MIME, and content checks
- alternative executable extensions / double extensions / traversal influence
- whether any render/include/interpret path can later touch the uploaded file
- whether image/document processing may transform a file write into code execution

### 4) Analyze template/render/interpretation surfaces

Record:
- engine type
- editable locations
- preview/test/render hooks
- whether user-controlled data reaches evaluation/compilation paths
- whether the capability resembles known dangerous patterns

### 5) Build chain hypotheses

Do not just list bugs. Write chains.

Use formats like:
- low-privilege template edit → template execution → RCE
- upload → path control / reachable interpreter → RCE
- auth weakness / privilege bypass → config mutation → execution surface opened → RCE
- exposed middleware/admin console → script/template capability → RCE

For each hypothesis, state:
- preconditions
- possible path
- current evidence
- missing proof
- best next validation step

### 6) Judge fit for 微步-style preference

Explicitly assess whether the line is moving toward:
- direct RCE
- file upload + unauth/weak-auth combination
- low-privilege backend action that opens a high-risk execution path

If not yet a good fit, say what is missing instead of forcing the conclusion.

### 7) Keep shared context in Markdown, not a field table

Create or update a readable Markdown document.

Recommended title:
- `RCE专题共享上下文.md`

Recommended sections:
1. 专题目标与当前判断
2. 高价值功能面
3. 鉴权与角色边界观察
4. 上传链分析
5. 模板/渲染/解释执行面分析
6. 配置 / 插件 / 集成能力分析
7. 成链假设
8. 与微步偏好的贴合度判断
9. 下一步建议

Prefer initializing from `references/RCE专题共享上下文模板.md` and then updating it incrementally.

Keep the sections human-readable and continuable. Prefer short concrete paragraphs over schema-like tables.

## Output expectations

A good invocation of this skill should usually produce:
- a prioritized list of high-value surfaces
- 1-3 chain hypotheses worth pursuing
- a judgment of whether the line is promising for 微步-style focus
- an updated Markdown shared context document
- a recommendation to either:
  - deepen now
  - keep as observation
  - downgrade for now

## Avoid these failure modes

- Do not treat keyword hits as conclusions.
- Do not mark every upload feature as high-risk automatically.
- Do not hard-commit to RCE when evidence is still weak.
- Do not make the skill Java-only.
- Do not turn this into a heavy repo-wide scoring framework before the simple version proves useful.
- Do not replace the main audit. Serve it.

## Practical note for implementation evolution

Version 1 should stay light:
- methodology-driven
- chain-driven
- context-writing driven

Only after this proves useful should you attach larger keyword packs or language-specific search material such as the Java RCE file.
