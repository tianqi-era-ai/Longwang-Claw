# Loop9 Verify V4 Harness Control Contract

这份文件把 `loop9-verify-v4` 当前 active Harness 纪律收束成一页。它面向外部读者、维护者和协助装配的 AI。

## 1. 先拆开两个概念

`semantic owner` 和 `runtime placement` 不能混成一个东西。

- `semantic owner`：谁拥有意义、选择、accept/reject、最终 freeze 和 repo-level truth。
- `runtime placement`：某个对象或阶段在哪里生产、由谁执行、是否隔离。

关键规则：

- parent-owned 不等于 parent-inline。
- isolated-produced 不等于 child-owned。
- child runtime 不能偷走 repo-level truth。

## 2. Parent 永远拥有 repo 级意义

Parent 层拥有：

- repo intake / repo selection
- repo truth relocation
- repo-start-pack / parent-draft-pack 的 accept/reject
- current round root freeze
- repo-task-brief freeze
- repo-findings-board freeze
- queue item / gate selection
- child runtime binding
- stage-handoff 编译
- repo closure review
- coverage snapshot freeze
- external readout truth source control
- repo-round verdict
- delivery-report-bridge verdict consumption
- final-local-review completion freeze

Child 可以返回 stage-local truth，但不能直接宣布 repo closure。

## 3. Child 只做 bounded stage work

当前第一波 child stage 默认是 isolated：

- `repo-selection-pack = must-isolated`
- `env-bootstrap = must-isolated`
- `finding-replay = must-isolated`
- `distillation = must-isolated`
- `delivery-reports = must-isolated`

Child 输出应收敛到：

- `repo-selection-proposal.*.md`
- `stage-verdict.<stage>.md`
- receipt / blocked / fixed-point / thin writeback

Child 不应：

- 直接链到另一个 child
- 扩大隐藏上下文
- 写到 frozen round root 之外
- freeze queue scope
- freeze repo closure
- 把 historical kept 当成本轮 terminal disposition

## 4. Handoff / verdict 是硬边界

Parent 编译薄 handoff：

```text
stage-handoff.<stage>.md
```

Child 返回薄 verdict：

```text
stage-verdict.<stage>.md
```

handoff 负责约束输入，verdict 负责返回 stage-local truth。repo-level freeze 必须回到 parent 消费后才成立。

## 5. Timeout 和模型波动不能被误读

AI child work 的 timeout 首先是 caller-side budget / scheduling failure，不是 repo truth。

默认纪律：

1. child 没写出 usable verdict 时，记录为 timeout-budget failure。
2. 先增加 timeout 或调整 carrier，再重跑。
3. 不把 timeout 消费成 `blocked-confirmed` 或 repo-level truth。
4. 只有检查到运行时证据后，才能把 timeout 升级成 prompt / worker 质量问题。
5. 一次失败不证明设计失败，一次成功不证明鲁棒。

## 6. 同一 repo flow 不应默认断到下一轮聊天

允许：

- parent 等待 child
- parent poll child
- 同一 repo flow 长时间保持打开
- child 慢，但 parent 不丢 owner

不允许默认：

- child 发起后让用户下次再问
- 把 `sessions_yield` 当成同一 repo mainline 的正常分段方式
- delivery tail 未收口就把 repo-round-verdict 当成 repo-mainline-done

## 7. 不要把 Harness 做成厚控制面

Harness 保护的是 AI 原生控制纪律，不是新建一个厚 job system。

不要引入：

- 厚 orchestrator
- 厚 queue runtime
- 厚 registry
- 厚 scoreboard
- 样例 demo / smoke / CI

代码只做确定性桥接；AI 仍保留语义判断和主线意义所有权。

## 8. 对照 active refs

详细规则以这些 active refs 为准：

- `workspace/skills/loop9-verify-v4/references/parent-boundary.md`
- `workspace/skills/loop9-verify-v4/references/owner-placement-matrix.md`
- `workspace/skills/loop9-verify-v4/references/runtime-isolation.md`
- `workspace/skills/loop9-verify-v4/references/parent-io-contract.md`
- `workspace/skills/loop9-verify-v4/references/stage-chain.md`
- `workspace/skills/loop9-verify-v4/references/handoff-compiler.md`

## 一句话

Loop9 Verify V4 的 Harness contract 是：parent 拥有 repo-level truth，child 只做隔离的 bounded stage work，所有 timeout、handoff、verdict 和 closure 都必须回到 parent 语义层消费后才算真实进展。
