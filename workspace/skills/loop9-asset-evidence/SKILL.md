---
name: loop9-asset-evidence
description: Add a thin real-world asset-evidence layer for Loop9 weibu-submission target prioritization. Use when candidate repos/products are already narrowed down and you need to judge which target better fits current micro-step submission preferences based on China-mainland deployment scale, public exposure evidence, and government/county-level signal. Not for broad repository discovery, not for final launch orchestration, and not for large-scale asset export.
---

# Loop9 Asset Evidence

Use this skill to add a thin real-world asset-evidence layer before final target choice in `weibu-submission` flows.

## Core role

Use this skill to:
- validate whether a narrowed candidate is truly widely deployed in mainland China
- estimate whether public exposure scale is materially strong
- look for government / county-level / public-institution signal
- generate a conservative evidence card for upstream target selection

Do not use this skill to:
- do broad repository discovery or discover repositories from scratch
- replace the main discovery brain
- launch audits
- take over planner / queue / cron logic
- export large raw asset lists

## Minimal workflow

1. Confirm or switch identification surface (product name / alias / component name / title)
2. Probe Hunter first for scale and ICP/county signal
3. Probe FOFA second for scale / fingerprint / `.gov.cn` reinforcement
4. Use Shodan only when small supplementary detail is needed
5. Keep validation low-quota: stats first, then tiny samples, then evidence card
6. For a formal `weibu-submission` candidate judgment, upsert the compact result into `references/history-cases.md` instead of leaving history sync as a manual follow-up
7. Return a conservative summary to the caller; final target choice stays upstream

## Low-quota rule

Always prefer:
- statistics first
- fingerprint tightening second
- extremely small human-checkable samples third
- evidence-card output last

Do not start with deep pagination or large raw exports.

## References

Read these references as needed:
- `references/query-patterns.md`
- `references/evidence-card-schema.md`
- `references/platform-discipline.md`
- `references/sample-profiles.md`

Suggested loading pattern:
- read `query-patterns.md` when deciding how to probe a target
- read `evidence-card-schema.md` when writing the evidence card / summary
- read `platform-discipline.md` when deciding exact low-quota probe shape
- read `sample-profiles.md` when judging whether the target looks like a strong sample or a contrast sample
- read `history-cases.md` when a new repo-side candidate needs quick historical comparison against already-checked targets
- after a formal query/judgment, update `history-cases.md` via `python3 bin/loop9-asset-evidence-ad-hoc-probe.py history-upsert ...`

## Important boundaries

- Keep the skill thin
- Do not reduce priority judgment to raw count alone; preserve the lane for moderate-scale but early high-value-scene cases
- Let scripts handle exact field plumbing and probe execution only after those parts are stable
- Let the model handle fuzzy prioritization, sample-profile interpretation, and conservative wording
- Keep API keys and planner/launch logic outside the skill
