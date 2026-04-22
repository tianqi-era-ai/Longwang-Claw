# learning-delta — active in-flight anchor vs detached continuation

## delta identity
- abstract_id: `LDV4-010`
- repo: `cross-repo / mechanism-layer`
- delta_scope: `same-repo mainline completion gate + delivered-repo re-entry suppression`
- current_level: `observed`
- parent_family: `loop9-verify-v4`

## abstract layer
当前这轮值得保留的最小抽象 truth 是：

> **只有被 parent 接受、并且仍处于进行中的 current-round anchors，**
> **才有资格延续“同一个 repo mainline”。**
> **脱离 active round 的旧 env/bootstrap/replay artifacts 只能作为 support signals。**
> **因此 parent 必须把 repo completion 做成 fail-closed：**
> **既不能在 delivery tail 之前把 `repo-round-verdict` 当成 `repo-mainline-done`，**
> **也不能在 `auto-select` 里用 detached continuation evidence 静默重开一个已交付 repo。**

## case layer
这次机制层失误其实有两个表面，但它们共享同一个根因：
- 一方面，`repo-round-verdict` 之后的 `delivery-report-bridge -> final-local-review` 没有被继续消费，却被错误地叙述成了可以停在这里；
- 另一方面，`sparkshop` 已经有 canonical delivery markers，但同 repo 的旧 Tencent CVM env/replay 资产又被错误地读成 continuation anchor，从而在 `auto-select` 里看起来像是“合理继续”。

正确修复不是只记住这一个 repo 的教训，而是把 continuation authority 缩回到：
- accepted `parent-selection-acceptance`
- current round root
- accepted `repo-task-brief`
- accepted `repo-findings-board`

如果这些 active in-flight anchors 并不存在，那么旧 env/replay 资产只能辅助判断，不得：
- 取代 canonical suppressors，
- 触发 silent reopen，
- 或把 `repo-round-verdict` 之后的未消费 tail 伪装成“以后再聊也行”的软停点。

## evidence refs
1. `~/.openclaw/workspace/skills/loop9-verify-v4/SKILL.md`
2. `~/.openclaw/workspace/skills/loop9-verify-v4/references/repo-selection.md`
3. `~/.openclaw/workspace/skills/loop9-verify-v4/references/repo-selection-pack.md`
4. `~/.openclaw/workspace/skills/loop9-verify-v4/references/parent-closure-chain.md`
5. `~/.openclaw/workspace/skills/loop9-verify-v4/references/runtime-isolation.md`
6. `~/.openclaw/workspace/reports/2026-04-17-loop9-v4-tencent-cvm-sparkshop-followup/intake/repo-selection-proposal.sparkshop.r1-active-tencent-cvm-followup.md`
7. `~/.openclaw/workspace/reports/2026-04-17-loop9-v4-tencent-cvm-sparkshop-followup/intake/parent-selection-acceptance.sparkshop.r1-active-tencent-cvm-followup.md`

## level judgment
- current_level: `observed`
- promotion_reasoning: `one concrete regression made the same abstract guard visible on both the tail-completion side and the selection-suppressor side`

## no-overclaim note
- 这条 delta 当前还只是 `observed`
- 它并不表示所有 detached historical artifacts 都毫无价值；它们仍可作为 support-level context
- 它真正否定的是两种越权读法：
  - 把 detached artifacts 当成 active continuation authority
  - 把 `repo-round-verdict` 当成足以结束 repo mainline 的 completion gate
