# Hash semantics anomaly cases

> 用途：
> 当 publish 检测阶段出现 `hash-semantics-anomaly:*` 时，先读这份案例，再决定：
> - 这是历史 raw hash 滞留
> - 这是 multipart 旧口径残留
> - 还是某种临时归一化输入未留档
>
> 这不是主流程规则，而是 **AI 判读尾部异常** 的经验层。

## 判读优先顺序

### 1. 先判断是否是“历史 raw hash 滞留”

满足以下特征时，优先按这类理解：
- state 中的 `last_content_hash` 能在历史 publish 现场元信息里对应到 `sha256_source`
- 或者能证明它对应某个更早时刻的 source raw hash
- 但当前 source file 已经变化，state 没同步刷新

这类情况通常意味着：
- 不是新的第三种语义
- 而是旧 state 停留在历史 raw hash 上

### 2. 再判断是否是“multipart 旧口径残留”

满足以下特征时，优先按这类理解：
- doc 有 `source_parts` 且 `len(source_parts) > 1`
- state hash 等于当前 `part01.md` raw hash
- 但不等于当前完整拼接正文的 render hash

这类情况说明：
- 老 state 是按 detector 旧逻辑写的
- 只记录了第一片 raw hash
- 当前应视为 legacy multipart state，而不应继续触发 publish 主流程

### 3. 最后才判断为“临时归一化输入未留档”

满足以下特征时，可暂时归到这类：
- state hash 既不等于当前 raw
- 也不等于当前保留下来的 render 文件 hash
- 但历史执行记录多次把它当作一个“可解释的 canonical 值”使用
- 当前又找不到对应输入体文件

这类情况通常说明：
- 某次执行时使用了临时拼接/归一化后的正文输入
- 但该输入本身没有被保留
- 需要 AI / 人工复核，而不是让 detector 继续强推 publish

## 已知案例

### Case A — FUDforum `real_poc_final_status`
- doc_key: `realpoc::20260316-223431-FUDforum-xesn::status::real_poc_final_status`
- 结论：**历史 raw hash 滞留**
- 证据：`tmp/fudforum-publish/meta.json` 中直接记录了
  - `source_markdown = .../real_poc_final_status.json`
  - `sha256_source = 5d496b...`
- 说明：state 中的 hash 只是那次 publish 时刻的 raw source hash，后来 source 变了

### Case B — apache-shiro `original_goal`
- doc_key: `loop9::20260314-000000-apache-shiro-ax31::original_input::original_goal`
- 当前判断：**高概率历史 raw hash 滞留**
- 现象：
  - 当前 raw / 当前保留下来的 publish 临时正文都等于 `3af33...`
  - state 里仍是 `6d94...`
- 说明：高概率是更早一轮 source 内容 hash 残留，但现场证据不如 FUDforum 那样闭环

### Case C — top-think-framework `original_goal`
- doc_key: `loop9::20260314-173132-top-think-framework-s5qz::original_input::original_goal`
- 当前判断：**高概率历史 raw hash 滞留**
- 现象：
  - state = `dc1410...`
  - 当前 raw = `6625a1...`
- 说明：当前更像旧 source hash 残留

### Case D — top-think-framework `solution_v3`
- doc_key: `loop9::20260314-173132-top-think-framework-s5qz::findings::solution_v3`
- 当前判断：**高概率历史 raw/source hash 滞留**
- 现象：
  - state = `8d4808...`
  - 当前 raw = `5162a0...`
  - 当前 render = `263dbb...`
- 说明：不是当前 raw，也不是当前 render，但更像早期 source 内容 hash

### Case E — processwire `solution_v5`
- doc_key: `loop9::20260316-133331-processwire-c035::findings::solution_v5`
- 当前判断：**临时归一化输入未留档（优先这样理解）**
- 现象：
  - state = `2ba21b...`
  - 当前 raw `part01.md` = `9cc58d...`
  - 当前保留下来的 render 文件 = `a2965f...`
- 说明：
  - 它不是当前 raw
  - 也不是当前保留 render 文件
  - 但历史执行记录多次把它称作“当前多分片内容哈希”
- 处理建议：
  - 先不要自动 publish
  - 先按 anomaly 留给 AI / 人工判读

## 遇到 anomaly 时的建议动作

### 可以直接跳过主发布、只做记录的情况
- 历史 raw hash 滞留
- multipart 旧口径残留

### 应该升级为人工/AI 判读的情况
- 当前 raw / render 都对不上
- 且样本不在已知案例中
- 或者样本在已知案例中，但证据出现新变化

## 不要做的事
- 不要因为 anomaly 就立刻重写 state 全库
- 不要把每个 anomaly 都硬编码成新程序分支
- 不要让 anomaly 再次自动吃掉 publish 队列
