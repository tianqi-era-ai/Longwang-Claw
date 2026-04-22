# Longwang-Claw
龙王小龙虾（LongWangCraw）是一套开源、国产、可控的 AI 原生网络安全工作流体系，能把漏洞发现→环境搭建→PoC 验证→证据固定→报告交付全流程自动化打通，让 AI 能持续推进复杂安全任务直到闭环交付。

`Longwang-Claw` 是把本地 `~/.openclaw` 里已经存在的龙王小龙虾核心自动化流程，按可公开的技术资产直接抽出来后的装配仓。

当前这一版优先纳入的是已经能直接装配回 `~/.openclaw/workspace` 的核心闭包：

- `workspace/HEARTBEAT.md`
- `workspace/bin/`
- `workspace/lib/`
- `workspace/config/`
- `workspace/plans/`
- `workspace/skills/`
- `workspace/heartbeat/`
- `workspace/prompts/`
- `workspace/OpenClaw_实装入口设计.md`
- `workspace/TELEGRAM_小龙虾封装说明.md`
- `workspace/REPO-STRUCTURE.md`
- `workspace/Super8/.opencode/`
- `workspace/Super8/*.md`
- `scripts/`
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
    HEARTBEAT.md
    bin/
    lib/
    config/
    heartbeat/
    plans/
    prompts/
    skills/
    Super8/
      .opencode/
    ...
  scripts/
```

## 先读什么

- `docs/仓库填充计划.md`
- `docs/给AI的装配说明.md`
- `docs/20-核心工作流全景总览.md`
- `docs/31-Dispatcher主线说明.md`
- `docs/32-定时任务与长任务调度说明.md`
- `docs/33-Skill_Tool_Wrapper_Harness工程说明.md`
- `docs/OpenClaw_实装入口设计.md`

## 当前已落的核心资产

- Dispatcher / launch guard / cron helper / docker inventory
- verify-v4 auto runner / openclaw-super8 sync helper
- AI-native development skill
- wrapped audit / status / verify-v4 / env-bootstrap / finding-replay / distillation
- real-poc / real-poc-preflight / delivery-reports / asset-evidence
- RCE focus / RCE inventory / unauth inventory
- Feishu publisher / Feishu delivery publisher
- Super8 wrapper、command、agents、XML source-of-truth 与启动说明
- Super8 `.opencode` plugin dependency files与 OpenCode 傻瓜流程说明
- OpenClaw / Telegram 实装入口原始文件、heartbeat 调度入口、heartbeat 子任务 prompt
- `scripts/bootstrap_openclaw_layout.py` 薄初始化脚本

后续继续沿着同一路线补更多闭包，不另起一套新结构。

## 当前同步的关键设计稿

- `workspace/plans/2026-03-26-loop9-concurrency-config-and-launch-guard.md`
- `workspace/plans/2026-03-16-heartbeat-loop9-status-subagent-design.md`
- `workspace/plans/2026-03-17-loop9-real-poc-preflight-skill.md`
- `workspace/plans/2026-03-28-loop9-远程-docker-靶场宿主机方案草案.md`
- `workspace/plans/2026-03-29-loop9-artifact-consumer-judgement-v0.md`
- `workspace/plans/2026-03-27-loop9-asset-evidence-skill-io-contract-v1.md`
- `workspace/plans/2026-04-09-ai-native-development-skill-plan.md`
- `workspace/plans/loop9-rce-skill-methodology-plan-2026-03-18.md`

这些文档不是宣发材料，也不是运行态输出，而是对现有 `bin / skills / Super8 wrapper` 的接线边界、输入输出约束和方法论补充说明，适合给 AI 或维护者直接阅读。
