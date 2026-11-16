# End-to-end checks and recorded demos

November 16, 2026. Application baseline: `91812d1`; favicon update: `e2da911`; published demos: `992f094`. This pass adds recorded demonstrations, repeatable browser checks and a missing application favicon. It does not enable live AI or add production books. Public deployment and complete-playback evidence appears below.

## What the recordings show

All profiles and questions are invented. There is no audio. English captions, written steps, downloadable WebM videos and screenshots are available in the [published guide's demo section](https://sandeshbagmare.github.io/astrology-evidence/#demos).

- **Desktop, 1280×800:** automatic separate workspace; explicit UTC offset for a repeated local time; profile save; native chart; a question tied to the exact chart; insufficient-evidence result; unconfigured library-search state; completed private export; confirmed workspace deletion.
- **Mobile, 390×844, JavaScript disabled:** ordinary forms; unknown birth time; withheld precise calculations; chart-bound reading and explicit abstention; completed export and deletion.
- **Published guide tour:** section navigation, reading order, keyboard-compatible research disclosure, application preview, launch gates and mobile layout. This tour was recorded before the demo section itself was added; the final players and assets are tested separately.

The videos show real browser interactions with the local Python app and public guide, not a public hosted Python service. The missing corpus and disabled AI are visible; no generated answer is presented as verified astrological prediction.

## Fresh evidence

| Check | Result and boundary |
|---|---|
| Local Python application suite | 342 passed, 5 skipped in 31.05s; skips require PostgreSQL/Qdrant services unavailable locally |
| Native calculation suite | 35 passed in 1.23s under the existing approved Python 3.12 interpreter |
| Ruff | Pass across source and tests |
| mypy | Pass across 31 source modules |
| Prior exact baseline CI | `91812d1` Python, documentation and Pages all passed; the prior service-backed suite passed all 382 tests with no skips |
| Recorded desktop journey | Pass: chart snapshot binding, abstention, export download 200/no-store, confirmed deletion; zero JavaScript page errors |
| Recorded mobile journey | Pass with JavaScript disabled: ordinary forms, unknown-time limitations, export download 200/no-store and deletion |
| Fresh application browser checks | 24 screen/width checks; 65 native chart facts for the invented input; chart binding/abstention/reading deletion; foreign profile/chart/reading reads and reading deletion all 404, curator UI 403; JavaScript-disabled repeated-time input/export queue/workspace deletion; no page errors |
| Independent guide review | Final local verifier independently passed: 14 assets, five anchors, five widths, complete playback of all three videos, 7/7/5 caption cues within duration, zero browser errors. Portrait video measured 308 x 667 at a 390px viewport |
| Local final guide and videos | Coordinator and independent reviewer both passed `tests/browser/verify-pages.js`: 14 assets 200, five anchor targets, widths 1440/1024/768/390/320, keyboard skip/disclosure, all three videos played from start to ended and caption bounds passed |
| Additional web/health regression | 38 passed after the favicon change; 14 non-failing dependency deprecation warnings |
| Documentation/UI JavaScript | Eight Node tests passed, four browser scripts passed syntax checks, 91 documentation files validated with no issues |
| Published CI | Demo publication `992f094` passed Python, documentation/UI JavaScript and Pages deployment. Python: 382 passed, no skips, in 23.17s; Ruff/mypy, wheel build and packaged assets passed |
| Published browser check | PASS at 08:51 UTC: 20 repository links and 14 assets returned 200, all five anchor targets exist, all five widths fit, keyboard skip/disclosure passed, all three videos played to completion with valid caption bounds; zero page errors or unexpected request failures |

The independent API worker could not start because its model service rejected the request. Its attempted run is not counted as a test result. Coordinator browser tests cover the recorded journeys and fresh cross-workspace checks; existing automated security/ownership coverage and the previous independent 15-check adversarial review remain separate evidence. Two additional reviewers independently checked demo scripts/documentation; one also reran the complete final guide verifier locally. Their concrete findings (poster coverage, complete playback, portrait sizing and stale authentication wording) were corrected.

The final recordings last **23.92s desktop**, **22.76s mobile** and **15.84s guide**. An initial desktop recording with a cold-start blank segment was replaced; captions were aligned with the final videos. The mobile player preserves the native portrait ratio.

## Reproduce

Start the local synthetic app and privacy worker using [the runbook](RUNBOOK.md). Keep authentication, AI and embeddings disabled. With the installed Playwright CLI and an available browser:

```powershell
playwright-cli -s=verification open http://127.0.0.1:18766/ --browser msedge
playwright-cli -s=verification run-code --filename tests/browser/verify-app.js
playwright-cli -s=verification run-code --filename tests/browser/record-demos.js
playwright-cli -s=verification run-code --filename tests/browser/record-guide.js
playwright-cli -s=verification goto https://sandeshbagmare.github.io/astrology-evidence/
playwright-cli -s=verification run-code --filename tests/browser/verify-pages.js
```

Use the port where your app is actually running; 18766 is this development session's port. Scripts use isolated browser contexts, synthetic inputs and relative artifact paths. The recording script requests workspace deletion before closing each context. A running privacy worker is required to complete exports and queued purges. Rerecording changes videos and caption timing; review captions before publication. Tokens, cookies, traces, raw exports and browser storage are not published.

For a local guide preview, run `python -m http.server 18767 --bind 127.0.0.1` inside `docs`, navigate to that URL and run the same guide verifier. Repository-link checking runs against the published guide; the local preview checks local assets and playback.

## Confidence and limits

Passing these checks provides evidence for the exercised flows and deployed files; it cannot establish 100% correctness. Browser playback is tested in installed Microsoft Edge on Windows. Safari, Firefox, real mobile hardware, a full assistive-technology audit, sustained load and container execution are not claimed. Live provider behavior, licensed corpus quality, independent chart accuracy, expert interpretation/evaluation, inactive-workspace purge policy and production recovery remain open gates. The public Pages site is the guide and media host; the Python app is still a local development process.

## Exact published CI evidence

The demo publication commit is `992f0949f89741c2a3dacb1006cfa875006d1b43`; the favicon application change is `e2da911`. All three workflows completed successfully:

- [Python run 43832094881](https://github.com/sandeshbagmare/astrology-evidence/actions/runs/43832094881): 382 tests passed, no skips, in 23.17s with PostgreSQL 16/Qdrant 1.20; Ruff, mypy across 31 modules, wheel build and packaged web assets passed.
- [Documentation run 43832095094](https://github.com/sandeshbagmare/astrology-evidence/actions/runs/43832095094): documentation checker and eight Node tests passed.
- [Pages deployment 43832094170](https://github.com/sandeshbagmare/astrology-evidence/actions/runs/43832094170): deployed the guide/media. The public page returned 200 with the demo section.

The owner push was accepted while the required documentation status was still pending. These are verified post-push workflow outcomes; the push itself is not described as proof that branch protection blocked an unverified change.

## Final public browser result

The final `tests/browser/verify-pages.js` run passed against `https://sandeshbagmare.github.io/astrology-evidence/` at 08:51 UTC on November 16, 2026. This used the final paced verifier against the deployed guide/media revision `992f094`.

| Deployed check | Observed result |
|---|---|
| Repository links | All 20 unique GitHub links returned 200 |
| Site assets | All 14 unique linked assets, including posters, returned 200; videos use `video/webm`, captions use `text/vtt` |
| Fragment targets | All five exist |
| Responsive layout | 1440, 1024, 768, 390 and 320px: document width equals viewport width |
| Keyboard | Skip link first in tab order; disclosure opens with Enter |
| Desktop recording | 23.92s, 1280 x 800; played to `ended`; seven caption cues within duration; no media error |
| Mobile recording | 22.76s, 390 x 844; played to `ended`; seven caption cues within duration; no media error |
| Guide recording | 15.84s, 1280 x 800; played to `ended`; five caption cues within duration; no media error |
| Browser errors | Zero page errors and zero unexpected request failures |
| Native media cancellations | Three `ERR_ABORTED` media transfers for the exact sources that completed playback; reported separately by the verifier |

The final follow-up changes the verifier and evidence documents; it does not change the deployed HTML, stylesheet, media or application behavior tested here. Scripts are attached for reproduction; browser storage and raw exports are excluded.

## Verification issues investigated

The first public link-check burst received GitHub HTML HTTP 429 for an existing repository document. Isolated subsequent requests returned 200. Repository checks now run sequentially with four seconds between requests, at most three attempts, bounded backoff and respect for numeric/date `Retry-After`; missing links still fail the check. A requested cooldown over 45 seconds stops the run so the operator can retry later.

A public run completed every video but the request monitor flagged canceled native media transfers. A diagnostic run reproduced `net::ERR_ABORTED` for the same exact video URLs while all three players reached `ended` with no media error. The verifier reports those cancellations separately and permits them only for media sources whose complete playback, metadata and captions already passed. Every other request failure, page error, failed asset status or incomplete video remains fatal. These are verifier corrections, not claims that failed playback was ignored.
