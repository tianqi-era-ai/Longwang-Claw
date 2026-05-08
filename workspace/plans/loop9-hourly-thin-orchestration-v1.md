# Loop9 小时级薄调度方案 v1

## 目标

只做一层**薄调度**，不做总控平台。

当前公开示例保留五条小时级 lane：

- `0,30` 分：audit（仓库审计）
- `5,25,45` 分：poc（real-poc）
- `15,50` 分：publish（静态 Audit/PoC 产物上传/同步）
- `35` 分：delivery report publisher（标准交付报告上传）
- `55` 分：verify-v4 auto runner（动态环境搭建与 PoC 复现 carrier 启动）

各 lane 彼此独立，并发上限仍从 `workspace/config/loop9-dispatch.json` 读取。

## 硬约束

1. **已有 skill 是主角，dispatcher 只是门卫**
2. **可以有统一状态视图，但不能单点真相依赖**
3. **每次发车前实时复查事实**
4. **PoC 完成判定必须看 workflow 级状态，不得偷懒看 round passed**
5. **低置信度 publish 推迟，不在后台 inline 反问用户**

## 当前实现边界

已实现：

- `bin/loop9-dispatch plan <kind>`
  - 计算当前是否应跳过 / 发车
  - 检查 per-kind lock
  - audit: 扫描 `targets/` 与已有 Loop9 run
  - poc: 调用 `refresh_real_poc_status.py` 看 workflow 是否完成
  - publish: 调用 `build_publish_plan.py` + Feishu state 判断是否需要增量同步
- `bin/loop9-dispatch claim/release/clear/defer/show-lock`
  - 提供最小锁 / defer / 历史记录能力
- `bin/loop9-dispatch cooldown-set/cooldown-show/cooldown-clear`
  - 提供失败后按候选目标短时冷却的能力，避免反复撞同一对象
- 本地状态目录：`automation-state/loop9/`

尚未启用：

- 真正的 cron job 安装
- 以 agentTurn 方式把 plan/claim 与 skill 调用串起来

## 状态目录

- `automation-state/loop9/locks/<kind>.json`
- `automation-state/loop9/cooldowns/<kind>/<candidate>.json`
- `automation-state/loop9/history.jsonl`
- `automation-state/loop9/deferred.jsonl`

说明：

- 锁只是**辅助门禁**，不是世界真相。
- cooldown 只是**失败后的短时避让**，不是永久判死刑。
- audit / poc 的最终“是否正在跑”仍优先看 observe 目录。
- publish 因为没有长期 observe 目录，所以更依赖短时锁，但仍应结合 Feishu state 做幂等判断。

## v1 的保守策略

### audit

- 只挑 `targets/` 下**还没有已完成审计 run** 的目标
- 对“已有完成 run 但想重跑”的情况，v1 默认不自动重跑
- 这是保守故意设计，避免系统偷偷二刷老项目

### poc

- 只挑已有 completed audit run 的目录
- 每次用 `refresh_real_poc_status.py` 重新计算 workflow 级状态
- `workflow_completion=passed` 才算完成

### publish

- 只挑 completed audit run
- 用 `build_publish_plan.py` 生成计划
- 若 `project.confidence=low`：
  - 不自动发布
  - 记入 `deferred.jsonl`
  - 后续由心跳/汇总告知用户
- 若 Feishu state 显示 artifact 缺失或内容 hash 变化：才视为需要同步

## 手动计划检查入口

先不要急着挂真实 cron。当前推荐先跑：

```bash
~/.openclaw/workspace/bin/loop9-dispatch plan audit
~/.openclaw/workspace/bin/loop9-dispatch plan poc
~/.openclaw/workspace/bin/loop9-dispatch plan publish
~/.openclaw/workspace/bin/loop9-cron-install --summary
```

它们会分别用于：

- 输出 `audit / poc / publish` 三类当前 plan
- 输出最终 cron 定义摘要（默认全 disabled）

用来确认：

- 是否因 lock 跳过
- 是否因 cooldown 跳过
- 当前候选是谁
- 当前发车理由是什么
- 最终 cron 定义是否仍保持 disabled

## 下一步接线方式（建议）

建议用 3 个 isolated cron agentTurn，而不是 main-session systemEvent。

当前仓库内已经有一个只负责输出最终 disabled 定义的辅助脚本：

```bash
~/.openclaw/workspace/bin/loop9-cron-install
```

注意：它当前**不会真的安装 cron**，只会输出定义，避免再次出现“边开发边接真实 cron”的错误。

每个 cron agentTurn 做：

1. 读对应 skill
2. `bin/loop9-dispatch plan <kind>`
3. 若应跳过：直接 `NO_REPLY`
4. 若应执行：
   - 先 `claim`
   - 在真正进入长任务/同步前，先向 `<announce-topic>` 发一条很短的“开始通知”
   - 再调用对应 skill
   - publish 成功后 `release publish --status completed`
   - publish 失败后 `release publish --status failed`，并视情况 `cooldown-set publish ...`
   - audit/poc 发车后可不立刻 release，交给短时锁 + observe 检查共同防重
   - 若 audit/poc 启动失败，则 `release ... --status failed` 并进入 cooldown

## 收尾进度（当前还剩 3 步）

### Step 1（已完成）
- 薄调度内核
- lock / defer / cooldown
- audit / poc / publish 候选扫描
- 手动计划检查入口

### Step 2（进行中）
- 把 3 个 cron agentTurn 执行稿压成更强约束的“傻瓜版”执行稿
- 明确成功 / 失败 / cooldown / defer 时的动作

### Step 3（进行中）
- 形成“可安装但默认 disabled”的 cron 定义最终版
- 做一轮从定义到手动计划检查的最终交叉复核
- 交给你拍板是否真的挂上 cron

## 一个明确未决点

v1 故意没有自动处理：

- 审计 rerun 策略
- publish 的优先级队列
- 更细的 cooldown / retry 分层
- `publish` 成功后的二次确认回写（当前仍主要依赖 Feishu state 与 artifact hash）

这些可以后续加，但不应该先于 v1 基础门禁落地。

## 当前结论

到现在为止，v1 已经达到：

- **可计划**（plan）
- **可门禁**（lock / cooldown / defer）
- **可手动检查**（plan + cron summary）
- **可生成最终 disabled cron 定义**

但仍然**故意未把真实 cron 挂上去**。
这一步保留给最后的人类确认。
- 额外的人机可见性增强：dispatcher 一旦确认“本轮真的要执行”，会先向 `<announce-topic>` 发送一条开始通知，再进入长任务或同步。
