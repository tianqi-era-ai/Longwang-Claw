# Runtime isolation binding (current V4.4 cross-platform reading)

## Purpose

This ref freezes the current **runtime-facing** rule for child execution placement.

Read it together with:
- `references/owner-placement-matrix.md`

The goal is:
- protect repo-level owner at the parent,
- move child-stage work off the parent by default,
- keep the same handoff/verdict contract in isolated runtime,
- stop old `inline by convenience` drift from re-entering as a normal reading,
- and keep one repo flow able to finish **unattended in one continuous run** even if child work waits or blocks for a long time.

## First split to remember

Runtime placement is **not** semantic owner.

So:
- child work may run isolated without gaining repo closure authority,
- parent-owned objects may be isolated-produced without stopping being parent-owned,
- and `must-isolated` is about runtime placement, not about who owns repo truth.

## Canonical cross-platform primitive

For isolated child work, the parent should default to one bounded `child agent / isolated executor`.

Required properties:
- separate context / working-memory boundary from the parent
- thin `stage-handoff.<stage>.md` input instead of inherited long parent context
- writes back into the same current round root for repo-mainline child work,
  or into the same bounded pre-start intake surface for `repo-selection-pack`
- parent may wait / poll / block while the child runs
- child returns through `stage-verdict.<stage>.md`,
  or through `repo-selection-proposal.*.md` for `repo-selection-pack`

Typical platform mappings may differ, for example:
- `OpenClaw = sessions_spawn + runtime=subagent + mode=run + cleanup=delete`
- `Codex = spawn_agent / equivalent child-agent thread`
- `other platforms = any equivalent isolated worker / session / process`

The mapping is adapter detail, not canonical meaning.
Isolation changes runtime mode, not canonical storage root.

Special pre-start exception:
- `repo-selection-pack` may run **before** current round root exists
- so the parent should choose one bounded pre-start intake surface for its request / proposal / acceptance
- only after parent selection acceptance does current round root fix begin

For all later repo-mainline child work,
the parent should already have the current round root fixed before isolated child work begins.

If a platform-level policy blocks one exact primitive,
keep the isolation requirement and choose the nearest equivalent bounded isolated executor instead of silently broadening parent inline context.

The parent may:
- wait,
- poll,
- block,
- and stay in the same repo loop while the child runs.

## Explicit skill invocation = isolation authorization

When the user explicitly invokes `loop9-verify-v4` as the active skill surface,
that invocation should be read as semantic authorization for the bounded
`must-isolated` / `isolated-by-default` child work needed by the same repo mainline.

Hard meaning:
- this is a cross-platform semantic rule, not a one-platform keyword trick
- adapter/runtime choice still belongs to the current platform
- if the platform exposes a compatible child primitive, the parent should use it by default rather than waiting for a second redundant delegation keyword
- if a stricter platform/runtime policy still requires extra approval or blocks child execution, the parent must surface that before stage execution rather than silently normalizing back to parent-inline

## Authorization phrase normalization

For this skill family, the parent should treat the following as equivalent
authorization phrasing when attached to the same request:
- preferred exact phrases:
  - `subagent`
  - `delegation`
  - `parallel agent work`
  - `child agent`
  - `isolated executor`
- equivalent English phrases:
  - `sub-agent`
  - `delegate`
  - `parallel agent`
  - `child worker`
  - `isolated worker`
  - `isolated run`
  - `isolated task`
  - `background task`
  - `background worker`
  - `spawn_agent`
  - `spawn`
  - `forked worker`
  - `separate worker`
  - `separate context`
- equivalent Chinese phrases:
  - `子代理`
  - `子 Agent`
  - `子Agent`
  - `委派`
  - `委托执行`
  - `并行代理`
  - `并行执行`
  - `隔离任务`
  - `隔离执行`
  - `独立执行器`
  - `独立上下文`
  - `后台任务`
  - `后台执行`

Normalization rule:
- case / hyphen / spacing variants count equivalently
- Chinese / English / mixed-language wording counts equivalently when meaning is clear
- adapter-specific API names are hints, not the only valid spellings
- if the user also states a child-model preference such as `same model` or `与主Agent一样的模型`, preserve that preference when supported, otherwise disclose the nearest supported fallback

## Timeout / wobble attribution discipline

When isolated child work is AI-led and output-shape-sensitive:
- timeout is first a **caller-side budget/scheduling failure**, not child truth,
- timeout is first a **caller-side budget/scheduling failure**, not prompt/worker quality evidence,
- one failed run is not enough to conclude semantic failure,
- one successful run is not enough to conclude hardening/robustness.

Required parent discipline:
1. if a child times out before writing a usable `stage-verdict.<stage>.md`, record that as `timeout-budget failure`
2. increase timeout materially and rerun before drawing semantic conclusions
3. do not consume timeout as `blocked-confirmed`, `handoff-required`, or any repo-level truth
4. only inspected runtime/process evidence may promote timeout into prompt/worker diagnosis
5. when wobble is plausible, compare multiple attempts before widening a repair lane or freezing a strong negative judgment
6. keep workflow/agent retry mechanics at the parent dispatcher layer rather than burying them in opaque child defaults
7. keep retry policy/strategy responsibility at the parent dispatcher layer

Selection-stage corollary:
- for `repo-selection-pack`, replace `stage-verdict.<stage>.md` with `repo-selection-proposal.*.md`
- the same timeout / wobble discipline still applies

Do **not** use:
- a platform-specific primitive name as the semantic contract
- a thick job / queue / orchestrator layer

## Frozen stage -> runtime mapping

Current first-wave child placement is now read as:
- `repo-selection-pack = must-isolated` (pre-start stage only)
- `env-bootstrap = must-isolated`
- `finding-replay = must-isolated`
- `distillation = must-isolated`

Hard meaning:
- isolated is now the current production default for first-wave child stages,
- inline is no longer a normal reading of these stages,
- and any later inline use would have to be treated as an explicit manual exception rather than a silent fallback.

## Current inline status

Inline is **not** a current production default for `repo-selection-pack` or first-wave child work.

It is now a **high-threshold manual exception** only.

If a future round ever uses inline at all, all of the following should already be true:
1. the parent must remain fully in place or owner / closure / active-scope freeze would clearly drift,
2. the bounded question is already extremely small and stable,
3. the inline context would actually be smaller than an isolated handoff, not bigger,
4. parent long-context drift would not increase,
5. the executor explicitly knows this is an exception, not a restored default.

Do not silently reopen inline by using phrases like:
- thin enough
- probably okay inline
- quicker this time
- just one shortcut

## Startup disclosure / inline-exception discipline

Before substantial repo work begins, whenever the expected path includes
`must-isolated` or `isolated-produced` work, the parent should explicitly announce one posture:
- `isolated-run confirmed`
- `extra authorization still required`
- `inline-exception required`

Hard meaning:
1. silent inline fallback is forbidden
2. if the platform/runtime still requires extra approval, the parent should pause and surface that explicitly before the affected stage
3. if an inline exception is unavoidable, the parent should say why, keep the effective input as thin as the intended handoff, and record the exception as runtime-placement drift rather than treating inline as normal behavior
4. when the platform supports child runs but a default child model/runtime is incompatible, retry with the nearest supported equivalent before declaring inline necessary

## Same-repo continuation discipline

### Allowed
Current production explicitly allows:
- long child runtime,
- parent wait / poll / block,
- same repo flow staying open while a child runs,
- same repo flow taking time,
- the parent keeping the same run alive while delivery-tail stages are still pending.

### Forbidden
Current production explicitly forbids treating any of the following as the normal continuation path for **the same repo mainline**:
- launch child now, consume verdict in a later user turn,
- `sessions_yield` as the normal way to split one repo round across chats,
- half-run now / resume by later manual conversation,
- leaving repo-level owner temporarily suspended until a fresh chat arrives,
- treating `repo-round-verdict` as “done enough for later chat continuation” while the delivery tail is still pending.

One-line freeze:
- **waiting is allowed; breaking the repo flow across new user turns is not the default continuation path.**

## Parent recovery path

The parent must always do this in the same order:
1. compile / run `repo-selection-pack`
2. accept / reject `repo-selection-proposal`
3. fix the current round root
4. run `repo-start-pack` and freeze active scope back at the parent
5. write `stage-handoff.<stage>.md`
6. freeze the current runtime placement
7. spawn exactly one bounded isolated child run
8. wait / poll / block if needed while keeping the same repo flow alive
9. child writes `stage-verdict.<stage>.md` + artifact refs back into that same round root
10. parent consumes the verdict
11. parent refreshes board -> closure review -> external readout -> repo-round verdict
12. parent continues the same run with `delivery-report-bridge`
13. parent consumes `stage-verdict.delivery-reports.*`
14. parent runs `final-local-review`
15. parent performs one explicit experience-sedimentation check (`no-new-delta` or one thin `learning-delta`)
16. only then may the parent treat the repo mainline as `done` or truthfully tail-blocked

If a child run exits without a usable `stage-verdict.<stage>.md`,
that does **not** count as stage progress.

For `repo-selection-pack`, replace that with:
- no usable `repo-selection-proposal.*.md`
- and do not consume timeout / wobble as semantic selection truth

If the parent has not yet consumed the returned verdict,
that does **not** count as the repo flow being finished.

## Hard boundary

- runtime placement stays parent-owned
- isolation does **not** mean bigger context
- `repo-selection-pack` is stage-only; isolation there does **not** imply admission as an independent child skill
- isolated child work must still follow `references/handoff-compiler.md`
- isolated child work must not create a second canonical output tree
- children may not chain directly to each other
- `repo-selection-pack` may not create the current round root by itself
- except for the bounded pre-start selection surface,
  both parent-owned and child-owned objects must still return into the same current round root / `objects` / `artifacts` split
- child must-isolated placement does **not** grant repo closure authority
- same repo flow may not treat “child launched” as equivalent to “repo round complete enough for later chat continuation”
- same repo flow may not treat `repo-round-verdict` as equivalent to “repo mainline complete enough for later chat continuation”
