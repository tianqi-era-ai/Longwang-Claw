# LongWangClaw Harness

Harness 是 LongWangClaw 的进阶工程层，用来说明复杂 AI 工作流如何在模型随机性、长任务、子阶段隔离、timeout、降智和多轮回跳中保持可控。

它不是新的主入口，也不是把工作流改造成厚 orchestrator。当前主入口仍然是：

- Audit：`workspace/skills/loop9-wrapped-audit/SKILL.md`
- Real-PoC：`workspace/skills/loop9-real-poc/SKILL.md`
- 动态复现：`workspace/skills/loop9-verify-v4/SKILL.md`
- 报告：`workspace/skills/loop9-delivery-reports/SKILL.md`

## 当前公开边界

这个目录只放 active、可解释、可迁移的 Harness 工程说明：

- 语义 owner 和 runtime placement 的拆分
- parent / child stage 的职责边界
- isolated executor / child agent 的使用纪律
- timeout / provider failure / model wobble 的归因纪律
- handoff / verdict / receipt 的薄写回边界
- 防止厚脚本、厚队列和厚 orchestrator 重新夺权

这个目录不放：

- 历史报告
- live validation 运行产物
- synthetic test output
- 靶标源码
- exploit demo
- CI / smoke
- 历史归档备份

## 当前 active 对照

Harness 当前主要对应 `loop9-verify-v4` family 的 active 控制面约束：

- `workspace/skills/loop9-verify-v4/references/parent-boundary.md`
- `workspace/skills/loop9-verify-v4/references/owner-placement-matrix.md`
- `workspace/skills/loop9-verify-v4/references/runtime-isolation.md`
- `workspace/skills/loop9-verify-v4/references/parent-io-contract.md`
- `workspace/skills/loop9-verify-v4/references/stage-chain.md`
- `workspace/skills/loop9-verify-v4/references/handoff-compiler.md`

`harness/loop9-verify-v4-control-contract.md` 是给外部读者和 AI 装配者看的高层收束；真实执行仍以 `workspace/skills/loop9-verify-v4/` 下的 active refs 为准。

## 一句话

Harness 不是更多脚本，而是让 AI 原生长工作流在不确定环境里不漂移、不误判、不失控的一组控制面纪律。
