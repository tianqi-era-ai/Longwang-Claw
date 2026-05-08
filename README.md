# Longwang-Claw

`Longwang-Claw` 是一套可直接回填到 `~/.openclaw` 的公开工作区装配仓。
它保留龙王小龙虾的核心工作流闭包，但不携带运行态数据、案例产物或账号态配置。

## 这里有什么

- `extensions/openclaw-lark/`
- `workspace/bin/`
- `workspace/lib/`
- `workspace/config/`
- `workspace/hooks/`
- `workspace/plans/`
- `workspace/plugins/`
- `workspace/skills/`
- `workspace/heartbeat/`
- `workspace/prompts/`
- `workspace/Super8/.opencode/`
- `workspace/Super8/*.md`
- `workspace/HEARTBEAT.md`
- `workspace/OpenClaw_实装入口设计.md`
- `workspace/TELEGRAM_小龙虾封装说明.md`
- `workspace/REPO-STRUCTURE.md`
- `scripts/bootstrap_openclaw_layout.py`
- `docs/`

## 这里不放什么

- `reports/`
- `runs/`
- `targets/`
- `logs/`
- `memory/`
- `~/.openclaw/openclaw.json`
- `.config/opencode/`
- `.codex/sessions/`
- `node_modules/`
- `__pycache__/`
- CI / smoke / demo / target-sync 之类的外围闭环

## 怎么回填

```bash
python3 scripts/bootstrap_openclaw_layout.py --workspace-root ~/.openclaw/workspace
```

如果目标根不是默认的 `~/.openclaw`，再显式传入：

```bash
python3 scripts/bootstrap_openclaw_layout.py \
  --openclaw-root /absolute/path/to/.openclaw \
  --workspace-root /absolute/path/to/.openclaw/workspace
```

这个脚本只复制仓库里已经存在的文件，不引入 manifest，也不安装运行时。

## 本地前置

- `python3`
- `git`
- `Node.js >= 22`（用于 `extensions/openclaw-lark/`）
- 使用资产探测工具前，在 shell 里自行设置：
  - `FOFA_KEY`
  - `HUNTER_API_KEY`
  - `SHODAN_KEY`

## 先读什么

- `docs/仓库填充计划.md`
- `docs/给AI的装配说明.md`
- `docs/20-核心工作流全景总览.md`
- `docs/31-Dispatcher主线说明.md`
- `docs/32-定时任务与长任务调度说明.md`
- `docs/33-Skill_Tool_Wrapper_Harness工程说明.md`
- `docs/OpenClaw_实装入口设计.md`
