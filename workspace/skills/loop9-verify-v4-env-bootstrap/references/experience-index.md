# Env-Bootstrap Experience Index

This is the thin **experience visibility layer** for `loop9-verify-v4-env-bootstrap`.

Keep it small:
- expose only reusable abstract truths
- keep case narration elsewhere
- do not let the index itself become a case dump

## How to use this file

- `observed` entries are visible hints, not hard defaults
- if one entry looks relevant, drill into its deep refs
- do not let one case-specific lesson silently become a new thick planner

## Minimal entry shape

- `abstract_id`
- `state`
- `abstract`
- `relevance hints`
- `deep refs`

## Observed

### EVB4-001
- state: `observed`
- abstract:
  - For DB-backed env bootstrap, container-running is not readiness truth. Judge readiness only after the dependency accepts a real query or equivalent live probe, and postpone stale-install-marker decisions until that readiness truth exists.
- relevance hints:
  - DB container is `running` but import/probe still hits connection refused
  - copied working tree already contains install markers such as `install.lock`
  - temptation to classify the env from HTTP reachability or container state alone
- deep refs:
  - `skills/loop9-verify-v4-env-bootstrap/references/observed-lessons.tencent-cvm-sparkshop-r8-r16.md#evb4-001-honest-db-readiness-before-stale-install-judgment`
  - `reports/2026-04-16-loop9-v4-tencent-cvm-env-bootstrap/rounds/sparkshop/r9-remote-draft-bootstrap-db-ready-seed/objects/stage-handoff.env-bootstrap.sparkshop.r9-remote-draft-bootstrap-db-ready-seed.md`

### EVB4-002
- state: `observed`
- abstract:
  - For config-dependent findings, `ready_for_poc` must be gated by the critical seed/config truth, not by HTTP liveness or login-page reachability alone. If the needed config row is absent, the honest verdict is still env-gap blocked.
- relevance hints:
  - pages look healthy but the finding depends on DB-backed config such as `store_way`
  - replay is blocked by empty schema / missing business rows
  - temptation to treat route liveness as replay readiness
- deep refs:
  - `skills/loop9-verify-v4-env-bootstrap/references/observed-lessons.tencent-cvm-sparkshop-r8-r16.md#evb4-002-config-truth-gates-ready_for_poc`
  - `reports/2026-04-16-loop9-v4-tencent-cvm-finding-replay/rounds/sparkshop/F2-r1-ai-native-minimal/objects/attempt-receipt.sparkshop.F2-r1-ai-native-minimal.md`
  - `reports/2026-04-16-loop9-v4-tencent-cvm-env-bootstrap/rounds/sparkshop/r16-remote-draft-bootstrap-full-sql-file-import/artifacts/post_install_remediation_report.json`

### EVB4-003
- state: `observed`
- abstract:
  - When vendor seed is noisy, keep the canonical installation truth focused on the smallest critical rows and system signals. Non-critical dirty seed may be trimmed, and installer-page visibility may be downgraded to non-blocking only after the critical truth is already landed.
- relevance hints:
  - one large vendor seed block is malformed but non-essential for the current PoC lane
  - import exit codes are noisy or mixed
  - installer pages remain visible after key seed truth is already present
- deep refs:
  - `skills/loop9-verify-v4-env-bootstrap/references/observed-lessons.tencent-cvm-sparkshop-r8-r16.md#evb4-003-trim-noncritical-seed-and-downgrade-installer-noise-honestly`
  - `reports/2026-04-16-loop9-v4-tencent-cvm-env-bootstrap/rounds/sparkshop/r12-remote-draft-bootstrap-trim-city-seed/objects/stage-handoff.env-bootstrap.sparkshop.r12-remote-draft-bootstrap-trim-city-seed.md`
  - `reports/2026-04-16-loop9-v4-tencent-cvm-env-bootstrap/rounds/sparkshop/r16-remote-draft-bootstrap-full-sql-file-import/artifacts/post_install_hook_report.json`

### EVB4-004
- state: `observed`
- abstract:
  - If the runner diverges from a verified manual positive sample, do not keep widening the automation blindly. Use the manual path as a truth comparator and align the runner to the specific proven feed path, probe field, and full input material that produced the real success.
- relevance hints:
  - manual on-box sample succeeds while the runner still fails
  - suspected differences include truncated input, wrong probe field, wrong SQL feed path, or wrong principal
  - temptation to add more automation before reconciling the runner with known-good truth
- deep refs:
  - `skills/loop9-verify-v4-env-bootstrap/references/observed-lessons.tencent-cvm-sparkshop-r8-r16.md#evb4-004-manual-positive-sample-as-runner-truth-comparator`
  - `reports/2026-04-16-loop9-v4-tencent-cvm-env-bootstrap/rounds/sparkshop/r14-remote-draft-bootstrap-root-seed-truth/objects/stage-handoff.env-bootstrap.sparkshop.r14-remote-draft-bootstrap-root-seed-truth.md`
  - `reports/2026-04-16-loop9-v4-tencent-cvm-env-bootstrap/rounds/sparkshop/r15-remote-draft-bootstrap-file-seed-import/objects/stage-handoff.env-bootstrap.sparkshop.r15-remote-draft-bootstrap-file-seed-import.md`
  - `reports/2026-04-16-loop9-v4-tencent-cvm-env-bootstrap/rounds/sparkshop/r16-remote-draft-bootstrap-full-sql-file-import/objects/stage-handoff.env-bootstrap.sparkshop.r16-remote-draft-bootstrap-full-sql-file-import.md`

### EVB4-005
- state: `observed`
- abstract:
  - For PHP app env bootstrap, browser-visible capability must be grounded in explicit extension truth. A login page `200` is not enough if captcha/image endpoints still fail because required extensions such as `gd` are missing from the built image.
- relevance hints:
  - outer HTML renders but captcha, thumbnail, or installer image checks still fail
  - runtime error mentions image functions such as `imagecreate`
  - thin generated Dockerfile installs only DB/cache extensions and silently omits browser-critical image support
- deep refs:
  - `skills/loop9-verify-v4-env-bootstrap/references/observed-lessons.tencent-cvm-sparkshop-r8-r16.md#evb4-005-browser-visible-php-capabilities-need-explicit-extension-truth`
  - `reports/2026-04-16-loop9-v4-tencent-cvm-env-bootstrap/rounds/sparkshop/r8-remote-draft-bootstrap-install-seed/objects/stage-handoff.env-bootstrap.sparkshop.r8-remote-draft-bootstrap-install-seed.md`
  - `reports/2026-04-16-loop9-v4-tencent-cvm-finding-replay/rounds/sparkshop/F3-r1-ai-native-minimal-r16/objects/attempt-receipt.sparkshop.F3-r1-ai-native-minimal-r16.md`

### EVB4-006
- state: `observed`
- abstract:
  - If remote APT installation is genuinely required, treat it as a real bootstrap gate. Prefer the smallest viable source or mirror substitution first, and escalate to proxy paths such as ClashParty only when official plus simple mirror routes still fail or stall.
  - If the frozen Tencent CVM loopback proxy is intentionally meant to reach the operator's Mac-local Clash, prefer reverse `SSH -R` backhaul to that Clash port rather than standing up a fake proxy process on the Tencent CVM.
- relevance hints:
  - Dockerfile/container repair is blocked on `apt-get update` or package fetches
  - large package indexes stall even though smaller registry/image pulls work
  - temptation appears either to skip the package need entirely or to jump to proxy complexity too early
- deep refs:
  - `skills/loop9-verify-v4-env-bootstrap/references/observed-lessons.tencent-cvm-sparkshop-r8-r16.md#evb4-006-treat-apt-reachability-as-a-real-bootstrap-gate-with-explicit-escalation-order`
  - `reports/2026-04-16-loop9-v4-tencent-cvm-env-bootstrap/rounds/sparkshop/r16-remote-draft-bootstrap-full-sql-file-import/artifacts/runtime-hotfix-captcha-gd.md`
