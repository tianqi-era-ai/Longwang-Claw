# Routing and Boundaries

## Use `ai-native-development` when

### 1) The product logic is model-led
Examples:
- dispatcher / planner / coach / router
- evaluator / reflection / self-repair loop
- agent memory / ownership / handoff design
- LLM application mainline behavior
- AI-native simulation or role behavior

### 2) The hard part is semantic, not mechanical
Examples:
- deciding the right canonical owner
- deciding whether a route change is real progress or same-family narrowing
- preventing false progress credit
- deciding whether learning was actually consumed
- keeping the control surface thin and live

### 3) The program should stay subordinate
Examples:
- scripts only persist state, capture receipts, or enforce timeouts
- code is a bridge, not the main thinker

## Use the traditional development lane when

### 1) The main object is deterministic software
Examples:
- build a website/app/API
- refactor a service or module
- fix tests / CI / deployment scripts
- build a CLI / script / automation tool
- implement a feature where program correctness is the main difficulty

### 2) The work is program-first even if AI helps
Examples:
- AI helps plan code structure, but the result is still ordinary software engineering
- the key risks are typing, API contracts, performance, build, deploy, and regressions

## Mixed-task rule

When both are present:
- keep the parent task in `ai-native-development` if the mainline is AI-native,
- let deterministic coding be a bounded subtask,
- do not let bounded coding substeps rewrite the parent task’s control model.

## Fast anti-misroute checklist

If most answers are “yes”, stay AI-native:
- Is the main problem about ownership / frontier / policy / learning / handoff?
- Is object semantics more important than ordinary code structure?
- Would a thicker engineering protocol likely distort the real task?
- Is “truth / receipt / live consumption” more important than “did the script run”? 

If most answers are “yes”, use the traditional lane:
- Is the main problem feature implementation or refactor?
- Are build/test/deploy/code correctness the dominant risks?
- Would success still make sense without any AI-native control surface?

## One-sentence rule

If the system is trying to make **AI think and act as the main control layer**, use `ai-native-development`.
If the system is trying to make **software work correctly as the main object**, use the traditional development lane.
