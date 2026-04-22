# LDV4-008 Action Probe Vs Canonical Replay

## Delta identity
- abstract_id: `LDV4-008`
- state: `observed`
- theme: `action-endpoint probe semantics and seed-truth gating`

## Abstract layer

For action-style routes whose real exploit semantics depend on a non-GET method or on seeded business config, a bootstrap-time bare route probe does **not** settle finding truth by itself.

Use this split instead:
- `env-bootstrap` route probes answer only surface reachability / debug shape unless the route's canonical method is the same as the probe
- `finding-replay` must still use the canonical method on the same live runtime host before terminalizing the finding
- when the finding depends on seeded config, first verify that the critical config truth actually exists

Hard reading:
- bare `GET /action-endpoint -> 500` is not by itself a finding falsification
- bare route samples are not a substitute for canonical replay
- if seed/config truth is still missing, terminalize the row as env-gap blocked rather than as finding failure

## Case layer

SparkShop on Tencent CVM exposed the contrast cleanly:
- earlier `F2-r1` was honestly `blocked-confirmed` because the remote env still had an empty `app` schema and `uploadFile()` died on missing `store_way`
- later `r16 env-bootstrap` established `table_count=62`, `store_way=local`, and a reusable ready env
- even in that ready env, `env_result.json` still contained a bare `GET /api/common/uploadFile -> 500` route sample
- but a fresh remote multipart `POST /api/common/uploadFile` and the canonical PoC replay both succeeded, returned same-origin `/storage/...svg` URLs, and preserved the uploaded marker on fetch

So the durable lesson is not “ignore probes” and not “every 500 is harmless”.
The lesson is:
- keep probe truth in its lane
- keep canonical replay truth in its lane
- and make seed/config readiness explicit before judging an action-style finding

## Evidence refs
1. `/Users/xlx/.openclaw/workspace/reports/2026-04-16-loop9-v4-tencent-cvm-finding-replay/rounds/sparkshop/F2-r1-ai-native-minimal/objects/attempt-receipt.sparkshop.F2-r1-ai-native-minimal.md`
2. `/Users/xlx/.openclaw/workspace/reports/2026-04-16-loop9-v4-tencent-cvm-env-bootstrap/rounds/sparkshop/r16-remote-draft-bootstrap-full-sql-file-import/env_result.json`
3. `/Users/xlx/.openclaw/workspace/reports/2026-04-16-loop9-v4-tencent-cvm-env-bootstrap/rounds/sparkshop/r16-remote-draft-bootstrap-full-sql-file-import/artifacts/post_install_remediation_report.json`
4. `/Users/xlx/.openclaw/workspace/reports/2026-04-16-loop9-v4-tencent-cvm-finding-replay/rounds/sparkshop/F2-r2-ai-native-minimal-r16-receipt/objects/attempt-receipt.sparkshop.F2-r2-ai-native-minimal-r16-receipt.md`

## Level judgment
- current judgment: `observed`
- why not higher yet:
  - the pattern is now live-consumed inside one real Tencent CVM lane
  - but it is still supported by one repo family rather than multiple near-enough samples

## No-overclaim note

Do not flatten this into:
- “GET probes never matter”
- or “any 500 on an action route can be ignored”

The narrower rule is:
- if the route's real semantics require another method or seeded config,
- and the env/readiness evidence says those prerequisites were previously missing,
- then replay truth must come from the canonical action path after seed truth is re-established.
