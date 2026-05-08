# LongWangClaw｜AI 装配与质检说明

这份文档给 OpenClaw、OpenCode、Codex 或其它 AI 读取。你的目标是把公开仓装配成一个本机可跑的 LongWangClaw 工作区，并用 doctor 判断端到端闭环差什么。

## 不要先发明新目录

只认这套公开结构：

```text
LongWangClaw/
  workspace/
    bin/
    lib/
    config/
    hooks/
    heartbeat/
    plans/
    plugins/
    prompts/
    skills/
    Super8/.opencode/
    Super8/工作流_提示词工程/
  extensions/openclaw-lark/
  templates/
  scripts/
  docs/
```

装配到本机后对应：

```text
~/.openclaw/
  extensions/openclaw-lark/
  workspace/
    bin/
    lib/
    config/
    hooks/
    heartbeat/
    plans/
    plugins/
    prompts/
    skills/
    Super8/.opencode/
    Super8/工作流_提示词工程/
```

不要创建 `src/` 重构版，不要新增 adapters，不要新增 targets/demo/CI/smoke。

## 标准步骤

1. 回填公开工作区：

```bash
python3 scripts/bootstrap_openclaw_layout.py --workspace-root ~/.openclaw/workspace
```

2. 复制 profile：

```bash
cp workspace/config/longwang.example.json workspace/config/longwang.local.json
```

3. 让用户或上层 AI 填 `longwang.local.json`。不要猜真实 token。

4. 渲染前检查：

```bash
python3 scripts/render_longwang_config.py --profile workspace/config/longwang.local.json --dry-run
```

这一步会同时检查 OpenClaw、OpenCode、Codex、cron、env 模板，以及 OpenCode agents 的 `model` / `variant` 是否能从统一 profile 渲染。

5. 全局 doctor：

```bash
python3 scripts/longwang_doctor.py --profile workspace/config/longwang.local.json --json
```

6. 只按 doctor 的 lane 结果修补：

- `audit`
- `real_poc_static`
- `static_feishu_publish`
- `dynamic_verify`
- `delivery_report`
- `delivery_feishu_publish`
- `cron`

7. 用户确认 profile 填完后，才写本机配置：

```bash
python3 scripts/render_longwang_config.py --profile workspace/config/longwang.local.json --write
```

写入后，`~/.openclaw/workspace/Super8/.opencode/agents/*.md` 的 frontmatter 应与 `models.opencode.agentModel` 和 `models.opencode.variant` 一致。

## 六段闭环怎么判断

### audit

必须存在：

- `workspace/skills/loop9-wrapped-audit/SKILL.md`
- `workspace/Super8/.opencode/command/loop9.md`
- `workspace/Super8/.opencode/agents/loop9-controller.md`
- `workspace/Super8/.opencode/_scripts/loop9_authorized_review.py`
- `opencode`
- `tmux`

### real_poc_static

必须存在：

- `workspace/skills/loop9-real-poc/SKILL.md`
- `workspace/skills/loop9-real-poc/scripts/run_loop9_real_poc.py`
- `workspace/skills/loop9-real-poc/scripts/refresh_real_poc_status.py`
- `opencode`
- `tmux`

### static_feishu_publish

必须存在：

- `workspace/skills/loop9-feishu-publisher/SKILL.md`
- `extensions/openclaw-lark/`
- Feishu app 私有配置
- `~/.openclaw/workspace/memory/loop9-feishu-publisher-state.json` 可创建或可写

### dynamic_verify

必须存在：

- `workspace/skills/loop9-verify-v4/SKILL.md`
- `workspace/skills/loop9-verify-v4-env-bootstrap/SKILL.md`
- `workspace/skills/loop9-verify-v4-finding-replay/SKILL.md`
- `workspace/bin/loop9-verify-v4-auto-run.sh`
- `codex`
- `docker`
- `remoteRuntime.*` 或等效本机 Docker runtime 配置

### delivery_report

必须存在：

- `workspace/skills/loop9-delivery-reports/SKILL.md`
- `workspace/skills/loop9-delivery-reports/scripts/build_repo_delivery_reports.py`

### delivery_feishu_publish

必须存在：

- `workspace/skills/loop9-feishu-delivery-publisher/SKILL.md`
- `workspace/skills/loop9-feishu-delivery-publisher/scripts/build_report_publish_plan.py`
- Feishu app 私有配置

### cron

必须存在五条 lane：

- Audit
- Real-PoC
- 静态 raw artifact 发布
- 标准交付报告发布
- Verify V4 Auto Runner

公开示例文件：

```text
workspace/plans/loop9-hourly-cron-jobs.example.json
```

本机真实文件由模板渲染：

```text
templates/cron/jobs.json.tpl -> ~/.openclaw/cron/jobs.json
```

## 修补原则

- 先修 profile 和模板渲染，再修脚本。
- 先看 doctor JSON，不要靠猜。
- 若缺 token / 私钥 / app secret，停止并让用户本机填写，不要从历史文件里搜真实值。
- 若缺 `reports/` / `runs/` / `targets/`，不要补进仓库；这些是运行产物或靶标源码。
- 若某条 lane 因示例 profile 占位而 blocked，这是正常状态，不代表公开仓缺资产。
- 若 Python/Bash/Node 语法失败，优先修具体文件，不要重构工作流。

## 禁止操作

- 不要复制 `~/.openclaw/openclaw.json`。
- 不要复制 `~/.config/opencode/opencode.json`。
- 不要复制 `~/.codex/config.toml` 或 sessions。
- 不要复制 `reports/`、`runs/`、`targets/`、`memory/`、`logs/`。
- 不要把 Feishu / Telegram / OpenAI / FOFA / Hunter / Shodan 的真实 key 写入仓库。
- 不要新增 CI、smoke、demo、target-sync 作为本轮装配条件。
- 不要把宣发/运营材料或首发案例名单补进仓库；这些只作为宣发侧人工选材。

## Harness

Harness 已单独放在仓库根目录 `harness/`。它是高级控制面说明层，不是新的 runtime 入口。

AI 可以阅读：

- `harness/README.md`
- `harness/loop9-verify-v4-control-contract.md`

但修补运行链路时仍以 `workspace/skills/loop9-verify-v4/` 下的 active refs 为准。不要把 Harness 扩展成厚 orchestrator、CI、smoke 或 demo。
