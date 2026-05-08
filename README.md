# LongWangClaw

LongWangClaw（龙王小龙虾）是一套可装配到 OpenClaw 工作区里的 AI 原生安全工作流资产。它的目标不是展示几个孤立脚本，而是把 Audit、Real-PoC 静态编写、静态产物上传、动态环境搭建与 PoC 复现、本地标准交付报告、动态复现后的报告上传串成一条能运行、能检查、能继续修补的闭环。

这个仓库的主形态是“可回填的 OpenClaw 工作区”，不是重新工程化的 `src/` 包。

## 先读什么

1. `docs/端到端运行手册.md`：真实六段流程入口。
2. `docs/配置与私有化指南.md`：哪些配置必须本机填写，哪些不能入仓。
3. `docs/AI装配与质检说明.md`：给 OpenClaw / OpenCode / Codex 读的装配与修补步骤。
4. `docs/20-核心工作流全景总览.md`：产品工作流全景。

## 快速装配

```bash
python3 scripts/bootstrap_openclaw_layout.py --workspace-root ~/.openclaw/workspace
cp workspace/config/longwang.example.json workspace/config/longwang.local.json
python3 scripts/render_longwang_config.py --profile workspace/config/longwang.local.json --dry-run
python3 scripts/longwang_doctor.py --profile workspace/config/longwang.local.json
```

确认 `workspace/config/longwang.local.json` 已填好私有值后，才写入本机配置：

```bash
python3 scripts/render_longwang_config.py --profile workspace/config/longwang.local.json --write
```

## 核心目录

- `workspace/bin/`：Loop9 调度、启动守门、verify-v4 自动入口、资产探测薄工具。
- `workspace/lib/`：调度状态、并发、目标门禁、OpenCode runner 薄封装。
- `workspace/config/`：公开调度配置与 `longwang.example.json`。
- `workspace/skills/`：Audit、Real-PoC、Feishu 发布、verify-v4、报告生成等 skill。
- `workspace/Super8/.opencode/`：OpenCode Loop9 command 与 agents。
- `workspace/Super8/工作流_提示词工程/`：wrapper 发车所需的两个公开 prompt 模板，不包含历史案例输出。
- `extensions/openclaw-lark/`：OpenClaw 飞书通道插件源码。
- `templates/`：OpenClaw / OpenCode / Codex / cron / env 的本机私有配置模板。
- `scripts/render_longwang_config.py`：从统一 profile 渲染本机配置。
- `scripts/longwang_doctor.py`：全链路 readiness 质检。

## 六段执行链

1. Audit：`workspace/skills/loop9-wrapped-audit/SKILL.md`
2. Real-PoC 静态编写：`workspace/skills/loop9-real-poc/SKILL.md`
3. 静态 Audit/PoC 产物上传：`workspace/skills/loop9-feishu-publisher/SKILL.md`
4. 动态环境搭建与 PoC 复现：`workspace/skills/loop9-verify-v4/SKILL.md`
5. 本地标准交付报告：`workspace/skills/loop9-delivery-reports/SKILL.md`
6. 动态复现后的标准报告上传：`workspace/skills/loop9-feishu-delivery-publisher/SKILL.md`

## 明确不包含

仓库不放真实运行态、真实账号态、靶标源码和交付产物：

- `reports/`
- `runs/`
- `targets/`
- `logs/`
- `memory/`
- `~/.openclaw/openclaw.json`
- `~/.config/opencode/opencode.json`
- `~/.codex/config.toml`
- `~/.codex/sessions/`
- `.env*`
- 私钥、token、真实 API key

FOFA / Hunter / Shodan、Feishu、OpenAI/OpenCode/Codex、远程 Docker/CVM 等私有值都从 `workspace/config/longwang.local.json` 或本机环境变量注入，不在公开仓内置默认明文值。

## 质检目标

`scripts/longwang_doctor.py` 会按 lane 输出 readiness：

- `audit`
- `real_poc_static`
- `static_feishu_publish`
- `dynamic_verify`
- `delivery_report`
- `delivery_feishu_publish`
- `cron`

示例 profile 里保留了占位符，所以 Feishu、远程 runtime、cron 默认会显示 blocked/partial。用户填完本机 profile 并渲染后，doctor 应能明确告诉 AI 哪条 lane 已经可跑、哪条还差什么。
