# Super8 本机使用说明（Loop9）

## 当前状态

这台机器上已经完成：

- Open Code 安装
- Oh-My-Open Code 安装
- `~/.config/opencode/` 备份配置恢复
- `Super8/.opencode/` 项目级 command / agents 接通
- `/loop9` 原生命令模式完整链路验证通过

## 推荐入口

在 `Super8` 目录下执行：

```bash
./.opencode/_scripts/loop9_authorized_review.py '<本地项目路径>'
```

默认行为：

- 基于仓库模板自动生成 prompt
- 自动填入目标项目名与本地绝对路径
- 调用：

```bash
opencode <Super8> --agent loop9-controller --prompt "请参照 '<prompt-file>'"
```

## 实验入口

如需显式测试 Open Code command 模式：

```bash
./.opencode/_scripts/loop9_authorized_review.py --mode command '<本地项目路径>'
```

当前说明：

- 该模式使用 `opencode run --dir <Super8> --command loop9 ...`
- 入口消息只传“读取并执行某个任务文件路径”，不直接展开文件正文
- 这样可以尽量降低因关键词触发 analyze-mode / 预处理污染的概率
- 但在当前 oh-my-opencode 环境下，这个模式仍然不如 agent 默认模式稳

## Prompt 输出位置

默认输出到：

```bash
Super8/temp/loop9-prompts/<target>-<timestamp>.md
```

## Loop9 运行产物

运行产物位于：

```bash
Super8/temp/loop9/<run_id>/
```

典型内容：

- `original_goal/`
- `shared_context/`
- `solution_v1...vN/`
- `validation_report_v1...vN/`

每个目录都应包含：

- `index.md`
- `partNN.md`
- `manifest.json`

## 标准状态检查命令

统一使用：

```bash
./.opencode/_scripts/loop9_status.sh
```

它会汇总：

- 最新 observe 日志
- 最新 loop9 run_dir
- 最新审计报告文件
- 最新 OpenCode session

推荐把它作为 heartbeat / 通知 / 人工查看时的统一状态入口。

## 时间窗口提醒（很重要）

不要因为前 30~60 秒看不到完整产物树，就立刻判定失败。

当前这套环境里，尤其是 command 路线下，常见现象是：

- 先进入 session
- 先读任务文件
- 先对目标仓库做结构探索（例如 glob / read / todo）
- 然后才逐步进入 `temp/loop9/<run_id>/...` 的标准产物落盘

实践建议：

- **短观察窗口**：1 分钟内只能判断“是否启动、是否读文件、是否开始探索”
- **中观察窗口**：5 分钟更适合看是否开始创建 run_dir 和初始目录
- **长观察窗口**：15~20 分钟更适合判断是否真正进入标准化 Loop9 闭环

结论：

> 对 command 模式不要过早中断；过早 kill 进程会把“只是慢”误判成“完全没跑”。

## 已验证记录

本机已使用本地示例目标做过非利用型链路验证：

- command mode 已完整生成 `shared_context` / `solution_v*` / `validation_report_v*`
- `/loop9 -> controller -> solver/validator/refiner` 链已确认跑通

## 注意

- 当前默认入口已经切换为 **原生命令模式**。
- `agent` 模式仅保留为回退兜底。
- 仓库内旧教程文档里的 Windows 绝对路径问题已修正为本地可用形式。
