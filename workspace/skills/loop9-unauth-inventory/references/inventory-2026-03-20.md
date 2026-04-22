# Loop9 Unauthenticated Inventory — 2026-03-20 curated snapshot

This reference captures the manually reviewed outcome of the 2026-03-20 unauthenticated/public-facing consolidation pass.

## 1. Confirmed / high-confidence unauth-related projects

### Active pool

- **FUDforum**
  - Findings:
    - unauthenticated temporary-attachment IDOR / file-read
    - exposed `install.php` enables unauthenticated takeover
  - Type: unauth file-read + installer-exposed takeover
  - Maturity: real_poc-backed / validation-backed

- **Open Web Analytics**
  - Findings:
    - unauthenticated `POST v1/siteUsers` ACL write
    - anonymous tracking -> referer fetch -> SSRF chain
  - Type: unauth state change + SSRF
  - Maturity: real_poc-backed / solution-backed

- **Geeklog**
  - Findings:
    - `pingback.php` unauthenticated SSRF
    - bundled Filemanager unauthenticated arbitrary file upload
  - Type: unauth SSRF + unauth upload surface
  - Maturity: solution-backed / validation-backed

- **ThinkSNS Plus**
  - Findings:
    - unauthenticated front-end path traversal arbitrary file read
    - stale password-reset code -> account takeover
    - stale PC dynamic-login code -> account takeover
    - stale registration code -> expired-code registration /抢注
  - Type: unauth file-read + account takeover family
  - Maturity: real_poc-backed / validation-backed

- **InvoicePlane**
  - Finding: installer re-entry can be progressed unauthenticated and rewrite DB config when `ipconfig.php` remains writable
  - Type: installer-exposed reconfiguration takeover
  - Maturity: real_poc-backed / validation-backed

- **InvoiceNinja**
  - Findings:
    - default `UPDATE_SECRET=secret` exposes `/update`
    - `/setup/check_db` and `/setup/check_mail` remain reachable for unauth SSRF / probing
    - some `guest` middleware-protected routes are effectively publicly reachable because the middleware logs out and continues
  - Type: default-secret trigger + setup SSRF/probe + public-route weakness
  - Maturity: real_poc-backed / solution-backed

- **Elgg**
  - Finding: unauthenticated account enumeration + password-reset mailbomb
  - Type: account-flow abuse
  - Maturity: real_poc-backed / validation-backed

- **Monitorr**
  - Findings:
    - unauthenticated upload preserving PHP suffixes -> conditional RCE
    - copied admin routes execute unauthenticated registration before later denial
    - unauthenticated blind SSRF / internal service discovery
    - unauthenticated preference/site/CSS writers allow persistent tampering
  - Type: unauth upload + unauth state change + SSRF + control-plane tamper
  - Maturity: real_poc-backed

- **LimeSurvey**
  - Finding: unauthenticated direct plugin dispatch can invoke `TwoFactorAdminLogin::beforeDeactivate`
  - Type: unauth dangerous plugin action
  - Maturity: real_poc-backed / solution-backed

- **Dolibarr**
  - Finding: online-sign token empty -> unauthenticated forged sign / reject
  - Type: unauth business-state modification
  - Maturity: real_poc-backed / solution-backed

- **SuiteCRM**
  - Findings:
    - `jjwg_Maps` unauthenticated geocode trigger
    - `acceptDecline` anonymous invite-state modification
    - `responseEntryPoint` anonymous FP_events invite-state modification
  - Type: unauth state change / external-trigger abuse
  - Maturity: real_poc-backed / validation-backed

- **ImpressCMS**
  - Finding: installer reentry allows unauthenticated reconfiguration when `/install/` remains reachable
  - Type: installer-exposed reconfiguration takeover
  - Maturity: real_poc-backed

- **Phorum**
  - Findings:
    - unauthenticated forum configuration leak via `getforumsettings`
    - stronger review line also retained JSONP / front-end script-execution-oriented surfaces in solution analysis
  - Type: unauth config leak
  - Maturity: real_poc-backed / solution-backed

- **MACCMS10**
  - Finding: public `api/timming` can unauthenticatedly trigger backend tasks and SSRF-adjacent abuse
  - Type: unauth task trigger / SSRF-adjacent abuse
  - Maturity: real_poc-backed / solution-backed

- **Z-BlogPHP**
  - Finding: anonymous `put_appcentre.php` helper can be driven into package unpack / PHP write under accepted deployment assumptions
  - Type: anonymous helper exposure -> conditional high-impact write/RCE
  - Maturity: real_poc-backed

- **Matomo**
  - Findings:
    - unfinished-install / installation-window anonymous takeover
    - anonymous maintenance-window `updateCorePlugins=1` trigger
  - Type: installer/maintenance-window unauth state change
  - Maturity: solution-backed / real-poc-side refinement-backed

- **Magento2**
  - Findings:
    - anonymous address custom-attribute upload endpoint without inherited login gate
    - anonymous custom-option file download chain lacked object ownership enforcement in review
  - Type: unauth upload / file access boundary issue
  - Maturity: solution-backed / validation-backed
  - Boundary: not promoted as a clean default high-value candidate

- **HumHub**
  - Finding: pre-install state unauthenticated administrator takeover
  - Type: installer/pre-install takeover
  - Maturity: real_poc-backed / validation-backed

- **phpIPAM**
  - Finding: fresh/default-state unauthenticated installer postinstall takeover
  - Type: installer postinstall takeover
  - Maturity: real_poc-backed / validation-backed

- **OpenCart** `[archive-valid]`
  - Findings:
    - `install/upgrade_1` unauthenticated config rewrite and admin-directory migration
    - `install/upgrade_4` unauthenticated schema rewrite
    - `install/upgrade_5` unauthenticated core-setting rewrite
  - Type: installer/upgrader exposure -> destructive reconfiguration
  - Maturity: archive-valid solution-backed

- **DedeCMS** `[archive-valid]`
  - Finding: `plus/guestbook/edit.inc.php` anonymous guestbook modification chain
  - Type: anonymous content tampering
  - Maturity: real_poc-backed

- **Joomla CMS**
  - Finding: public `com_ajax` + `sampledata/testing` guest persistent write on development-state installs
  - Type: guest persistent write
  - Maturity: validation-backed / real-poc-backed

- **e107**
  - Finding: public `install.php` insecure deserialisation via `previous_steps`
  - Type: unauthenticated installer deserialisation
  - Maturity: solution-backed

- **Contao**
  - Findings:
    - captcha bypass on public route
    - Host Header–driven reset/opt-in link poisoning -> token theft / account takeover
  - Type: unauth flow abuse / takeover chain
  - Maturity: solution-backed / validation-backed

- **MantisBT**
  - Findings:
    - Host / `X-Forwarded-Host` reset-link poisoning
    - exposed `admin/install.php` SSRF / reinstall surface
    - default `administrator` / `root` bootstrap-account issue
  - Type: unauthenticated takeover / installer exposure / default-state issue
  - Maturity: solution-backed / real_poc-backed

- **Roundcube**
  - Findings:
    - installer merge-config sensitive disclosure
    - installer SMTP / IMAP test SSRF
    - public OAuth backchannel logout-token signature-bypass route
  - Type: installer exposure + public auth-flow weakness
  - Maturity: validation-backed / solution-backed

- **OpenDocMan**
  - Finding: exposed installer/upgrader allows unauthenticated destructive reset and schema mutation
  - Type: installer/upgrader destructive takeover
  - Maturity: solution-backed / validation-backed

- **Facturascripts**
  - Findings:
    - installer first-boot takeover / `config.php` poisoning
    - `/MyFiles/Public` token-bypass traversal
    - public static-file traversal on `Files` routes
    - weakly protected `/deploy` rebuild / disable-plugins actions
  - Type: installer poisoning + unauth file-read / action trigger
  - Maturity: solution-backed / validation-backed

- **YOURLS**
  - Findings:
    - custom page route traversal -> local PHP include
    - public-mode remote title fetch -> SSRF
  - Type: front-end no-auth LFI + conditional SSRF
  - Maturity: solution-backed / validation-backed

- **Bagisto**
  - Finding: public `ImageCache` route traversal -> unauthenticated arbitrary file read
  - Type: unauth file-read
  - Maturity: solution-backed / validation-backed

- **Faveo Helpdesk**
  - Findings:
    - public installer route set missing effective installer protection
    - unauthenticated client/ticket reply-state write issue in accepted analysis
  - Type: unauth installer + unauthenticated state change
  - Maturity: solution-backed / validation-backed

- **Mibew**
  - Finding: password-reset poisoning via request-derived host -> operator account takeover
  - Type: unauthenticated takeover chain
  - Maturity: solution-backed / validation-backed

- **openSIS-Classic**
  - Finding: unauthenticated staff/parent password reset takeover
  - Type: unauthenticated account takeover
  - Maturity: solution-backed / validation-backed

- **RosarioSIS**
  - Findings:
    - default-install-chain admin takeover risk
    - public registration CAPTCHA can be client-forged -> unauth bulk registration
  - Type: default-state takeover + unauth registration abuse
  - Maturity: solution-backed

- **helpdeskz-dev**
  - Findings:
    - legacy auto routing exposes staff controllers without auth
    - unauthenticated path-traversal delete via editor route
    - chain into front-visible persistent XSS in retained analysis
  - Type: unauth route exposure + state/destructive action
  - Maturity: solution-backed

- **Admidio**
  - Findings:
    - unauthorized documents/files rename/move under public-facing confusion chain
    - public SAML SSO trust failure
    - OIDC introspection/revocation semantics appear unauthenticated in source review
  - Type: unauth authz/authn design weaknesses
  - Maturity: solution-backed

- **EasyAppointments**
  - Finding: `google/get_google_calendars?provider_id=<id>` unauthorized Google Calendar metadata read
  - Type: unauth third-party metadata leak
  - Maturity: solution-backed / validation-backed

- **ERPNext**
  - Finding: `task_info` public page leaks Task information without authorization
  - Type: unauth information disclosure
  - Maturity: solution-backed

- **NotrinosERP**
  - Finding: sensitive runtime files left under web root with effective protection mainly dependent on `.htaccess`
  - Type: unauth sensitive-file exposure design flaw
  - Maturity: solution-backed

- **LibreBooking**
  - Findings:
    - unauthenticated iCal export leaks reservation details when `rn` is known
    - fresh-install first registrant auto-admin remains a real scene-dependent issue
  - Type: unauth info leak + default-state role bootstrap issue
  - Maturity: solution-backed / validation-backed

- **Wallabag**
  - Finding: failed import files land in public directory and become anonymously readable
  - Type: authenticated plant -> anonymous read result
  - Maturity: solution-backed
  - Boundary: do not model this as a pure no-auth input bug

## 2. Useful conditional / event-type / weaker but real unauth-related items

- **WebCalendar**
  - `wizard/index.php` unauthenticated installer/config takeover if `wizard/` remains online

- **Leantime**
  - public cron endpoint allows unauthenticated triggering of scheduled workload

- **Piwigo**
  - legacy `upgrade.php` remote-site branch can be guest-triggered on affected legacy deployments

- **OpenProject**
  - `sys/fetch_changesets` may become unauthenticated when an official feature is enabled with blank key

- **GroupOffice**
  - guest-accessible `ajaxWidget -> Plupload` creates unauth temp-file write / disk-fill primitive

- **OpenPSA**
  - `lostpassword` anonymous forced reset direction kept as a real chain in later rounds

- **CRM (hsz4)**
  - predictable public verification/reset tokens (`uniqid()`) weaken public-token secrecy
  - real but not yet a clean default no-auth takeover chain

## 3. Do not overstate / not recommended for formal high-value unauth inventory

These projects mention front-end / anonymous / token / installer surfaces, but the latest review explicitly says they should **not** be treated as formal high-value unauthenticated findings:

- **Froxlor**
- **Redaxo**
- **ProcessWire**
- **MODX**
- **SMF**
- **Shopware**
- **WordPress**
- **Moodle**
- **Winter**
- **Freshrss**
- **ProjectSend**
- **phpList3**
- **Laravel CRM**
- **EspoCRM** (public token/reset edges exist, but strong no-auth candidate remains explicitly unconfirmed)
- **Mautic** (anonymous open redirect is real, but not a formal high-value unauth candidate)
- **Snipe-IT**
- **BookStack**
- **WackoWiki**
- **Redmine**
- **Wallabag** as a primary no-auth source bug
- **QloApps** hotel-review upload direction
- **hi-events** token-holder secret-link style leads
- **GLPI** anonymous tmp upload enum/delete only as conditional and lower-priority
- **Magento2** as a clean default no-auth high-value candidate

Reason pattern:

- event/deployment-dependent only,
- token-holder / secret-holder conditional,
- authenticated plant + public trigger,
- validator explicitly downgraded,
- or evidence insufficient for a stable no-auth high-value conclusion.

## 4. Recommended wording

Use:

- `confirmed / high-confidence unauth-related`
- `installer / setup / upgrade exposure`
- `event-type / deployment-window`
- `token-holder conditional issue`
- `not recommended for formal high-value unauth inventory`

Avoid:

- treating every installer issue as a steady-state default runtime bug,
- treating every token issue as a pure no-auth bug,
- treating every public route as a high-value unauthenticated vulnerability,
- mixing archive-valid findings with discarded archive backups.