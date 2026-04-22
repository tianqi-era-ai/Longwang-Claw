# `loop9_authorized_review.py` 必须保留行为清单

目的：为后续把 `loop9_wrapped_audit` 迁移到公共 OpenCode runner core 提供**护栏**。这份清单不是理想化设计，而是基于当前经实践验证过的行为总结出来的“不能随便丢”的点。

---

## 1. 入口与 CLI 兼容性必须保留

- 文件名继续保留：`Super8/.opencode/_scripts/loop9_authorized_review.py`
  - 虽然实现已是 Python，但文件名与调用点不能轻率改。
- CLI 形状必须保留：
  - `--mode command|agent`
  - `--transport tmux|direct`
  - `--policy internal-full-audit|weibu-submission`
  - `<LOCAL_TARGET_PATH>`
  - `[PROMPT_OUT_PATH]`
- 默认值必须保守保持：
  - `mode=command`
  - `transport=tmux`
  - `policy=internal-full-audit`

**原因**：这些外部接口已经被文档、习惯和上层技能依赖。

---

## 2. `loop9` 的关键调用组合必须保留

对 Loop9 这条线，必须保留这一经验组合：

```bash
opencode run --print-logs --command loop9 --agent loop9-controller
```

### 必须保留的原因

- `--command loop9` 是当前实战中最稳定的主入口
- 同时套 `--agent loop9-controller` 是为了进一步稳定 Loop9 的多 SubAgent / 循环编排
- 这虽然看起来不够“教科书式优雅”，但它是当前环境里验证过的关键成果

### 明确禁止的轻率改动

- 不要因为“看起来重复”就删掉 `--agent loop9-controller`
- 不要把这条线改回仅 `--agent loop9-controller`
- 不要因为抽 core 就把 loop9 的特例抹平
- 不要把这层经验只留在文档里；代码里也必须保留显眼的维护注释/常量，明确提醒后续维护者不要随手改这个参数

---

## 3. 目标元信息注入必须保留

当前 wrapper 会在 prompt 文件开头注入权威目标元信息，包括：

- 审计目标源码项目名
- 审计目标源码根目录
- run_id 命名规则
- 明确禁止把 `Super8` 误当作审计目标名

### 这层注入必须保留

因为它直接防止以下真实错误：
- Loop9 内部把当前编排仓库名 `Super8` 误用为 run_id 目标名
- 审计结果目录命名错位
- 后续 heartbeat / observe / 结果检索混乱

---

## 4. prompt 文件落盘与路径约定必须保留

必须保留：

- prompt 文件真正写入磁盘，而不是只以内存字符串传给 opencode
- 默认目录：
  - `Super8/temp/loop9-prompts/`
- 默认文件名带：
  - target name
  - policy suffix（必要时）
  - timestamp

### 原因

- 方便调试、回溯、复盘
- 长任务失败时，prompt 文件本身就是关键现场证据
- 后续手工复跑、比对 prompt 差异时也依赖这个文件

---

## 5. observe 目录体系必须保留

必须保留独立 observe dir，默认在：

- `Super8/temp/loop9-observe/`

并保留这些基础文件：

- `run.meta`
- `prompt.txt`
- `command.txt`
- `run_and_capture.sh`
- `started_at.txt`
- `finished_at.txt`
- `opencode.exit_code`
- `opencode.typescript.log`
- `opencode.clean.log`
- `observe.summary.json`
- `tmux.session.txt`
- `tmux.attach.txt`
- `launch.summary.txt`
- `session.id`（若能提取）
- `session.export.json` / `session.export.stderr.log`（若成功导出）

### 原因

这不是装饰，而是：
- 长任务追踪的基石
- heartbeat / status 检查的主要数据源
- 问题排查时的第一现场

---

## 6. tmux 默认优先级必须保留

必须继续保持：
- `tmux` 是默认 transport
- 长任务默认走 tmux detached session
- 启动后返回 attach 信息

### 原因

Loop9 审计本身是典型长任务：
- 1~2 小时正常
- 3~5 小时也可能
- 中途可能要看 pane 输出、做调试、观察 session 状态

如果丢掉 tmux 默认优先级，稳定性和可观测性会明显下降。

---

## 7. `script` / `tee` 双路径捕获必须保留

当前 wrapper 有一个很关键的兼容处理：

### 优先
如果是完整 tty 且 `script` 可用：
- 用 `script -q ...` 捕获 typescript log

### fallback
如果不是 tty，或者 `script` 不适用：
- 降级到 `tee`

### 这层逻辑必须保留

因为这是为了处理真实环境里出现过的坑：
- `tcgetattr/ioctl: Operation not supported on socket`
- direct / 非交互 / 非 tty 场景下 `script` 崩掉

不能为了代码更短就删掉。

---

## 8. session id 提取与 export helper 必须保留

当前 wrapper 会：

1. 从 clean log 里正则提取 `session.id`
2. 如果提取成功，再运行 `opencode export`
3. 生成：
   - `session.export.json`
   - `session.title.txt`
   - `session.updated.txt`

### 这层能力必须保留

因为它提供了：
- 会话级别的进一步可观测性
- 后续状态脚本、问题排查、人工回看所需的信息

---

## 9. direct 模式的 `exec` 语义必须保守保留

当前 direct 模式不是再起一个子进程然后返回，而是：

- `os.execvp(...)`

### 这层语义要谨慎保留

原因：
- 保证 direct 模式下没有额外 wrapper 进程悬挂
- 行为更接近旧 shell wrapper 的最终 `exec`
- 避免长任务退出码 / 信号传播变形

如果未来想变，必须明确评估，不是顺手改。

---

## 10. `agent` 模式的保守失败行为必须保留

当前 `--mode agent` 并不是“正常可用路径”，而是明确打印说明后退出失败。

### 必须保留这种保守态度

因为当前经验判断是：
- agent 模式比 command 模式不稳定
- 容易不遵从预设流程
- 甚至会自己跑偏，不走预期 Loop9 编排

在没有新的稳定证据前，不要把它包装成“也很好用”。

---

## 11. policy 与模板映射必须保留

当前 policy -> prompt template 的映射关系必须保留：

- `internal-full-audit`
- `weibu-submission`

以及：
- prompt 模板真正从文件读取
- target/path 占位替换后再写出 prompt 文件

这层属于 workflow 层，而不是 core 层；迁移时不要丢。

---

## 12. “先落盘、再启动”的顺序必须保留

在真正启动 opencode 之前，必须先完成：

- prompt 文件写出
- observe dir 建好
- run.meta / prompt.txt / command.txt 写好
- run_and_capture.sh 写好

### 原因

如果任务刚启动就崩：
- 仍然有完整现场
- 人可以接着查
- 不会出现“任务没跑起来，现场也没留下”的尴尬状态

---

## 13. 核心边界：公共 core 与 loop9 特例要分层

后续抽公共 runner core 时，必须坚持：

### core 层负责
- 运行 OpenCode command/agent
- tmux/direct
- observe/log/session/export
- 稳定运行与捕获

### loop9 launcher 层负责
- policy 模板选择
- target 元信息注入
- `loop9` 特例组合：`--command loop9 --agent loop9-controller`
- Loop9 相关的 prompt 组织

### 不能做的错误抽象
- 为了“统一”而抹掉 loop9 的经验特例
- 为了“漂亮”而删掉调试/追踪/兼容细节

---

## 14. 当前迁移策略建议

建议迁移顺序：

1. 先抽公共 core
2. 先让低风险 launcher（如 `loop9_real_poc`）吃 core
3. 再迁移 `loop9_wrapped_audit`
4. 迁移时用本清单逐条对照

不要直接一步重写 `loop9_authorized_review.py`。

---

## 一句话总结

后续不是“重写一个更漂亮的 wrapper”，而是：

> **在不丢失现有实战经验的前提下，把稳定运行 OpenCode 长任务的公共能力抽出来。**

只要和这句话冲突，就应该优先怀疑新设计，而不是怀疑旧经验。
