# OpenCode Runner Core 重构计划

目标：抽取一套可复用、稳定、可追踪、好调试的 OpenCode 长任务运行核心；优先服务 `loop9_wrapped_audit` 与 `loop9_real_poc`，并保持对 `Super8/.opencode/_scripts/loop9_authorized_review.py` 这类经实战验证代码的敬重与兼容。

## 原则

- [x] 明确认可：`--command loop9 --agent loop9-controller` 是 Loop9 这条线的实战关键经验，不做“自以为更合理”的轻率改动
- [x] 明确认可：`Super8/.opencode/_scripts/loop9_authorized_review.py` 中很多细节是反复踩坑调出来的，优先消化、复用、抽取，不轻易推翻
- [x] 先抽公共能力，再让上层 launcher 复用；避免先重写业务再补基础设施
- [x] 先保守迁移 `loop9_real_poc`，后谨慎迁移 `loop9_wrapped_audit`
- [x] Python 作为主要编排语言；shell 只保留必要的运行包裹与 tmux 落地层

## 阶段 A：理解与规划

- [x] A1. 重新通读 `loop9_authorized_review.py`，识别其中经实践验证的关键经验点
- [x] A2. 明确公共层 / workflow 层 / prompt 层的三层边界
- [x] A3. 落地本地计划文件，用 checkbox 跟踪状态
- [x] A4. 列出 `loop9_authorized_review.py` 中“必须保留”的行为清单（见 `plans/loop9-authorized-review-must-keep.md`）

## 阶段 B：抽取 OpenCode Runner Core（最小可行）

- [x] B1. 新建公共 Python core 目录（例如 `workspace/lib/opencode_runner/`）
- [x] B2. 抽取通用参数模型：command/agent、transport、cwd、observe_root、prompt、metadata
- [x] B3. 抽取通用 observe 目录初始化：`run.meta` / `prompt.txt` / `command.txt`
- [x] B4. 抽取 tmux session 启动逻辑
- [x] B5. 抽取 direct 模式启动逻辑
- [x] B6. 抽取生成 `run_and_capture.sh` 的公共能力
- [x] B7. 保留 `loop9` 特例能力入口：支持 `--command loop9 --agent loop9-controller`
- [x] B8. 对 core 做 dry-run / py_compile / 最小自测

## 阶段 C：先迁移 loop9_real_poc（低风险验证）

- [x] C1. 让 `skills/loop9-real-poc/scripts/run_loop9_real_poc.py` 改为调用公共 core
- [x] C2. 保持现有 CLI 语义不变
- [x] C3. 验证 dry-run、tmux launch、observe 目录产物（本轮按缩窄范围完成：dry-run / tmux launch / observe 首批产物已验证；长任务稳定性观察交由后续人工调试）
- [x] C4. 打包 skill 并提交 checkpoint

## 阶段 D：谨慎迁移 loop9_wrapped_audit（高敏感）

- [x] D1. 先做“行为对照清单”，确保不丢掉现有关键经验（见 `plans/loop9-authorized-review-must-keep.md`）
- [x] D2. 在不改变入口文件名与 CLI 形状的前提下，引入公共 core
- [x] D3. 保留 `--command loop9 --agent loop9-controller` 的关键组合
- [x] D4. 保留 target metadata 注入、prompt 文件生成、tmux/observe 细节
- [x] D5. 验证 dry-run / tmux 启动 / 观察目录 / attach 信息（本轮按缩窄范围完成：help + py_compile + tmux 启动 + observe/attach 已验证；长任务稳定性观察交由后续人工调试）
- [x] D6. 提交 checkpoint（此前迁移 checkpoint：workspace `7f1b107`；Super8 `7d7932c`。漏点修复补丁：workspace `2b81482`；Super8 `0af3143`。本轮 Python 入口与维护护栏收尾：workspace `030951f`；Super8 `fb71597`）

## 阶段 E：统一状态查询与后续增强

- [x] E1. 抽取统一 status 查询工具（给 observe dir 返回结构化状态）
- [x] E2. 统一日志/产物 schema，减少后续 heartbeat/status 的特殊分支（本轮够用版完成：已统一 `run.meta` / `launch.summary` / `observe.summary` / `status` 的 schema 标识；`run.meta.json` / `launch.summary.json` 已真实落盘；`status.py` 已支持 tmux session 存活判断）
- [ ] E3. 评估是否支持更多 OpenCode command，而不污染 core

## 当前状态摘要

- [x] 已完成：`loop9_real_poc` 第一版 launcher 已经存在，并已通过 dry-run
- [x] 已完成：新方向已经明确为“瘦外层、重用 OpenCode/Loop9 本体”
- [x] 已完成：公共 runner core 第一版已落地，并已接入 `loop9_real_poc`
- [x] 已完成：`loop9_wrapped_audit` 已完成 command/tmux 路径迁移、去除明显重复 helper，并有 checkpoint
