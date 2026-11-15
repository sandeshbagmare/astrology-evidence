# Accessibility and responsive validation

Prepared and primary sources inspected: 2026-11-15. Status: proposed requirements and validation protocol; no application, browser, assistive-technology or automated accessibility tests have run. This dossier extends documents 09, 21 and 43 without changing their scope.

## Standard, priorities and release evidence

Target WCAG 2.2 AA across complete core journeys, including authentication handoff, errors and dynamic states. WCAG is the normative reference; WAI tutorials, Understanding documents and ARIA Authoring Practices explain implementation approaches rather than independently certifying compliance [S1–S7]. Product choices below are acceptance targets.

**Critical blockers:** inaccessible login/consent, keyboard traps, lost submission data, unavailable uncertainty choices, invisible focus, unreadable evidence, or status that falsely implies completion. Fix before real-user release. **Other conformance failures:** contrast, names, relationships and reflow failures remain release issues even when an automated tool rates them moderate. **Informational improvements:** wording refinements and additional convenience shortcuts can enter the backlog when no requirement or task completion is affected. Tool severity is not the product's sole priority system.

The release record must include build identifier, synthetic fixtures, browser/OS/screen-reader versions, test date, reviewer, screenshots where useful, reproduction steps and unresolved findings. Zero critical automated findings is necessary but cannot substantiate WCAG conformance alone. Manually assess every applicable A/AA criterion; do not label untested criteria passed [S1, S10].

## Component matrix

| Component | Proposed semantics and behavior | Primary validation |
|---|---|---|
| Navigation | Landmarks, page heading, skip link, ordinary links | Keyboard order; heading navigation |
| Google entry and consent | Named sign-in action; separate processing choice | Cancellation, return, refusal |
| Birth inputs | Labels, grouped certainty choices, explicit formats | Unknown/interval/DST errors |
| Place selection | Named candidates and manual fallback | Keyboard selection; announced result count |
| Chart | Named SVG summary plus adjacent data table | Equivalent facts and uncertainty |
| Evidence disclosure | Button with expanded state | Enter/Space; preserved focus |
| Source drawer | Declared modal or nonmodal behavior | Escape, tab sequence, return |
| Generation status | Stable polite status region | Transition announcements only |
| Validation | Summary links and associated field errors | Recovery without lost values |
| Export/delete | Named scope, status, confirmation where destructive | Focus and downloadable alternatives |

Native controls are preferred; adding ARIA does not supply missing keyboard behavior. Disclosure controls expose expanded/collapsed state and work with Enter and Space [S3]. All evidence categories retain literal labels: Calculated, Traditional interpretation, AI synthesis, Disagreement and Unavailable. Color, icon shape or chart position alone never communicates category or certainty; this implements the project's evidence distinction and WCAG use-of-color requirement [S1].

## Birth data, authentication and validation

Proposed birth-date controls have distinct day, month and year labels, Gregorian-calendar instructions, and a normalized confirmation such as “15 November 1990.” Avoid an unlabeled numeric date or mandatory calendar-only interaction. A certainty fieldset offers Exact, Approximate and Unknown; selecting Unknown removes exact-time requirements and displays the unavailable chart factors. Approximate time reveals labelled interval endpoints, local zone and an explicit explanation for intervals crossing midnight. Keep unavailable precision distinct from an input error.

Exact time exposes the chosen 12/24-hour convention and AM/PM where relevant. Ambiguous local times offer labelled occurrences with their offsets; nonexistent times explain the problem and retain inputs. Place suggestions include city, region and country. A failed lookup retains the typed query and exposes manual coordinates/zone entry. Associate help and errors with their fields; after rejected submission focus the error-summary heading and provide links to invalid controls. Avoid simultaneous assertive announcement of every field error [S4].

Google sign-in has an accessible text name and visible focus. Test the app's entry, canceled sign-in, returned error and authenticated return; record third-party barriers separately and do not claim control over Google's screens. The provider disclosure and consent decision remain independently reachable after login. Refusal must preserve permitted chart/library access. Do not impose an additional memory puzzle or disable password-manager/paste interactions in app-owned authentication surfaces; review accessible authentication requirements during integration [S1].

## Sources, charts and partial updates

A desktop citation panel may be nonmodal: allow normal tab movement into the reading. If implemented as a modal drawer, give it a name, move focus inside, make background interaction inert, contain Tab/Shift+Tab, provide a visible close button and support Escape. For long content, initially focus its heading rather than making a screen reader announce the whole excerpt as one description. Restore focus to the invoking citation, or a documented logical successor if it no longer exists [S2]. Mobile full-page evidence instead has a meaningful title and back link preserving the selected claim.

The chart's short accessible description identifies chart type and points to its equivalent table. The table includes planet, position, house where supported, units and unavailable/alternative values; captions identify snapshot and method. Users must obtain every meaningful fact without interpreting geometry. A decorative duplicate graphic may be hidden only when its equivalent information is complete. Avoid turning every SVG line into a focus stop. Complex-image guidance supports pairing a concise description with detailed structured information [S8].

For HTMX, preserve stable input identifiers, labels, error associations and the active editing control across appropriate swaps. The library documents focus preservation for identified inputs, but this does not establish correct focus for every replaced element [S9]. Navigation updates title and heading focus deliberately; polling never does. If an explicit user action removes its focused control, choose a logical destination. Keep ordinary forms and source-page links functional when enhancement fails.

Generation can occupy the configured 150-second total deadline; provider timeout is at most 120 seconds and bounded by remaining time. Display only actual persisted phases, such as Finding passages or Checking references. Do not invent percentages or optimistic completion countdowns. Use a stable polite region for meaningful phase changes and one terminal announcement; repeated identical polls, token updates and decorative elapsed-time changes remain silent. Completion offers “Read answer” without stealing focus. Timeout, cancellation and uncertain failure remain distinct, retain the question and offer explicit retry. Status-message guidance requires relevant changes to be available without receiving focus and cautions against unnecessary interruption [S5].

Withdrawal replaces an excerpt with a clear unavailable-source message when the authoritative update is received. If the reader is in that panel, retain a usable heading/close control and announce the change once; never replace the entire page with a live region. Rights enforcement remains server-side, including print/export reads.

## Responsive, text and visual checks

Validate 320, 375, 640, 1024 and 1440 CSS-pixel layouts, portrait/landscape and desktop resizing. At 320 CSS pixels, prose and primary controls reflow without two-dimensional scrolling. The WCAG exception for genuinely two-dimensional material is narrow: a chart/table container may scroll when necessary, but its headings, controls and surrounding explanation must reflow [S6]. Test 200% text enlargement separately and 400% browser zoom from a 1280-pixel viewport. Sticky composers, banners and drawers must not cover focused controls.

Use the existing 44×44 CSS-pixel control design target. WCAG 2.2 AA's target-size criterion is 24×24 with defined exceptions, not an unconditional 44-pixel requirement [S7]. Measure text contrast at 4.5:1 for ordinary text and 3:1 for qualifying large text; meaningful control boundaries/states need 3:1 against adjacent colors. Check light, dark, forced-colors and focus states rather than approving palette tokens in isolation [S1].

Test long permitted Sanskrit passages, diacritics, mixed Latin/Devanagari, missing-font fallback and late font loading. Declare excerpt language, preserve selectable Unicode text, avoid splitting grapheme clusters or clipping combining marks, and verify line-height with real source fixtures. Use local fonts already proposed in document 09. Do not infer correct Sanskrit pronunciation merely from a language attribute.

Reduced-motion mode removes nonessential drawer movement, animated scrolling and decorative progress motion; keep equivalent static status text. This product preference exceeds the AA baseline for interaction animation, which is addressed at AAA [S11]. Print and accessible HTML exports retain evidence labels, references, uncertainty and withdrawal notices, with unclipped tables. PDF accessibility requires separate verification if PDF is introduced. RTL support is future work, not an MVP claim; prefer logical layout properties now and schedule mixed-direction testing when an RTL interface is enabled.

## Acceptance cases and execution protocol

Each numbered case is pending and must record pass/fail plus evidence:

1. Complete sign-in return and cancellation with keyboard only.
2. Decline provider consent and reach permitted chart/library screens.
3. Enter a date without a pointing device; verify normalized confirmation.
4. Select Unknown time and submit without a hidden mandatory time.
5. Correct a reversed approximate interval through linked field errors.
6. Resolve a repeated local time using clearly named offset choices.
7. Recover from a place-search failure through manual entry.
8. Open a disclosure using Enter and Space; verify announced state.
9. Open/close a modal source drawer; verify containment and restored focus.
10. Navigate a nonmodal panel without a keyboard trap.
11. Read all chart facts and uncertainty through its table alone.
12. Poll an unchanged generation state repeatedly without repeated speech.
13. Reach completion, timeout and cancellation with one terminal announcement each.
14. Edit the question during permitted background updates without focus loss.
15. Receive a withdrawal update without exposing a stale excerpt or losing navigation.
16. Operate every primary action at 320 CSS pixels and 400% desktop zoom.
17. Enlarge text 200%; inspect Sanskrit combining marks and long edition titles.
18. Measure contrast, visible focus and targets in both themes and forced colors.
19. Enable reduced motion; retain understandable progress and navigation.
20. Print/export a limited reading with labels, references and uncertainty intact.

Run axe-core against each reachable state, including open drawers and validation errors; inspect incomplete/manual-review results [S10]. Execute the cases manually with keyboard-only navigation, NVDA with Firefox or Chrome on Windows, and VoiceOver with Safari on macOS/iOS; record exact combinations at execution. Review speech order, labels, focus restoration, touch exploration and announcement repetition. Include a no-JavaScript journey and a simulated slow/disconnected response. Failures become reproducible issues tied to components and criteria. No automated scan replaces these tasks.

## Inspected primary references

All retrieved 2026-11-15; URLs are recorded as source identifiers, not implementation verification.

- S1: `https://www.w3.org/TR/WCAG22/`
- S2: `https://www.w3.org/WAI/ARIA/apg/patterns/dialog-modal/`
- S3: `https://www.w3.org/WAI/ARIA/apg/patterns/disclosure/`
- S4: `https://www.w3.org/WAI/tutorials/forms/notifications/`
- S5: `https://www.w3.org/WAI/WCAG22/Understanding/status-messages.html`
- S6: `https://www.w3.org/WAI/WCAG22/Understanding/reflow.html`
- S7: `https://www.w3.org/WAI/WCAG22/Understanding/target-size-minimum.html`
- S8: `https://www.w3.org/WAI/tutorials/images/complex/`
- S9: `https://htmx.org/attributes/hx-swap/` and `https://htmx.org/docs/`
- S10: `https://github.com/dequelabs/axe-core`
- S11: `https://www.w3.org/WAI/WCAG22/Understanding/animation-from-interactions.html`
