# 龙王小龙虾｜Dispatcher 主线说明

## 先给结论

在 LongWangClaw 里，Dispatcher 是 Loop9 主线的阶段判断与推进层。它不是普通 wrapper，也不是某个子阶段脚本。

它负责回答这些问题：

- 当前 repo 处在哪一阶段
- 下一步该进入 Audit、Real-PoC、发布、Verify V4、报告还是恢复
- 当前 blocker 是环境问题、验证问题、交付问题，还是运行载体问题
- 某个阶段结束后，是否应该进入下一阶段，而不是把局部成功误当成整体完成

## 当前职责

Dispatcher 当前承担七类职责：

1. 检查 repo、run、observe、报告和队列状态。
2. 根据状态分发到正确阶段。
3. 读取阶段产物，而不是只发车不消费结果。
4. 识别 env-side blocker，并把主线带回环境修复。
5. 识别 transport/provider 失败，避免误判成 repo 语义完成。
6. 控制并发和 launch guard，避免同类长任务互相踩踏。
7. 把单 repo 从当前状态推进到验证收口、本地标准报告和最终本地复盘。

## 当前阶段执行器

当前公开仓里，主线不再以旧的 `loop9-env-bootstrap` / `loop9-poc-verification` 名称作为 active 外部入口。那些名称只保留为历史背景或旧设计口径。

当前 active 阶段是：

### Audit

- 入口 skill：`workspace/skills/loop9-wrapped-audit/SKILL.md`
- wrapper：`workspace/Super8/.opencode/_scripts/loop9_authorized_review.py`
- OpenCode command：`workspace/Super8/.opencode/command/loop9.md`
- agents：`workspace/Super8/.opencode/agents/`

Audit 负责把目标源码推进到标准 Loop9 audit run。

### Real-PoC 静态编写

- skill：`workspace/skills/loop9-real-poc/SKILL.md`
- 入口：`workspace/skills/loop9-real-poc/scripts/run_loop9_real_poc.py`
- 状态刷新：`workspace/skills/loop9-real-poc/scripts/refresh_real_poc_status.py`

Real-PoC 负责把完成的 audit run 转换为可复用 PoC Python 文件和迭代证据。

### 静态 Audit/PoC 产物上传

- skill：`workspace/skills/loop9-feishu-publisher/SKILL.md`
- 计划入口：`workspace/skills/loop9-feishu-publisher/scripts/build_publish_plan.py`

这一段发布 raw audit / PoC 过程产物，不等于标准交付报告发布。

### Verify V4 动态复现

- parent skill：`workspace/skills/loop9-verify-v4/SKILL.md`
- child skill：`workspace/skills/loop9-verify-v4-env-bootstrap/SKILL.md`
- child skill：`workspace/skills/loop9-verify-v4-finding-replay/SKILL.md`
- child skill：`workspace/skills/loop9-verify-v4-distillation/SKILL.md`
- 自动入口：`workspace/bin/loop9-verify-v4-auto-run.sh`

Verify V4 是当前动态环境搭建、PoC replay、证据蒸馏和 repo-complete 收口的 active 语义入口。

### 本地标准交付报告

- skill：`workspace/skills/loop9-delivery-reports/SKILL.md`
- build bridge：`workspace/skills/loop9-delivery-reports/scripts/build_repo_delivery_reports.py`
- final review bridge：`workspace/skills/loop9-delivery-reports/scripts/run_final_local_review_bridge.py`

这一段生成本地标准报告树，并进入最终本地复盘。

### 动态复现后的标准报告上传

- skill：`workspace/skills/loop9-feishu-delivery-publisher/SKILL.md`
- 计划入口：`workspace/skills/loop9-feishu-delivery-publisher/scripts/build_report_publish_plan.py`

这一段只上传标准交付报告树，不重新同步 raw audit artifacts。

## Publish 与 repo 闭环的边界

原始 Dispatcher 口径里有一条正确边界：repo 主线闭环终点是验证收口、本地标准报告、最终本地复盘；publish 不应该和本地报告生成混成一个动作。

当前公开仓在此基础上做了更清楚的拆分：

- repo 语义闭环：由 Verify V4 / delivery reports / final local review 收口。
- 对外同步闭环：由 `loop9-feishu-publisher` 和 `loop9-feishu-delivery-publisher` 两条独立 lane 处理。

所以 LongWangClaw 的端到端链路包含两段上传，但 Dispatcher 不应把“生成标准报告”和“上传标准报告”写成同一个阶段。

## 环境问题回路

如果动态复现或 preflight 判断 blocker 是 env-side：

1. 子阶段输出 dispatcher-readable 的 env repair / return-to-env 信号。
2. Dispatcher 回到 `loop9-verify-v4-env-bootstrap` 或等效环境修复路径。
3. 环境收口后再回到 finding replay。
4. 不能把环境失败吞成 repo 失败。

## 不应再误当主入口的旧口径

以下名字只作为历史 lineage，不作为当前公开仓默认主入口：

- `loop9_env_poc_dynamic_verify`
- `loop9-env-bootstrap`
- `loop9-poc-verification-preflight`
- `loop9-poc-verification`

当前对外说明、doctor 和 AI 装配手册都应使用 `loop9-verify-v4` family 的 active 名称。

## 当前一句话总结

Dispatcher 是 LongWangClaw 的主线推进层：子阶段负责干活，Dispatcher 负责阶段判断、回退、恢复、并发边界和闭环推进；上传被拆成独立发布 lane，不与本地 repo 语义闭环混在一起。
