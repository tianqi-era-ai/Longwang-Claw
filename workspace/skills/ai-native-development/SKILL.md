---
name: ai-native-development
description: |
  AI-native development guardrail for agentic systems, LLM applications, AI workflows, evaluators, planners, dispatchers, coaches, routers, simulators, and other model-led features where the main difficulty is frontier ownership, policy evolution, truth/receipt, or semantic control flow rather than ordinary software implementation. Use when the task is to design or refactor an AI-native workflow or agent system, define thin canonical objects/verdicts/handoffs/receipts, separate model-native reasoning from thin program bridges, prevent false progress in agent systems, or build prompts/control surfaces for AI-led products. Do not use for script/program-first traditional software development, and do not route the parent AI-native task through `coding-agent`; if coding help is needed, keep it as a bounded deterministic substep only.
---

# AI-Native Development

Use this skill when the system being built is **AI-led at its core**. The main job here is not “write more code”; it is to keep the AI-native control surface thin, truthful, and evolvable.

High-severity warning:
- if an AI-native task starts silently sliding into `Python/script-first/program-first` control,
- treat that as a **serious route failure**, not as ordinary implementation detail.

This failure mode is dangerous because once a runner / request schema / helper directory starts acting like the semantic owner, it tends to spread:
- more meaning gets buried in code,
- more later work starts depending on those code surfaces,
- and the system can re-enter a more sophisticated form of `鬼打墙`: no longer obviously fake, but still structurally trapped.

## Mandatory activation protocol

When the user explicitly tells you to read this skill, or when the task plausibly belongs in this lane, do the following **before** proposing implementation details:
1. restate the intended control model in one sentence:
   AI should own meaning; code should only bridge deterministic hard edges.
2. inspect the **live local tree/control surface**, not just abstract intent, prior memory, or clean-history assumptions.
3. actively search for candidate takeover surfaces such as:
   `scripts/`, runner CLIs, request JSON schemas, orchestration-heavy Python, route/gate registries, or helper directories that are starting to carry semantics.
4. ask the hard question first:
   `Did the mainline already drift away from handoff/verdict/receipt into program-first control?`
5. if the answer is even plausibly yes, pause expansion and do a drift audit before adding new machinery.

Required discipline:
- lead with the most severe control-model risk you find, not with convenience improvements,
- prefer subtraction / deletion / demotion over compensating additions when the active lane already drifted,
- inspect the current live files that actually govern the route,
- and do **not** let “it is only an experiment” or “it already exists” justify keeping a wrong control surface active.

## High-visibility uncertainty and timeout discipline

### 1. Treat retry / replay / compare as dispatcher-native duty
In AI-native systems, uncertainty management is part of the parent/dispatcher job itself.

Because model wobble / 随机降智 / output instability / latency variance / occasional long convergence are all native to the terrain, the parent/dispatcher must assume it may need to:
- rerun,
- retry after failure,
- replay the same prompt under a wider budget,
- compare multiple attempts before semantic judgment,
- and separate retry-policy design from semantic design.

This is a **qualitative default**, not a special-case trick:
- the exact retry count / timeout size / replay policy varies by context,
- but the need for retry/replay/compare logic itself is native and expected.

If the dispatcher does not absorb this responsibility, it will keep misdiagnosing normal AI uncertainty as prompt/product failure.

### 2. Treat model variability as native, not exceptional
In AI-native work, model wobble / 随机降智 / output instability is part of the terrain.

Do not assume:
- one bad run proves the prompt/control surface is wrong,
- one good run proves the prompt/control surface is robust,
- one run is enough when the task is fragile and output-shape-sensitive.

When a task is AI-led and the result quality can wobble, the parent/dispatcher must be willing to:
- rerun,
- retry,
- compare multiple attempts,
- and separate `stochastic wobble` from `semantic design failure`.

### 3. Treat timeout as caller-side failure, not prompt-quality evidence
For subagents / delegated runs / worker calls, timeout belongs to the calling contract.

Default reading:
- if a task times out, that is first and foremost **caller under-budgeting / bad timeout estimation / bad scheduling discipline**,
- timeout by itself does **not** say the worker is bad,
- timeout by itself does **not** say the prompt is bad,
- timeout by itself does **not** say the semantic design is wrong.

Required discipline:
- prefer generous timeout budgets for important AI-native runs,
- if a run times out, increase timeout materially and rerun before drawing semantic conclusions,
- record timeout separately as `caller-side budget failure`, not as worker/prompt evidence,
- do **not** use timeout as a quality signal for the worker/prompt unless you have inspected the execution path and found concrete process evidence such as a dead loop, pathological drift, or a clearly prompt-induced non-convergent behavior.

### 4. Separate four different failure classes
Do not collapse these into one bucket:
- `semantic failure` — wrong truth / wrong object / wrong output shape
- `timeout-budget failure` — caller did not give enough time or scheduled badly
- `stochastic wobble` — same setup sometimes succeeds, sometimes fails
- `process-pathology evidence` — inspected runtime/process evidence shows the worker/prompt itself is inducing non-convergence

The parent layer must diagnose which class it is dealing with before widening a repair lane or rewriting the control surface.

## Default routing rule

If a task can plausibly be treated as AI-native, treat it as AI-native **by default**.

Prefer this skill over the traditional complex-development / Rapper6-style lane when the task is about:
- agent or multi-agent behavior
- workflow / dispatcher / planner / coach / router logic
- LLM application mainline behavior
- evaluator / self-repair / reflection / policy loops
- AI-native product features or simulations
- thin canonical objects, verdicts, handoffs, receipts, or learning deltas

Reserve the traditional lane for **script/program-first** projects where the main difficulty is deterministic software implementation.

## Read explicit hazard declarations literally

If the user explicitly tells you to read this skill, or explicitly names a danger such as:
- `鬼打墙`
- `厚 Python 控制面`
- `大 Python orchestrator`
- `script-first`
- `runner became the child`
- `request JSON became the child`
- `AI 原生被程序主导`

you must read the request as:
- a request to inspect for that exact failure family,
- not merely a request to absorb the skill’s general theme.

Required behavior:
- audit the current work/tree/control surface for concrete instances of the named danger,
- surface the most severe mismatch first,
- and do **not** downgrade a control-model threat into “small cleanup” just because the code happens to run.

If the user is warning about AI-native drift, your first question should become:
- `Did the mainline silently become program-first?`

not:
- `Can I make the program version slightly cleaner?`

## Escalation rule when the user has to repeat the warning

If the user needs to:
- repeat the same AI-native warning,
- ask whether you missed something obvious,
- or push you multiple times to re-check the route,

treat that as evidence that you likely **under-applied this skill already**.

Required response:
1. stop defending or extending the current path,
2. re-read this skill and the live files that own the current route,
3. perform a fresh drift/hazard audit,
4. surface the most severe wrong-turn first,
5. only resume implementation after the parent AI-native lane is re-established.

Do not interpret repeated correction as mere preference refinement.
Interpret it as a likely route-failure signal.

### Explicit exclusion: do not use `coding-agent` as the parent lane
For AI-native mainline work, do **not** switch the parent task into `coding-agent` just because the task is large, code-adjacent, or needs file exploration.

`coding-agent` is allowed only for **bounded deterministic substeps** after the AI-native parent control model is already clear.
Examples:
- implementing a small bridge script that an already-defined AI-native design needs,
- applying a narrow code patch,
- doing isolated deterministic refactor work.

Do not let `coding-agent` redefine the main task as ordinary software engineering when the real task is still AI-native.

## Core operating model

### 1. Let AI own meaning
Let the model own:
- situation reading
- dominant pattern recognition
- frontier narrowing
- canonical owner selection
- next-hop focus
- qualitative blocker-family judgment

### 2. Let code own only hard edges
Let programs/scripts own:
- file IO and state persistence
- bridge/executor calls
- timeout / rollback / fail-closed guards
- bounded deterministic retry mechanics around local bridges/executors when the retry rule itself is already settled
- receipt capture
- permission / safety boundaries
- deterministic validation where semantics are already settled

Important split:
- program retry **mechanics** may be code
- workflow/agent retry **mechanics** should be owned by the AI-native dispatcher
- retry **policy/strategy responsibility** stays with the AI-native dispatcher

Do not bury workflow/agent retry policy inside opaque code defaults.
The dispatcher should decide things like:
- whether to rerun at all
- whether to widen timeout
- whether to replay the same prompt or vary it
- whether to compare multiple attempts
- whether to stop, escalate, or reframe

### 3. Keep the control surface thin
Prefer a small number of thin artifacts such as:
- verdict
- canonical object
- handoff
- receipt
- truth-backed learning delta

Do not grow a thick protocol, giant registry, or branch-heavy rules engine unless there is a real hard-edge reason.

## High-severity pathology: script-first takeover

In AI-native work, the following should be treated as a **high-severity pathology**, not a neutral implementation preference:
- a new `scripts/` directory becoming the practical mainline of an AI-native skill,
- a runner CLI or request JSON becoming the canonical child interface,
- success being narrated as “the script ran” instead of “the verdict/receipt truthfully closed,”
- growing a larger Python state machine because semantic judgment feels hard,
- allowing bridge code to decide owner / focus / frontier / meaning.

This is severe because it:
- steals semantic ownership from the AI layer,
- rewards mechanical growth instead of truthful closure,
- makes later cleanup harder by giving accidental authority to helper code,
- and can metastasize into a more elaborate but still trapped control surface.

Default suspicion signatures:
- new runner files appear inside an AI-native skill without a separately stabilized handoff/verdict contract,
- request payloads become more detailed than the canonical markdown handoff,
- reports start talking more about `runner`, `schema`, `flags`, `outputs`, or `transport metadata` than about truth boundary,
- bridge code starts compiling policy rather than merely executing a bounded choice,
- the system begins preserving script surfaces “because they already exist” rather than because live mainline truth depends on them.

Default response when you see this pattern:
1. stop expanding the script/program surface,
2. check whether the active contract truly depends on it,
3. if not, delete / archive / demote it out of the active lane,
4. restore handoff/verdict/receipt as the mainline control surface,
5. only then decide whether any bounded bridge still deserves to remain.

Repair preference:
- do **not** first make the runner cleaner, more configurable, or more reusable,
- do **not** add adapters around the wrong surface just because deletion feels disruptive,
- and do **not** spend the main effort polishing a route that may not deserve to exist.

When in doubt, repair by subtraction first.

Admission bar for any code artifact inside an AI-native active lane:
1. it solves a deterministic hard edge rather than semantic ownership,
2. it is subordinate to a stable AI-native contract,
3. it is replaceable without changing the control model,
4. it has live-used justification rather than speculative future value,
5. it is easy to rollback or delete.

## Non-negotiable AI-native rules

### A. No object growth as fake progress
Do not count these as real progress by themselves:
- new objects appearing
- richer summaries
- better wording
- more state fields
- writeback success
- more detailed hints

Real progress requires one of:
- new accepted evidence
- a real receipt
- a consumed handoff
- a live-used default change
- a true owner/frontier shift that changes the next cycle’s actual behavior

### B. No request without truth closure
If the system emits a request, it must converge toward a bounded truth state such as:
- receipt-confirmed
- blocked-confirmed
- request-unconsumed
- handoff-consumed

Do not let “requested”, “probing”, or “pending” masquerade as completion.

### C. No self-evolution without live consumption
A policy/learning artifact does **not** count as self-evolution unless:
1. it comes from truth-backed outcome,
2. it changes the next-turn default,
3. the new default is actually consumed by a later live cycle,
4. rollback remains possible.

### D. No thick traditional control by default
Do not default to:
- stage-heavy engineering protocols
- thick mode/gate systems
- registry/protocol/executor expansion
- over-programming semantic judgment

If a traditional structure is introduced, justify it as a hard-edge constraint, not as aesthetic engineering.

### E. No script-first takeover in the active AI-native lane
Do not let any of the following become canonical by convenience:
- runner CLI
- request JSON schema
- large Python orchestrator
- thick helper directory under an AI-native skill
- route/gate registry that starts deciding meaning

Hard rule:
- if one of these appears, prove it is a bounded bridge.
- if you cannot prove that, treat it as wrong by default.
- “it works” is not sufficient justification.
- “we can clean it later” is not sufficient justification.

## Boundary with the traditional development lane

Use the traditional complex-development / Rapper6-style lane only when the task is mainly:
- backend/frontend feature implementation
- API integration
- deterministic refactor
- build/deploy/test plumbing
- script-heavy automation
- program-native product work where software structure is the main object

### Mixed tasks
For mixed tasks:
- keep the **parent task** in the AI-native lane,
- allow **local substeps** to dip into traditional coding only for bounded deterministic work,
- do not let those substeps take over the main narrative or control model.

## Red flags

Stop and re-check if you notice any of these:
- you are designing a thicker protocol before the frontier is clear
- you are growing many control objects that all try to steer the same cycle
- you are rewarding request/probe shells as if they were true progress
- you are using code to settle a semantic judgment that AI should own
- you are reporting “almost solved” based on structure, not truth/receipt/live consumption
- you are pulling an AI-native task into a traditional development protocol just because the task is large
- you are treating retry/replay as optional recovery instead of native dispatcher work
- you are diagnosing prompt quality from timeout alone
- you are widening a repair lane before doing a proper rerun / compare discipline
- you are adding or preserving a `scripts/` subtree inside an AI-native skill without proving it is only a thin bridge
- you are describing the mainline in terms of `runner`, `schema`, `flags`, or `script output` rather than handoff/verdict/receipt
- the user explicitly warned about script-first drift, and you still treated it as a secondary cosmetic issue
- the user had to repeat the same route warning, and you still kept trying to refine the old path
- you are reading only summaries / memory / git assumptions instead of the live files currently shaping the route
- you are keeping experimental program surfaces in the active lane merely because deleting them feels inconvenient
- a helper program is starting to decide owner, focus, frontier, or next-hop meaning
- your “cleanup” instinct is to improve the runner rather than question whether the runner should exist in the active lane at all

## Practical deliverables to prefer

When possible, prefer producing:
- thin markdown plans
- thin markdown handoffs
- thin JSON verdicts
- canonical objects with explicit owner/target/focus
- bounded handoff + receipt shapes
- live-consumed learning deltas
- short anti-bounce rules that protect truth, ownership, and repeat handling
- very small bridge snippets only after the AI-native contract is already clear
- short drift audits that name which surfaces were deleted / demoted / kept and why
- explicit deletion/demotion of accidental script-first surfaces when they are not truly required

## Reference

For routing examples and sharper boundary calls, read `references/routing-and-boundaries.md`.
