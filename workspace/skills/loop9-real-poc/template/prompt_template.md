# Loop9 Real PoC Task

你现在要做的，不是重新做代码审计；而是基于**已经完成的 Loop9 代码审计结果**，持续产出真正可用的 Python PoC 文件。

## 第一性原理

- 核心目标：**PoC 文件本身**。
- 外层包装不是重点；重点是借助 OpenCode 的 loop9 工作流，持续、多轮、直接地把 PoC 写出来。
- 不要为了格式制造大量中间产物。
- 输出优先级高于包装优先级。

## 权威输入

- 审计运行目录：`{{AUDIT_RUN_DIR}}`
- 共享 PoC 目录：`{{SHARED_POC_DIR}}`
- PoC 模板文件：`{{POC_TEMPLATE_PATH}}`
- 最少迭代轮数：`{{MIN_ITERATIONS}}`
- 最大迭代轮数：`{{MAX_ITERATIONS}}`
- 本轮 solution 目录前缀：`{{REAL_POC_SOLUTION_PREFIX}}`
- 本轮 validation 目录前缀：`{{REAL_POC_VALIDATION_PREFIX}}`
- 全局映射清单：`{{REAL_POC_MANIFEST_PATH}}`
- 文件级终态文件：`{{REAL_POC_FINAL_STATUS_PATH}}`

## 机器字段保留规则（高优先级，必须遵守）

如果任务文件顶部已经给出如下机器字段：

- `run_kind:`
- `root_audit_run_dir:`
- `shared_poc_dir:`

那么你在生成 fresh iteration run 的 `original_goal/part01.md` 时，必须在顶部**原样保留这些字段名与取值**：

- 使用 snake_case 原字段名
- 不要翻译成 `Run kind` / `Root audit run dir` / `Shared PoC dir`
- 不要只保留语义等价的人类说明
- 这些字段属于机器可读身份锚点，不是普通自然语言说明

## 任务目标

从审计运行目录中，识别所有**已经被认定为 Passed 的漏洞**，并为每个漏洞产出一个对应的 Python PoC 文件。

最终目标是：
- 一个 Passed 漏洞，对应一个 `.py` 文件
- 所有这些 `.py` 文件，都位于共享 PoC 目录中
- 每一轮都必须形成结构化、可审计、可回看的过程产物，而不是只留下最终 `.py`

## 非常重要的工作方式

### 1. 共享 PoC 目录是持久状态

`{{SHARED_POC_DIR}}` 不是临时输出目录，而是整个 PoC 编写过程的共享工作区。

你在每一轮都必须：
- 先读取这个目录里已经存在的 `.py` 文件
- 理解它们已经做到什么程度
- 在原文件基础上继续修改 / 增强
- 不要每轮都从零重写全部 PoC

但要特别注意：
- `{{SHARED_POC_DIR}}` 只是共享工作区，不是唯一可信过程记录
- 不允许只改最终 `.py` 而不留下结构化轮次记录
- 任何重要修改，都必须在该轮的 solution / validation 产物中留下可审计痕迹
- `{{REAL_POC_MANIFEST_PATH}}` 是共享工作区的全局映射清单，必须被持续维护

### 2. 一个漏洞对应一个文件

- 共享目录下，每个 Passed 漏洞都应该有一个独立 `.py` 文件
- 文件名应稳定、可读、可复用
- 如果某漏洞已有 `.py`，优先继续修改该文件
- 如果某漏洞还没有 `.py`，才新建文件

### 3. 每个 PoC 文件都必须带固定溯源注释块

共享目录中的每个 `.py` 文件顶部都必须包含固定、清晰、可读的溯源注释块。

至少包含以下字段：
- `Source-Run:` 当前审计 run 目录
- `Source-Report:` 对应的 `solution_v*` / `validation_report_v*` / `shared_context/*` 文件
- `Source-Finding:` 该 PoC 对应的具体漏洞名称 / finding 标识
- `Classification:` 例如收录候选 / 酌情池 / 内部保留 / 条件型链路
- `Preconditions:` 该 PoC 成立所依赖的前提
- `Defense-Model:` 防御机制建模结果；若未观察到相关信号，允许写 `none-observed`
- `Defense-Notes:` 防御说明；若无实质防御信号，允许写 `none`
- `Payload-Constraints:` Payload 受限情况；若无特殊限制，允许写 `none`
- `Confidence:` `high` / `medium` / `low`
- `Status:` `draft` / `refined` / `frozen`

要求：
- 不是每个 finding 都必须硬编一大段黑白名单分析
- 如果未观察到实质防御信号，明确写 `Defense-Model: none-observed`、`Defense-Notes: none`、`Payload-Constraints: none` 即可
- 如果观察到过滤 / 黑白名单 / 禁用函数 / 动态策略来源等信号，则这些字段必须反映真实判断，不能留空，也不能假装“默认无防御”

这些字段不是装饰；它们是后续每轮读取、对照、去重、冻结时的硬性锚点。

### 4. 每一轮开始前，先做严格的 1v1 映射对照

在任何修改发生前，你必须先完成一次“报告 ↔ 本地 PoC 文件”的严格映射检查：
- 列出当前所有 Passed 漏洞
- 先读取 `{{REAL_POC_MANIFEST_PATH}}`（如果已存在）
- 列出共享目录下已有的所有 `.py`
- 通过文件头溯源注释，将每个 `.py` 与具体 finding 做 1v1 对照
- 检查是否存在重复映射、遗漏映射、错误映射
- 先更新 `{{REAL_POC_MANIFEST_PATH}}` 的当前映射状态
- 只有在映射关系清楚后，才允许创建新文件或修改旧文件

禁止：
- 未做对照就直接新建文件
- 不读取 manifest 就直接按印象修改
- 一个 finding 被多个功能重复的 `.py` 占用
- 一个 `.py` 同时模糊对应多个 finding

### 5. PoC风格要简单直接

强制参考模板：`{{POC_TEMPLATE_PATH}}`

要求：
- 风格简单、直接、够用
- 去掉不必要的抽象和花哨结构
- 优先真实可理解、可改、可填参数、可在实验环境中跑
- 不要写成过度工程化的小框架

### 6. 以“可用 PoC”为目标，而不是以“文档完整”为目标

你真正要完成的是 PoC 文件，而不是一堆解释。

可以有简短注释，但不要让解释喧宾夺主。

### 7. 安全边界

- 默认面向受控实验环境 / 本地复现环境
- 不要默认写破坏性 payload
- 当漏洞适合先做存在性证明 / 安全验证版 PoC 时，先给出安全边界内的最强版本
- 如果要进一步走到更强利用，必须在代码注释中明确说明额外前提与风险

### 8. 防御感知与动态策略来源（按需强制，禁止一刀切）

这部分是本任务的新增高优先级要求。

原则：
- 不是所有项目、所有 finding 都存在黑名单 / 白名单 / 防御链
- **禁止**为了凑格式，给明显没有相关证据的 finding 硬编防御机制
- 但是，只要审计材料、已有 PoC、源码片段、payload 设计里出现明显信号，就必须把防御机制当成 PoC 设计变量，而不是只按漏洞原理直写 payload

至少把以下几类东西视为防御信号：
- 黑名单 / 白名单 / allowlist / denylist / 关键词过滤 / 拦截 / WAF / sanitize
- `disable_functions`、命令执行函数限制、对 `system` / `exec` / `shell_exec` / `passthru` / 反引号等形态的额外限制
- 动态策略来源：数据库、`sysconfig`、缓存配置文件、配置重写后落盘生效、后台设置写入后运行时加载
- 插件、权限链、环境约束带来的附加限制

对每个 finding，在真正修改 `.py` 之前，先做一个**最小防御建模**：
- 是否存在防御：`confirmed` / `suspected` / `none-observed` / `unknown`
- 防御来源类型：`hardcoded-source` / `database-driven` / `config-file` / `cache-rewrite` / `runtime-env` / `plugin-or-permission` / `mixed`
- 对 payload 的影响：`none` / `keyword-filter` / `function-disabled` / `allowlist-gated` / `permission-gated` / `unknown`
- 当前处理策略：`safe-marker-only` / `primary-plus-fallback` / `note-only-because-low-confidence`

强制要求：
- 如果防御信号存在，但你没有充分把握，**不允许**静默假设绕过一定成立
- 这时必须在 `.py` 注释和本轮 `solution/index.md`、`validation/index.md` 中写清楚：
  - 哪些防御点已确认
  - 哪些只是怀疑
  - 当前 payload 为什么可能被拦或可能绕过
  - 为什么此时只能给安全验证版 / 候选 fallback / 低置信说明
- 候选绕过 payload 可以写，但不能把“未验证的猜测”伪装成“默认可靠方案”

DedeCMS 一类特殊情况：
- 如果目标存在“数据库 / sysconfig / cache 配置重写 / 后台设置落盘后再生效”这类链路，必须把它当成**动态策略来源**来额外判断
- 这类项目不能只看静态源码里有没有过滤函数；还要判断运行时限制是否可能来自数据库或配置文件

## 你要读取的材料

你必须主动阅读并利用：
- 审计运行目录下的 `solution_v*`
- 审计运行目录下的 `validation_report_v*`
- 审计运行目录下的 `shared_context/`
- 共享 PoC 目录下已有的 `.py` 文件
- `{{POC_TEMPLATE_PATH}}`

## 老范式轮次落盘要求（强制）

你必须显式复用老范式的核心约束：**每一轮都要留下 solution 与 validation 两类结构化产物**。

### 目录隔离硬规则

`real_poc_*` 相关产物**必须**放在 `real_pocs/` 目录内，不能与审计主目录平级混放。

禁止生成到这些位置：
- `<run_dir>/real_poc_solution_vN/`
- `<run_dir>/real_poc_validation_report_vN/`
- `<run_dir>/real_poc_final_status.json`

正确位置只能是：
- `<run_dir>/real_pocs/real_poc_solution_vN/`
- `<run_dir>/real_pocs/real_poc_validation_report_vN/`
- `<run_dir>/real_pocs/real_poc_final_status.json`

原因：审计主目录与 real-poc 目录混放，会显著提高后续模型读取时的误判概率。

目录规则：
- 第 N 轮 solution 目录：`{{REAL_POC_SOLUTION_PREFIX}}N/`
- 第 N 轮 validation 目录：`{{REAL_POC_VALIDATION_PREFIX}}N/`
- 本 MVP 阶段，每个目录至少写一个 `index.md`

例如：
- `{{REAL_POC_SOLUTION_PREFIX}}1/index.md`
- `{{REAL_POC_VALIDATION_PREFIX}}1/index.md`

### 每轮强制顺序

每一轮都必须按这个顺序执行，不能跳步：
1. 先做 finding ↔ `.py` 的 1v1 映射检查
2. 先写本轮 `solution/index.md`
3. 再去创建/修改 `{{SHARED_POC_DIR}}` 下的 `.py`
4. 再写本轮 `validation/index.md`
5. 再决定哪些修改被接受、哪些问题留到下一轮

禁止：
- 直接只改 `.py` 不写本轮 solution
- 把 validator 降格成脑内步骤，不落盘
- 先改完大量 `.py`，事后再补写一份空洞的 round note

### 全局映射清单 `manifest.json`（强制维护）

`{{REAL_POC_MANIFEST_PATH}}` 是共享 PoC 工作区的全局状态表。

它不替代：
- `.py` 文件头溯源注释
- 每轮 `solution/index.md`
- 每轮 `validation/index.md`

它负责维护“当前全局态”，至少应包含：
- `schema`
- `run_dir`
- `shared_poc_dir`
- `generated_by`
- `findings` 数组

每个 finding 条目至少包含：
- `finding_id` 或稳定标题
- `title`
- `source_report`
- `classification`
- `preconditions`
- `mapped_file`
- `status`
- `last_round`
- `validator_verdict`

每轮开始时：
- 先读取并校正 `manifest.json`

每轮结束时：
- 根据本轮实际改动和 validator 结论更新 `manifest.json`

### 文件级终态文件 `real_pocs/real_poc_final_status.json`（强制对齐）

`{{REAL_POC_FINAL_STATUS_PATH}}` 是 **PoC 工作流整体状态** 的文件级锚点，并且必须放在 `real_pocs/` 目录内，不能与审计主目录平级。

它和 `manifest.json` 的职责不同：
- `manifest.json` 维护的是 finding ↔ `.py` ↔ 当前条目状态
- `real_poc_final_status.json` 维护的是 **整个 real-poc 工作流是否已整体完成**

禁止把下面两件事混为一谈：
- `某一轮 validation PASSED`
- `整个 PoC 编写工作流已完成`

每轮结束时，你都必须让 `real_pocs/real_poc_final_status.json` 与当前事实保持一致。

它至少应表达清楚：
- `latest_round`
- `latest_round_semantics`
- `latest_round_source`
- `latest_round_validation_status`
- `recorded_min_iterations`
- `min_iterations`
- `min_iterations_source_kind`
- `min_iterations_normalization`
- `min_iterations_satisfied`
- `all_findings_mapped`
- `all_findings_accepted_or_frozen`
- `all_findings_frozen`
- `workflow_completion`
- `workflow_completion_reason`

硬规则：
- **只有**在“最新轮 validation 通过 + 达到最少轮次 + finding / manifest 状态收敛”时，才允许把 `workflow_completion` 写成完成态
- 如果只是“本轮 PASSED，但整体还没到终态”，必须明确写成 `not-yet`
- 如果只是冻结检查轮、且本轮无需修改，也仍然必须更新该文件
- 一旦共享 `real_pocs/` 已经达到 `{{MAX_ITERATIONS}}` 的封顶轮次，就**绝不允许**再创建 `real_poc_solution_v{{MAX_ITERATIONS+1}}`、`real_poc_validation_report_v{{MAX_ITERATIONS+1}}` 或任何更高轮次目录
- 若此时发现 shared `manifest.json` 或 `real_poc_final_status.json` 与真实冻结状态不一致，只允许进入 **repair-only** 模式：
  - 允许修正状态文件、必要的 manifest 字段、以及本轮 run-local 的说明文件
  - 不允许通过新建更高轮次 shared round 来“修状态”
  - 不允许删除既有 shared 历史目录来伪造从未越界
  - **不允许为了宣称“已完成”而回写/篡改/伪造当前完成轮次数字**
  - `latest_round` / `last_round` 这类轮次字段必须尊重已经存在的共享事实；若它们不合理，也只能在说明中记录冲突，不能靠伪造轮次把状态写漂亮

### 每轮 `solution/index.md` 至少包含

- 本轮编号
- 当前 finding 列表
- 当前 `.py` 列表
- 当前 `manifest.json` 摘要
- 1v1 映射结果（已覆盖 / 缺失 / 重复 / 可疑错配）
- 本轮计划修改项
- 实际修改项
- 本轮冻结判断（若有）
- 对存在明显防御信号的 finding，补一段最小防御建模摘要：
  - 是否存在防御
  - 防御来源类型
  - 对 payload 的影响
  - 本轮是否需要 fallback / 注释说明 / 仅保守验证

### 每轮 `validation/index.md` 至少包含

- 本轮校验范围
- 对每个 finding / `.py` 的结论：accepted / revise / blocked / frozen
- 是否存在边界表述问题、参数错配、条件漏写
- 对存在明显防御信号的 finding，检查其 `.py` 是否已经写清：
  - `Defense-Model`
  - `Defense-Notes`
  - `Payload-Constraints`
  - `Confidence`
- `manifest.json` 是否与当前 `.py` / finding 状态一致
- 是否存在投机取巧：跳过映射、无依据新建文件、把条件型链路写成默认通杀、为了凑轮次乱改结构、发现防御信号却完全不建模
- 下一轮建议

## 你要特别关注

- 哪些漏洞已经被认定为 **Passed**
- 哪些 PoC 已经存在但还很粗糙
- 哪些 PoC 可以直接在旧文件上修正
- 哪些 Passed 漏洞还没有对应 PoC 文件
- 哪些轮次记录已经完整落盘，哪些还没有

## 迭代要求

- 若不能一次性完成所有 Passed 漏洞的 PoC，也必须持续推进
- 默认目标仍然是**最少跑 {{MIN_ITERATIONS}} 轮**；当前默认应与核心 Loop9 保持一致，按 **3 轮起步** 理解
- 最大轮次按核心 Loop9 的默认上限 **{{MAX_ITERATIONS}}** 处理
- 后续轮次的工作类型必须受约束，不能为了修改本身而修改
- 每一轮都要复用共享 PoC 目录，而不是推倒重来

### 提前完成后的冻结式静态验收规则

如果所有 Passed 漏洞对应的 PoC 在较早轮次就已经构建完整，则：
- 后续轮次**禁止**为了修改本身而修改
- 禁止无意义重构、变量改名、函数拆分、结构重排、过度封装、装饰性抽象
- 剩余轮次应转为**纯静态参数级打磨 / 冻结式验收轮**

冻结式验收轮只允许做以下事情：
- 对照审计报告，检查默认参数是否准确
- 检查 URL / Path / Header / Query / Body / Payload 构造是否与漏洞原理严格一致
- 检查前提条件、风险边界、成功判定逻辑是否写清楚
- 仅在确有必要时做最小改动

如果本轮检查后确认无需改动：
- 明确输出：`状态：已冻结，无需修改`
- 保持当前 `.py` 文件内容不变
- 继续进入下一轮的只读验收，而不是为了凑轮次制造新改动
- **即使没有代码改动，也仍然必须写出该轮的 `solution/index.md` 与 `validation/index.md`**，把冻结判断完整落盘
- 如果 shared 已封顶且仅存在状态漂移，则本轮只能写 repair-only 的 run-local 记录，不能再把 shared 轮次继续向上推进

## 成功标准

成功不是写一堆中间分析，而是：
- 共享 PoC 目录中，尽可能多的 Passed 漏洞都拥有对应 `.py`
- 每个 `.py` 都能通过文件头注释被严格追溯到具体 finding
- 每一轮都留下成对的 `real_pocs/real_poc_solution_vN/index.md` 与 `real_pocs/real_poc_validation_report_vN/index.md`
- `{{REAL_POC_MANIFEST_PATH}}` 能稳定反映当前 finding ↔ `.py` ↔ validator 状态
- 这些轮次文件足以复盘：改了什么、为什么改、validator 怎么看、为什么冻结或继续
- 这些 `.py` 明显比初稿更接近真实可用 PoC
- 对存在明显防御信号的 finding，PoC 已至少做到：
  - 明确写出防御建模结果
  - 说明 payload 约束或不确定性
  - 在低置信场景下不假装默认绕过可靠
- 多轮之间有连续积累，而不是重复劳动
- 当 PoC 已成熟时，后续轮次表现为稳定冻结而不是无意义漂移

## 最终输出要求

工作重点在共享 PoC 目录中的 `.py` 文件本身。

你可以在最终总结里简要说明：
- 哪些 Passed 漏洞已拥有 PoC
- 哪些 PoC 被明显改进了
- 哪些仍未完成

但真正的核心交付物，是：

`{{SHARED_POC_DIR}}` 下的全部 PoC `.py` 文件。
