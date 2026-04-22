# Agentic blocker diagnosis

## Purpose

This ref freezes the execution posture that lets `loop9-verify-v4` stay honest **without** becoming passive:

> when a queue row hits friction, do not stop at the first surface symptom.
> Classify the blocker, choose the smallest truthful repair, rerun boundedly, and only then freeze terminal truth.

## One-line operating posture

> First failure is evidence, not verdict.
> Repair what is cheaply materializable.
> Prove landing before calling a state-changing PoC confirmed.

## Blocker classes the parent should distinguish

### 1. Transport / budget / caller-side failure
Examples:
- network wobble
- timeout with no usable receipt
- child killed before writing a verdict
- container port not yet accepting connections

Default response:
- widen timeout materially
- rerun boundedly
- restart the minimal runtime unit if needed
- record this as scheduler/runtime friction, not finding truth

Do not:
- freeze `fresh-blocked` from timeout alone
- diagnose prompt quality from one interrupted run

### 2. Env not yet materialized
Examples:
- containers exist but app/bootstrap is incomplete
- database is empty though vendor seed exists
- dependent service is down but recoverable inside the lab

Default response:
- complete the minimal bootstrap
- prefer official/vendor material over invented fixtures
- keep the repair inside the same repo round when it is cheap and reversible

### 3. Seed / auth / target-material mismatch
Examples:
- wrong `sid`
- stale token
- missing seeded admin row
- claim depends on a live object id that changed in the fresh runtime

Default response:
- relocate live ids from the current runtime
- refresh auth/session material
- import official seed when the repo ships one
- generate bounded disposable test material only when that is the truthful way to answer the question

Important reading:
- a reachable helper route plus a failing main PoC often means **material mismatch**, not transport collapse

### 4. Shared blocker spanning multiple rows
Examples:
- `B3-B6` all depend on the same honest admin auth material
- several rows all need the same install / DB materialization before replay is even meaningful
- one cheap captcha/login/bootstrap repair could reopen a whole bucket

Default response:
- separate the shared blocker from row-local exploit truth
- repair the shared blocker once when that repair is cheap, reversible, and truthful
- capture the resulting reusable live material
- then replay the affected rows one by one

Do not:
- freeze every row independently while the shared blocker still obviously explains them all
- mistake the shared unblock for row-local confirmation

### 5. Success-response shell without landing
Examples:
- `HTTP 200` but target row did not change
- soft-delete endpoint returns success but object remains visible
- API acknowledges a mutation that only a control principal can actually land

Default response:
- compare before/after state on the target object
- when possible, add a control replay using the rightful principal
- classify only the landed effect as finding truth; treat a false success shell as a separate implementation issue

### 6. True manual / policy / destructive boundary
Examples:
- exploit path requires external secrets not available in the lab
- only destructive/high-risk action remains
- required dependency is not legally or operationally admissible

Default response:
- freeze `fresh-manual-needed` or `fresh-skip-by-policy`
- explain the exact missing prerequisite
- do not blur this into generic “failed”

## Minimal self-repair ladder

When the row is still worth pushing, prefer this order:

1. verify the runtime is actually alive
2. separate timeout/transport evidence from semantic finding evidence
3. inspect whether official seed or shipped default material exists
4. ask whether several unfinished rows are stalled by the same shared blocker
5. if yes, repair that shared blocker once and capture reusable live material
6. relocate live ids / sids / target rows from the current runtime
7. refresh auth/session/token state
8. rerun the bounded PoC
9. for mutation claims, verify landing with before/after state
10. only then freeze terminal disposition

## Allowed initiative

The skill is allowed to do all of the following without waiting for a fresh user turn when they are cheap, reversible, and directly relevant:
- rerun with a materially wider timeout
- restart the app/service inside the disposable lab
- import official shipped seed data
- clear one cheap shared bootstrap/auth blocker and reuse the resulting honest material across the affected row cluster
- query current live ids and route parameters
- register a disposable low-privilege account
- create bounded control material for before/after comparison
- run owner/control replays to disambiguate a false success shell

## Anti-patterns

Do not:
- stop at the first blocker-shaped symptom
- call everything “network issue”
- build a thick repo-specific fixture tower just to force confirmation
- multiply one cheap shared blocker into `N` separate false `manual-needed` rows
- overclaim from `HTTP 200`
- downgrade a real landing proof just because the first attempt looked messy
- ask the user to manually continue the same repo round when the next truthful repair is already obvious and cheap

## Truth boundary

This ref makes the skill **more agentic**, not less honest.

The point is:
- solve the cheap unknowns independently
- let one cheap shared unblock reopen the whole affected row bucket when that is the truthful shape
- keep the queue moving
- and still freeze `fresh-blocked` when the replay truly does not land after the bounded repair ladder has been exhausted
