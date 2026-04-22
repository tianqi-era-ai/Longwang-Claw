# Loop9 RCE Inventory — 2026-03-20 curated snapshot

This reference captures the manually reviewed outcome of the 2026-03-20 consolidation pass.

## 1. Confirmed / high-confidence RCE-related projects

### Active pool

- **Monitorr**
  - Finding: unauthenticated upload preserves PHP suffixes under a browser-served path, leading to likely default-deployment RCE
  - Type: unauthenticated upload -> conditional RCE
  - Maturity: real_poc-backed
  - Evidence: `Super8/temp/loop9/20260313-223031-Monitorr-a1f7/real_pocs/manifest.json`

- **Apache Shiro**
  - Finding: fixed rememberMe key -> deserialization / RCE
  - Type: deserialization RCE
  - Maturity: solution-backed / validation-backed
  - Evidence: `Super8/temp/loop9/20260314-000000-apache-shiro-ax31/solution_v5/part01.md`

- **top-think-framework**
  - Finding: public deserialization RCE exposure in version 8.0.0 (CVE-2024-44902)
  - Type: deserialization RCE exposure
  - Maturity: real_poc-backed
  - Evidence: `Super8/temp/loop9/20260314-173132-top-think-framework-s5qz/real_pocs/manifest.json`

- **Z-BlogPHP**
  - Finding: anonymous `put_appcentre.php` -> `App::UnPack()` -> `zb_users/` scoped PHP write / RCE
  - Type: accepted-deployment-surface supply-chain/helper RCE
  - Maturity: real_poc-backed
  - Evidence: `Super8/temp/loop9/20260314-193254-zblogphp-nifw/real_pocs/manifest.json`

- **ZenTaoPMS**
  - Findings:
    - repository-validation command injection to server-side RCE
    - extension ZIP traversal -> arbitrary file write -> likely follow-on RCE
  - Type: backend RCE + arbitrary write -> likely RCE
  - Maturity: solution-backed / validation-backed
  - Evidence: `Super8/temp/loop9/20260314-213123-zentaopms-0001/solution_v4/part01.md`

- **MODX**
  - Finding: dashboard PHP widget causes arbitrary PHP execution
  - Type: authenticated/backend direct execution primitive
  - Maturity: solution-backed / validation-backed
  - Evidence: `Super8/temp/loop9/20260316-183503-modx-2zo6/solution_v3/part01.md`

- **phpwcms**
  - Finding: CP Form unauthenticated upload to public directory with `.phtml`-class direct RCE landing surface
  - Type: unauthenticated upload -> conditional RCE
  - Maturity: solution-backed / validation-backed
  - Evidence: `Super8/temp/loop9/20260316-203438-phpwcms-8a7f/solution_v3/part01.md`

- **SMF**
  - Finding: HTTPS download chain does not verify certificates; admin package install can be MITM-hijacked into code execution
  - Type: supply-chain-to-RCE
  - Maturity: real_poc-backed
  - Evidence: `Super8/temp/loop9/20260316-213341-SMF-7D27/real_pocs/manifest.json`

- **Vanilla**
  - Findings:
    - legacy addon/theme/application metadata `eval()` -> admin-triggered RCE
    - locale pack enumeration `eval()` -> admin-triggered RCE
  - Type: backend/admin-triggered RCE
  - Maturity: solution-backed / validation-backed
  - Evidence: `Super8/temp/loop9/20260316-vanilla-153234-6f4a/solution_v3/part01.md`

- **EspoCRM**
  - Finding: extension/upgrade ZIP upload Zip Slip -> backend arbitrary path write, potential RCE
  - Type: arbitrary write -> potential RCE
  - Maturity: real_poc-backed
  - Evidence: `Super8/temp/loop9/20260317-083401-espocrm-d666/real_pocs/manifest.json`

- **Matomo**
  - Findings:
    - plugin ZIP upload can overwrite always-activated core plugin directory -> backend PHP overwrite / later RCE
    - update HTTP fallback creates update-chain RCE surface
  - Type: plugin-chain / update-chain to RCE
  - Maturity: solution-backed
  - Evidence: `Super8/temp/loop9/20260317-104153-matomo-wsit/solution_v1/part01.md`

- **OrangeHRM**
  - Finding: pre-install installer config injection causes pre-authenticated PHP code execution
  - Type: pre-install pre-auth RCE
  - Maturity: solution-backed / validation-backed
  - Evidence: `Super8/temp/loop9/20260318-103519-orangehrm-4xjy/solution_v5/part02.md`

- **LimeSurvey**
  - Finding: plugin ZIP install path traversal via config.xml metadata name -> backend arbitrary file write / likely RCE
  - Type: arbitrary write -> likely RCE
  - Maturity: real_poc-backed
  - Evidence: `Super8/temp/loop9/20260318-024715-LimeSurvey-65m3/real_pocs/manifest.json`

- **phpList3**
  - Finding: `fckphplist.php` arbitrary file write / path traversal -> RCE
  - Type: backend arbitrary file write -> direct RCE
  - Maturity: solution-backed / validation-backed
  - Evidence: `Super8/temp/loop9/20260319-013658-phplist3-7m4p/solution_v4/part01.md`

- **Leantime**
  - Finding: marketplace plugin install/enable chain to RCE under compromised source or transport
  - Type: supply-chain-to-RCE
  - Maturity: solution-backed / validation-backed
  - Evidence: `Super8/temp/loop9/20260319-123637-leantime-BGBQ/solution_v3/part01.md`

- **ProjectSend**
  - Finding: arbitrary remote update package install -> app-root write -> RCE
  - Type: backend update-chain direct RCE
  - Maturity: solution-backed / validation-backed
  - Evidence: `Super8/temp/loop9/20260319-163403-projectsend-8qds/solution_v3/part02.md`

- **LibreBooking**
  - Finding: admin email-template edit -> path traversal arbitrary file write -> Web-directory landing -> RCE
  - Type: backend arbitrary file write -> RCE
  - Maturity: solution-backed / validation-backed
  - Evidence: `Super8/temp/loop9/20260319-193423-librebooking-8cbf/solution_v3/part01.md`

### Archive-valid pool

- **DedeCMS**
  - Findings:
    - `dede/sys_info.php` config rewrite persistent RCE
    - `dede/article_template_rand.php` write PHP + `require_once` RCE
    - `dede/tag_test_action.php` template-test direct `eval` RCE
    - `dede/tpl.php` arbitrary tag PHP file write / RCE
  - Type: backend direct RCE / file-write-to-RCE
  - Maturity: real_poc-backed
  - Evidence: `Super8/temp/loop9/loop9_archive_有效但都已入库_不再需要关注/20260313-110840-DedeCMS-qkp9/real_pocs/manifest.json`

## 2. Confirmed but lower-confidence wording / conditional emphasis

- **ThinkSNS Plus**
  - Finding: backend extension upload writes arbitrary file to public disk, with potential RCE / trojan-drop value
  - Type: arbitrary write -> potential RCE
  - Maturity: real_poc-backed
  - Evidence: `Super8/temp/loop9/20260313-124531-thinksns-plus-la33/real_pocs/manifest.json`

## 3. Suspicion / worth manual review, but do not flatten into confirmed RCE

- **phpBB**
  - Multiple solution rounds mention an admin-to-RCE direction.
  - Validator repeatedly says not to present it as a default closed RCE chain.
  - Treat as manual-review-worthy suspicion, not confirmed inventory-grade RCE.

- **Chamilo**
  - `test_mailer` is best described as SSRF with deployment-dependent RCE escalation potential.
  - Do not relabel it as confirmed RCE.

- **hi-events**
  - Conditional arbitrary file upload / potential RCE language appears.
  - Later wording keeps it bounded and not a default confirmed RCE.

- **laravel-crm**
  - Low-privilege backend file drop with authenticated RCE extension value under common deployment.
  - Still environment-dependent and not fully promoted.

- **facturascripts**
  - Upload filename trust gap exists, but reliable RCE depends on deployment/server behavior.

- **qloapps**
  - Review-image upload is a meaningful surface, but static review does not support current unauthenticated RCE promotion.

- **winter**
  - Theme-import chain plus `CodeParser` gives a dangerous execution sink.
  - Missing stable arbitrary-write primitive in the reviewed round; keep as suspicion/lead.

- **freshrss**
  - Update/extension execution capability exists, but default posture is not a clean unauthenticated RCE.

- **grav (v1 claim only)**
  - Earlier `safe_functions` / Twig rewrite RCE claim was later removed as unconfirmed.
  - Keep only as historical suspicion, not active confirmed finding.

## 4. Excluded by default from the full inventory

- `loop9_archive_弃用任务备份/`
  - Do not include by default, even if RCE-like items exist there.
  - These are discarded/deprecated backups and should be called out separately if the user explicitly wants them.

## 5. Recommended wording for user-facing summaries

Use:

- `confirmed / high-confidence`
- `solution-backed but not yet shared`
- `suspected only / worth manual review`
- `archive-valid historical result`
- `archive-discarded backup (excluded by default)`

Avoid:

- treating SSRF-with-RCE-upgrade as confirmed RCE
- treating validator-downgraded admin-to-RCE directions as closed default RCE
- mixing archive-valid and archive-discarded pools