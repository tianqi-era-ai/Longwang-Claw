# Longwang-Claw｜给 AI 的装配说明

这份文档不是普通 README，而是给 OpenClaw、小龙虾、Codex、OpenCode 或其它 AI 直接读取后，参照执行装配用的说明。

## 装配目标

把本仓中的内容放回一套真实可用的本地目录里，核心目标是恢复出：

- `Audit`
- `Env Bootstrap`
- `自动化验证`
- `Real-PoC`
- `标准交付报告`
- `状态查看与长任务观察`

## 目录约定

默认按下面的目录理解，不要擅自发明新层：

```text
~/.openclaw/
  workspace/
    bin/
    lib/
    config/
    plans/
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

如果当前机器上还没有这套目录，优先按这个结构创建，再把本仓对应文件放进去。

## 当前必须落位的目录

1. `workspace/bin/`
2. `workspace/lib/`
3. `workspace/config/`
4. `workspace/plans/`
5. `workspace/skills/`
6. `workspace/Super8/.opencode/`
7. `workspace/Super8/START_HERE_Loop9.md`
8. `workspace/Super8/README.loop9-local.md`
9. `workspace/Super8/.gitignore`

## 装配顺序

1. 先确认目标根目录：`~/.openclaw/workspace/`
2. 把 `workspace/lib/` 放好
3. 把 `workspace/bin/` 放好
4. 把 `workspace/config/` 与 `workspace/plans/` 放好
5. 把 `workspace/skills/` 放好，确保 skill 内部的 `references/`、`scripts/`、`template/` 一起带上
6. 把 `workspace/Super8/.opencode/command/`、`agents/`、`_scripts/`、`_xml/` 放好
7. 把 `workspace/Super8/.opencode/package.json`、`bun.lock`、`OpenCode——审计0day——傻瓜流程.md`、`loop9_wrapped_audit/` 放好
8. 把 `workspace/Super8/START_HERE_Loop9.md`、`workspace/Super8/README.loop9-local.md`、`workspace/Super8/.gitignore` 放好
9. 再检查关键入口是否存在

## 当前关键入口

- `workspace/bin/loop9-dispatch`
- `workspace/bin/loop9-launch-guard`
- `workspace/bin/loop9-cron-install`
- `workspace/bin/loop9-verify-v4-auto-run.sh`
- `workspace/bin/git-sync-openclaw-super8`
- `workspace/bin/openclaw-docker-inventory.py`
- `workspace/skills/loop9-rce-audit-focus/SKILL.md`
- `workspace/skills/loop9-rce-inventory/SKILL.md`
- `workspace/skills/loop9-unauth-inventory/SKILL.md`
- `workspace/skills/loop9-feishu-publisher/SKILL.md`
- `workspace/skills/loop9-feishu-delivery-publisher/SKILL.md`
- `workspace/skills/loop9-wrapped-audit/SKILL.md`
- `workspace/skills/loop9-status/SKILL.md`
- `workspace/skills/loop9-verify-v4/SKILL.md`
- `workspace/skills/loop9-verify-v4-env-bootstrap/SKILL.md`
- `workspace/skills/loop9-real-poc/SKILL.md`
- `workspace/skills/loop9-delivery-reports/SKILL.md`
- `workspace/Super8/.opencode/command/loop9.md`
- `workspace/Super8/.opencode/agents/loop9-controller.md`
- `workspace/Super8/.opencode/agents/loop9-solver.md`
- `workspace/Super8/.opencode/agents/loop9-validator.md`
- `workspace/Super8/.opencode/agents/loop9-refiner.md`
- `workspace/Super8/.opencode/loop9_wrapped_audit/SKILL.md`
- `workspace/Super8/.opencode/_scripts/loop9_authorized_review.py`
- `workspace/Super8/.opencode/_scripts/loop9_status.sh`
- `workspace/Super8/.opencode/_scripts/split_loop9_xml.py`
- `workspace/Super8/.opencode/_xml/loop9.master.xml`
- `workspace/Super8/.opencode/package.json`
- `workspace/Super8/.opencode/bun.lock`
- `workspace/Super8/.opencode/OpenCode——审计0day——傻瓜流程.md`
- `workspace/Super8/START_HERE_Loop9.md`
- `workspace/Super8/README.loop9-local.md`

## 建议一并给 AI 读取的设计稿

如果装配者不只是复制文件，而是还要理解这套主线怎么接、哪些 skill 负责什么、哪些输入输出不能乱改，建议把下面这些计划稿一并喂给 AI：

- `workspace/plans/2026-03-26-loop9-concurrency-config-and-launch-guard.md`
- `workspace/plans/2026-03-16-heartbeat-loop9-status-subagent-design.md`
- `workspace/plans/2026-03-17-loop9-real-poc-preflight-skill.md`
- `workspace/plans/2026-03-28-loop9-远程-docker-靶场宿主机方案草案.md`
- `workspace/plans/2026-03-29-loop9-artifact-consumer-judgement-v0.md`
- `workspace/plans/2026-03-27-loop9-asset-evidence-skill-io-contract-v1.md`
- `workspace/plans/2026-04-09-ai-native-development-skill-plan.md`
- `workspace/plans/loop9-rce-skill-methodology-plan-2026-03-18.md`

这些文件是解释层，不是运行态目录；它们的作用是帮助 AI 参照着还原接线方式、理解方法论和边界，不是替代 `bin/`、`skills/`、`lib/` 本体。

## 关键约束

- 不要把 `skills/` 只拷 `SKILL.md`，要一起保留 `references/`、`scripts/`、`template/`
- 不要把 `workspace/lib/` 漏掉，否则 `bin` 和部分 skill 脚本会断
- 不要把 `workspace/Super8/.opencode/command/`、`agents/`、`_scripts/`、`_xml/` 改名
- 不要擅自把路径体系改成别的样子，优先保持 `~/.openclaw/workspace/...`
- 如果引用材料里仍残留类似 `/Users/<name>/.openclaw/...` 的旧路径，把它理解成“当前操作者自己的 `~/.openclaw/...`”，不要把用户名本身当成硬约束

## 外部依赖与可选环境

这批仓库内容本身不带外部工具二进制，但默认会依赖这些外部能力：

- 基础命令：`python3`、`git`
- 自动化主线：`opencode`
- verify-v4 auto：`codex`
- 后台运行/观察：`tmux`
- 容器与靶场：`docker`、`docker compose`（按需）
- 可选同步能力：Feishu 相关 MCP / tool 能力

当前这台机器上能确认到的是：

- 已存在 `~/.codex/`
- 没看到 `~/codex/`
- 没看到 `~/opencode/`

所以对其它操作者或 AI 来说，不要硬编码 `~/codex`、`~/opencode` 这种路径；优先按“命令是否在 PATH 中可用”来判断。

如果当前环境不是本机 Docker，而是把 runtime 放到远端 Linux / 腾讯云 CVM 宿主机上跑，优先按下面这条路线理解：

- 控制面仍在本地 `~/.openclaw/workspace`
- 远端机器只承担 Docker / compose / 对外复测 runtime
- 默认走 `SSH + rsync + docker compose` 这类薄远程执行，不额外发明厚控制面
- 先读 `workspace/plans/2026-03-28-loop9-远程-docker-靶场宿主机方案草案.md`

## 薄初始化脚本

如果你不是手动装配，而是想快速把本仓内容回填到 `~/.openclaw/workspace/`，可以直接跑：

```bash
python3 scripts/bootstrap_openclaw_layout.py --workspace-root ~/.openclaw/workspace
```

这个脚本只做**直接复制仓库里已有文件**，不引入 manifest，不碰 runtime state，也不会替你安装 `opencode` / `codex` / `docker`。

## 当前不在本仓第一批范围内的内容

这版仓库重心是自动化主线本身，不是运行态数据。

因此当前不应把下列本地运行态目录当作首批公开资产去恢复：

- auth / pairing / device / session / logs
- 本地 cron 运行记录
- 本地 memory / tmp / runs / automation-state
- 实际 targets 源码目录
- 实际 reports 交付产物目录
- `~/.codex/sessions/`、`~/.config/opencode/` 这类本机运行态/账号态目录

## 推荐阅读顺序

1. `docs/20-核心工作流全景总览.md`
2. `docs/31-Dispatcher主线说明.md`
3. `docs/33-Skill_Tool_Wrapper_Harness工程说明.md`
4. `docs/OpenClaw_实装入口设计.md`
5. `workspace/plans/2026-03-29-loop9-artifact-consumer-judgement-v0.md`
6. `workspace/plans/2026-03-28-loop9-远程-docker-靶场宿主机方案草案.md`
7. `workspace/Super8/START_HERE_Loop9.md`
8. `workspace/skills/ai-native-development/SKILL.md`
9. `workspace/skills/loop9-verify-v4/SKILL.md`
