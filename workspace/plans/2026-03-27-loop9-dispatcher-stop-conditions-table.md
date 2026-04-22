# 2026-03-27 Loop9 Dispatcher 停止条件总表

## 目的

把当前 Loop9 verify mainline 中所有“可能导致主线停下”的条件拆成：
- 合法停止
- 非法提前停止
- 子阶段仅回交控制权（不可自行宣布主线结束）

当前总原则：

> Dispatcher 是唯一有权决定 repo 主线是否停止的组件。
> 子阶段只能回交结果 / blocker / 观察，不得擅自结束 repo 主线。

---

## A. 合法停止条件（唯一允许）

### A1. repo-mainline-done
- 含义：repo 主线已真正收口
- 权限：Dispatcher 可以停止
- 备注：这是唯一正常成功结束态

### A2. 用户明确人工停止
- 含义：用户明确要求 stop / pause / abort
- 权限：Dispatcher 可以停止
- 备注：高优先级人工控制

### A3. 宿主级硬故障 / 外部资源彻底不可用
- 含义：继续尝试已无现实基础
- 示例：
  - Docker daemon 整体不可用
  - 本地磁盘/权限/文件系统严重损坏
  - 关键网络基础设施整体不可达且无法开展任何有效尝试
- 权限：Dispatcher 可以停止
- 备注：**不包括** 单次 LLM/provider 不可用；这类只算 blocker / 运行异常，不是合法停止

### A4. 达到预算上限
- wall-clock >= 40 分钟
- blocker_count >= 10
- 权限：Dispatcher 可以停止本轮 slice，并立即 self-reenter 或由 cron 接续
- 备注：这是 slice 级合法停止，不是 repo 主线永久结束

---

## B. 非法提前停止条件（必须移除 / 修正）

### B1. child-running 就自然停
- 旧现象：`sticky-running-skip` 导致 driver 提前结束
- 纠偏：child 在跑时，Dispatcher 应持续监护，直到 child 回交或预算耗尽

### B2. `partial / E_NOT_IMPLEMENTED` 被当成 repo 结束
- 旧现象：env bootstrap 跑完自己会做的薄流程后直接收口
- 纠偏：partial 只是 blocker 事件，必须回交 Dispatcher 继续编排

### B3. `current hook = none` 或 `repair ladder 用完`
- 旧现象：当前已知 hook / ladder 没有更多动作，就停止
- 纠偏：这只是“当前自动化知识不足”的 blocker，不是合法停止

### B4. `non-installable` / `recent-failure` 被 planner 直接跳过
- 旧现象：planner 会把一些 repo 视为暂时不值得继续
- 纠偏：对 sticky current repo，这些只能转成 blocker / remediation，不得直接放弃

### B5. 子阶段自己认为“现在不会了”
- 旧现象：env/bootstrap/verify 子阶段对 repo 主线拥有事实上的结束权
- 纠偏：子阶段只能交回控制权，不能宣布主线结束

### B6. 单次 cron / LLM timeout 直接断主线
- 旧现象：一次 agent turn 超时可能让主线中断
- 纠偏：超时属于运行异常，不是 repo 终止条件。应由 Dispatcher / cron / self-reenter 接续

---

## C. 子阶段仅回交控制权（统一协议）

子阶段统一只允许返回以下语义之一：

### C1. continue
- 含义：当前阶段已经把 repo 推到下一阶段，可继续
- 示例：env ready for verify

### C2. blocker
- 含义：当前阶段遇到新阻塞，但 repo 主线不应结束
- 示例：
  - partial / E_NOT_IMPLEMENTED
  - env failed
  - verify unresolved
  - 端口不通 / 安装未完成 / target-specific 问题

### C3. handoff
- 含义：当前阶段已完成自己的一段，交回 Dispatcher 编排下一阶段
- 示例：
  - env finished its current thin automation path
  - report bridge finished and waiting next scheduling decision

### C4. hard-stop
- 含义：只在命中“合法停止条件”时使用
- 权限：仅 Dispatcher 最终裁决
- 子阶段不得自行把普通 partial/failure 升级成 hard-stop

---

## D. 当前执行纪律

1. 子阶段输出不再视为 repo-level final truth
2. Dispatcher 必须读取：
   - 当前结果
   - blocker key
   - observability artifacts
   - handoff / dispatcher_return
3. 只要没命中 A 类条件，主线都应继续
4. `partial`、`E_NOT_IMPLEMENTED`、`none-hook`、`not-installable`、`child-running` 都不是合法停止

---

## E. 对 mall4j 的直接解释

mall4j 之前提前停住，不应再解释成“合理 partial 结束”，而应解释成：
- 当前系统存在停止权错位
- env 子阶段越权把“薄流程跑完”误当成“repo 主线可结束”
- Dispatcher 没有把 partial 当 blocker 继续接手

这正是当前要修复的核心系统 bug。
