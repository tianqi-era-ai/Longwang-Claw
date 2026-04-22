# 2026-04-09 ai-native-development skill 与 Rapper6 边界重构计划

- [x] 读取并重定位当前主约束：AGENTS.md / AGENTS_PLUS.md / TOOLS.md / skill-creator / 相关 memory
- [x] 确认用户口径：`ai-native-development` 为新 skill 名；默认路由改为“能用 AI 原生开发 skill 的，默认都不用传统开发 skill”
- [x] 梳理 Rapper6 / 复杂开发协议 当前边界与误触发来源
- [x] 新建 `skills/ai-native-development/` skill（实战护栏型，不做官僚协议）
- [x] 明确写入：AI 原生开发 vs 传统开发 的路由边界、禁止线、下沉规则
- [x] 收紧 `AGENTS_PLUS.md` 中《小龙虾复杂开发协议（最小可行版 v0.3）》的触发条件，明确其只面向“脚本和程序原生优先的传统开发项目”
- [x] 在 `TOOLS.md` / `AGENTS.md` 里补一条高显眼规则：AI workflow / Agent / LLM app / AI-native 功能设计，默认优先 `ai-native-development`
- [x] 自检：确认新旧规则不会互相打架；确认没有把 AI 原生任务再吸回 Rapper6/复杂开发协议
- [ ] git checkpoint

## 本轮已完成的关键实现

- 已创建：`skills/ai-native-development/`
  - `SKILL.md`
  - `references/routing-and-boundaries.md`
- 已打包：`skills/dist/ai-native-development.skill`
- 已把边界写回：
  - `AGENTS.md`
  - `TOOLS.md`
  - `AGENTS_PLUS.md`
  - `小龙虾复杂开发协议（最小可行版 v0.3）.md`

## 当前已对齐口径

- 新 skill 名：`ai-native-development`
- 它覆盖一整类：AI workflow、AI Agent、LLM 应用、AI 大模型主导模拟功能、AI 原生主导功能设计
- 它是“实战护栏 skill”，不是重型协议
- 默认路由：能用 AI 原生开发 skill 的，默认都不用传统开发 skill
- Rapper6 / 小龙虾复杂开发协议：只允许用于脚本和程序原生优先的传统开发项目
