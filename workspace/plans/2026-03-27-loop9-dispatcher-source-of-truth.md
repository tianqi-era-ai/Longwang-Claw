# 2026-03-27 Loop9 dispatcher source of truth

## 当前唯一正确口径（以本文件为准）

### 1. 外部入口

- **外部入口 = dispatcher**
- dispatcher 是 Loop9 主线的唯一总控层

它负责：
- 检查
- 分发
- 阶段判断
- 调 skill
- 读取阶段产物
- 决定下一阶段
- 环境问题回退
- 单 repo 闭环推进

### 2. 内部阶段执行器

dispatcher 调用的主要阶段执行器包括：

- `loop9-env-bootstrap`
  - 环境搭建 / 修复 / 健康检查 / handoff
- `loop9-poc-verification-preflight`
  - 发车前门禁 / readiness check / env-side blocker 识别
- `loop9-poc-verification`
  - 自动化 PoC 复现 / 自动修 PoC / 固化证据 / 收口结果
- repo follow-up 能力
  - verification 主线内部子阶段，不是外部入口
- `loop9-delivery-reports`
  - 本地标准报告生成
- final local review
  - 本地标准报告完成后的最终本地复盘

### 3. env 问题的正确回路

如果 verification / preflight / follow-up 发现真实 blocker 是 env-side：

1. 不应停在 verification 自己那里
2. 必须产出 **dispatcher-readable** 的 `return-to-env` / `env-revive` 信号
3. 必须回到 dispatcher
4. 由 dispatcher 再调 env bootstrap
5. env 完成后，再由 dispatcher 继续主线

换句话说：

- **env-side 问题的中枢处理者永远是 dispatcher**
- 不是某个 wrapper 自己半路消化

### 4. `loop9_env_poc_dynamic_verify` 的定位

- 它**不是**外部主入口
- 它**不是** canonical user-facing unified entry
- 它只能被视为：
  - 内部辅助组件
  - 兼容层
  - 或后续被 dispatcher 吸收的薄 helper

任何文档、skill、plan、说明中，如果把它写成：
- 外部统一入口
- 总入口
- 默认入口
- slash 主入口

都应视为**旧口径**。

### 5. 单 repo 主线闭环终点

dispatcher 对单 repo 的正确闭环终点是：

1. 验证收口
2. 本地标准报告
3. 最终本地复盘

### 6. publish 的边界

- **publish 不在这条闭环里**
- publish 是单独后续流程
- 不应再把“本地标准报告生成”和“发布”混成一个动作

### 7. 当前实施原则

- 先统一口径
- 再统一职责边界
- 再改 dispatcher 主线执行流
- 最后处理兼容 wrapper / 旧表述 / 收尾文档

在口径未统一前，不应继续扩大代码改造范围。
