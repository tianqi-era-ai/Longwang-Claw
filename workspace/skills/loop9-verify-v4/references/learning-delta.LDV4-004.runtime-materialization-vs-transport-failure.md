# learning-delta — runtime materialization vs transport failure

## delta identity
- abstract_id: `LDV4-004`
- repo: `dwsurvey`
- delta_scope: `current-round blocker diagnosis before negative finding freeze`
- current_level: `observed`
- parent_family: `loop9-verify-v4`

## abstract layer
当前这轮值得沉淀的最小抽象 truth 是：

> **当 PoC 首次失败，但 runtime 的 helper routes / containers 仍然 live 时，**
> **不要把失败草率归因给网络中断或 prompt 不行。**
> **先区分 transport failure 与 runnable-but-underprepared runtime；**
> **如果真正缺的是官方 seed、live id、sid、auth material 或其它可低成本补齐的运行物料，**
> **parent 应在同一 repo round 内先补齐这些物料并重放，再决定 finding 的 terminal disposition。**

## case layer
`dwsurvey` 这轮把这个边界暴露得很清楚：
- lab 中容器和匿名 helper routes 仍然可达，说明并不是整体 transport collapse；
- 先前卡住的关键，不是“PoC 没跑完”，而是 fresh runtime 没有被 materialize 到正确状态：
  - `F1` 缺官方 `db/dwsurvey-init.sql` seed；
  - `F2` 需要从当前库里重定位 live `sid`，而不是沿用错误的 `sid=1`；
  - `F3` 需要先走公开注册链，拿到真实的非 owner token；
- 在补齐这些 runtime material 之后，`F1 / F2 / F3` 都拿到了 fresh live receipt。

## evidence refs
1. `/Users/xlx/.openclaw/workspace/reports/2026-04-15-loop9-v4-dwsurvey-repo-complete/rounds/dwsurvey/r1-fresh-repo-complete/objects/attempt-receipt.dwsurvey.F1.r1-fresh-repo-complete.md`
2. `/Users/xlx/.openclaw/workspace/reports/2026-04-15-loop9-v4-dwsurvey-repo-complete/rounds/dwsurvey/r1-fresh-repo-complete/objects/attempt-receipt.dwsurvey.F2.r1-fresh-repo-complete.md`
3. `/Users/xlx/.openclaw/workspace/reports/2026-04-15-loop9-v4-dwsurvey-repo-complete/rounds/dwsurvey/r1-fresh-repo-complete/objects/attempt-receipt.dwsurvey.F3.r1-fresh-repo-complete.md`
4. `/Users/xlx/.openclaw/workspace/reports/2026-04-15-loop9-v4-dwsurvey-repo-complete/rounds/dwsurvey/r1-fresh-repo-complete/objects/repo-closure-review.dwsurvey.r1-fresh-repo-complete.md`

## no-overclaim note
- 这条 delta 不是说“所有失败都应该自动重试到成功”
- 它只适用于 transport failure 证据并不成立、而 runtime material mismatch 明显且可低成本补齐的场景
- 如果真正缺的是高风险外部依赖、不可接受的 destructive path，仍应 truthful 地落到 `fresh-manual-needed` 或 `fresh-skip-by-policy`
