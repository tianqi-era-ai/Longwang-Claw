# Experience index

This is the lightweight **visibility layer** for experience inside `loop9-verify-v4`.

Use it as an exposure surface, not as a full case library.

## Active reading boundary

Under the current `repo-complete` contract:
- this file is **on-demand only**; do not pull it into default repo intake / auto-selection / closure reading
- entries here do **not** drive default repo auto-selection
- entries here do **not** authorize repo closure from partial current-round handling
- many current entries originate from older bounded/sample repair rounds and should be read as **historical background hints**, not active product posture

If an entry looks relevant, use it to sharpen judgment on one finding or one queue posture.
Do not let it silently drag the whole skill back into proof/sample mode.

## What belongs here

Only keep a thin abstract entry that gives later executors a chance to notice:
- a reusable abstract truth
- its current state
- when it may be relevant
- where to read the deeper round/case artifacts

Do **not** paste full repo lessons here.

## How to read this file

- `observed` entries are **visible hints**, not defaults
- `validated` entries are stronger, but still not necessarily family defaults
- `promoted` entries may influence default reading only after stronger cross-sample proof exists

If an entry looks relevant, then drill down into its refs.

## Minimal entry shape

- `abstract_id`
- `state`
- `abstract`
- `relevance hints`
- `deep refs`

`deep refs` may point to:
- round-level `learning-delta` objects
- supporting round artifacts / verdicts
- and, when useful, repo-local experience cards

But the index entry itself must stay abstract and thin.

## Observed

### LDV4-001
- state: `observed`
- abstract:
  - On a repo that mixes frontdoor-anonymous lines with auth/business-seeded lines, keep queue truth honest: if the easy line is cheaply materializable, confirm it; if the harder line lacks truthful prerequisites, freeze that finding as a current-round `fresh-blocked` or `fresh-manual-needed` style terminal disposition instead of growing a thick repo-specific fixture tower just to make the queue look complete.
- relevance hints:
  - mixed finding families in one repo
  - official seed / lab state missing merchant/app/business prerequisites
  - temptation to build ad-hoc fixtures for cosmetic completeness
  - need to keep current-round queue truth honest
- deep refs:
  - `reports/2026-04-12-loop9-v4.1-修正设计/dax-pay-full-round/objects/learning-delta.dax-pay.second-sample-bounded-hardening.md`
  - `reports/2026-04-12-loop9-v4.1-修正设计/dax-pay-full-round/03-round-summary.md`
  - `reports/2026-04-12-loop9-v4.1-修正设计/dax-pay-full-round/06-repo-round-verdict.md`

### LDV4-002
- state: `observed`
- abstract:
  - On a repo with a ready env, when the replay blocker is truly stale auth/session rather than env collapse, one bounded thin auth repair may stay inside `finding-replay`; but the resulting decisive receipt only advances that finding's current-round disposition and may not be mistaken for repo-level completion while the rest of the queue remains unfinished.
- relevance hints:
  - ready env already exists
  - stale auth/session drift
  - temptation to misroute the problem into env repair
  - temptation to overclaim repo closure from one authenticated decisive receipt
- deep refs:
  - `reports/2026-04-12-loop9-v4-薄Skill设计/rounds/ibos/u2-auth-repair-full-repo-round/objects/learning-delta.ibos.u2-auth-repair-full-repo-round.md`
  - `reports/2026-04-12-loop9-v4-薄Skill设计/rounds/ibos/u2-auth-repair-full-repo-round/round-summary.md`
  - `reports/2026-04-12-loop9-v4-薄Skill设计/rounds/ibos/u2-auth-repair-full-repo-round/objects/repo-round-verdict.ibos.u2-auth-repair-full-repo-round.md`

### LDV4-003
- state: `observed`
- abstract:
  - When one stage materializes canonical local artifacts and the next stage validates those same artifacts immediately afterward, the consumer must first consume the producer's ready receipt or barrier state; until that barrier is ready, missing files should be read as `not-ready-yet`, not as `missing/broken`.
- relevance hints:
  - producer/consumer seam on the same repo mainline
  - canonical artifacts are written late in the producer stage
  - temptation to run bridge + final review in parallel for speed
  - false `missing-local-report-artifacts` or other fake blocked states appearing right after a producer launch
- deep refs:
  - `skills/loop9-verify-v4/references/learning-delta.LDV4-003.delivery-report-stage-barrier.md`
  - `skills/loop9-delivery-reports/scripts/run_delivery_report_bridge.py`
  - `skills/loop9-delivery-reports/scripts/run_final_local_review_bridge.py`

### LDV4-004
- state: `observed`
- abstract:
  - When a fresh replay first fails but the runtime still exposes live helper routes or healthy containers, do not collapse that friction into “network issue” or prompt failure. First separate transport/caller failure from runtime-material mismatch; if official seed, live ids, auth material, or other cheap truthful prerequisites can be materialized inside the lab, do that repair and rerun before freezing a negative current-round disposition.
- relevance hints:
  - first-run PoC failure with mixed signals
  - helper routes still live
  - empty database / wrong live id / stale auth / missing shipped seed
  - temptation to treat an interrupted or underprepared replay as semantic finding truth
- deep refs:
  - `skills/loop9-verify-v4/references/learning-delta.LDV4-004.runtime-materialization-vs-transport-failure.md`
  - `reports/2026-04-15-loop9-v4-dwsurvey-repo-complete/rounds/dwsurvey/r1-fresh-repo-complete/objects/attempt-receipt.dwsurvey.F1.r1-fresh-repo-complete.md`
  - `reports/2026-04-15-loop9-v4-dwsurvey-repo-complete/rounds/dwsurvey/r1-fresh-repo-complete/objects/attempt-receipt.dwsurvey.F2.r1-fresh-repo-complete.md`
  - `reports/2026-04-15-loop9-v4-dwsurvey-repo-complete/rounds/dwsurvey/r1-fresh-repo-complete/objects/attempt-receipt.dwsurvey.F3.r1-fresh-repo-complete.md`

### LDV4-005
- state: `observed`
- abstract:
  - For mutation-style findings, `HTTP 200` or `resultCode = 200` proves only that the request path accepted the call. Confirm the finding only after verifying the target object's state changed as claimed, ideally with before/after evidence and, when ambiguity remains, a control replay under the rightful principal.
- relevance hints:
  - delete/update/toggle style PoCs
  - suspiciously clean success response
  - soft-delete or async-looking endpoints
  - need to distinguish “success shell” from real unauthorized landing
- deep refs:
  - `skills/loop9-verify-v4/references/learning-delta.LDV4-005.state-changing-poc-needs-landing-proof.md`
  - `reports/2026-04-15-loop9-v4-dwsurvey-repo-complete/rounds/dwsurvey/r1-fresh-repo-complete/objects/attempt-receipt.dwsurvey.F4.r1-fresh-repo-complete.md`
  - `reports/2026-04-15-loop9-v4-dwsurvey-repo-complete/rounds/dwsurvey/r1-fresh-repo-complete/artifacts/replay-active-unblock/F4.serial.after-non-owner.txt`
  - `reports/2026-04-15-loop9-v4-dwsurvey-repo-complete/rounds/dwsurvey/r1-fresh-repo-complete/artifacts/replay-active-unblock/F4.serial.after-owner.txt`

### LDV4-006
- state: `observed`
- abstract:
  - When a repo's truthful bootstrap is `source-run Go + local YAML/DB state` rather than compose-first, keep state ownership with the mounted lab and use a container only as the disposable toolchain carrier. During the first `go toolchain + module` bring-up, port resets may still be download/compile delay rather than app failure, and bind-mounted app directories do not by themselves mean Go/module caches will persist across fresh containers.
- relevance hints:
  - Go repos with stale env handoff
  - compose-first looks false for the repo family
  - manual lab already carries YAML/SQLite/install state
  - first startup spends a long time in toolchain/module download
  - confusion about what Docker bind mounts do and do not persist
- deep refs:
  - `reports/2026-04-15-loop9-v4-bbs-go-repo-complete/rounds/bbs-go/r1-fresh-repo-complete/objects/learning-delta.bbs-go.r1-fresh-repo-complete.md`
  - `reports/2026-04-15-loop9-v4-bbs-go-repo-complete/rounds/bbs-go/r1-fresh-repo-complete/objects/stage-verdict.env-bootstrap.bbs-go.r1-fresh-repo-complete.md`
  - `reports/2026-04-15-loop9-v4-bbs-go-repo-complete/rounds/bbs-go/r1-fresh-repo-complete/objects/attempt-receipt.bbs-go.F1.r1-fresh-repo-complete.md`
  - `reports/2026-04-15-loop9-v4-bbs-go-repo-complete/experience/cards/EC006-go-manual-lab-containerized-runtime-revive.md`
  - `reports/2026-04-15-loop9-v4-bbs-go-repo-complete/experience/cards/BBSGO-EC001-manual-go-lab-docker-revive-cache-boundary.md`

### LDV4-007
- state: `observed`
- abstract:
  - When several unfinished rows are visibly stalled by the same cheap shared blocker such as partial install, missing DB materialization, or absent honest auth material, repair that blocker once, capture reusable live material, and then reopen each affected row one by one before freezing row-local negative truth. The shared unblock only proves replay-openable posture; it is not row confirmation and not repo closure.
- relevance hints:
  - one repo has a whole auth-gated or bootstrap-gated bucket parked behind the same blocker
  - multiple rows look independently failed, but all start from the same missing install/auth/material precondition
  - temptation to freeze every row as `fresh-blocked` / `fresh-manual-needed`
  - one honest login or one bootstrap repair could reopen a whole row cluster
- deep refs:
  - `skills/loop9-verify-v4/references/learning-delta.LDV4-007.shared-blocker-repair-before-row-freeze.md`
  - `reports/2026-04-16-loop9-v4-strict-isolated-repo-complete/rounds/buildadmin/r1-fresh-repo-complete/objects/learning-delta.buildadmin.r1-fresh-repo-complete.md`
  - `reports/2026-04-16-loop9-v4-strict-isolated-repo-complete/rounds/buildadmin/r1-fresh-repo-complete/objects/stage-verdict.env-bootstrap.buildadmin.auth-material.r1-fresh-repo-complete.md`
  - `reports/2026-04-16-loop9-v4-strict-isolated-repo-complete/rounds/buildadmin/r1-fresh-repo-complete/objects/repo-closure-review.buildadmin.r1-fresh-repo-complete.md`

### LDV4-008
- state: `observed`
- abstract:
  - For action-style routes whose real exploit semantics depend on multipart/non-GET requests or on seeded business config, bootstrap-time bare route probes answer only route/debug shape. Do not freeze row truth from those probes alone; first restore seed/config truth when needed, then replay the canonical action on the same live runtime host.
- relevance hints:
  - env artifacts show a bare `GET` sample on an upload/action endpoint
  - current finding really depends on `POST`, multipart, or another non-GET shape
  - earlier blocked truth mentions missing DB/config material such as `store_way`
  - temptation to overread a probe-time `500` as finding falsification
- deep refs:
  - `skills/loop9-verify-v4/references/learning-delta.LDV4-008.action-probe-vs-canonical-replay.md`
  - `reports/2026-04-16-loop9-v4-tencent-cvm-finding-replay/rounds/sparkshop/F2-r1-ai-native-minimal/objects/attempt-receipt.sparkshop.F2-r1-ai-native-minimal.md`
  - `reports/2026-04-16-loop9-v4-tencent-cvm-env-bootstrap/rounds/sparkshop/r16-remote-draft-bootstrap-full-sql-file-import/env_result.json`
  - `reports/2026-04-16-loop9-v4-tencent-cvm-finding-replay/rounds/sparkshop/F2-r2-ai-native-minimal-r16-receipt/objects/attempt-receipt.sparkshop.F2-r2-ai-native-minimal-r16-receipt.md`

### LDV4-009
- state: `observed`
- abstract:
  - For admin-gated replay, a broken login-side accessory such as captcha rendering does not automatically mean the row is auth-blocked. If the same live lab lane can still truthfully establish session feasibility by a bounded on-box path, continue to the protected route and classify the row from that route's decisive blocker instead.
- relevance hints:
  - admin login page is reachable but one accessory route like captcha image is 500/broken
  - the lab still has a truthful thin path to establish admin session feasibility
  - temptation to freeze the row as auth-blocked before replaying the protected feature
  - protected feature may still expose a clearer runtime/plugin-config blocker family
- deep refs:
  - `skills/loop9-verify-v4/references/learning-delta.LDV4-009.auth-accessory-break-vs-finding-blocker.md`
  - `reports/2026-04-16-loop9-v4-tencent-cvm-finding-replay/rounds/sparkshop/F3-r1-ai-native-minimal-r16/objects/attempt-receipt.sparkshop.F3-r1-ai-native-minimal-r16.md`
  - `reports/2026-04-16-loop9-v4-tencent-cvm-finding-replay/rounds/sparkshop/F3-r1-ai-native-minimal-r16/artifacts/logs/admin-ueditor.sparkshop.F3.r16.summary.log`

### LDV4-010
- state: `observed`
- abstract:
  - Only accepted in-flight round anchors extend the same repo mainline. Detached env/bootstrap/replay artifacts are support signals only. Therefore the parent must keep completion fail-closed until the delivery tail is consumed, and `auto-select` may not silently reopen a delivered repo from detached continuation evidence.
- relevance hints:
  - current round root already exists and `repo-round-verdict` has been emitted
  - temptation to treat that point as repo-mainline completion
  - the same repo also has canonical delivery markers plus detached older env/replay assets elsewhere in the workspace
  - temptation to read those detached assets as continuation anchors strong enough to beat suppressors during `auto-select`
- deep refs:
  - `skills/loop9-verify-v4/references/learning-delta.LDV4-010.active-inflight-anchor-vs-detached-continuation.md`
  - `skills/loop9-verify-v4/references/repo-selection.md`
  - `skills/loop9-verify-v4/references/parent-closure-chain.md`
  - `skills/loop9-verify-v4/references/runtime-isolation.md`

## Validated

- none yet

## Promoted

- none yet
