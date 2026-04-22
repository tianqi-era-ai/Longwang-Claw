# OpenClaw / Telegram 实装入口设计（当前版本）

## 目标

把当前已经验证可工作的 Super8 / Loop9 后台长跑流程，收束成更接近可直接使用的 OpenClaw / Telegram 入口组合。

---

## 推荐对外入口

### 1. 启动长任务

Skill / slash command 名：

- `loop9-wrapped-audit`

用途：
- 从 Telegram / OpenClaw 触发一个标准化的 Super8 长任务
- 内部统一调用 wrapper

目标调用：

```bash
cd ~/.openclaw/workspace/Super8
./.opencode/_scripts/loop9_authorized_review.py <local-target-path>
```

### 2. 查看状态

Skill / slash command 名：

- `loop9-status`

用途：
- 查看最新长任务状态
- 汇总 observe / run_dir / 报告文件 / session

目标调用：

```bash
cd ~/.openclaw/workspace/Super8
./.opencode/_scripts/loop9_status.sh
```

---

## Telegram 侧推荐交互模型

### 启动时

用户：

```text
/loop9-wrapped-audit ~/.openclaw/workspace/targets/pikachu
```

系统行为：
- 启动 wrapper
- 回复一条简短确认
- 明确说明这是后台长跑型任务
- 告知后续会在有意义进展或最终结果时通知

### 查询时

用户：

```text
/loop9-status
```

系统行为：
- 读取标准状态脚本输出
- 汇总成短消息
- 如果已有报告，优先指向报告路径

---

## 当前最适合的产品假设

> Telegram 不承担“复杂执行编排”，只承担“启动”和“查状态”。

也就是说：
- 启动：`loop9-wrapped-audit`
- 查询：`loop9-status`
- 执行：wrapper + OpenCode + Loop9
- 通知：heartbeat + 模板口径

这是目前最稳、最容易维护的形态。

---

## 为什么暂时不建议做得更复杂

当前还不建议直接在 Telegram 入口里加入：
- 自动 clone GitHub URL
- 自动切换多种底层模式
- 自动在 chat 里拼复杂 prompt
- 自动对不同类型项目做复杂分流

原因：
- 先把一个稳定主路径做扎实更重要
- 复杂入口会掩盖底层问题
- wrapper 已经是统一稳定层，应优先复用

---

## 当前建议的最小可实装组合

- `workspace/skills/loop9-wrapped-audit/SKILL.md`
- `workspace/skills/loop9-status/SKILL.md`
- `Super8/.opencode/_scripts/loop9_authorized_review.py`
- `Super8/.opencode/_scripts/loop9_status.sh`

这是最小、清晰、可维护的两命令体系。

---

## 下一步建议

如果继续推进实装，下一步应该优先做：

1. 检查 OpenClaw 是否能正确加载 workspace/skills 下这两个 skills
2. 在 Telegram 环境里验证：
   - `/loop9-wrapped-audit <path>`
   - `/loop9-status`
3. 再根据真实使用感受决定：
   - 是否增加更多参数
   - 是否增加 GitHub URL materialize 流程
   - 是否增加结果摘要专用入口

---

## 当前一句话结论

> 当前最适合进入 OpenClaw / Telegram 实装阶段的，不是一个巨型万能命令，而是一对清晰的命令：一个负责启动长任务，一个负责查看状态。
