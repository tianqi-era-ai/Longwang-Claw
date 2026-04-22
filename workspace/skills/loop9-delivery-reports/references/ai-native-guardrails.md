# Loop9 Delivery Reports — AI-Native Guardrails

This skill is allowed to have scripts, but the scripts are not the parent lane.

Control model:

- AI owns:
  - which round / report tree is the real source of truth
  - whether the live lane already drifted into script-first control
  - whether a mismatch is substantive truth drift or merely stale paper counters
  - final acceptance / rejection of the refreshed bundle
- code owns only:
  - deterministic file emission
  - deterministic copying / path binding
  - bounded receipt/marker writeback

## Mandatory drift audit

Before expanding or fixing the bridges, inspect all three surfaces together:

1. current round truth objects
   - `repo-findings-board`
   - `repo-closure-review`
   - `repo-round-verdict`
   - relevant `attempt-receipt / stage-verdict / stage-handoff.finding-replay.*`
2. live report tree
   - `workspace/reports/<repo>/`
3. active bridge code
   - `scripts/build_repo_delivery_reports.py`
   - `scripts/run_delivery_report_bridge.py`
   - `scripts/run_final_local_review_bridge.py`

Ask first:

- Did the mainline silently become “trust the generator / trust the review bridge” instead of “trust the handoff/verdict/receipt truth”?

If yes, fix the route before adding more machinery.

## High-severity drift signatures

Treat these as route-failure signals:

- the workflow is narrated as “run the script” before the truth objects are read
- the bridge starts owning inclusion policy, discrepancy interpretation, or acceptance policy
- a stale aggregate counter is trusted because it looks canonical
- a bridge script is treated as more authoritative than `stage-verdict` / `stage-handoff`
- more Python is added every time a report mismatch appears, instead of first re-checking the AI-native lane

## Hard-edge admission bar

Only keep a code change in the active lane if all are true:

1. it fixes a deterministic hard edge
2. the same fix could be explained without granting the script semantic ownership
3. the AI lane still has to inspect the result afterward
4. deleting the bridge later would not change the control model

Examples that usually qualify:

- choosing the current object file when multiple suffixed variants exist
- copying the right PoC file to the right deterministic location
- writing a stable manifest path

Examples that should trigger suspicion first:

- deciding report truth from old counters instead of row-level truth
- deciding publishability from opaque script policy
- turning the review bridge into a large policy engine

## Post-bridge AI checks

After any bridge run, AI must explicitly inspect:

- the included finding set
- the held-out finding set
- the effective PoC set
- whether `00 / 01 / 02 / 98 / 99` agree on the same bundle shape
- whether any upstream paper counters still disagree with row-level truth

If the bundle is locally self-consistent but upstream paper counters are stale:

- record the drift truthfully
- do not let old paper numbers override the refreshed bundle

## Repair preference

Preferred order:

1. restore AI-native ownership
2. repair wrong handoff/verdict/receipt truth if needed
3. repair a bounded deterministic bridge
4. only then consider whether new code is still necessary

Forbidden reflex:

- “a Python bug happened, therefore the answer is more Python”
