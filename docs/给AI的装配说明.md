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
    Super8/.opencode/_scripts/
```

如果当前机器上还没有这套目录，优先按这个结构创建，再把本仓对应文件放进去。

## 当前第一批必须落位的目录

1. `workspace/bin/`
2. `workspace/lib/`
3. `workspace/config/`
4. `workspace/plans/`
5. `workspace/skills/`
6. `workspace/Super8/.opencode/_scripts/`

## 装配顺序

1. 先确认目标根目录：`~/.openclaw/workspace/`
2. 把 `workspace/lib/` 放好
3. 把 `workspace/bin/` 放好
4. 把 `workspace/config/` 与 `workspace/plans/` 放好
5. 把 `workspace/skills/` 放好，确保 skill 内部的 `references/`、`scripts/`、`template/` 一起带上
6. 把 `workspace/Super8/.opencode/_scripts/` 放好
7. 再检查关键入口是否存在

## 当前关键入口

- `workspace/bin/loop9-dispatch`
- `workspace/bin/loop9-launch-guard`
- `workspace/bin/loop9-cron-install`
- `workspace/bin/openclaw-docker-inventory.py`
- `workspace/skills/loop9-wrapped-audit/SKILL.md`
- `workspace/skills/loop9-status/SKILL.md`
- `workspace/skills/loop9-verify-v4/SKILL.md`
- `workspace/skills/loop9-verify-v4-env-bootstrap/SKILL.md`
- `workspace/skills/loop9-real-poc/SKILL.md`
- `workspace/skills/loop9-delivery-reports/SKILL.md`
- `workspace/Super8/.opencode/_scripts/loop9_authorized_review.py`
- `workspace/Super8/.opencode/_scripts/loop9_status.sh`

## 关键约束

- 不要把 `skills/` 只拷 `SKILL.md`，要一起保留 `references/`、`scripts/`、`template/`
- 不要把 `workspace/lib/` 漏掉，否则 `bin` 和部分 skill 脚本会断
- 不要把 `workspace/Super8/.opencode/_scripts/` 改名
- 不要擅自把路径体系改成别的样子，优先保持 `~/.openclaw/workspace/...`
- 如果引用材料里仍残留类似 `/Users/xlx/.openclaw/...` 的源机器绝对路径，把它理解成“当前操作者自己的 `~/.openclaw/...`”，不要把用户名本身当成硬约束

## 当前不在本仓第一批范围内的内容

这版仓库重心是自动化主线本身，不是运行态数据。

因此当前不应把下列本地运行态目录当作首批公开资产去恢复：

- auth / pairing / device / session / logs
- 本地 cron 运行记录
- 本地 memory / tmp / runs / automation-state
- 实际 targets 源码目录
- 实际 reports 交付产物目录

## 推荐阅读顺序

1. `docs/20-核心工作流全景总览.md`
2. `docs/31-Dispatcher主线说明.md`
3. `docs/33-Skill_Tool_Wrapper_Harness工程说明.md`
4. `docs/OpenClaw_实装入口设计.md`
5. `workspace/skills/ai-native-development/SKILL.md`
6. `workspace/skills/loop9-verify-v4/SKILL.md`
