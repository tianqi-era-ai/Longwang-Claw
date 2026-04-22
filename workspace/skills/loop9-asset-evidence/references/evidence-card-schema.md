# evidence-card-schema.md

## 目标

定义资产证据卡的最小字段、写法纪律、以及反过度表述规则。

这个文件只负责：
- 字段长什么样
- 每个字段怎么写
- 哪些词能用，哪些词不能说死

---

## 建议字段

```markdown
# 资产证据卡：<Product>

## 1. 基础识别
- product_name:
- repo_url:
- fingerprint_confidence:
- primary_platform_for_proof:
- supporting_platforms:

## 2. 产品识别证据
- core_query:
- total_signal:
- stronger_fingerprint_candidates:
- ambiguity_note:

## 3. 中国部署规模证据
- china_asset_signal:
- scale_judgement:
- cross_platform_note:

## 4. 政务 / 县域 / 国企信号
- gov_soe_signal:
- icp_signal:
- county_level_signal:
- current_confidence_note:

## 5. 抽样验证
- sample_size:
- sample_validation_note:
- false_positive_risk_note:

## 6. 对 Loop9 的意义
- audit_roi:
- submission_fit:
- priority_bucket:
- why_high_priority:

## 7. 当前边界
- what_is_strong_signal:
- what_is_not_yet_hard_fact:
- next_thin_validation_step:
```

---

## 推荐枚举写法

### fingerprint_confidence
- `high`
- `medium`
- `low`

### china_asset_signal
- `high`
- `moderate`
- `weak`
- `not-seen`

### gov_soe_signal
- `high`
- `moderate`
- `weak`
- `not-seen`

### submission_fit
- `high`
- `medium`
- `low`
- `not-applicable`

### recommended_priority
- `high-priority-domestic-real-world`
- `moderate-real-world-signal`
- `contrast-sample-do-not-auto-promote`
- `not-applicable`

---

## 当前优先级判断边界（薄规则）

### `high-priority-domestic-real-world`
更适合用于：
- 主识别面稳定
- 总量强
- 高价值场景信号强
- 且至少有一层跨平台补强

### `contrast-sample-do-not-auto-promote`
更适合用于：
- 有一定现实部署
- 但高价值场景信号持续弱
- 即使识别面切对后，仍不应自动进入最高优先级池

### `moderate-real-world-signal`
当前更适合用于：
- **临时承载“勉强够格可发车”这一层**
- 总量较强但高价值场景偏弱，或总量一般但高价值场景提前出现
- 既不该直接抬到最高优先级
- 也不应被压成单纯对照样本

说明：
- 当前先继续沿用这个旧枚举
- 但不要把它误当成最终完整层级
- 真正的业务语义层应以《`weibu-submission` 价值门槛模型 v0》为准

---

## 字段写法纪律

### 1. 强信号
只有当下面至少两层同时成立时，才更适合写“强信号”：
- 总量信号强
- 平台识别稳定
- 有高价值场景信号
- 已做极小样本验证

### 2. 高置信度强信号
适用于：
- 不只是 stats
- 还有小样本明细支撑
- 且跨平台能互相补强

### 3. 对照样本
适用于：
- 有一定部署
- 但政务/县域/高价值场景信号弱
- 不应自动抬入最高优先级池

---

## 反过度表述规则

### 禁止直接写死的情况
不要把下面内容直接写成硬事实：
- 粗筛 total = 独立机构精确数量
- stats = 最终部署实锤
- 单平台单查询 = 终局事实

### 推荐写法
应优先写成：
- `强信号`
- `高置信度强信号`
- `出现明显县域/政务相关部署信号`
- `已完成第一轮极小样本验证`
- `仍不宜直接视为独立机构精确数量`

---

## 当前三个样本的写法锚点

### ZLMediaKit
推荐：
- `china_asset_signal: high`
- `gov_soe_signal: high`
- `submission_fit: high`
- `recommended_priority: high-priority-domestic-real-world`

### UReport / UReport2
推荐：
- `china_asset_signal: moderate`
- `gov_soe_signal: weak`
- `submission_fit: medium/low`
- `recommended_priority: contrast-sample-do-not-auto-promote`

### MaxKey
推荐：
- `china_asset_signal: moderate`
- `gov_soe_signal: moderate`
- `submission_fit: medium`
- `recommended_priority: moderate-real-world-signal`
- 并在说明里写清：`title clue 主识别面 + 高价值场景提前出现`

---

## 一句话版

> 证据卡不是战报，它是保守、可追溯、方便上游 workflow 做判断的中间产物。
