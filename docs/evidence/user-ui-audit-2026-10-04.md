# Independent usability audit — 4 October 2026

## Identity and limits

Audit target supplied by the operator: installed candidate `43bbb099a8b6`, source `22e7e46e72a5373111419f7ea90fb8bba45ddcd3`. The auditor did not operate, restart or inspect accounts on the Raspberry. Application files were not modified.

All browser executions used a fresh `git archive` of this exact source under ignored `.runtime/audit-usability-22e7`. Vite ran against that isolated snapshot on PC loopback ports 5197/5198; concurrent working-tree changes were not loaded. Chromium used an 800×480 touch-enabled viewport, EN/RO projects and E-Ink/night cases. API responses were explicit browser fixtures, not proof of actual network, Bluetooth, playback, preferences on disk or protected services.

## Executed evidence

- Existing complete browser suite: **232 passed in 3.1 minutes**. This includes screenshots, touch-target/layout/legibility surveys, setup/revisit, network profile recovery, transport, preparation failures, screensaver, personalization, free placement and reduced-motion cases.
- Additional independent audit: **12 completed probes in 23.9 seconds** across both languages and themes. Four exercise every option in the five appearance selectors, theme/accent buttons and keyboard controls; four reproduce the Bluetooth error-placement defect; four reproduce failed-location-save loss of search results. Passing a defect-reproduction probe confirms the defect, not usability acceptance.
- Additional lifecycle tour: **4 completed cases in 8.3 seconds**. Pair → connect → disconnect → forget, scan and power off/on; audio mute/unmute, touch volume and output; all three external-service buttons; diagnostics download trigger. Only fixture state transitions/request bodies are established.
- Early independent harness runs selected intentionally hidden `.keyboard-actions` controls. Corrected selectors use the visible final-row Apply and header Close. Those harness failures are not application defects.
- The diagnostics anchor emitted a download event, but the isolated Vite proxy could not reach a backend at 8765; resulting `diagnostics.txt` is not valid diagnostic-package evidence. Native response bytes/content and secret review remain OPEN.

Private traces/screenshots and extra tests remain in the ignored snapshot. The report contains no credentials, private network addresses or account captures. No quality score is assigned.

## Reproducible defects

| Priority | Trigger and observed result | Source recommendation |
|---|---|---|
| P1 | Open Bluetooth dialog → Disconnect → adapter returns 503. Dialog remains “Connected / Disconnect”; error and Retry appear behind the scrim, outside the active dialog. Reproduced EN/RO, both themes; screenshot visually inspected. | `app/ui/src/main.tsx:191`: add localized pending/error/retry feedback in the Bluetooth dialog, tied to the actual action. Apply the same review to power, scan, pair, connect and forget. |
| P2 | Settings → Weather → search → choose a result → preference save fails. All results disappear despite the location not being saved. Reproduced EN/RO, both themes. | `main.tsx:177` and setup location handler at 164: clear results only after `savePrefs` succeeds; preserve retry selection and show an explanation next to the failed location. |
| P2 | After a Bluetooth action fails, closing the dialog exposes “Try again”. Source inspection shows this calls `getState`, not the failed Bluetooth action. It is therefore a status refresh rather than action retry. | `main.tsx:121`: use operation-specific retries or label this action as updating status. Do not blindly repeat destructive operations. |

The owner-reported visualizer size/style and meteor appearance problems are under a separate implementation audit. Existing tests asserting wrapper heights or SVG element presence do not prove a meaningful visual difference or acceptable animation.

## Control inventory and coverage

This inventory groups repeated data-driven buttons by their command. It does not claim every possible station/file/network/device row or every hardware failure was exercised.

| Screen / command family | Commands and returns | Executed browser evidence; remaining gaps |
|---|---|---|
| Shell | Brand/Home, four navigation destinations, retract/reveal navigation, top/rail network status, quick settings, rail Bluetooth/audio | Navigation, retract/restore and all quick modal destinations executed. Native hit testing/gesture feel remain for operator. |
| Home | Expand/collapse weather, choose location, forecast expand/collapse, playback expansion, signal expansion, play/pause/stop, Radio/Media shortcuts | Existing personalized/transport tests execute these families and delayed collapse. Cross-row drag/save/cancel/reset and persistence through fixture reload covered. Screenshots do not certify actual persisted settings or every overlapping layout. |
| Home arrangement | Select card, drag handles, Done, Reset, Cancel; failed save remains editable | Existing free-placement/personalization tests. Every card choice is not independently enumerated by this additional audit. Native drag accuracy and offscreen/clipped arbitrary positions remain. |
| Radio | Search, country/language, keyboard apply/cancel, favorites filter, add/remove favorite, station play/pause/resume, catalog refresh/retry; previous/next station, pause/resume/stop, mute/volume | Existing radio/filter/signal/transport cases. Real catalog normalization and stream recovery remain adapter/native proofs; fixtures cannot prove Romania aliases or provider availability. |
| Local media | Library root, parent, directories, audio/video file, retry; audio previous/next/seek/play/pause/stop; video playback, seek/volume/mute/fullscreen/return | Existing local-player cases exercise queue flags, end/error, output loss, stop-before-video, broken video, retry and return. Real codecs, audio and filesystem permissions remain OPEN. |
| External services | YouTube, Netflix, Spotify; preparation cancel/retry; immersive return and keyboard hide | All three entry buttons executed with asserted request service IDs. Existing preparation/extension fixtures cover cancel/failure/return. Account login, DRM film playback/resolution and actual site controls are not covered. |
| Appearance | Rerun setup confirmation/cancel, language, both themes, navigation auto hide, three accents; Manual/Solar/Scheduled; start/end/timezone text entry | Existing setup/revisit tests plus every selector option/theme/accent executed. Additional audit does not exhaust each schedule/timezone invalid value or every language-switch combination. |
| Audio/saver customization | Off, Wave, Levels, Orbit, Ribbon, Mirror, Rings; Compact/Balanced/Large; saver Off/1/3/5/10/15/30; clock/playback or visualizer-only; preview | Every listed selector option executed and PATCH observed. Existing suites cover full-screen reveal/timeout/return, reduced motion and signal availability. Visual distinctness, desired proportions and real output signal remain separate acceptance. |
| Weather settings | City search/apply/cancel/result selection; Celsius readout, disabled Fahrenheit | Search, stale/late/empty results and failed-save reproduction. There is no manual weather-refresh button. Automatic timing/recovery requires backend/real network evidence. Celsius button is a readout with no command; unsupported Fahrenheit is disabled. |
| Network | Scan, open/secured network, password apply/cancel, saved-profile selection, password update, Forget confirm/cancel, dialog close | Existing network suite exercises explicit profile UUIDs, failures, repeated SSID selection and confirmation. Real Wi-Fi authentication/roaming/reconnection remain native. |
| Bluetooth | Power, scan, pair, connect, disconnect, forget, pairing reject/accept/code entry, close | Additional lifecycle fixture tour executes lifecycle/power/scan. Existing pairing tests cover confirmation rejection and wake. PIN/passkey variants, actual timeout/refusal, multi-prompt collisions and hardware lifecycle still need operator. |
| Audio settings/dialog | Output selection, touch volume, mute/unmute, dialog close | Additional lifecycle tour executes dialog controls; existing settings surveys inspect page. No physical speaker/output proof. |
| Home settings | Weather/forecast/playback visibility, Radio/Media shortcut toggles, arrange Home | Existing personalization cases and fixture reload. Additional audit does not prove filesystem persistence. |
| Diagnostics / exit | Download, exit/service confirmation/cancel, service return | Download trigger only; existing appliance-service fixture covers cancel/enter/return. Native package bytes, cleanup, service recovery and privacy remain OPEN. |
| Keyboard / dialogs | Digits, letters, diacritics, case, symbols, space, backspace, Apply, Close/Cancel; selector close, options, save failure | Visible key bank and special controls executed in additional appearance tour. Every symbol/caps combination and all long password/location strings are not exhaustive. Generic modal focus/backdrop/Escape behavior is not fully audited. |
| Recovery | Error dismiss, retry; backend unavailable; preparation error; file/catalog retry; selector save error | Existing failure cases plus new defects above. Not every adapter error code is injected. |

## Required native follow-up

The operator must verify the current release identity, then run the corresponding physical tour with a usable return path: actual preferences after restart, real touch selection and drag, all output routes/volume, Bluetooth lifecycle with refusal/disappearance, Wi-Fi credential failure/recovery, codec files, and authorized external playback. Inspect both languages/themes at 800×480, especially error dialogs and keyboard. Compare actual visualizer geometry between sizes/styles with identical signal input; confirm meteor direction/head/tail and irregular timing visually. A mock-success toast or 248 completed browser cases cannot establish these results or a 10/10 score.
