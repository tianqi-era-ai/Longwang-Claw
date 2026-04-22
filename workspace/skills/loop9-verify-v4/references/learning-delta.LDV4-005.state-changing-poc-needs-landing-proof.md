# learning-delta — state-changing PoC needs landing proof

## delta identity
- abstract_id: `LDV4-005`
- repo: `dwsurvey`
- delta_scope: `mutation-style finding confirmation discipline`
- current_level: `observed`
- parent_family: `loop9-verify-v4`

## abstract layer
当前这轮值得保留的最小抽象 truth 是：

> **对 state-changing PoC，`HTTP 200` / `resultCode = 200` 只证明请求路径被接受，**
> **不等于漏洞真的落地。**
> **在把 mutation-style finding 收口为 `fresh-confirmed` 之前，必须验证目标对象的 before/after state，**
> **必要时还要加入 rightful principal 的 control replay，来区分“成功回包壳”与“真正生效的越权修改/删除”。**

## case layer
`dwsurvey` 的 `F4` 正好给出了一个非常干净的反例：
- 非 owner token 调用 `delete-answer.do` 时返回 `HTTP 200`；
- 但立刻回读 SQL，victim `t_survey_answer` 行和 `t_survey_answer_json` 行都还在，删除并未落地；
- 同一路径改用 owner token 再执行一次，`t_survey_answer` 行才真正被删掉；
- 所以这条 finding 的 truthful 结论不是 “任意已认证删除成立”，而是：
  - any-authenticated delete claim = `fresh-blocked`
  - API 另有一个“误导性 success response shell”实现问题

## evidence refs
1. `/Users/xlx/.openclaw/workspace/reports/2026-04-15-loop9-v4-dwsurvey-repo-complete/rounds/dwsurvey/r1-fresh-repo-complete/objects/attempt-receipt.dwsurvey.F4.r1-fresh-repo-complete.md`
2. `/Users/xlx/.openclaw/workspace/reports/2026-04-15-loop9-v4-dwsurvey-repo-complete/rounds/dwsurvey/r1-fresh-repo-complete/artifacts/replay-active-unblock/F4.serial.before.txt`
3. `/Users/xlx/.openclaw/workspace/reports/2026-04-15-loop9-v4-dwsurvey-repo-complete/rounds/dwsurvey/r1-fresh-repo-complete/artifacts/replay-active-unblock/F4.serial.after-non-owner.txt`
4. `/Users/xlx/.openclaw/workspace/reports/2026-04-15-loop9-v4-dwsurvey-repo-complete/rounds/dwsurvey/r1-fresh-repo-complete/artifacts/replay-active-unblock/F4.serial.after-owner.txt`

## no-overclaim note
- 这条 delta 不是要求所有 PoC 都必须下钻到 SQL 层
- 它的适用边界是：claim 本身依赖“对象状态真的被改了/删了”，而接口回包又不足以单独证明 landing
- 如果外部可见 side effect 已经足够直接、且不存在“success shell”歧义，可以用同样强度的非 SQL receipt 替代
