# Repo selection (semantic surface)

## Status

This is the active **semantic** selector surface for `loop9-verify-v4`.

Read it together with:
- `references/repo-selection-pack.md`

Current active meaning:
- repo selection no longer applies only to missing `repo_ref`
- both auto-select and explicit repo intake now pass through the same pre-start selection stage
- this ref freezes **what selection means**
- `repo-selection-pack.md` freezes **how that meaning is carried in runtime**

If an older ref still pulls toward `proof-gap-first`, treat that older wording as historical background only.

## First precedence

Selection precedence is now:
1. **explicit `repo_ref` sets semantic priority**
2. if the same repo already has an accepted selection acceptance / current-round root / accepted `repo-task-brief` / accepted board in flight, continue that repo rather than re-selecting
3. otherwise evaluate repo candidates by repo-complete need, not by research convenience

Hard meaning:
- explicit repo still wins semantically
- but explicit repo no longer bypasses selection checking
- auto-select is for **unfinished verify work**
- not for reusing a historically useful sample repo
- not for picking the repo with the prettiest likely replay

## Two semantic modes

### 1. Auto-select

Current default question is:

> which repo most needs a truthful repo-complete current-round finish now?

### 2. Explicit repo check

When the user gives `repo_ref`, selection should now ask:

> can this repo truthfully continue as the active repo now,
> or does it show a high-risk delivered / suppressed / continuation-conflicted posture
> that the parent should make explicit before continuing?

Hard meaning:
- the check may warn
- the check may advise reject
- the check may ask for manual confirmation
- the check may not silently override the user's explicit repo
- if the child advises high-risk reject, the parent may still keep the explicit repo,
  but only through one visible explicit override

## Minimal state-source binding

Default repo selection should now bind to these real state sources, in this order:

### 1) Current-round continuation anchors
Use these first when the parent is already inside one repo flow:
- accepted `parent-selection-acceptance.*.md` when it exists
- current round root
- accepted `repo-task-brief.*.md`
- accepted `repo-findings-board.*.md`
- current round `objects/` and `artifacts/`

If those already exist for the active repo round, the correct answer is usually **continue the same repo**, not re-select another repo.

Hard boundary:
- only these accepted **in-flight** anchors count as continuation authority
- detached old env/bootstrap/replay artifacts from the same repo do **not** become continuation anchors by themselves
- if no accepted in-flight round currently exists, those detached artifacts are support signals only

### 2) Repo verify summaries
Primary durable repo-completion signal:
- `runs/repo-verify-*/repo_verify_summary.json`

Current workspace-observed useful fields include:
- `target_slug`
- `counts.total`
- `delivery.ready_for_delivery`
- `unresolved_finding_ids`
- `next_action`
- `summary`

These summaries should answer things like:
- is the repo already fully verified?
- is it already in `deliver-now` posture?
- does it still have unresolved findings?
- is it still blocked at `env-missing` / unreadable handoff level?

### 3) Canonical delivery bundle marker
Primary suppressor for verify auto-selection once a repo is already in delivery posture:
- `reports/<slug>/98-delivery-bundle.manifest.json`
- `reports/<slug>/99-最终本地复盘.md/json`

If a repo already has this canonical delivery marker chain, the default reading should move toward:
- already delivered / already in delivery lane / not the next default verify target
- in `auto-select`, this suppressor beats detached older env/replay assets from the same repo

### 4) Repo-local verify artifacts only as support
If summary/report signals are missing or ambiguous, supporting context may still come from:
- repo-local manifest / real_pocs artifacts
- older round artifacts
- local report bundles still being assembled

But these are support signals, not permission to ignore stronger summary/report completion evidence.

### 5) Historical sample / experience refs are background only
These may explain older choices, but may not drive current default selection:
- old bounded sample rounds
- `proof-gap / control-sample` notes
- `experience-index.md`
- historical repair writeups on `buildadmin / dax-pay / ibos`

The same sources also help explicit-repo-check answer:
- does the requested repo already look delivered / suppressed?
- does it conflict with an accepted continuation anchor?
- does continuing it need an explicit parent override?

## Default suppressors (do not auto-select)

A repo should now be suppressed from default verify auto-selection if any of the following are true:

### A. It already looks fully verified
For example, a `repo_verify_summary.json` shows all of:
- `delivery.ready_for_delivery == counts.total`
- `unresolved_finding_ids = []`
- and/or `next_action = deliver-now`

### B. It already has the canonical delivery manifest
If `reports/<slug>/98-delivery-bundle.manifest.json` already exists, and especially if `final-local-review` has completed, default verify auto-selection should back off.

This remains true even when the same repo still has detached older env/bootstrap/replay artifacts elsewhere in the workspace.

### C. It is only attractive as a historical sample
If the main reason to choose it is:
- it answered an older proof question well,
- it was a convenient bounded sample,
- it still has a beautiful historical replay receipt,

that is **not** enough to keep it in the default verify lane.

## Default positive signals (still eligible)

A repo may remain eligible for default verify auto-selection when the state sources point to unfinished verify work, for example:
- no trustworthy repo verify summary exists yet
- summary exists but still has unresolved findings
- summary shows `env-missing` / unreadable handoff / verification could not proceed
- repo still needs repo-complete verify finish even if it is not a glamorous proof sample
- canonical delivery manifest does not exist yet because verify itself is still unfinished

Current workspace-observed examples of this unfinished class:
- historically, `ureport` was a genuine positive candidate earlier on 2026-04-15
  before its canonical delivery bundle + final local review were written

Important current-state correction:
- do **not** keep reading current `ureport / sparkshop` as live unfinished examples
  just because older repo summaries still say `env-missing`
- once a canonical delivery bundle / final-local-review chain already exists,
  that present-state completion evidence beats the older env-missing summary for default selection

## Anti-repeat rules

- do not auto-select an old proof sample just because it can still answer some proof question
- do not auto-select by glamour, repo size, or historical convenience first
- do not let `historical-kept` or old replay beauty re-open an otherwise finished repo by default
- do not spend a recurring/hourly auto-select slot on a repo that is already `repo-mainline-done` just to confirm that its old runtime is still up
- post-closure liveness/status-sync on a delivered repo is monitor/heartbeat work, not default verify selection truth
- when recurring verify slots are scarce, advancing the unfinished repo queue beats re-probing a finished repo
- if summary/report completion evidence conflicts with historical sample value, **completion evidence wins**
- if a finished repo truly needs to be reopened for research, that should be explicit (`repo_ref`, explicit reopen intent, or a separate research entry), not silent default behavior

## Reopen boundary

- `auto-select` has no suppressor-override privilege
- if canonical delivery markers already exist, `auto-select` should suppress / back off rather than silently continuing the same repo from detached artifacts
- a delivered repo may be reopened only through explicit repo or explicit reopen intent
- a finished repo whose only remaining question is "is the old runtime still alive?" is not a default reopen candidate
- if that explicit reopen conflicts with suppressors, the parent should surface it as a visible override path during `explicit-repo-check`

## Parent consume expectation after selection stage

`repo-selection-pack` should now return one thin `repo-selection-proposal`,
and the parent should answer with one thin `parent-selection-acceptance`.

The accepted basis should point to the real state sources used, for example:
- which continuation anchors mattered
- which `repo_verify_summary.json` mattered
- whether a canonical delivery manifest / final-local-review marker was missing/present
- why finished historical sample repos were suppressed
- whether a candidate was suppressed because it only offered post-closure liveness/status-sync rather than unfinished repo-complete work
- whether the proposed continuation was active in-flight or only detached historical support
- whether explicit repo continuation required a visible parent override
- whether an earlier interrupted selection run was treated only as caller-side timeout-budget failure

Parent timeout discipline here is also part of selection meaning:
- if the isolated child exits before writing a usable `repo-selection-proposal`,
  the parent should record caller-side timeout-budget failure first
- do not freeze repo choice from that failed run
- rerun before promoting the event into any semantic repo judgment

This keeps selection explainable without growing a thick ranking protocol.

After that:
- `repo-task-brief` should inherit the accepted thin basis
- `repo-start-pack` should consume that accepted basis
- later start-side packets should **not** replay the whole selection narration

## One-sentence default

> Every repo intake now enters one thin pre-start selection stage:
> explicit `repo_ref` keeps semantic priority but still gets checked,
> and missing `repo_ref` means auto-select the repo that still needs truthful repo-complete verify finish using accepted in-flight continuation anchors + repo verify summaries + canonical delivery markers as the thin state sources.
