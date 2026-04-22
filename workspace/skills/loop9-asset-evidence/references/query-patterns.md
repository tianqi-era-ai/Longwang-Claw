# query-patterns.md

## 目标

记录 `loop9-asset-evidence` 中最稳定、最可复用的查询模式。

这个文件只回答三类问题：
- 先查什么
- 什么时候切换识别面
- 什么时候该收口，不要继续烧额度

不负责：
- 最终优先级结论
- 证据卡字段定义
- 平台通用纪律总表

---

## 总顺序

默认顺序：

1. 先确认识别面
2. 再确认中国部署规模
3. 再确认**最近一年**仍在使用的现实信号
4. 再确认政务 / 县域 / 高价值场景信号
5. 最后只做极小样本验证，并把少量样本留给 AI 判断

如果第二步就明显很弱，或第三/四步始终没有高价值信号，不要硬拧成强样本。

---

## 模式 A：强样本路线（ZLMediaKit 型）

适用特征：
- 组件名稳定
- 大盘量级大
- 政务 / 县域信号出现快

### Hunter
1. `app.name="ZLMediaKit"`
   - 先看总量
2. `app.name="ZLMediaKit" and icp.name="县"`
   - 看县域相关主体信号
3. 若值得继续，再抽样看第一页极小样本

### FOFA
1. `app="ZLMediaKit"`
   - 做规模对照
2. `app="ZLMediaKit" && host=".gov.cn"`
   - 做政务域名补强
3. 若值得继续，再做 `search/all size=5` 极小样本

### 收口标准
如果满足下面三件事，就足够进入“高优先级候选”判断：
- Hunter 总量强
- Hunter 县域/备案主体信号强
- FOFA `.gov.cn` 补强成立

---

## 模式 B：识别面切换路线（UReport / UReport2 型）

适用特征：
- 产品名本身不稳定
- 组件名 / 标题 / 正文层比产品名更好用
- 政务信号不一定会快速出现

### Hunter
1. 先试产品名
   - `app.name="UReport"`
2. 若结果弱/为 0，切识别面
   - `app.name="UReport2"`
   - `web.title="UReport"`
   - `web.body="UReport"`
3. 只要找到稳定识别面，就先停，不要一次试很多词

### FOFA
1. 不假设 `app=` 一定存在
2. 先试标题层
   - `title="UReport Console"`
3. 若标题层也弱，再决定是否值得继续深入

### 高价值信号验证
初始高价值验证不要只停在 `县` 一条上。

当前推荐扩展面：
- Hunter：`... and icp.name="县"`
- Hunter：`... and icp.name="教育"`
- Hunter：`... and icp.name="学校"`
- Hunter：`... and icp.name="大学"`
- Hunter：`... and icp.name="学院"`
- Hunter：`... and icp.name="医院"`
- Hunter：`... and icp.name="人民政府"`
- Hunter：`... and icp.name="教育局"`
- Hunter：`... and icp.name="水务"`
- Hunter：`... and icp.name="局"`
- Hunter：`... and icp.name="政"`
- Hunter：`... and icp.name="厅"`
- Hunter：`... and icp.name="国家"`
- Hunter：`... and icp.name="中国"`
- Hunter：`... and icp.name="人民"`
- Hunter：`... and icp.type="政府"`
- Hunter：`... and (icp.type="政府" || icp.type="机关" || icp.type="事业单位")`
- Hunter：`... and icp.type!="企业" and (icp.type="政府" || icp.type="机关" || icp.type="事业单位")`
- Hunter：`... and icp.web_name="政府门户"`
- Hunter：`... and icp.web_name="集团"`
- Hunter：`... and icp.name="集团"`
- Hunter：`... and domain.suffix="gov.cn"`
- Hunter：`... and domain.suffix="edu.cn"`
- FOFA：`title="UReport Console" && host=".gov.cn"`
- FOFA：`title="UReport Console" && host=".edu.cn"`
- FOFA：`title="UReport Console" && host=".org.cn"`

说明：
- 这些扩展查询不是同权重硬规则
- 这里的 `政 / 厅 / 国家 / 中国 / 人民`，应理解为 `icp.name="政"` 这类 ICP 字段查询，不是普通标题/正文词面命中
- 它们是高价值查询面的补充集合
- 最终仍要看命中的主体到底更像公立/政务/公共事业，还是商业教育/培训/普通企业语境

### 当前扩展结论（UReport / UReport2）
- 扩展后并非完全 0 信号
- `教育` 相关命中存在
- 但当前新命中主要集中在商业教育咨询主体，而不是教育局/学校/大学/政府/医院/水务这类更强高价值对象
- `.gov.cn` / `.edu.cn` / `.org.cn` 当前仍未形成有效补强

### 收口标准
如果出现：
- 有一定规模
- 识别面切换后可稳定命中
- 但扩展高价值查询面后仍然主要是商业主体或高价值信号持续弱

则更接近：
- 对照样本
- 中等现实部署
- 不自动抬入最高优先级池

---

## 模式 C：title clue 主识别面 + 高价值场景提前出现路线（MaxKey 型）

适用特征：
- 主产品名直打为 0 或明显偏弱
- title clue 比产品名更像真实入口
- 总量不算超大盘
- 但高价值场景可能较早出现

### Hunter
1. 先试主产品名
   - `app.name="MaxKey"`
2. 若弱/0，快速切到 title clue
   - `web.title="MaxKey"`
3. 若 title clue 有结果，再补高价值场景枪
   - `web.title="MaxKey" and icp.name="县"`

### FOFA
1. 先试标题层
   - `title="MaxKey"`
2. 再试 `.gov.cn` 补枪
   - `title="MaxKey" && host=".gov.cn"`

### 收口标准
如果出现：
- 主产品名不稳
- 但 title clue 稳
- 总量中等
- 且已有具体高价值落地样本

则更接近：
- `moderate-real-world-signal`
- 而不是因为总量不大就直接压成弱样本

---

## 模式 D：提前停止规则

遇到下面任一情况，应及时停手：

1. 产品名探针 0，切 1~2 个识别面后仍然弱
2. 规模信号中等或偏弱，且政务/县域信号持续为 0
3. 已经足够得出“不是强微步偏好样本”的判断
4. 已经有跨平台补强，不需要再继续堆明细

一句话：

> 资产证据层的目标不是把每个目标都查透，而是尽快判断它是不是更值得优先做。

---

## 固定保留的查询技巧

### 1. `.gov.cn` 补强
这条必须保留：
- FOFA：`host=".gov.cn"`

它是 Hunter `icp.*` 路线之外的重要跨平台补强。

### 2. 识别面切换
这条也必须保留：
- 产品名 != 最佳识别面
- 允许切到别名 / 组件名 / 标题 / 正文

这是 `UReport / UReport2` 样本给出的硬经验。

---

## 当前样本锚点

### ZLMediaKit
- Hunter `app.name="ZLMediaKit"` 强
- Hunter `... and icp.name="县"` 强
- FOFA `app="ZLMediaKit"` 强
- FOFA `... && host=".gov.cn"` 强

### UReport / UReport2
- `app.name="UReport"` 弱/0
- `app.name="UReport2"` 有中等规模
- `title="UReport Console"` 有中等规模
- 政务信号当前弱

### MaxKey
- `app.name="MaxKey"` 弱/0
- `web.title="MaxKey"` 有中等规模
- `title="MaxKey"` 有中等规模
- `web.title="MaxKey" and icp.name="县"` 已出现具体县域教育样本
- `.gov.cn` 当前弱/0，但不应因此抹掉高价值场景线索

---

## 一句话版

> 先决定“用什么识别面”，再决定“它是不是强现实样本”；不要把所有目标都硬查成 ZLMediaKit 那一类，也不要因为总量不大就错过 MaxKey 这种“高价值场景提前出现”的样本。
