---
name: loop9-rce-inventory
description: Build or refresh a Loop9 RCE-related project inventory from Loop9 audit outputs. Use when the user asks which Loop9 projects have RCE / code-execution / likely-RCE / supply-chain-to-RCE findings, wants a full list including archive historical-valid runs, wants suspected-but-not-confirmed RCE leads separated out, or needs a clean report that distinguishes active runs, archive-valid results, archive-discarded backups, and evidence maturity.
---

# Loop9 RCE Inventory

Build a clean Loop9 RCE-related inventory without mixing together confirmed results, conditional chains, and downgraded suspicion-only leads.

## Workflow

### 1. Set the scope first

Decide which pool the user wants:

- **Active only**: current `Super8/temp/loop9` runs, excluding archive
- **Full inventory**: active runs **plus** `loop9_archive_有效但都已入库_不再需要关注/`
- **Do not include by default**: `loop9_archive_弃用任务备份/` unless the user explicitly wants discarded/deprecated history

When the user says “全量” or explicitly wants to fix earlier omissions, include the valid archive pool.

### 2. Prefer evidence in this order

Use the strongest source available for each project:

1. `real_pocs/manifest.json`
   - best source for stable, shared, post-review findings
2. `validation_report_v*`
   - confirms whether the claim survived review
3. `solution_v*`
   - useful for RCE-related findings that exist in audit conclusions but have not yet been promoted into shared real-poc manifests
4. `shared_context/*`
   - only as support, not as the main proof source

Do not treat keyword grep hits alone as conclusions.

### 3. Separate findings into buckets

Always split output into these buckets when useful:

- **Confirmed / high-confidence RCE-related**
  - direct RCE
  - arbitrary file write -> likely RCE
  - supply-chain/install/update path -> code execution
  - deserialization RCE with accepted audit support
- **Solution-backed but not yet fully shared**
  - appears clearly in `solution_v*` and survives `validation_report_v*`
  - but not yet represented in shared `real_pocs/manifest.json`
- **Suspicion / worth manual review**
  - admin-to-RCE direction
  - deployment-dependent potential RCE
  - previously proposed but later downgraded by validator

Do not flatten these three buckets into one list.

### 4. Use precise language

Prefer these labels:

- **direct RCE**
- **authenticated/backend RCE**
- **arbitrary file write -> likely RCE**
- **supply-chain-to-RCE**
- **deserialization RCE exposure**
- **conditional / deployment-dependent RCE**
- **suspected only, not confirmed**

Avoid overstating:

- If validator explicitly said “do not call this closed/default RCE”, preserve that caution.
- If the finding is really SSRF with an RCE upgrade possibility, do **not** relabel it as RCE.
- If a project is only in discarded/deprecated archive, say that explicitly.

### 5. Recommended report shape

Prefer a compact table-like bullet format:

- **Project**
- **Finding title**
- **Type**
- **Maturity**
  - `real_poc-backed`
  - `validation-backed`
  - `solution-only`
  - `suspicion-only`
- **Pool**
  - `active`
  - `archive-valid`
  - `archive-discarded`
- **Evidence path**

If the user wants a faster executive summary, collapse by project and list the strongest RCE-related item only.

## Important boundaries

- Archive-valid results are still real results; they were omitted only by scope, not because they were false.
- Archive-discarded backups are not equal to archive-valid runs.
- A project can belong in the inventory even if the RCE finding is backend-only.
- A project with only “potential RCE” language belongs in the suspicion bucket unless validator-backed evidence upgrades it.

## Current curated reference

For the current curated inventory and the manually reviewed suspicion list from the latest pass, read:

- `references/inventory-2026-03-20.md`

Use that file as a starting point, then refresh against local artifacts if the user asks for re-checking, a newer snapshot, or a stricter/fuller inventory.