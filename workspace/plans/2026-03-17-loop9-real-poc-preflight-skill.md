# 2026-03-17 Loop9 real-poc preflight skill 计划

- [x] 明确目标：做一个用于 real-poc 定时任务正式选择 / 正式执行前的 preflight 自检 skill
- [x] 调研现有 loop9 real-poc / detect / refresh / cron 接口
- [x] 设计 skill 边界（scan / classify / safe-fix / block）
- [x] 初始化 skill 目录
- [x] 实现最小脚本
- [x] 编写 SKILL.md
- [x] 本地回放验证（至少覆盖 RuoYi / maccms10 / gogs / Monitorr / dokuwiki）
- [x] 打包 skill
- [x] git checkpoint

## 当前产物

- skill 目录：`workspace/skills/loop9-real-poc-preflight/`
- 脚本：`workspace/skills/loop9-real-poc-preflight/scripts/loop9_real_poc_preflight.py`
- 打包产物：`workspace/skills/dist/loop9-real-poc-preflight.skill`

## 当前决策模型

- `skip-already-success`
- `skip-already-success-after-safe-fix`
- `safe-fix-available`
- `allow-launch`
- `block-needs-human`

## 与未来 real-poc cron 的接法

推荐把它接在：
1. `plan poc` 选出候选之后
2. `claim poc` 之前
3. `run_loop9_real_poc.py` 启动之前

最小接法：
- 对候选 run 执行 `loop9_real_poc_preflight.py --json <run-dir>`
- 若 `preflight_decision` 为：
  - `skip-already-success*` → 不 launch，直接跳过
  - `safe-fix-available` → 若 cron 明确允许 safe-fix，则带 `--apply-safe-fixes` 重跑一次；否则跳过并上报
  - `allow-launch` → 继续 formal claim / launch
  - `block-needs-human` → 不 launch，进入人工复核

## 本轮验证要点

- `RuoYi-official` → `skip-already-success`
- `maccms10` → `skip-already-success`
- `gogs` → `block-needs-human`
- `Monitorr` → `block-needs-human`
- `dokuwiki` → `block-needs-human`

## 设计硬约束

1. 这个 skill 是 **preflight**，不是新的 real-poc orchestrator。
2. 默认只读；写入修复必须是 `--apply-safe-fixes` 这类显式开关。
3. safe-fix 仅限 parser-gap / 状态物化类问题，不能把 run-local PASS 误翻成 shared workflow PASS。
4. 输出要能直接被后续 cron / wrapper 消费：
   - allow
   - allow-with-safe-fix
   - block-needs-human
5. 必须为未来接入 real-poc cron 做准备：支持单 run、自检批量、JSON 输出、非 0 退出码语义。
