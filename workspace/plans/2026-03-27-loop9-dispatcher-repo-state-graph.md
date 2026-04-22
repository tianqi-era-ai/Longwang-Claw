# 2026-03-27 Loop9 dispatcher repo state graph (draft)

## 目标

把单 repo 在 dispatcher 主线中的状态转移关系写成显式图，而不是继续依赖聊天解释。

---

## 一、repo 级主线的标准节点

### S0. repo selected
- dispatcher 选中一个 repo 作为当前单 repo 主线对象

### S1. env-required
- 当前 repo 缺 env / env stale / env unreadable / env not ready
- 应进入 env bootstrap / env revive

### S2. verify-ready
- env 已 ready_for_poc
- 可以进入 repo-level verification

### S3. verify-running
- 正在跑 repo verifier / finding verifier / follow-up

### S4. env-return
- verification / preflight / follow-up 发现 env-side blocker
- 必须返回 dispatcher
- 由 dispatcher 再决定 env bootstrap / repair / hold

### S5. continue-verify-unresolved
- repo summary 认为仍有自动化可继续推进的 finding
- 继续跑 next_finding_id 或等价 follow-up

### S6. hold-env-blocked
- 当前 repo 暂时被 env 问题卡住，但不是立刻无限重试
- 这是主线的非成功停驻态之一

### S7. review-summary-manually
- 当前剩余 unresolved 已全部落入 manual-only 类
- 自动化主线在这里结束，等待人工判断

### S8. deliver-now
- repo-level verification 已完成到可交付状态
- 下一步应进入本地标准报告生成

### S9. local-report-generation
- 生成 `workspace/reports/<repo>/`

### S10. final-local-review
- 对本地标准报告做最终复盘与语义校正

### S11. repo-mainline-done
- 单 repo 闭环完成

---

## 二、当前代码已明确暴露出的关键状态语义

来自 `run_loop9_repo_verification.py` 的 `next_action`：

- `deliver-now`
- `return-to-env`
- `hold-env-blocked`
- `review-summary-manually`
- `continue-verify-unresolved`

这说明 repo summary 已经在输出一个比较像状态机的中间层。

### 结论 1

repo summary 的 `next_action` 已经是 dispatcher 状态图的天然基础，后续应优先围绕它来收拢，而不是另造第二套 repo 状态语义。

---

## 三、推荐状态转移图

```text
repo selected
  -> env-required
  -> verify-ready

env-required
  -> (dispatcher 调 env bootstrap)
  -> verify-ready
  -> hold-env-blocked

verify-ready
  -> verify-running

verify-running
  -> continue-verify-unresolved
  -> env-return
  -> review-summary-manually
  -> deliver-now
  -> hold-env-blocked

env-return
  -> dispatcher
  -> env-required

continue-verify-unresolved
  -> verify-running
  -> env-return
  -> review-summary-manually
  -> deliver-now
  -> hold-env-blocked

hold-env-blocked
  -> env-required
  -> review-summary-manually

review-summary-manually
  -> terminal (manual wait)

deliver-now
  -> local-report-generation

local-report-generation
  -> final-local-review

final-local-review
  -> repo-mainline-done
```

---

## 四、最关键的纪律

### 纪律 A：env-side blocker 一律回 dispatcher

无论 blocker 是在：
- repo verifier preflight
- single finding verifier
- follow-up
- auth-resolution 前置探针

只要根因是 env-side：
- 不应在局部 wrapper 内部自成闭环
- 必须回到 dispatcher

### 纪律 B：deliver-now 不是闭环终点

`deliver-now` 只代表：
- verification 收口到可交付

它后面还必须继续走：
- 本地标准报告
- 最终本地复盘

### 纪律 C：publish 不属于这个 repo 主线状态机

publish 是另一条后续线，不要塞进 repo 主线闭环里。

---

## 五、当前状态机与现状实现的对应关系

## 已经存在的部分

### 1. env-related signals
已有：
- `preflight-return-to-env`
- `dispatcher_branch=return-to-env`
- `env_followup`
- `execute_return_to_env.py`

### 2. repo summary state
已有：
- `next_action`
- `next_finding_id`
- `unresolved_finding_ids`
- `delivery.ready_for_delivery`
- `delivery.need_human_review`

### 3. follow-up transition helper
已有：
- `run_repo_verification_followup.py`
- 能消费 `continue-verify-unresolved`
- 能消费 `return-to-env`
- 能识别 `deliver-now`
- 能识别 `hold-env-blocked`

## 还缺的部分

### 1. dispatcher-native repo state driver
当前这些状态转移还散落在：
- repo verifier
- follow-up helper
- verify dispatch cycle
- delivery report skill

还没有统一收进 dispatcher 的官方主线驱动层。

### 2. local-report-generation / final-local-review 还没完全纳入 dispatcher 状态图执行器
目前更多是 sibling skill / plan 层定义，不是 dispatcher 已统一消费的状态。

---

## 六、Phase 1 结论

### 结论 2

当前单 repo 状态机并不是从零开始设计；它已经在这些地方长出雏形：
- repo summary `next_action`
- follow-up helper
- verify dispatch cycle
- delivery report stage

真正需要做的不是推翻重造，而是：

1. 把这些状态统一命名
2. 把 env-return 明确钉回 dispatcher
3. 把 `deliver-now -> report -> final-review` 接进同一个 repo 状态机
4. 再把驱动入口统一收回 dispatcher

---

## 七、一句话总结

> 单 repo 主线已经具备可识别的状态机骨架；当前最重要的不是再发明状态，而是把已有 `next_action` / env-return / follow-up / report 阶段统一收编进 dispatcher 驱动层，形成真正的 repo 级闭环。
