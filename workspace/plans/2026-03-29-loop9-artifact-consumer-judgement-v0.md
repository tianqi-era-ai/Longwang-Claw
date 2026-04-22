# 2026-03-29 Loop9 artifact-consumer judgement v0

[协议启动]
- 任务：把 unified blocker class `env/build-artifact/consumer-dockerfile` 落成 planner 可接入的前置判断规范
- 运行模式：GATED
- 当前阶段：PLAN
- 公开仓对照：本文记录的是旧 `loop9-env-bootstrap` mechanical substrate 上的前置路线判断设计；当前公开仓中可直接对照的 active child-stage 入口是 `skills/loop9-verify-v4-env-bootstrap/`
- 当前可信状态源：
  - `plans/2026-03-28-loop9-agentic-remediation-philosophy-plan.md`
  - `plans/2026-03-29-loop9-capability-building-remediation-design-first-cut.md`
  - `automation-state/loop9/verify-mainline/capability-building/...`
  - `skills/loop9-env-bootstrap/scripts/run_loop9_env_bootstrap.py`

---

## 1. 当前为什么需要这一步

当前主线已经有：
- capability-building artifact
- model-ready context bundle
- `jeecgboot` / `nginxwebui` 两个强样本
- 一个更高层 unified blocker class 候选：
  - `env/build-artifact/consumer-dockerfile`

但如果下一步直接“顺手改代码”，就很容易再次退化成局部 patch。

所以在真正接 planner 前，必须先把：

> **判断应该发生在哪里、读哪些证据、命中后如何分流**

写成窄规范。

---

## 2. 当前真实代码落点

### 2.1 现有 runtime 选择入口
文件：
- `skills/loop9-env-bootstrap/scripts/run_loop9_env_bootstrap.py`

当前关键函数：
- `choose_runtime(detect, cfg, repo_root)`

当前逻辑大致是：
1. 有 compose → `repo-compose`
2. 有 reusable Dockerfile → `hybrid`
3. 某些 repo-specific local routes
4. 否则 `generated-compose`

### 2.2 当前真实缺口
这段逻辑目前还缺少一个中间判断：

> 有 compose / Dockerfile 并不等于当前 fresh source checkout 可以直接 launch。

在下面两类场景里，这个等号是错的：
- Dockerfile `ADD dist/`
- Dockerfile `COPY target/*.jar`
- README 明示“下载发行 jar”或“先 pnpm build / mvn package”

也就是说：
- 当前 `repo-compose`
- 当前 `hybrid`

都可能在**太早**的时候被选中。

---

## 3. artifact-consumer judgement 的目标

这一步不是要让 planner 突然变得无所不能。

它只负责回答一个更前置的问题：

> 当前 Dockerfile / compose 路线，是不是在消费预构建工件？

如果答案是“是”，那么：
- 不应立即进入 repo-compose / hybrid launch
- 而应优先进入：
  - capability-building candidate
  - 或 prebuild-candidate
  - 或 model-led remediation

---

## 4. 第一版判断输入

### 4.1 Dockerfile 证据
重点看：
- `COPY target/`
- `COPY dist/`
- `ADD dist/`
- `COPY *.jar`
- `COPY build/`
- 其他明显消费工件的路径

### 4.2 README / docs 证据
重点看：
- `pnpm build`
- `npm run build`
- `yarn build`
- `mvn package`
- `gradle build`
- `下载发行 jar`
- `下载 release 包`
- 明示 Docker 路线是部署包消费端，而不是源码构建端

### 4.3 repo shape 证据
重点看：
- 多模块 Java 启动模块
- 前后端分仓/子目录
- 仓库根本没有 `dist/` / `target/` 现成产物
- compose 引用的服务与构建上下文看起来偏部署态

---

## 5. 第一版判断输出

建议在 detect/runtime planning 之间新增一个中间结构：

```json
{
  "artifact_consumer_judgement": {
    "matched": true,
    "confidence": "medium|high",
    "consumer_kind": "frontend-dist|java-jar|generic-build-output",
    "evidence": ["..."],
    "recommended_branch": "capability-building|prebuild-candidate",
    "should_block_direct_launch": true
  }
}
```

---

## 6. 第一版分流语义

### 命中前
当前：
- compose → repo-compose
- dockerfile → hybrid

### 命中后
改成：
- 先不要直接 repo-compose / hybrid launch
- 先输出一个显式 judgement
- 然后交给外层 dispatcher / capability-building 继续消费

一句话：

> 先承认“这条路线当前不像能直接 launch”，而不是先 launch 失败后再补诊断。

---

## 7. 两个强样本如何支撑这条规范

### JeecgBoot
- `README`: `pnpm install`, `pnpm build`
- `Dockerfile`: `ADD dist/ /var/www/html/`
- 失败：`/dist not found`

结论：
- 很强的 `frontend-dist artifact consumer`

### nginxwebui
- `README`: `下载最新版发行包jar`
- `Dockerfile`: `COPY target/nginxWebUI-*.jar /home/nginxWebUI.jar`
- 失败：`/target not found`

结论：
- 很强的 `java-jar artifact consumer`

---

## 8. 当前最薄接入点建议

### 建议接入顺序
1. 在 detect 阶段或 `choose_runtime()` 前，新增 artifact-consumer judgement helper
2. helper 只负责：
   - 读 Dockerfile / README 的强信号
   - 产出 judgement
3. `choose_runtime()` 消费这个 judgement
4. 若命中：
   - 不再直接给出普通 `repo-compose/hybrid`
   - 而是切到一个显式的“不要直接 launch”的中间分支

### 不要做成什么
- 不要一上来就把所有 build-order 全自动修掉
- 不要在这一步顺手补一堆 repo-specific special case
- 不要把 consumer judgement 直接写死成只认 `dist` / `target` 两种字符串

---

## 9. 当前待做项

- [x] 已明确真实代码落点：`choose_runtime()`
- [x] 已明确第一版判断目标与边界
- [x] 已明确两组强样本支撑
- [x] 已完成第一刀最薄代码接线：`detect_stack()` 现已新增 `artifact_consumer_judgement`，`choose_runtime()` 现会把该 judgement 带入 `runtime_plan` 并追加 warning note
- [x] 已完成第二刀 soft-branch 接线：`finalize_booted_partial()` 现会在命中 judgement 且未 ready_for_poc 时，把该问题升级为显式 `E_ARTIFACT_CONSUMER_ROUTE` blocker，并把 `artifact_consumer_judgement`、`blocking_items`、更明确的 `dispatcher_return` 一起写进 `env_result/dispatcher_handoff`
- [x] 已把 judgement helper 的最小 I/O 契约写进 reference：`skills/loop9-env-bootstrap/references/artifact-consumer-judgement.md`
- [x] 已完成第三刀 pre-launch soft reroute：在 `execute_draft_materialize()` / `execute_draft_bootstrap()` 中，若 `should_prelaunch_block_artifact_consumer(runtime_plan)=true`，则会在 `PLAN_RUNTIME` 后直接进入 `FINALIZE_OUTPUT`，写出 `E_ARTIFACT_CONSUMER_ROUTE` partial，并跳过误导性的后续 launch/materialize/boot 路线

---

## 10. 当前一句话

> planner 下一步真正该补的，不是“再聪明一点地重试 Docker”，而是先学会问：**这个 Dockerfile/compose 到底是在生成工件，还是在消费工件？**
