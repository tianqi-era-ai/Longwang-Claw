# 2026-03-26 Loop9 并发配置化 + 发车前保护

## 用户目标

1. 把 `audit` / `real-poc` 的“最大同时运行数量”从硬编码/散落规则里收敛到一个配置文件中，便于以后修改与迁移。
2. 增加统一的“发车前保护脚本”，在启动新的 Loop9 任务前检查：
   - swap
   - 磁盘剩余
   - Docker / Virtualization 相关压力
   - 活跃 `.opencode`
   - 当前 kind 的 active 槽位是否已满
3. 当前用户指定的默认并发上限：
   - `audit = 1`
   - `real-poc = 1`

## 设计决策

### A. 配置文件位置

采用：
- `config/loop9-dispatch.json`

原因：
- 属于用户可调的 durable 配置，不应该混进 `automation-state/` 这种运行态状态目录
- 以后迁移/复制更直接
- cron prompt / Python 入口 / 手工诊断都能读取同一份文件

### B. 统一守门脚本

新增：
- `bin/loop9-launch-guard`
- `lib/loop9_automation/launch_guard.py`
- `lib/loop9_automation/config.py`

目标：
- 让 audit 与 real-poc 在**真正 launch 前**共用同一套保护逻辑
- 避免“prompt 里说一套、脚本里又是另一套”

### C. 入口接入点

- audit：`Super8/.opencode/_scripts/loop9_authorized_review.py`
- real-poc：`skills/loop9-real-poc/scripts/run_loop9_real_poc.py`

这样无论是 cron 触发还是手工直接调用 canonical entrypoint，都会先过 guard。

### D. real-poc 锁槽位配置化

`lib/loop9_automation/state.py` 不再把 poc slot 数写死为 2。
改为从配置读取，并兼容旧的 `poc-slot-*.json` 文件，避免从 2 降到 1 之后旧锁文件直接失踪于视野之外。

## 本次默认阈值

见 `config/loop9-dispatch.json`：

- `audit.maxConcurrent = 1`
- `poc.maxConcurrent = 1`
- `launchGuard.swapUsedMiBMax = 8192`
- `launchGuard.dataAvailGiBMin = 20`
- `launchGuard.rootAvailGiBMin = 20`
- `launchGuard.activeOpencodeCountMax = 3`
- `launchGuard.activeOpencodeRssMiBMax = 12288`
- `launchGuard.virtualizationRssMiBMax = 2048`

## 关联更新

- `lib/loop9_automation/detect.py`
  - audit / poc 的 plan 逻辑都开始读取配置上限
- `plans/loop9_cron/loop9-cron-agentturn-audit.md`
  - 改为配置驱动 + 守门脚本驱动
- `plans/loop9_cron/loop9-cron-agentturn-poc.md`
  - 改为配置驱动 + 守门脚本驱动

## 验证目标

1. Python 文件全部 `py_compile` 通过
2. `python3 bin/loop9-launch-guard show audit --json` 能输出配置与快照
3. `python3 bin/loop9-launch-guard check audit --json` 能输出 allow/block 判断
4. `./bin/loop9-dispatch plan poc --json` 仍能正常工作，并带出配置化上限信息
