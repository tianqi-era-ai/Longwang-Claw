# 2026-03-16 HEARTBEAT × loop9-status × SubAgent 小设计稿

## 目标

把 heartbeat 的职责收束为**调度与汇报框架**，而不是承载 `loop9-status` 的具体展示格式；
同时让 `loop9-status` 继续保持**通用技能**身份：

- 可被**人手动调用**
- 可被**heartbeat 定时触发**
- 不为某一种触发来源做狭窄绑定

其中：

- 红黄绿灯 / 卡片式摘要，只属于 `workspace/skills/loop9-status/SKILL.md`
- `HEARTBEAT.md` 不直接内嵌该格式规则
- heartbeat 调 `loop9-status` 时，优先采用 **SubAgent 模式**，以获得隔离、稳态、低耦合

---

## 已确认约束（来自用户本轮口径）

1. `loop9-status` 是**通用技能**，不是 heartbeat 专属技能
   - 既可被手动命令触发
   - 也可被 heartbeat 触发
   - 不要把它写成“只服务 heartbeat”的窄接口

2. 红黄绿灯样式只影响 `loop9-status` skill
   - 不扩散到整个 `HEARTBEAT.md`
   - `HEARTBEAT.md` 不负责定义这套展示层细节

3. heartbeat 中调用相关 skill 时，优先考虑 **SubAgent 模式**
   - 目的是隔离、避免阻塞、降低上下文污染
   - 不让 heartbeat 主线程承载过多具体任务细节

4. `loop9-status` 被 heartbeat 定时调用时，需要有**最小间隔保护**
   - 与上一次被 heartbeat 定时调用相隔 **10 分钟及以上**，才允许再次调用
   - 目的是避免极端情况下高频连续触发

---

## 问题复盘（为什么需要这次设计）

历史上 heartbeat 中的 Loop9 检查曾经稳定输出红黄绿灯卡片；
但在一次故障窗口之后，出现了两层问题：

1. 一段时间 heartbeat 连正常回复都没有（连续 timeout）
2. 恢复后虽然能再次跑状态检查，但不再稳定读取 / 服从 `loop9-status` skill，导致格式漂移，不再稳定输出红黄绿灯卡片

说明当前链路中存在两个结构性薄弱点：

- **skill 触发链不够硬**：heartbeat 恢复后可能直接退化成“读 HEARTBEAT.md + 直接跑脚本 + 临场总结”
- **展示规则归属不够稳**：关键格式只存在于 skill 中，但 heartbeat 又没有强约束自己必须走 skill

因此，需要重新把边界和触发规则设计清楚。

---

## 职责分层（推荐）

## 1. `HEARTBEAT.md` 的职责

只负责：

- 定义有哪些需要周期检查的项目
- 定义各项目的触发条件 / 节流条件 / 是否需要汇报
- 定义应调用哪个 skill / 子任务入口
- 定义 heartbeat 主线程如何处理“无变化 / 有变化 / 子任务失败”

不负责：

- 具体状态摘要格式（例如红黄绿灯卡片）
- 具体业务字段解释
- 具体脚本输出的人类可读封装细节

### 换言之

`HEARTBEAT.md` 是**调度层规范**，不是 `loop9-status` 的展示模板文件。

---

## 2. `loop9-status` skill 的职责

负责：

- 运行 canonical status script
- 解释 Loop9 状态
- 把状态总结成适合用户阅读的最终摘要
- 维护自己的输出风格（含红黄绿灯）

### 输出风格归属

以下内容应继续只存在于 `workspace/skills/loop9-status/SKILL.md` 中：

- `🟢 / 🟡 / 🔴` 的语义
- 卡片式摘要结构
- `一句话总览`
- mobile-friendly 输出偏好

这样可保证：

- 手动调用 `loop9-status` 时风格一致
- heartbeat 调用 `loop9-status` 时风格一致
- 风格只在一个地方维护

---

## 3. heartbeat 主线程 / 调度层 的职责

负责：

- 判断本轮是否需要做 Loop9 检查
- 判断是否满足最小触发间隔（10 分钟）
- 若满足，则启动 `loop9-status` 子任务
- 获取子任务结果后，决定：
  - 发给用户
  - 还是保持安静

### 不负责

- 自己拼装 Loop9 红黄绿灯卡片
- 自己重写 `loop9-status` 的展示逻辑
- 自己直接替代该 skill 做人类可读总结

---

## SubAgent 方案（推荐形态）

## 调度原则

heartbeat 发现本轮需要做 Loop9 状态检查时：

- 不直接在主线程里展开大量 Loop9 状态解释
- 而是以 **SubAgent / isolated task** 的方式调用一个专门子任务
- 该子任务负责：
  - 读取 / 遵循 `loop9-status` skill
  - 生成面向用户的状态摘要

## 优点

1. **隔离性更好**
   - 不让 heartbeat 主线程背太多 Loop9 上下文

2. **不易阻塞其它心跳项**
   - 后续若 heartbeat 还要挂邮件、日历、天气等检查，不容易互相干扰

3. **恢复性更好**
   - 某一次子任务失败，不至于污染整个 heartbeat 线程的思路

4. **技能边界更清楚**
   - `loop9-status` 的业务解释和展示层，留在它自己的技能上下文里完成

---

## 10 分钟最小间隔规则

## 规则本身

仅当 `loop9-status` 是**被 heartbeat 定时触发**时，增加以下节流：

- 若距离上一次 heartbeat 触发的 `loop9-status` 调用 **不足 10 分钟**
- 则本轮**不再触发**该 skill

## 适用范围

- 只限制 heartbeat → loop9-status 的定时调用路径
- **不限制人工手动调用** `loop9-status`
- **不限制其它触发源**（如未来显式命令、专项任务）

## 目的

避免极端情况下出现：

- heartbeat 窗口抖动
- 重试堆叠
- 多轮连续高频触发同一个 Loop9 检查任务

## 需要的最小状态

建议由 heartbeat 调度层维护一份最小记录（后续实现时再决定放哪里），至少包含：

- 上一次 heartbeat 触发 `loop9-status` 的时间
- 上一次是否成功拿到子任务结果
- 上一次是否实际发给用户

注意：

- 这里只是**节流状态**
- 不是再次把 `loop9-status` 的业务状态摘要塞进 heartbeat 调度层

---

## 推荐的执行链

### 人工手动触发时

用户手动调用：

- `/loop9_status`
- 或其它明确入口

执行链：

- 直接进入 `loop9-status` skill
- 由 skill 自己输出红黄绿灯卡片

### heartbeat 触发时

heartbeat 主线程：

1. 判断 Loop9 是否属于本轮需检查项
2. 判断距离上次 heartbeat 触发 `loop9-status` 是否 >= 10 分钟
3. 若满足：
   - 启动 `loop9-status` 子任务（SubAgent）
4. 子任务：
   - 运行 `loop9-status` 技能逻辑
   - 产出红黄绿灯卡片摘要
5. heartbeat 主线程：
   - 根据子任务结果与本轮策略，决定是否发给用户

---

## 明确避免的错误实现

### 1. 不要把红黄绿灯模板复制进 `HEARTBEAT.md`

否则会出现：

- `loop9-status` 里一份
- `HEARTBEAT.md` 里又一份
- 后续两边漂移

### 2. 不要让 heartbeat 主线程直接替代 `loop9-status`

否则会退化成：

- heartbeat 自己跑脚本
- heartbeat 自己解释字段
- heartbeat 自己写卡片

这会再次把职责边界搞混。

### 3. 不要为了 SubAgent 再堆复杂中间框架

应保持薄封装：

- heartbeat 只做调度
- subagent 只做 skill 执行
- 不再额外建设 registry / protocol / state machine 之类重层

---

## 设计结论（当前推荐）

当前推荐采用：

- `HEARTBEAT.md` = 调度层
- `loop9-status` = 通用技能 + 唯一展示规则归属
- heartbeat 调用 `loop9-status` 时使用 **SubAgent 模式**
- 增加 heartbeat → `loop9-status` 的 **10 分钟最小触发间隔**

这套设计同时满足：

- 手动调用与定时调用并存
- 红黄绿灯格式只归属到 `loop9-status`
- heartbeat 不再背负具体展示逻辑
- 避免极端情况下高频重复触发

---

## 下一步（如果进入实现）

建议实现顺序：

1. 先改 `HEARTBEAT.md`
   - 明确 Loop9 检查项应调用 `loop9-status` 子任务
   - 明确 10 分钟最小间隔规则
   - 不写红黄绿灯模板细节

2. 再确认 `loop9-status` skill
   - 保持 / 强化红黄绿灯卡片输出规范
   - 确保手动与 heartbeat 调用共用同一输出逻辑

3. 最后实现 heartbeat → SubAgent 调度逻辑
   - 只做薄封装
   - 不额外发散成复杂框架
