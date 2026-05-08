# LongWangClaw｜给 AI 的装配说明

先读 `docs/AI装配与质检说明.md`。这份文件是兼容旧入口名的短版。

## 必须完成的顺序

```bash
python3 scripts/bootstrap_openclaw_layout.py --workspace-root ~/.openclaw/workspace
cp workspace/config/longwang.example.json workspace/config/longwang.local.json
python3 scripts/render_longwang_config.py --profile workspace/config/longwang.local.json --dry-run
python3 scripts/longwang_doctor.py --profile workspace/config/longwang.local.json --json
```

如果没有授权目标，先跑合成契约夹具：

```bash
python3 scripts/longwang_doctor.py --profile workspace/config/longwang.example.json --contract-fixture fixtures/contract --json
```

这只验证最小文件契约和发布计划解析，不是真实漏洞 demo。

用户填完 `workspace/config/longwang.local.json` 后，才允许：

```bash
python3 scripts/render_longwang_config.py --profile workspace/config/longwang.local.json --write
```

## 目标闭环

- Audit：`workspace/skills/loop9-wrapped-audit/SKILL.md`
- Real-PoC 静态编写：`workspace/skills/loop9-real-poc/SKILL.md`
- 静态 Audit/PoC 产物上传：`workspace/skills/loop9-feishu-publisher/SKILL.md`
- 动态环境搭建与 PoC 复现：`workspace/skills/loop9-verify-v4/SKILL.md`
- 本地标准交付报告：`workspace/skills/loop9-delivery-reports/SKILL.md`
- 动态复现后的标准报告上传：`workspace/skills/loop9-feishu-delivery-publisher/SKILL.md`

## 不要搬

- `~/.openclaw/openclaw.json`
- `~/.config/opencode/opencode.json`
- `~/.codex/config.toml`
- `~/.codex/sessions/`
- `reports/`
- `runs/`
- `targets/`
- `memory/`
- `logs/`
- `.env*`
- 私钥、真实 token、真实 API key
- 宣发/运营材料
- 首发案例名单
- `fixtures/contract/` 到 runtime targets

私有配置统一从 `workspace/config/longwang.local.json` 渲染，或从本机环境变量注入。

Harness 已单独放在 `harness/`，只作为高级控制面说明，不作为新的执行入口或 demo。
