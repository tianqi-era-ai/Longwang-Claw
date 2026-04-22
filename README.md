# Longwang-Claw

`Longwang-Claw` 是把本地 `~/.openclaw` 里已经存在的龙王小龙虾核心自动化流程，按可公开的技术资产直接抽出来后的装配仓。

当前这一版优先纳入的是第一批核心闭包：

- `workspace/bin/`
- `workspace/lib/`
- `workspace/config/`
- `workspace/plans/`
- `workspace/skills/`
- `workspace/Super8/.opencode/_scripts/`
- `docs/`

本仓当前的重心不是案例产物、宣发资料、靶场源码，也不是运行态数据，而是这套自动化主线本身：

- Audit
- Env Bootstrap
- 自动化验证
- Real-PoC
- 标准交付报告
- 关键中间桥接与状态面

## 当前目录

```text
Longwang-Claw/
  docs/
  workspace/
    bin/
    lib/
    config/
    plans/
    skills/
    Super8/.opencode/_scripts/
```

## 先读什么

- `docs/仓库填充计划.md`
- `docs/给AI的装配说明.md`
- `docs/20-核心工作流全景总览.md`
- `docs/31-Dispatcher主线说明.md`
- `docs/33-Skill_Tool_Wrapper_Harness工程说明.md`
- `docs/OpenClaw_实装入口设计.md`

## 当前已落的第一批核心资产

- Dispatcher / launch guard / cron helper / docker inventory
- AI-native development skill
- wrapped audit / status / verify-v4 / env-bootstrap / finding-replay / distillation
- real-poc / real-poc-preflight / delivery-reports / asset-evidence
- Super8 wrapper 启动入口与状态入口

后续继续沿着同一路线补更多闭包，不另起一套新结构。

