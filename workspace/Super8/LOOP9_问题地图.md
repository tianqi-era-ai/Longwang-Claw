# LOOP9 问题地图 / 决策地图

> 目标：把当前 Super8 / Open Code / oh-my-opencode / Loop9 相关问题压缩成一份可追踪、可决策、可交接的说明。

---

## 1. 当前目标

当前真正要达成的是：

1. 让 `Super8/.opencode/_scripts/loop9_authorized_review.py` 成为**稳定主入口**
2. 默认入口能够在本机：
   - 生成 prompt 文件
   - 启动 Loop9 流程
   - 落盘到 `temp/loop9/<run_id>/...`
3. 后续再考虑把这套流程通过 OpenClaw 封装成 Telegram / slash command 入口

---

## 2. 已确认事实

### 2.1 环境已搭好

这台机器上已经完成：

- `opencode-ai 1.2.20`
- `oh-my-opencode 3.10.0`
- `~/.config/opencode/` 已从仓库备份恢复
- `noop-lsp.js` 的旧绝对路径已修到本机 home 目录
- `Super8/.opencode/` 已被 Open Code 识别

### 2.2 Loop9 项目资产是存在且可加载的

已确认存在：

- `.opencode/command/loop9.md`
- `.opencode/agents/loop9-controller.md`
- `.opencode/agents/loop9-solver.md`
- `.opencode/agents/loop9-validator.md`
- `.opencode/agents/loop9-refiner.md`

### 2.3 Wrapper 已存在

主脚本：

- `.opencode/_scripts/loop9_authorized_review.py`

当前职责：

- 生成 prompt 文件
- 将目标路径写入 prompt
- 根据模式选择：
  - `agent` 分支
  - `command` 分支

### 2.4 `command` 模式 CLI 参数已确认

错误写法：

```bash
opencode run --command /loop9 ...
```

正确写法：

```bash
opencode run --command loop9 ...
```

即：**非交互 CLI `--command` 不要带前导 `/`**。

### 2.5 `skill(name="loop9")` 可以解析 command

已从 oh-my-opencode 运行时代码中确认：

- `skill(name="item-name")` 可以用于 commands
- commands 在这个入口下要**省略前导 slash**

所以运行时里出现：

- `Skill "loop9"`

并不意味着它一定读到了一个独立的 Loop9 SKILL 文件。
它很可能拿到的是：

- `.opencode/command/loop9.md`

### 2.6 `skills_broken/` 里的旧 Loop9 skill 不是当前主嫌疑源

仓库里可见的旧 skill 主要在：

- `.opencode/skills_broken/loop9x_only_preHandle（一直会干扰循环流、会严重偏离）/SKILL.md`

它是废弃/干扰性资产，但**不是当前最主要来源**。
当前更主要的是 command → runtime skill 统一解析路径。

---

## 3. 已观察到的实际行为

### 3.1 `command` 分支行为

`./.opencode/_scripts/loop9_authorized_review.py --mode command '<target>'`

现象：

1. 能生成 prompt 文件
2. 能进入 `loop9-controller`
3. 能看到运行时出现：
   - `Skill "loop9"`
4. 但**不会稳定创建新的**：
   - `temp/loop9/<run_id>/original_goal`
   - `shared_context`
   - `solution_v*`
   - `validation_report_v*`

### 3.2 `agent` 分支行为

`./.opencode/_scripts/loop9_authorized_review.py '<target>'`

现象：

1. 能进入 `loop9-controller`
2. 在 prompt wording 优化后，不再只是简单反问“你想让我怎么处理这个文件”
3. 但依然会出现：
   - controller 读取任务文件后
   - 再尝试走 `skill(name="loop9")`
4. 因而**仍未稳定进入**它自己的 run_dir + solver/validator/refiner 主流程

---

## 4. 当前最小问题定义

当前的问题不是：

- 环境没装好
- 仓库没识别到 `.opencode`
- prompt 文件路径错了
- wrapper 完全失效
- 旧 Loop9 skill 残留导致所有问题

当前最小而准确的问题定义是：

> `loop9-controller` 在当前环境中，倾向于再次调用 `skill(name="loop9")`，而不是直接执行其自身定义好的 orchestration 主流程。

---

## 5. 为什么这件事重要

因为 `loop9-controller.md` 的设计目标，本来就是：

1. 创建 `run_dir`
2. 直接调用 `loop9-solver`
3. 再循环调用 `loop9-validator` / `loop9-refiner`
4. 最终合并输出

按这个设计，它**不需要**再去通过 `skill loop9` 绕一圈。

所以当前异常点不是“不会读文件”，而是：

> **读完之后没有直接编排，而是再次寻找 `loop9` 入口。**

---

## 6. 当前已踩过的坑

### 坑 1：把 `/loop9 ...` 整段塞进 `--prompt`

这是不够正统的写法。
虽然某些场景下看起来能跑，但不适合当长期稳定方案。

### 坑 2：`--command /loop9`

这是错误写法。
CLI command 模式应使用：

- `--command loop9`

### 坑 3：入口消息里直接展开大量任务正文

如果入口消息直接携带大量“分析”“审计”“研究”等字眼，容易被 oh-my-opencode 的关键词预处理 / mode 注入机制污染。

当前规避策略：

- 入口消息只传“读取并执行某个任务文件路径”
- 具体要求都放进任务文件正文里

### 坑 4：误把 `Skill "loop9"` 理解为旧 skill 残留

这是最容易误判的一点。

当前更准确的理解是：

- runtime 允许 `skill(name="loop9")` 去解析 command
- 所以日志里的 `Skill "loop9"` 可能只是 command 的另一种调用入口表象

---

## 7. 当前主入口建议

### 默认主入口

```bash
cd ~/.openclaw/workspace/Super8
./.opencode/_scripts/loop9_authorized_review.py '<本地项目路径>'
```

当前默认：

- `agent` 分支

原因：

- 相比 command 分支更稳
- 前置污染风险更低
- 更适合作为长期入口

### command 分支当前定位

```bash
./.opencode/_scripts/loop9_authorized_review.py --mode command '<本地项目路径>'
```

当前定位：

- 实验模式
- 不作为默认长期入口
- 可用于对比测试与排查

---

## 8. 现在不建议做的事

### 8.1 不建议现在就封装 OpenClaw slash command 到 Telegram

原因：

- 底层 Loop9 主流程还没彻底稳
- 如果过早封装外层入口，只会把当前底层问题变成“更方便重复触发的问题”

### 8.2 不建议继续把时间花在 command 分支的前置污染细节上

原因：

- user 已明确表示这类小 bug 不值得长期纠缠
- oh-my-opencode 官方后续可能修复
- 当前更高价值的是把默认 agent 主入口打通

---

## 9. 现在值得优先做的事

### 9.1 优先方向

如果后续继续修，最值得做的是：

> 让 `loop9-controller` 在读取任务文件后，**直接执行自身编排逻辑**，不要再通过 `skill(name="loop9")` 绕回 command 入口。

### 9.2 这件事为什么是最小刀法

因为：

- wrapper 已经基本成型
- prompt 文件路径策略已经清楚
- 环境安装没问题
- 运行时 command/skill 语义也已经看懂

剩下最集中的问题点，就是 controller 的这个执行决策。

---

## 10. 决策建议（给未来的自己/会话）

### 若目标是“先能长期稳定用”
优先策略：

1. 继续以 `agent` 分支作为默认入口
2. 若要修，只修 controller 的“再转 skill loop9”行为
3. 不碰大范围 oMo 规则 / hook

### 若目标是“继续研究为什么会这样”
研究重点：

1. `loop9-controller` 为什么偏向 `skill(name="loop9")`
2. 它在什么条件下会直接创建 run_dir
3. runtime 对 command / skill 的统一解析细节

### 若目标是“以后做 Telegram slash command”
前置条件：

- 先让本地默认入口稳定
- 再把 slash command 作为外层触发器封装
- slash command 应以调用主 SH 脚本为主，而不是自己重新拼复杂 prompt

---

## 11. 当前一句话总结

> Super8 的 Loop9 问题已经从黑盒缩小成了一个很具体的执行偏差：`loop9-controller` 读到任务后会再次通过 `skill(name="loop9")` 解析已有 command，而不是直接进入自身的 orchestration 主流程。环境、路径、wrapper、command 语义都已经基本摸清；后续若要继续修，最值得动的就是 controller 的这一个点。
