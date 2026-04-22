# 2026-03-27 Loop9 资产证据层 skill 输入/输出字段契约 v1

## 目标

在三类真实样本（`ZLMediaKit` / `UReport-UReport2` / `MaxKey`）回收到 skill 之后，给 `loop9-asset-evidence` 一个比 v0 更稳定的 IO contract。

这版重点收两件事：
- `recommended_priority` 到底怎么用
- 什么时候必须把 `title clue` 也当成一等输入 hints

---

## 1. v1 相比 v0 的关键变化

### 1.1 `knownTitleClues` 升级为正式 hints
原因：
- `MaxKey` 已证明：有些候选里，title clue 不是补充，而是主识别面
- 所以 v1 不再只保留 `knownAliases` / `knownComponentNames`
- `knownTitleClues` 现在应作为正式可选输入保留

### 1.2 `recommended_priority` 与 `sample_profile` 明确分层
- `sample_profile` 负责描述“它像哪类样本”
- `recommended_priority` 负责给上游一个保守优先级桶

也就是：
- `sample_profile` 更像解释层
- `recommended_priority` 更像上游 workflow 可消费的决策层

### 1.3 `recommended_priority` 不再按“量大=优先”理解
这条现在必须写死：

> `recommended_priority` 不是原始总量排序结果，而是 **样本画像 + 规模信号 + 高价值场景信号 + 跨平台补强** 的保守合成判断。

---

## 2. 输入契约 v1

## 2.1 建议结构

```json
{
  "policy": "weibu-submission",
  "candidate": {
    "productName": "MaxKey",
    "repoUrl": "https://gitee.com/dromara/MaxKey.git",
    "sourcePlatform": "gitee",
    "sourceKind": "repo-candidate",
    "vendorName": "dromara",
    "mainlandUseEvidence": "README 声称广泛用于医疗、金融、政府、制造"
  },
  "hints": {
    "knownAliases": ["JEECG"],
    "knownComponentNames": ["UReport2"],
    "knownTitleClues": ["MaxKey", "MaxKey单点登录认证系统"],
    "preferredQueries": ["web.title=\"MaxKey\""],
    "expectedProfile": "unclear"
  }
}
```

---

## 2.2 必填字段

### `policy`
当前允许值：
- `weibu-submission`

### `candidate.productName`
- 必填
- 这是最小起点
- 但不能假设它必然是最佳识别面

---

## 2.3 强烈建议字段

### `candidate.repoUrl`
用途：
- 让证据卡可追溯
- 方便把 repo 侧事实和资产侧事实挂起来

### `candidate.sourcePlatform`
建议枚举：
- `github`
- `gitee`
- `gitcode`
- `manual`

### `hints.knownAliases`
适用：
- 品牌名 / 产品名 / 资产名不一致

### `hints.knownComponentNames`
适用：
- 组件名路线比产品名更稳
- 如 `UReport -> UReport2`

### `hints.knownTitleClues`
适用：
- title clue 明显比产品名更像真实入口
- 如 `MaxKey`

---

## 2.4 可选字段

### `candidate.sourceKind`
示例：
- `repo-candidate`
- `manual-target`
- `named-range`

### `candidate.vendorName`
用途：
- 补厂商/组织语境

### `candidate.mainlandUseEvidence`
用途：
- 保留上游已有的中国实际使用线索
- 但不应当作硬真相

### `hints.preferredQueries`
用途：
- 只作为建议
- 不应强制覆盖 skill 的判断

### `hints.expectedProfile`
建议值：
- `strong-domestic-real-world`
- `contrast-check`
- `unclear`

---

## 2.5 v1 的当前输入决策

### `knownAliases` / `knownComponentNames` / `knownTitleClues` 三者分开保留
原因：
- 三者不是一个概念
- 混在一起会弱化解释能力
- 真实样本已经分别证明了三者的必要性

### 如果上游不给 hints，skill 可以自己薄试一次识别面
但限制保持不变：
- 只试少数几个面
- 不允许无限试词
- 不能把“探针自由度”做成脚本里的暴力枚举

---

## 3. 输出契约 v1

## 3.1 建议结构

```json
{
  "status": "ok",
  "policy": "weibu-submission",
  "product_name": "MaxKey",
  "primary_identification_surface": "title-clue",
  "sample_profile": "high-value-scene-early",
  "fingerprint_confidence": "medium",
  "china_asset_signal": "moderate",
  "gov_soe_signal": "moderate",
  "submission_fit": "medium",
  "recommended_priority": "moderate-real-world-signal",
  "notes": [
    "主产品名不直接命中，title clue 才是主识别面",
    "规模中等，但县域教育统一认证场景已出现"
  ],
  "next_probe_suggestion": "optional-fofa-detail-sample",
  "evidence_card_path": "reports/...md"
}
```

---

## 3.2 当前推荐返回字段

### `status`
允许值：
- `ok`
- `not-applicable`
- `insufficient-signal`

### `policy`
原样回显

### `product_name`
原样回显或规范化名称

### `primary_identification_surface`
建议值：
- `product-name`
- `alias`
- `component-name`
- `title-clue`
- `body-clue`

### `sample_profile`
建议值：
- `strong-sample`
- `contrast-sample`
- `high-value-scene-early`
- `unclear`

### `fingerprint_confidence`
- `high | medium | low`

### `china_asset_signal`
- `high | moderate | weak | not-seen`

### `gov_soe_signal`
- `high | moderate | weak | not-seen`

### `submission_fit`
- `high | medium | low | not-applicable`

### `recommended_priority`
- `high-priority-domestic-real-world`
- `moderate-real-world-signal`
- `contrast-sample-do-not-auto-promote`
- `not-applicable`

### `notes`
- `string[]`
- 只放简短结论，不放原始日志

### `next_probe_suggestion`
建议值：
- `none`
- `optional-fofa-detail-sample`
- `optional-hunter-thin-sample`
- `switch-identification-surface`
- `stop-do-not-overprobe`

### `evidence_card_path`
- 指向具体证据卡 markdown

---

## 3.3 v1 的使用语义（重点）

### `sample_profile` 是“它像谁”
它回答：
- 更像 `ZLMediaKit`
- 更像 `UReport/UReport2`
- 更像 `MaxKey`
- 还是当前看不清

### `recommended_priority` 是“上游现在先怎么摆它”
它回答：
- 应不应该更接近最高优先级池
- 应不应该保留在中间池
- 应不应该明确不自动上抬

### 二者不要混成一个字段
因为：
- `sample_profile` 更偏解释层
- `recommended_priority` 更偏 workflow 消费层

---

## 3.4 `recommended_priority` 当前语义边界

### `high-priority-domestic-real-world`
更像：
- 主识别面稳定
- 总量强
- 高价值场景信号强
- 跨平台补强成立

锚点：
- `ZLMediaKit`

### `contrast-sample-do-not-auto-promote`
更像：
- 有一定现实部署
- 但高价值场景信号持续弱
- 识别面切对后仍然不够强

锚点：
- `UReport / UReport2`

### `moderate-real-world-signal`
当前更像：
- **临时承载 C 档：勉强够格可发车**
- 总量较强但高价值场景偏弱，或总量一般但高价值场景提前出现
- 不宜直接抬到最高优先级
- 也不应被压成纯对照样本

当前锚点：
- `MaxKey`
- `1Panel`

说明：
- 这不是一个完美语义命名
- 只是当前枚举体系下的临时承载桶
- 等 B 档（真正中价值可发车）出现稳定锚点后，再考虑是否拆枚举

### `not-applicable`
只用于：
- policy 不匹配
- 当前调用本身就不该由该 skill 处理

---

## 3.5 `status` 与 `recommended_priority` 的配合

### 当 `status = ok`
- 应返回完整分类字段
- 包括 `sample_profile` 与 `recommended_priority`

### 当 `status = not-applicable`
- `recommended_priority` 应为 `not-applicable`
- 不要假装给出强弱判断

### 当 `status = insufficient-signal`
- 允许返回部分分类字段
- 但应明显提示“不足以做强判断”
- `recommended_priority` 可以省略，或保守降到 `contrast-sample-do-not-auto-promote`
- 当前更推荐：**允许省略**，避免假装有结论

---

## 4. 当前结论：IO contract 是否已经比 v0 稳定

结论：**是，已经明显比 v0 稳定。**

原因：
- 三类样本画像已经齐了
- `recommended_priority` 的边界已经不再飘
- `knownTitleClues` 的必要性已经被真实样本证明

但它仍然不是“永远不改”的最终版。

更准确的说法是：
- 已经足够进入 **v1 可实现 / 可引用状态**
- 但仍应允许后续小范围修词与枚举细修

---

## 一句话版

> v1 IO contract 的关键收敛是：把 `knownTitleClues` 正式升格，把 `sample_profile` 与 `recommended_priority` 分层，并明确 `recommended_priority` 不是“谁数量大谁更优先”，而是保守样本判断后的 workflow 桶位建议。
