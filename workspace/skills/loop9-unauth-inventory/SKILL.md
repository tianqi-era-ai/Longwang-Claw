---
name: loop9-unauth-inventory
description: Build or refresh a Loop9 inventory focused on unauthenticated, anonymous, no-auth, pre-auth, installer-exposed, weak-token, and default-secret-related findings from Loop9 audit outputs. Use when the user asks which audited or partially audited Loop9 projects contain unauthenticated/public-facing issues, wants a full list including archive historical-valid runs, wants installer/event-type issues separated from steady-state public vulnerabilities, or wants a companion list of projects that mention anonymous/public/token/installer surfaces but should NOT be overstated as confirmed high-value unauthenticated findings.
---

# Loop9 Unauth Inventory

Build a clean inventory of Loop9 unauthenticated/public-facing findings without mixing together steady-state public bugs, installer/deployment-window issues, token-holder chains, and downgraded boundary items.

## Workflow

### 1. Set scope first

Pick the pool before collecting results:

- **Active only**: current `Super8/temp/loop9` runs, excluding archive
- **Full inventory**: active runs **plus** `loop9_archive_有效但都已入库_不再需要关注/`
- **Exclude by default**: `loop9_archive_弃用任务备份/`

When the user says “全量” or wants to fix earlier omissions, include the valid archive pool.

### 2. Prefer evidence in this order

Use the strongest artifact available for each project:

1. `real_pocs/manifest.json`
2. `validation_report_v*`
3. `solution_v*`
4. `shared_context/*` only as support

Do not conclude from grep hits alone.

### 3. Treat these as the main trigger words, not final verdicts

These phrases are useful for discovery but not enough by themselves:

- `未授权`
- `无权限`
- `匿名`
- `未认证`
- `unauthenticated`
- `anonymous`
- `guest`
- `pre-auth`
- `installer`
- `install.php`
- `default secret`
- `token`
- `password reset`
- `account takeover`

Many Loop9 runs mention these words while ultimately concluding “do not overstate”. Always read the surrounding judgment.

### 4. Separate findings into buckets

Always split the inventory into these buckets when useful:

- **Confirmed / high-confidence unauth-related findings**
  - steady-state public no-auth exposure
  - anonymous state change / data read / file read / upload
  - unauthenticated account takeover path
  - installer / setup / upgrade takeover when exposure is treated as a real retained finding
- **Real but conditional / event-type / deployment-window findings**
  - installer re-entry
  - unfinished-install / pre-install takeover
  - public route only when a non-default feature remains exposed
  - token/secret issues that still need leakage, possession, or enablement conditions
- **Do not overstate / manual-review-only leads**
  - projects that repeatedly mention frontend / anonymous / token / installer language
  - but validator or final solution explicitly says they are not confirmed high-value unauthenticated findings

Do not flatten these buckets into one list.

### 5. Use precise labels

Prefer labels like:

- **steady-state unauthenticated public issue**
- **anonymous state-change issue**
- **unauthenticated file-read / info-leak**
- **unauthenticated upload surface**
- **unauthenticated account-takeover path**
- **installer-exposed takeover / reconfiguration**
- **event-type / deployment-window issue**
- **token-holder / secret-holder conditional issue**
- **not recommended for formal high-value unauth inventory**

Avoid overstating:

- SSRF-with-possible-upgrade is not automatically takeover or RCE.
- Token possession chains are not pure no-auth bugs unless the token source is low-precondition and public.
- Installer findings are often real, but they may still need separate labeling as deployment-window or event-type issues.

### 6. Recommended report shape

Prefer a compact bullet-table shape:

- **Project**
- **Finding title**
- **Type**
- **Maturity**
  - `real_poc-backed`
  - `validation-backed`
  - `solution-backed`
  - `lead-only`
- **Pool**
  - `active`
  - `archive-valid`
  - `archive-discarded`
- **Boundary note**
- **Evidence path**

If the user wants a faster summary, collapse by project and keep only the strongest unauth-related item.

## Important boundaries

- Archive-valid findings are still real findings; omission by a previous pass can be scope-related, not correctness-related.
- Archive-discarded backups should not be merged into the main inventory by default.
- Installer/wizard findings should usually be separated from steady-state public vulnerabilities.
- Mentions of `frontend / anonymous / token / installer` are discovery hints, not proof of a formal high-value unauthenticated finding.

## Current curated reference

For the current manually reviewed snapshot, including both the recommended inclusion list and the “do not overstate” exclusion guidance, read:

- `references/inventory-2026-03-20.md`

Use that file as the starting point, then refresh against local artifacts when the user asks for a newer or stricter pass.