# AI-native minimal finding-replay lane

This note defines the intended **minimum** for `finding-replay` when we want the lane to stay AI-native rather than drift into a script-first runner product.

## Canonical owner split

AI should own:
- the bounded replay question
- the current smallest action set
- the truth boundary
- the decision of whether the lane is:
  - `receipt-confirmed`
  - `blocked-confirmed`
  - `fixed-point`
  - `handoff-required`

Thin bridges may own only:
- SSH / rsync transport
- one-off PoC execution
- curl / HTTP capture
- deterministic file writeback
- receipt persistence

Hard reading:
- bridge execution is subordinate
- bridge success is not semantic success
- `stage-verdict.finding-replay.md` remains the child completion object

## Minimal replay cycle

1. Parent freezes one active finding and one bounded replay question.
2. Parent writes `stage-handoff.finding-replay.md`.
3. Child reads hot refs first and chooses the next smallest truthful remote/local action set.
4. Child may use thin bridges only as needed to answer the bounded question.
5. Child writes:
   - `attempt-receipt.<repo>.<finding>.md`
   - `stage-verdict.finding-replay.md`
   - minimal evidence refs
6. Parent consumes the verdict and writes back only active-finding truth.

## Tencent CVM reading

When `runtime_target=tencent-cvm` is frozen:
- the replay truth should be produced on the Tencent CVM itself
- remote `127.0.0.1` / `localhost` belong to the Tencent CVM, not the Mac host
- Docker commands, host-side Python/curl, container-shell commands, and PoC replays should happen on that server
- the child may still keep the artifact root on the Mac side if that helps reporting, but runtime truth must come from the Tencent CVM

### Action-endpoint probe discipline

If env-bootstrap artifacts already sampled an action endpoint with a bare probe:
- do not automatically treat that sample as finding truth unless the route's canonical method is the same as the probe
- for upload/multipart/action routes, canonical replay must still use the real method on the Tencent CVM itself
- if the finding depends on seeded config, verify the critical config truth first instead of terminalizing from route-shape noise alone

## Bridge choices that are acceptable

Acceptable first-version bridge choices include:
- a direct SSH command sequence
- one canonical PoC copied over with `rsync`
- one tiny inline Python probe
- one existing thin helper script

Not acceptable as the mainline:
- defining replay truth primarily through a request JSON schema
- treating a runner script as the semantic owner
- rewarding richer transport metadata as if it were new replay truth

## Self-evolution boundary

This lane may become more reusable over time, but only through live-consumed truth:
- a new rule/handoff shape is not self-evolution by itself
- it counts only when a later live replay actually uses the new default
- rollback should remain easy

So for early Tencent CVM work, prefer:
- thinner handoffs
- fewer bridge defaults
- clearer truth boundaries

Not:
- thicker runner protocols
- broader parameter surfaces
- more automation fields without live semantic gain
