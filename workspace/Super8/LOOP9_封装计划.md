# LOOP9 封装计划（面向小龙虾 / Telegram 斜杠命令）

## 目标

把当前 Super8 的 Loop9 本地流程进一步收敛为：

- 一个**最小修改后的 controller 方案**（先提出，不直接替换）
- 一个未来可在 OpenClaw / Telegram 使用的 slash command 入口
- 明确约定：**主要调用应该经过 SH wrapper，而不是每次手工拼命令**

---

## 1. Controller 最小修改提案（先提案，不直接切换）

建议保留现有 `loop9-controller.md`，新增一个本地 fixed 变体：

- `.opencode/agents/loop9-controller.fixed.md`

它的目标不是重写整个流程，而是只补几条硬规则：

1. 禁止再次调用 `skill(name="loop9")`
2. 禁止再次触发 `/loop9` 或任何等价 command/skill 入口
3. 收到“读取并执行任务文件”的消息后：
   - 先 read 文件
   - 直接创建 `temp/loop9/<run_id>/...`
   - 直接调用 `loop9-solver`
4. 不先总结、不先反问、不先转手

这是一种**手术刀式**最小改法。

---

## 2. 小龙虾 / Telegram slash command 封装方向

推荐封装思路：

### 外层 slash command

- `/loop9_wrapped_audit <local-target-path>`

### 内层唯一稳定入口

统一调用：

- `Super8/.opencode/_scripts/loop9_authorized_review.sh`

原因：

- prompt 文件生成逻辑已经集中在 wrapper
- 本地路径填充逻辑已经集中在 wrapper
- mode 选择逻辑已经集中在 wrapper
- 后续修 bug 只需要改 wrapper，而不是改多个入口

### 重要隔离原则

这个面向小龙虾 / Telegram 的 skill 或 slash command，**只应该作为外层入口存在**。

必须避免：

- 被本地 `loop9` command 反向引用
- 被 `loop9-controller` / `skill(name="loop9")` 这类内部路径再次吞进去
- 变成另一个会被本地 Loop9 流程递归调用的“loop9 风格 skill”

换句话说：

> 它是 Telegram / OpenClaw 的外部入口，不是本地 Loop9 runtime 的内部组成部分。

---

## 3. 已知坑（必须写进封装说明）

### 坑 1：不要手工长期维护复杂 `opencode ...` 调用

- 应以 wrapper 作为主入口
- Telegram / slash command 也应该尽量调用 wrapper

### 坑 2：`command` 模式不要带前导 slash

正确：

```bash
opencode run --command loop9 ...
```

错误：

```bash
opencode run --command /loop9 ...
```

### 坑 3：入口消息不宜直接展开大段 prompt 正文

- 尤其在 oh-my-opencode 环境下
- 容易触发关键词模式注入 / analyze-mode 污染
- 应尽量只传：路径 + 动作

### 坑 4：日志里的 `Skill "loop9"` 不一定是旧 skill 残留

更大的可能是：

- runtime 通过 `skill(name="loop9")` 统一解析了 command
- 实际来源是 `.opencode/command/loop9.md`

### 坑 5：当前 `loop9-controller` 可能再次绕回 `skill loop9`

- 这会阻止它直接进入 run_dir + solver/validator/refiner 主流程
- 这也是当前最核心的问题之一

### 坑 6：不要过早判定 command 路线失败

在当前环境里，command 路线常见的前期表现是：

1. 先进入 session
2. 先读 prompt / task file
3. 先建立 todo / 做 glob / read / 仓库结构探索
4. 然后才逐步进入 Loop9 标准落盘

所以：

- 30~60 秒内看不到完整 `temp/loop9/<run_id>/...` 不代表失败
- 5 分钟更适合观察 run_dir 是否出现
- 15~20 分钟更适合判断是否真的没进入标准闭环

---

## 4. 当前建议策略

### 默认策略

- wrapper 默认仍走 `agent` 分支
- `command` 分支保留为实验/排查用途

### 如果后续修复 controller

- 优先切到 `loop9-controller.fixed.md`
- 再考虑把 wrapper 默认 agent 指向 fixed 版本
- 在此之前，不应过度承诺 command 分支的稳定性

---

## 5. 下一步可做的事

1. 让你确认 `loop9-controller.fixed.md` 这版最小提案是否接受
2. 如果接受：
   - 再把 wrapper 接到 fixed controller
   - 再重新跑本地 Loop9 闭环验证
3. 如果本地闭环跑通：
   - 再做 OpenClaw / Telegram slash command 真正落地

---

## 6. 当前一句话原则

> 先把本地 wrapper + fixed controller 跑稳，再把它封成小龙虾 slash command；不要反过来把一个还不完全稳的底层先包成更容易触发的外层入口。
