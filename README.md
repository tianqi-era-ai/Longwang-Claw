# LongWangClaw

LongWangClaw（龙王小龙虾）是一套可装配到 OpenClaw 工作区里的 AI 原生安全工作流产品包。它的公开目标不是展示孤立脚本，而是让外部用户在填完本机私有配置后，能检查并启动 Audit、Real-PoC、静态产物上传、动态环境搭建与 PoC 复现、本地标准交付报告、动态复现后的标准报告上传这条闭环。

仓库主形态保持为可回填的 `~/.openclaw` 工作区资产，不改成传统 `src/` 包。

## 推荐阅读顺序

1. `docs/首跑验收手册.md`：如何用自己的授权仓库做真实首跑，以及如何使用 contract fixture 做契约检查。
2. `docs/闭环契约地图.md`：六段链路的 owner、入口、输入、输出、ready/blocked 判据。
3. `docs/配置与私有化指南.md`：哪些私有配置必须本机填写，哪些绝对不能入仓。
4. `docs/AI装配与质检说明.md`：给 OpenClaw / OpenCode / Codex 读取的装配和修补步骤。
5. `docs/端到端运行手册.md`：真实六段流程入口。
6. `harness/README.md`：Harness 高级控制面纪律，只读说明层。

## 标准装配路径

```bash
python3 scripts/bootstrap_openclaw_layout.py --workspace-root ~/.openclaw/workspace
cp workspace/config/longwang.example.json workspace/config/longwang.local.json
python3 scripts/render_longwang_config.py --profile workspace/config/longwang.local.json --dry-run
python3 scripts/longwang_doctor.py --profile workspace/config/longwang.local.json
```

用户填完 `workspace/config/longwang.local.json` 后，才写入本机真实配置：

```bash
python3 scripts/render_longwang_config.py --profile workspace/config/longwang.local.json --write
```

## 首跑验收

真实能力验收必须使用用户自己的授权目标。没有授权目标时，只能跑合成契约夹具：

```bash
python3 scripts/longwang_doctor.py \
  --profile workspace/config/longwang.example.json \
  --contract-fixture fixtures/contract
```

`fixtures/contract/` 只验证文件契约和发布计划解析，不包含真实漏洞、真实 target、exploit demo、首发案例或宣发材料。

## 核心目录

- `workspace/bin/`：Loop9 调度、启动守门、verify-v4 自动入口、资产探测薄工具。
- `workspace/lib/`：调度状态、并发、目标门禁、OpenCode runner 薄封装。
- `workspace/config/`：公开调度配置与 `longwang.example.json`。
- `workspace/skills/`：Audit、Real-PoC、Feishu 发布、verify-v4、报告生成等 skill。
- `workspace/Super8/.opencode/`：OpenCode Loop9 command、agents、wrapper 脚本和 XML。
- `workspace/Super8/工作流_提示词工程/`：wrapper 发车所需的公开 prompt 模板，不包含历史案例输出。
- `extensions/openclaw-lark/`：OpenClaw 飞书通道插件源码。
- `templates/`：OpenClaw / OpenCode / Codex / cron / env 的本机私有配置模板。
- `fixtures/contract/`：最小合成契约夹具，只供 doctor 和发布计划解析。
- `scripts/`：bootstrap、配置渲染、全局 doctor。
- `harness/`：Verify V4 Harness 高级控制面说明，不参与 bootstrap 回填。

## 六段执行链

1. Audit：`workspace/skills/loop9-wrapped-audit/SKILL.md`
2. Real-PoC 静态编写：`workspace/skills/loop9-real-poc/SKILL.md`
3. 静态 Audit/PoC 产物上传：`workspace/skills/loop9-feishu-publisher/SKILL.md`
4. 动态环境搭建与 PoC 复现：`workspace/skills/loop9-verify-v4/SKILL.md`
5. 本地标准交付报告：`workspace/skills/loop9-delivery-reports/SKILL.md`
6. 动态复现后的标准报告上传：`workspace/skills/loop9-feishu-delivery-publisher/SKILL.md`

## Doctor 输出

`scripts/longwang_doctor.py` 会同时输出两层结果：

- layer readiness：`repo_static`、`local_config`、`rendered_config`、`toolchain`、`contract_fixture`、`lane_readiness`
- lane readiness：`audit`、`real_poc_static`、`static_feishu_publish`、`dynamic_verify`、`delivery_report`、`delivery_feishu_publish`、`cron`

示例 profile 里保留占位符，所以 Feishu、runtime、cron 默认出现 blocked/partial 是正常状态。填完本机 profile 并渲染后，doctor 应能明确告诉 AI 哪条 lane 已可跑、哪条还差什么。

## 明确不包含

仓库不放真实运行态、账号态、靶标源码和交付产物：

- `reports/`
- `runs/`
- `targets/`
- `logs/`
- `memory/`
- `cron/runs/`
- `~/.openclaw/openclaw.json`
- `~/.config/opencode/opencode.json`
- `~/.codex/config.toml`
- `~/.codex/sessions/`
- `.env*`
- 私钥、token、真实 API key
- 宣发/运营材料
- 首发案例名单
- 真实漏洞报告
- 真实 target/demo

FOFA / Hunter / Shodan、Feishu、OpenAI/OpenCode/Codex、local Docker 或远程 Docker/CVM 等私有值都从 `workspace/config/longwang.local.json` 或本机环境变量注入，不在公开仓内置默认明文值。
