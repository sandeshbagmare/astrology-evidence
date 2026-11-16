# Sign-in-free workspace and UI refresh plan

Updated November 16, 2026. The user explicitly removed sign-in from current scope, deferred authentication, and authorized comparable-site research, parallel development, testing, commits and publication. This supersedes earlier MVP requirements for mandatory Google login. Historical authentication research remains useful for a later optional feature.

## Goal and design

Open directly into a calm astrology workbench. Keep Python/FastAPI/Jinja and the existing calculation, source-rights and bounded reading services. Use a warm ivory surface, deep teal/ink text, restrained gold accents, readable type, visible focus and responsive navigation. These visual choices are engineering defaults informed by the public-site review in [45 UI refresh research](45-ui-refresh-research.md), not a claim of measured superiority to other products.

The current sections are overview, birth profiles, chart explorer, readings, source library and data controls. Desktop navigation can use a sidebar; narrow layouts must expose every action without horizontal page scrolling. Forms group birth details, place/timezone, uncertainty and calculation method. Chart screens separate overview, facts, withheld calculations and provenance. Readings separate support status, source teachings, calculated facts and limitations. Empty states explain the next available action.

## Access and ownership

- Default `AUTHENTICATION_ENABLED=false`. No Google, development-login, sign-in or sign-out step is shown or required in the normal app.
- Each browser receives a fresh random anonymous workspace, backed by the existing user/session/CSRF records. Never use the shared synthetic-demo owner for anonymous visitors.
- Existing valid guest cookies reopen their own workspace. Expired/revoked/deleted sessions start a fresh guest workspace on navigation; deleted owners are never revived. Old signed-in sessions are not silently reused as guest identities.
- Keep ownership checks, origin validation, CSRF, expiry, safe cookies, data export and deletion. Removing account login does not authorize making birth records or readings public.
- Health/static and public source requests should not create workspace records. A first mutation without a bootstrapped workspace or valid CSRF is denied; ordinary page navigation and `/api/me` provide bootstrap.
- Explain that this browser holds access: another browser/device has a different workspace, and clearing cookies loses access. There is no cross-device recovery until an authentication feature is explicitly designed.
- Curator administration remains operator-authorized; anonymous visitors do not become curators. AI, content-rights and production-operation gates remain intact.
- `AUTHENTICATION_ENABLED=true` is a retained future compatibility path with protocol regressions, not a feature in the current user journey.

## Work and verification

1. Research 6–8 primary/public comparable products. Record inspected pages, visible features, access limits and design recommendations without copying assets or invented app internals.
2. Write failing guest regressions, implement automatic isolated access, and verify fresh browser independence, expired/deleted sessions, blocked legacy auth routes, first-request CSRF, admin denial and conditional production settings.
3. Write meaningful route/interaction regressions and redesign the Jinja shell, grouped forms, overview, profile/chart lists, reading/library/data screens. Preserve ordinary forms and DST-offset review, source-rights checks and deletion confirmation.
4. Run focused tests per subsystem, independent code/spec review, then the combined Python suites, native chart tests, Ruff, mypy, Node regressions and documentation validation. Check all major screens at desktop and 320px, keyboard focus, no-JavaScript entry, loading/errors and two separate browser workspaces.
5. Commit coherent tested changes with `[GPT-6.1 Sol]`, publish the updated guide, verify exact remote CI/build/Pages, and record the actual evidence in implementation progress and the model handoff article.

## Acceptance and limits

The normal browser can create a profile, calculate a chart, ask a bounded reading question, inspect available sources and use data controls without seeing or performing sign-in. No anonymous browser can read, mutate, export or delete another workspace. Missing model/corpus configuration produces clear limited behavior; the refresh must not fill empty states with fabricated predictions or book content. Authentication, licensed books, reviewed rules, independent chart references, expert evaluation and production deployment remain separate future work/gates.

## Progress

- Research and baseline inspection: eight official public sites compared, with access limits in dossier 45.
- Guest access and UI/navigation: implemented and reviewed with regression tests.
- Shared controls added during review: default 60 new workspaces per shared 60-second window and 100 accepted readings per UTC day, stored in database quota buckets. Replays are free; deletion/restart cannot refund global budget. Each reading still has a maximum of two model attempts.
- Final local checks through `ca3556f`: 342 non-native tests passed with five external-service skips, 35 native tests passed, Ruff/mypy and eight Node tests passed, and 90-document validation passed. Browser exercised 24 layouts plus guest isolation, DST/chart/reading, no-JavaScript/export/deletion. A privacy worker completed an export; owner download returned 200/no-store and another browser received 404.
- Independent reviews cleared operation-render errors, historical-chart binding, contrast corrections, short-viewport sidebar reachability, prerequisite chart guidance, bounded session repair, absolute expiry and stale historical-cookie recovery. The final security reviewer independently passed 15 adversarial checks. See [implementation progress](../implementation/PROGRESS.md) for remote CI/publication evidence.
