# Longwang-Claw｜给 AI 的装配说明

这份文档给 OpenClaw、Codex、OpenCode 或其它 AI 直接读取后按图装配用。
只做“复制现有公开资产”，不做推断式补齐。

## 装配目标

把仓库回填成一套可直接落回 `~/.openclaw` 的公开工作区，核心闭环是：

- `Audit`
- `Env Bootstrap`
- `自动化验证`
- `Real-PoC`
- `标准交付报告`
- `状态查看与长任务观察`

## 目录约定

默认只认下面这套结构，不要擅自发明新层：

```text
~/.openclaw/
  extensions/
    openclaw-lark/
  workspace/
    HEARTBEAT.md
    OpenClaw_实装入口设计.md
    TELEGRAM_小龙虾封装说明.md
    REPO-STRUCTURE.md
    bin/
    lib/
    config/
    hooks/
    heartbeat/
    plans/
    plugins/
    prompts/
    skills/
    Super8/
      .gitignore
      START_HERE_Loop9.md
      README.loop9-local.md
      .opencode/
        package.json
        bun.lock
        OpenCode——审计0day——傻瓜流程.md
        command/
        agents/
        loop9_wrapped_audit/
        _scripts/
        _xml/
```

如果机器上还没有这套目录，先按这个结构建好，再把仓库里的对应文件放进去。

## 先装什么

1. 先放 `workspace/HEARTBEAT.md`、`workspace/OpenClaw_实装入口设计.md`、`workspace/TELEGRAM_小龙虾封装说明.md`、`workspace/REPO-STRUCTURE.md`
2. 再放 `workspace/lib/` 和 `workspace/bin/`
3. 再放 `workspace/config/`、`workspace/hooks/`、`workspace/heartbeat/`、`workspace/prompts/`
4. 再放 `workspace/plans/`、`workspace/plugins/`、`workspace/skills/`
5. 再放 `workspace/Super8/.opencode/` 及 `workspace/Super8/*.md`
6. 如需飞书通道能力，再放 `extensions/openclaw-lark/`

## 明确要保留的原样目录

- `workspace/bin/`
- `workspace/lib/`
- `workspace/config/`
- `workspace/hooks/`
- `workspace/heartbeat/`
- `workspace/plans/`
- `workspace/plugins/`
- `workspace/prompts/`
- `workspace/skills/`
- `workspace/Super8/.opencode/`
- `workspace/Super8/*.md`
- `extensions/openclaw-lark/`

其中 `workspace/skills/` 必须连同 `references/`、`scripts/`、`template/` 一起保留。

## 明确不要搬的东西

- `reports/`
- `runs/`
- `targets/`
- `logs/`
- `memory/`
- `~/.openclaw/openclaw.json`
- `~/.config/opencode/`
- `~/.codex/sessions/`
- `node_modules/`
- `__pycache__/`
- 任何案例产物、宣发材料、demo、CI、smoke、target-sync 资产
- 任何运行态缓存、会话、日志、临时目录

## 外部依赖

公开仓本身不自带这些工具，但装配与运行时会默认依赖它们：

- `python3`
- `git`
- `Node.js >= 22`（`extensions/openclaw-lark/`）
- `opencode`
- `codex`
- `tmux`
- `docker` / `docker compose`（按需）

如果你要跑资产探测相关工具，先在 shell 里设置：

- `FOFA_KEY`
- `HUNTER_API_KEY`
- `SHODAN_KEY`

仓库里不再提供这些 key 的默认明文值。

## 怎么装配

直接运行薄装配脚本：

```bash
python3 scripts/bootstrap_openclaw_layout.py --workspace-root ~/.openclaw/workspace
```

自定义根目录时：

```bash
python3 scripts/bootstrap_openclaw_layout.py \
  --openclaw-root /absolute/path/to/.openclaw \
  --workspace-root /absolute/path/to/.openclaw/workspace
```

这个脚本只复制仓库中已经存在的文件，不引入 manifest，也不替你安装运行时。

## 推荐阅读顺序

1. `docs/仓库填充计划.md`
2. `docs/20-核心工作流全景总览.md`
3. `docs/31-Dispatcher主线说明.md`
4. `docs/32-定时任务与长任务调度说明.md`
5. `docs/33-Skill_Tool_Wrapper_Harness工程说明.md`
6. `workspace/HEARTBEAT.md`
7. `workspace/heartbeat/loop9-status-dispatch.md`
8. `workspace/OpenClaw_实装入口设计.md`
9. `workspace/TELEGRAM_小龙虾封装说明.md`
10. `workspace/Super8/START_HERE_Loop9.md`
11. `workspace/skills/ai-native-development/SKILL.md`
12. `workspace/skills/loop9-verify-v4/SKILL.md`
