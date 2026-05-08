# LongWangClaw Contract Fixture

这个目录是最小合成契约夹具，只用于验证公开仓的装配形状、文档契约、发布计划解析和 doctor 输出。

它不是：

- 真实靶标源码
- 真实漏洞案例
- exploit demo
- 首发案例
- 宣发材料
- 运行报告归档

夹具分成两段：

- `audit-run/`：模拟一个最小 Loop9 audit run 和 Real-PoC 产物形状，供静态发布计划解析。
- `report/`：模拟一个最小标准交付报告树，供动态复现后的标准报告发布计划解析。

doctor 只会读取这些文件，并把临时检查输出放到系统临时目录；不会把本目录复制到 `~/.openclaw/workspace/targets`，也不会触发真实 Feishu、Docker、OpenCode 或 Codex 执行。
