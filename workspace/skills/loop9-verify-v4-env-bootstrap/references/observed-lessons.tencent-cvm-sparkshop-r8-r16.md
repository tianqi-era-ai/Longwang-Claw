# Observed Lessons — Tencent CVM SparkShop `r8 -> r16`

This note distills the real SparkShop Tencent CVM climb into a small set of active env-bootstrap lessons.

Ordering rule:
- abstract truth first
- case manifestation second
- safe reuse boundary last

## EVB4-001 Honest DB Readiness Before Stale Install Judgment

### Abstract

For DB-backed env bootstrap, container-running is not readiness truth.

Do not:
- remove or trust copied install markers too early
- run import/remediation merely because the container is up
- classify the env from HTTP health while the DB cannot yet answer a real query

Instead:
- wait for a real DB probe
- then judge stale install markers
- then run the next seed/import step

### Case manifestation

SparkShop `r8 -> r9` exposed this cleanly:
- `r8` already had the right service shape in place
- but remediation still hit MySQL too early, so import failed on `connection refused`
- `r9` repaired the sequence by explicitly waiting for MySQL readiness before stale-lock and seed decisions

### Safe reuse rule

Reuse this lesson when:
- the app/runtime already looks alive
- but the true env question still depends on DB-backed install or seed state

Do not overapply it to:
- purely stateless routes
- envs whose canonical prerequisite is not a DB at all

## EVB4-002 Config Truth Gates `ready_for_poc`

### Abstract

For config-dependent findings, `ready_for_poc` must be gated by the critical seed/config truth, not by HTTP reachability or a login page alone.

If the finding depends on a row such as `store_way`, then:
- a missing row means the env is still blocked for that finding family
- even if the site homepage and admin login page both render

### Case manifestation

SparkShop `F2 uploadFile` made this visible:
- pages were already reachable
- but the finding still died on missing `store_way`
- the truthful env reading stayed blocked until the seed truth actually landed in `r16`

### Safe reuse rule

Before calling an env `ready_for_poc`, ask:
- what exact config/business truth does the next frozen finding require?
- has that truth really landed yet?

If not, keep the verdict at env-gap rather than overstating readiness.

## EVB4-003 Trim Non-Critical Seed And Downgrade Installer Noise Honestly

### Abstract

When vendor seed is noisy, keep the canonical installation truth focused on the smallest critical rows and signals.

That means:
- a clearly non-critical malformed seed block may be trimmed
- noisy import exit codes may be tolerated if the critical truth still lands
- installer-page visibility may be downgraded to non-blocking only after critical install truth exists

### Case manifestation

SparkShop `r11 -> r16` showed the concrete bundle:
- `set_city` vendor seed was malformed and non-critical for the current PoC lane
- trimming it unblocked the critical `sys_setting / store_way / admin / install.lock` truth
- even after those landed, installer pages could still render, but `r16` could honestly classify them as non-blocking rather than as proof the env was uninstalled

### Safe reuse rule

Only trim when all of the following hold:
- the dirty seed block is well-identified
- it is non-critical for the current env question
- the retained critical truth is explicit and testable

Do not turn this into:
- blanket tolerance for unknown import errors
- “installer page visible therefore ignore everything”

## EVB4-004 Manual Positive Sample As Runner Truth Comparator

### Abstract

If the runner diverges from a verified manual positive sample, treat the manual path as a truth comparator.

Do not first grow more automation.
First reconcile:
- input completeness
- feed path
- DB/user principal
- probe field names
- any other concrete difference between runner and manual truth

### Case manifestation

SparkShop `r14 -> r16` required exactly that:
- manual remote import already proved a positive sample
- runner still diverged
- the real remaining gaps were concrete:
  - wrong probe field (`key` vs `k`)
  - wrong feed path assumptions
  - and finally the decisive one: runner had only been reading the first `300k` chars of `install.sql`
- `r16` only converged after aligning the runner to the manual truth path:
  - full SQL file
  - city-seed trim
  - root file import
  - corrected `store_way` probe

### Safe reuse rule

When a manual positive sample exists:
- prefer narrowing the runner toward that sample
- avoid adding fresh orchestration layers before the divergence is explained

The manual sample is a comparator, not a license to skip truthful artifact capture.

## EVB4-005 Browser-Visible PHP Capabilities Need Explicit Extension Truth

### Abstract

For PHP app env bootstrap, route liveness is not the same thing as browser-operable truth.

If installer or login flows depend on image/render capabilities such as captcha generation, then:
- the required PHP extensions must be treated as explicit env truth
- a `200` login page does not prove the browser can actually complete the flow
- a missing extension such as `gd` should be classified as an env gap, not as a minor UI annoyance

### Case manifestation

SparkShop exposed this twice across the same Tencent CVM climb:
- early handoff notes already flagged installer-required extensions such as `redis / exif / gd`
- later on the live `r16` browser path, `/admin/login/index.html` rendered but `/admin/login/captcha` still returned `500`
- the decisive runtime error was `Call to undefined function utils\\imagecreate()`, which traced back to missing `gd` in the generated PHP image

### Safe reuse rule

Reuse this lesson when:
- the app is a PHP image built from a thin generated Dockerfile
- browser completion depends on captcha, image resize, thumbnail, or installer environment checks
- the site shell renders but an image/action endpoint still `500`s

Before calling the env browser-verifiable, explicitly check:
- `php -m` for the needed extension set
- the real action/image endpoint, not only the outer HTML page

Do not overapply it to:
- findings whose proof path is fully API-only and does not depend on the browser completing an image-backed flow

## EVB4-006 Treat APT Reachability As A Real Bootstrap Gate, With Explicit Escalation Order

### Abstract

If the live env genuinely needs APT-installed build/runtime packages, then APT reachability is part of env truth and must not be hand-waved away.

Use an explicit escalation ladder:
- first try the smallest viable source adjustment
- if that works, stop there
- only escalate to a proxy path such as ClashParty when simpler source substitution still cannot unblock the required package install

### Case manifestation

SparkShop `r16` captcha hotfix made this concrete:
- the live repair genuinely needed Debian build deps to compile PHP `gd`
- large `deb.debian.org` package-index fetches stalled on the Tencent CVM
- switching only the blocking APT fetches to `mirrors.cloud.tencent.com` immediately unblocked the install
- because the simple mirror route already worked, there was no need to widen the repair into a ClashParty proxy path

### Safe reuse rule

Reuse this lesson when:
- a remote Dockerfile or container repair truly needs APT-installed packages
- the package step is blocking truthful env bootstrap or live runtime repair
- there is pressure to either overcomplicate networking too early or to pretend the package step is optional

Preferred order:
- keep base-image/runtime choices as stable as possible
- try the smallest source or mirror substitution that unblocks the package fetch
- only if official and simple mirror routes both still fail or stall, escalate to a proxy-based path
- if that proxy path is still needed and the frozen Tencent CVM loopback proxy is intentionally the operator's Mac-local Clash path, prefer reverse `SSH -R` backhaul to the Mac Clash port rather than emulating a local proxy on the Tencent CVM

Do not turn this into:
- unconditional mirror switching without checking whether official fetches are already fine
- premature proxy complexity when a plain mirror swap is enough

## EVB4-007 Historical Tencent CVM Rounds Should Default To Cold Snapshots

### Abstract

On a shared Tencent CVM, historical validation rounds are part of runtime pressure truth.

Do not:
- leave old env-bootstrap rounds running just because they once reached a useful state
- keep multiple MySQL/app stacks hot when only one decisive runtime is still active
- let `restart: unless-stopped` silently turn historical snapshots into auto-reviving memory leaks

Instead:
- inspect Docker/memory pressure before materializing a new remote round
- keep only the current decisive round runtime hot by default
- allow one declared `published-final` public runtime per delivered repo to remain hot when operators still need direct access
- preserve older useful rounds as **stopped** snapshots, with named images / volumes kept only when they still matter as restartable evidence

### Case manifestation

SparkShop on the shared Tencent CVM exposed this directly on `2026-04-18`:
- historical rounds `r1`, `r4`, `r5`, `r7`-`r15` were still running even though `r16` was already the decisive runtime
- those old stacks were carrying many extra `mysqld` processes and drove the host to roughly `6.2 GiB used / 128 MiB free` on a `7.5 GiB` machine
- the retained historical containers also still carried `restart=unless-stopped`, so a reboot or daemon recovery would have brought them back again
- converting those historical rounds to cold snapshots by stopping them and switching restart policy to `no` restored the host to roughly `1.9 GiB used / 4.5 GiB free` while keeping `r16` hot and the older evidence still restartable

### Safe reuse rule

Reuse this lesson when:
- a Tencent CVM is shared across multiple Loop9 rounds or repos
- old Docker stacks are still live even though the mainline has already converged to a later decisive round
- host pressure is starting to distort bootstrap/replay truth by causing avoidable memory scarcity

Preferred retention order:
- keep the latest decisive runtime hot only if it is still actively needed
- keep one repo-level `published-final` runtime hot only when there is an explicit public-access/operator contract
- keep older important rounds as stopped snapshots
- keep a short operator-visible retention note near the remote workspace root when manual cleanup changes hot/cold status, and make that note distinguish `published-final` from ordinary cold snapshots
- only reclaim containers / images / volumes older than `12h`, and never reclaim the current decisive runtime or anything marked/recorded as `published-final`

Do not turn this into:
- blind deletion of historical images/volumes that still serve as restartable evidence
- keeping every successful round hot “just in case”
- treating shared-host memory pressure as somebody else’s cleanup problem
