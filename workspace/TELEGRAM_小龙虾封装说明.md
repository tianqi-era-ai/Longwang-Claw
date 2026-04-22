# Telegram / 小龙虾 封装说明（Super8 / Loop9）

## 目标

把当前已经验证可工作的 Super8 Loop9 流程，整理成一个适合通过 OpenClaw / Telegram 调用的外层入口。

这里的核心不是“重新发明命令”，而是：

- 统一入口
- 统一说明
- 统一避坑
- 统一长任务处理方式

---

## 一句话原则

> Telegram / 小龙虾 侧只做 **外层入口**；真正执行必须统一走 `Super8/.opencode/_scripts/loop9_authorized_review.py`。

也就是说：

- Telegram 负责“触发”
- Wrapper 负责“真正执行”
- OpenCode / Loop9 负责“长跑与产出”

---

## 推荐的对外命令名

建议对外暴露的 skill/slash command 名称：

- `loop9-wrapped-audit`

对应 skill 文件：

- `workspace/skills/loop9-wrapped-audit/SKILL.md`

这个名字的优点：

- 不直接叫 `loop9`
- 不和本地 command `loop9` 混名
- 明确表达“这是 wrapper 外层入口，不是底层 runtime 组件”

---

## 推荐调用方式

用户在 Telegram / 小龙虾侧可以使用：

```text
/loop9-wrapped-audit /absolute/path/to/local/repo
```

或者在需要切换审计口径时，显式带上 policy：

```text
/loop9-wrapped-audit --policy weibu-submission /absolute/path/to/local/repo
```

例如：

```text
/loop9-wrapped-audit ~/.openclaw/workspace/targets/pikachu
```

```text
/loop9-wrapped-audit --policy weibu-submission ~/.openclaw/workspace/targets/pikachu
```

---

## 内部唯一稳定入口

真正执行时，应该统一调用：

```bash
cd ~/.openclaw/workspace/Super8
./.opencode/_scripts/loop9_authorized_review.py [--policy internal-full-audit|weibu-submission] <local-target-path>
```

不要在 Telegram 侧重写复杂命令，不要手工重组 prompt，不要在 chat 里重新拼 `opencode ...`。

原因：

- prompt 文件生成逻辑在 wrapper 里
- 路径填充逻辑在 wrapper 里
- mode 选择逻辑在 wrapper 里
- 后续 bugfix / 规避逻辑也应该继续收敛在 wrapper 里

---

## 长任务原则（必须写死）

这一类任务必须当成 **后台长跑型任务** 处理。

推荐统一状态检查命令：

```bash
cd ~/.openclaw/workspace/Super8
./.opencode/_scripts/loop9_status.sh
```

后续 heartbeat / 通知 / 人工查看都应优先复用这条标准状态入口。

### 时间预期

- 1-2 小时：正常
- 3-5 小时：也可能出现

### 操作原则

- 启动后不要因为几十秒或几分钟内没有完整结果就判定失败
- 不要手动 kill
- 让任务自己运行到完成 / 异常 / 超时
- 有意义的新进展时再通知用户

### 为什么

因为当前这套环境下，尤其是 command 路线，常见前期表现是：

1. 先进入 session
2. 先读 prompt / task file
3. 先做 glob / read / repo exploration / todos
4. 然后才进一步长出报告或 Loop9 标准产物

所以：

> 短时间看不到完整产物，不代表失败。

---

## 推荐观察窗口

### 1 分钟内
只适合判断：
- 有没有启动
- 有没有读 prompt
- 有没有开始探索

### 5 分钟内
更适合看：
- 有没有开始创建 run_dir
- 有没有出现初步产物

### 15-20 分钟
更适合判断：
- 是否真的开始产出 usable report
- 是否开始进入较完整的标准化闭环

---

## 当前已验证可用的现实情况

以 Pikachu 为例，command 路线已经证明：

- 可以长时间运行
- 可以完成 repo 结构探索
- 可以产出实际可读结果：
  - `temp/pikachu-audit-report.md`
  - `temp/pikachu-audit-medium-notes.md`
  - `temp/pikachu-audit-shared-context.md`

这说明：

> command 路线可以视为“可工作、可长跑、可产出结果”的现实路径。

虽然它未必每次都严格长成最理想的 `temp/loop9/<run_id>/...` 树，但从实用角度已经可用。

---

## 易踩坑（必须提醒）

### 坑 1：不要手工长期维护 ad-hoc 命令

错误思路：
- 每次在聊天里重新拼 `opencode ...`
- 每次自己组织 prompt 文字

正确思路：
- 始终通过 wrapper 进入

### 坑 2：不要把 Telegram 外层入口做成内部 runtime 组件

也就是说，面向 Telegram / 小龙虾的 skill：

- 不能再被本地 `loop9` command 反向引用
- 不能被 `skill(name="loop9")` 这种内部路径吞进去
- 不能变成“另一个本地 loop9 风格 skill”

它应该始终只是：

> 外部入口

### 坑 3：command 模式不要带前导 slash

正确：

```bash
opencode run --command loop9 ...
```

错误：

```bash
opencode run --command /loop9 ...
```

### 坑 4：不要在入口消息里展开大段 prompt 正文

大段正文容易触发：
- analyze-mode 污染
- 关键词注入
- 非预期前置处理

更好的做法：
- 入口只传：路径 + 动作
- 正文都在任务文件里

### 坑 5：不要把“看起来慢”误判成“失败”

这是当前最常见误区。

---

## 心跳/后台跟进建议

已经建议通过 heartbeat 检查：

- `Super8/temp/loop9-observe/`
- `Super8/temp/loop9/`
- latest OpenCode session for `Super8`
- `Super8/temp/` 下的最终报告文件

如果有新进展：
- 给用户短通知
- 如果有最终报告：给出摘要 + 路径

---

## 当前推荐定性

当前这套流程最适合被描述为：

> 一个通过 Telegram / 小龙虾触发、通过 wrapper 执行、由 OpenCode/Loop9 在后台长跑完成、并由 heartbeat 跟进通知的标准化本地审计工作流。

---

## 未来推荐的对外说法

可以直接对用户说：

- 这是一个**后台长跑型**工作流
- 启动后不需要盯着等
- 有进展会通知
- 有结果会给摘要和路径
- 标准入口是 slash command，底层统一通过 wrapper 跑

## 配套文件

当前已经准备好的相关文件：

- `workspace/skills/loop9-wrapped-audit/SKILL.md`
- `workspace/skills/loop9-status/SKILL.md`
- `workspace/OpenClaw_实装入口设计.md`
- `workspace/TELEGRAM_小龙虾封装说明.md`
- `Super8/START_HERE_Loop9.md`
- `Super8/TELEGRAM_通知模板.md`
- `Super8/TELEGRAM_默认行为规范.md`
- `Super8/下一步计划.md`
- `Super8/README.loop9-local.md`
- `Super8/LOOP9_封装计划.md`
