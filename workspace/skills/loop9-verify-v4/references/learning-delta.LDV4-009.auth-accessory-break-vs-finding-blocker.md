# LDV4-009 Auth Accessory Break Vs Decisive Finding Blocker

## Delta identity
- abstract_id: `LDV4-009`
- state: `observed`
- theme: `admin-gated replay / auth accessory failure / decisive blocker classification`

## Abstract layer

For admin-gated finding replay, a broken auth accessory such as a captcha renderer, helper image route, or other login-side UI support is **not automatically** the row's decisive blocker.

Use this split instead:
- first ask whether the current live lab lane can still truthfully establish admin session feasibility by a thinner on-box path
- if yes, take that bounded path once and continue to the protected feature's own replay surface
- then classify the row from the protected feature's decisive behavior, not from the accessory failure alone

Hard reading:
- broken captcha rendering is still real env truth
- but it does not by itself prove that the finding is auth-blocked
- if session feasibility can still be truthfully established inside the same lab lane, the row should be judged from the protected route's own blocker family

## Case layer

SparkShop on Tencent CVM `r16` exposed the split cleanly:
- `GET /admin/login/captcha` returned `HTTP 500`
- runtime log showed `Call to undefined function utils\imagecreate()`
- but the same-session math-captcha state still existed server-side, so a bounded on-box path could truthfully establish admin session feasibility
- after login, the real finding surface remained broken in its older family:
  - `GET /admin/ueditor/index?action=config` returned `[]`
  - `POST /admin/ueditor/index?action=catchimage` returned `HTTP 500`
  - runtime log again recorded `Undefined array key "catcherPathFormat"`

So the durable lesson is not “captcha break does not matter”.
The narrower lesson is:
- keep login accessory truth in its lane
- keep admin-session feasibility truth in its lane
- and freeze the finding from the protected route's decisive blocker when that blocker is now observable

## Evidence refs
1. `/Users/xlx/.openclaw/workspace/reports/2026-04-16-loop9-v4-tencent-cvm-finding-replay/rounds/sparkshop/F3-r1-ai-native-minimal-r16/objects/attempt-receipt.sparkshop.F3-r1-ai-native-minimal-r16.md`
2. `/Users/xlx/.openclaw/workspace/reports/2026-04-16-loop9-v4-tencent-cvm-finding-replay/rounds/sparkshop/F3-r1-ai-native-minimal-r16/artifacts/logs/admin-ueditor.sparkshop.F3.r16.runtime.log`
3. `/Users/xlx/.openclaw/workspace/reports/2026-04-16-loop9-v4-tencent-cvm-finding-replay/rounds/sparkshop/F3-r1-ai-native-minimal-r16/artifacts/logs/admin-ueditor.sparkshop.F3.r16.summary.log`

## Level judgment
- current judgment: `observed`
- why not higher yet:
  - the pattern is now live-consumed in one real Tencent CVM replay lane
  - but it is still supported by one repo family and one auth-accessory failure shape

## No-overclaim note

Do not flatten this into:
- “broken captcha can be ignored”
- “server-local session recovery equals normal user login feasibility”
- or “any login-side break means the row is replay-openable”

The narrower rule is:
- if the same live lab lane can still truthfully prove session feasibility,
- then continue to the protected route,
- and freeze the row from the protected route's decisive blocker rather than from the accessory failure alone.
