# sample-profiles.md

## 目标

用少量真实样本告诉未来 `loop9-asset-evidence` skill：
- 什么叫强样本
- 什么叫对照样本
- 什么叫“规模一般，但高价值场景提前出现”的样本
- 什么样的目标不该自动抬入最高优先级池

---

## 当前三类样本总览

### A 类：强样本 / 可优先推进型
代表：`ZLMediaKit`

特征：
- 主识别面稳定
- 中国公网规模强
- Hunter 县域 / ICP / 备案主体信号强
- FOFA `.gov.cn` 补强成立
- 极小样本能给出可人工核验的政务/公机构线索

推荐更接近：
- `high-priority-domestic-real-world`

### B 类：对照样本 / 不自动抬高型
代表：`UReport / UReport2`

特征：
- 产品名与最佳识别面不一致
- 有一定现实部署
- 但高价值场景信号持续偏弱
- 不应因为“有一些量”就被抬进最高优先级池

推荐更接近：
- `contrast-sample-do-not-auto-promote`

### C 类：title-clue-driven / 中等规模但高价值场景提前出现型
代表：`MaxKey`

特征：
- 主产品名不直接命中
- title clue 才是主识别面
- 总量不是超大盘
- 但高价值场景（如县域教育统一认证）会较早出现

推荐更接近：
- `moderate-real-world-signal`
- 并保留“可人工上调”的空间

---

## 样本 A：ZLMediaKit（强样本）

### 样本画像
- 组件识别稳定
- 中国公网规模大
- Hunter 县域/备案主体信号强
- FOFA `.gov.cn` 补强成立
- 极小样本明细可见明确政务域名与服务端回显

### 当前关键事实
- Hunter `app.name="ZLMediaKit"` 强
- Hunter `app.name="ZLMediaKit" and icp.name="县"` 强
- FOFA `app="ZLMediaKit"` 强
- FOFA `app="ZLMediaKit" && host=".gov.cn"` 强
- FOFA 极小样本里，多条 `.gov.cn` 主机回显 `ZLMediaKit(...)`

### 对 skill 的启发
如果一个目标同时满足：
- 规模大
- 识别稳
- 政务/县域信号强
- 跨平台补强成立

那么它应更接近：
- `high-priority-domestic-real-world`

---

## 样本 B：UReport / UReport2（对照样本）

### 样本画像
- 产品名与最佳识别面不一致
- 有一定现实部署
- 但政务 / 县域信号当前弱
- 不是“没价值”，但不像强样本那样适合直接冲最高优先级

### 当前关键事实
- `app.name="UReport"` 不行
- `app.name="UReport2"` 有中等规模
- `title="UReport Console"` 有中等规模
- 扩展高价值查询面后，`教育` 方向有少量命中
- 但当前新命中主要集中在商业教育咨询主体，而不是教育局/学校/大学/政府/医院/水务等更强高价值对象
- FOFA `.gov.cn` / `.edu.cn` / `.org.cn` 当前仍弱/无

### 对 skill 的启发
这类目标说明：
- 识别面必须能切换
- 不是所有有现实部署的产品都值得抬入最高优先级池
- skill 不仅要会“挑强者”，还要会“及早识别不够强的目标”

推荐更接近：
- `contrast-sample-do-not-auto-promote`
- 而不是因为中等规模就直接升到 `high-priority-domestic-real-world`

---

## 样本 C：MaxKey（title clue 主识别面 + 中等规模 + 高价值场景提前出现）

### 样本画像
- 主产品名不直接命中
- title clue 才是当前主识别面
- 总量中等，不算超大盘
- 但高价值场景信号并不弱

### 当前关键事实
- Hunter `app.name="MaxKey"` = `0`
- Hunter `web.title="MaxKey"` = `164`
- FOFA `title="MaxKey"` = `52`
- Hunter `web.title="MaxKey" and icp.name="县"` = `2`
- 返回样本直达：`象山县教育局教科研中心`
- FOFA `title="MaxKey" && host=".gov.cn"` = `0`

### 对 skill 的启发
这类目标说明：
- 未来 skill 不能只盯“大盘规模”
- title clue 有时不是补充层，而是主识别面
- `.gov.cn` 为 0 不等于高价值信号为 0
- 如果 Hunter 的县域/教育/统一认证信号已经很具体，就应保留人工上调空间

推荐更接近：
- `moderate-real-world-signal`
- 且附带说明：`high-value-scene-early`

---

## 优先级边界（从三类样本回收出的当前规则）

### 可接近 `high-priority-domestic-real-world`
至少更像：
- 主识别面稳定
- 总量强
- 高价值场景信号强
- 且至少有一层跨平台补强

### 更像 `contrast-sample-do-not-auto-promote`
至少更像：
- 有一定部署
- 但高价值场景信号持续弱
- 识别面虽然能切对，但切对后仍然不够强

### 更像 `moderate-real-world-signal`
至少更像：
- 总量中等或偏弱
- 但已经出现具体、可信的高价值落地场景
- 不宜直接抬到最高优先级
- 也不应被压成单纯对照样本

---

## 一句话版

> `ZLMediaKit` 教 skill 学会“看见强样本”，`UReport / UReport2` 教 skill 学会“不要把中等规模目标错抬成最强样本”，`MaxKey` 教 skill 学会“规模一般，但高价值场景提前出现时，不要误伤成普通弱样本”。
