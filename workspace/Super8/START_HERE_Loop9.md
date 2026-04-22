# START HERE · Super8 / Loop9

如果你只看一份文件，就先看这个。

## 最常用入口

### 1) 启动一个本地目标的标准化长任务

```bash
cd ~/.openclaw/workspace/Super8
./.opencode/_scripts/loop9_authorized_review.sh <local-target-path>
```

例子：

```bash
./.opencode/_scripts/loop9_authorized_review.sh /absolute/path/to/local/repo
```

说明：
- 这是当前**主入口**
- 优先通过 wrapper 启动，不要手工长期维护复杂 `opencode ...` 命令
- 当前默认是 `command` 分支；`agent` 分支保留为回退/排查用途

### 2) 查看当前长任务状态

```bash
cd ~/.openclaw/workspace/Super8
./.opencode/_scripts/loop9_status.sh
```

它会汇总：
- 最新 observe 日志
- 最新 loop9 运行目录
- 最新报告文件
- 最新 OpenCode session

---

## 如果你是从 Telegram / 小龙虾 进来的

外层入口设计看这里：

- `../TELEGRAM_小龙虾封装说明.md`
- `../skills/loop9-wrapped-audit/SKILL.md`

聊天侧默认行为看这里：

- `TELEGRAM_默认行为规范.md`
- `TELEGRAM_通知模板.md`

关键原则：
- Telegram / 小龙虾 只做**外层入口**
- 真正执行统一交给 wrapper
- 长任务默认后台长跑
- heartbeat 负责进展检查与通知

---

## 必须知道的坑

### 坑 1：不要过早 kill

这类任务：
- 1~2 小时正常
- 3~5 小时也可能

短时间无结果不代表失败。
command 路线经常会先：
1. 读任务文件
2. 探索目标仓库
3. 做子审计 / 交叉验证
4. 然后才逐步产出完整结果

### 坑 2：不要误把运行时 `Skill "loop9"` 当成旧 skill 残留

当前更准确的理解是：
- runtime 可能用统一入口解析 command / skill
- `loop9` 的主要活跃来源仍然是 `.opencode/command/loop9.md`

### 坑 3：不要在入口消息里展开大段 prompt 正文

更好的方式：
- 入口只传路径 + 动作
- 真正的任务要求都放进任务文件正文

---

## 关键文档导航

### 本地运行与问题分析
- `README.loop9-local.md`
- `LOOP9_问题地图.md`
- `LOOP9_封装计划.md`
- `下一步计划.md`

### 对外封装 / 通知
- `TELEGRAM_默认行为规范.md`
- `TELEGRAM_通知模板.md`
- `../TELEGRAM_小龙虾封装说明.md`
- `../skills/loop9-wrapped-audit/SKILL.md`

### 当前 controller 相关
- `.opencode/agents/loop9-controller.md`
- `.opencode/agents/loop9-solver.md`
- `.opencode/agents/loop9-validator.md`
- `.opencode/agents/loop9-refiner.md`

---

## 当前一句话策略

> 本地统一通过 wrapper 启动，状态统一通过 `loop9_status.sh` 查看，对外统一按 Telegram / 小龙虾 的长任务模型处理。
