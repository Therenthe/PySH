# UX: task-based settings and recovery — 24 October 2026

## Problem and result

The user rated usability 5/10: related options were scattered across unrelated
menus. Appearance contained setup, language/timezone, theme, navigation,
visualization and rest settings. The Network-labelled Settings action opened a
generic status dialog. Speaker pairing and output selection had no task bridge.

The installed candidate is `dd9a018bf755`, production source
`38b07da667e94f7abf18b98f4e4a62e169de6af8`. Six task groups expose thirteen
scoped sections. The [canonical option map](../UX_REORGANIZATION_2026_10_24.md)
retains every existing operation and preference key; no data migration is needed.

Gear opens full Settings. A separate header action opens Quick controls in one
tap, with current playback and volume first. Back returns to the interrupted
Radio/Media page. Pairing and output selection link to each other; Rest links to
the shared visualizer. Radio offers an initially visible Choose speaker action
without audio and one-tap search/filter reset. Standby explicitly leaves the Pi
running. Fixed Celsius is a readout, not a fake Fahrenheit choice. Text entry has
a 48px Clear all action, with Cancel retaining the original value.

## Method and evidence

Three bounded reviewers used the installed PySH touch, Impeccable and Browser
UAT instructions. Reviewers A and B were independent. Tests use isolated,
deterministic, loopback Chromium contexts, 800×480, EN/RO × Ink/night. Screenshots
and six-field defect ledgers remain private; no accounts or raw operational data
are published. New UI does not imply real network/audio/DRM acceptance.

| Evidence | Observed result |
|---|---|
| Independent baselines | A: 76 captured states and complete source inventory. B: 156 captured states and task-path analysis. Appearance measured 836px in a 296px panel. |
| Reorganized complete browser tour | A R2: 188 checks / 120 captures; B R2: 40 checks / 192 captured states. Thirteen sections, save/reload, Back, contextual navigation and recovery observed. |
| Latest independent review | B R7: 52/52 checks, 40 captures on the canonical final build, including long retained output errors, full modal clipping and hit tests before scrolling. |
| Shared range interaction | A R4: 60 cases / 160 checks across Quick, Audio page/modal and brightness, fast/held/rejected responses and playback. Later Quick-specific deltas were retested separately. |
| Focused UX regression | 48 task/navigation cases passed on R4, including canonical uniqueness, language/theme, error ownership, polling, clear/filter recovery and return paths. |
| Broader affected regression | R3 executed 470 cases: 446 passed, 24 failed stale test destinations. All 24 have matching passing retests within an 84/84 R4 follow-up. This was not one clean 470-case final-build run. |
| Final Quick guards | R7: 16/16 cases passed, including fast/held/rejected volume and long retained output errors, exact mutation/retry and full 48px bounds inside the modal before auto-scroll. |
| Existing backend/extension checks | 650 Python passed, 32 platform skips; 82 extension contracts passed. No backend or extension production changes in this lot. |
| Build and packaging | TypeScript, Vite, repository structure and explicit 107-file runtime package passed. Source/tree verified against GitHub before activation. |

R3→R4 application differences are explicitly recorded: Quick geometry and feedback
placement changed after a real defect. The 24 locator failures were not hidden or
used as evidence of product defects; corrected tests retain their behavioral
assertions. Earlier runs invalidated by development reload and setup/locator
mistakes remain in the private ledger. Counts of screenshots are not independent
E2E tests. An empty mechanical detector result is not a conformance certificate.

## Iterations that found real defects

1. R1: Choose speaker was below the Radio viewport. Recovery moved before artwork
   and inactive visualization is omitted when there is no audio output.
2. R2: a fourth filter pill truncated Favorites. Reset moved to the list heading.
3. R3: committing volume inserted feedback between pointer-up and Chromium's
   compatibility click. The new target under the finger was Audio, opening the
   wrong dialog. Trusted event traces and a failing regression reproduced this.
   R4 anchors Quick at the top, keeps feedback after controls and uses compact
   destination buttons; no global click suppression was added.
4. R4–R6: recovery actions were below the fold, then clipped by 2px / 1px with
   long intent text. R7 uses compact, labelled 48px retry/dismiss icons aligned
   to the message top. The cause is first; exceptionally long text can scroll
   within its own bounded area. Controls remain visible without a swipe.

## Installation and native verification

The package was activated after an independently readable, checksum-verified PC
backup. All 107 runtime file hashes and all 29 saved preferences matched after
activation; previous runtime `e1a82fcc1327` is retained. Gateway and Ethernet were
unchanged. The previously playing selected radio resumed with audio readiness.

Native tour PASS on the installed candidate: 84 captures across four EN/RO ×
theme contexts, all thirteen settings sections, Home, Radio, Media, services,
keyboard, visualizer selection and protected service-mode cancellation. All six
categories fit without menu scrolling. Quick opens in one tap; a touch at the
existing volume preserves its value and keeps Quick open. Rest→Visualizer,
Bluetooth→Output, and Settings Back→Radio/Media pass. The actual catalog contains
40 stations in each captured Radio context; no live search correctness is inferred.

The responsible agent inspected four native contact sheets and full-size Settings
and Quick captures. The native tour uses injected browser touch, not a physical
finger. All original preferences and playback were restored, normal Chromium
restarted, and temporary diagnostic listeners and owned windows closed. It does not delete media or change the
network, browser accounts, OS, boot firmware or storage image.

## Limits

No numeric 10/10 score is certified. All thirty complete product criteria remain
OPEN: physical full-touch acceptance, audible output, Netflix/DRM, actual network
handover and sustained performance have separate evidence requirements. This lot
addresses task organization and observed recovery defects; it does not erase
earlier requested work or convert historical checks into new acceptance.
