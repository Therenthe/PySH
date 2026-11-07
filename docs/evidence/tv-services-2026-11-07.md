# Digi and Orange TV Go — scoped evidence, 7 November

## Charter

800×480, EN/RO and Ink/Night. Real Digi mark in TV; external Digi drawer
returns directly to Channels through a fixed, acknowledged owner command.
Orange TV Go opens the official browser service with protected-media preparation,
existing profile, device controls, keyboard and an acknowledged route back.
No account/cookie/credential reads, network/audio changes or public stream.

## Source checks

991Python passed,46platform skips,11subtests;194JavaScript passed.
TypeScript/build and repository structure passed. Detector returned no findings.
Vite retains the existing large-chunk warning.
Final176browser cases passed:24new and152regressions across EN/RO and both themes.
Independent8Services/Digi and8externaldrawer contexts passed after fixing
TVS-VIS-01: the fifth service was initially clipped. Allfive now fit, including
active radio/pending. Touch targets≥48px; text contrast≥6.04; 56privatevisual
captures plus UAT captures bind to source hashes. Logo720×414 renders64×48.
DigiChannels ack/error/retry, focus/Escape, accountcorner access and Orange
keyboard/preparation/exactURL gate are covered by owned fixtures.
Native installation and real account verification remain pending.
Candidate runtime `18f88045b294` has232files. Fullproductacceptance remainsOPEN.

## Official sources

- [Orange browser/login FAQ](https://www.orange.ro/aplicatii/orange-tv-go/faq.html).
- [Official Orange TV Go](https://tvgo.orange.ro/).
- [Official Digi Sport1](https://www.digisport.ro/live/digisport-1).
- Digi mark from the broadcaster's own [asset](https://www.digisport.ro/static/theme-repo/bin/images/logo-digisport.png), stored unchanged for identification.

A visible service entry is not a claim of subscription playback. Orange login
and playback require the user's own eligible account and remain unverified
until exercised on the target. Raw screenshots/logs remain private.

Runtime package is built from immutable Git-exported source, with canonical LF
line endings. The preliminary working-tree package was not published or installed.

## Native R1

Runtime `18f88045b294`, code `c3993dd00d3a9c00402e42fa568247046153bcaa`.
232runtimefile hashes and29preferences verified; prior6314da69ecce retained.
PC backup checksum and readable contents verified; gateway/network preserved.
Real screenshot shows the Digi mark. Topedge pull → Channels closes the Digi
window and displays TV Channels in the existing profile. This also exercises
the new worker1.4.3/return-tv path.

One native attempt exceeded the existing8s menu inactivity timeout and hit an
underlying Digi sociallink. The generated window was closed through its normal
close control; immediate pull→Channels retest passed. Classified as test
precondition timing, not a claim that the first attempt passed.

Orange homepage and PySH sheet loaded, but Signin navigated to the official
`https://www.orange.ro/accounts/login-user`, outside the initial exact-host
allowlist. R1 lacked keyboard/return there: TVS-AUTH-01, major, requires R2.
Independent fresh public browser reproduced this route, without credentials.
Subscription playback remains unverified; no accounts/profiles were read/reset.

## R2 authentication scope

The exact HTTPS host/path `www.orange.ro/accounts/login-user` permits only
keyboard/status/acknowledged return, with no hardware-control privileges.
The authentication sheet omits sliders and output controls; the existing
service profile remains intact. Worker1.4.4/background-tv-services-v8.js.
All197JavaScript tests and TypeScript/structure checks passed; backend remains
identical to the991Python passing source. Final66browser cases passed (4expanded auth+24services+38extension regressions).
Native R2 verification remains pending. No real credentials have been entered.

Independent auth review passed4full and4keyboard-sized contexts.
TVS-AUTH-VIS-02 found the auth sheet clipped its Keyboard action at800×240.
The auth-only bounded-scroll correction keeps the sheet within232px; a
realistic touch pan exposes the whole48px Keyboard action. Contrast≥6.16,
modal focus/Escape and account-button access passed. No visible scrollbar.

A zero-duration CDP swipe suppressed the following tap's click. Separate
controlled probes showed200ms single-move and280ms stepped gestures working;
final fixtures use a paced gesture. This is retained as a harness-timing
limitation, not counted as a successful zero-duration gesture. Two old tests
now exclude the intentionally hidden Channels button from target geometry;
the obsolete larger-Home-width assertion was removed without relaxing48px.

## Native R2 and focused-field correction

Runtime `917de2f7f36e`, code `ead54c134a94c835a7120e6b7a9c38783f227417`:233hashes
and29preferences/backupPC verified, previous18f88045b294 retained. DigiChannels
return passed again. Orange homepage/login now has the handle; focusing the
empty email input opens the actual native keyboard. Pull→Media while the
keyboard is open closes the owned browser and hides the keyboard. Worker1.4.4
and existing profile were exercised without any entered credentials.

TVS-AUTH-03, major: the real240px viewport left the focused email field at278px,
below the visible page. R3 adds auth-only active-field scrolling on focus/resize;
it observes field type/geometry only and does not read content.
Native R3 verification remains pending.

R3 source checks:199JavaScript passed; backend is unchanged from991Python
passing source, TypeScript/structure and targeted detector passed. Version1.4.5
retains unchanged v8 worker. Auth field visibility uses a guarded animation
frame after focus/resize, and ignores noneditable or replaced active elements.
Final70browser cases passed:4long-form field,4auth menu/short viewport,
24service and38extension regression cases.17source pins remained unchanged.
Owned fixtures observed zero PySH reads of auth values. Native R3 verification
remains pending.

## Native R3, final integration result

Runtime `96764525dbc5`, code `42ac4d908b9285e72d43155e0182f7a5bc940290`,
previous `917de2f7f36e` retained.233runtime hashes/29preferences verified on
activation;872source blobs matched GitHub. PC backup checksum and readable
contents verified. Network/gateway preserved,3services active, no diagnostic
ports opened and no temporary input devices left.

On this final candidate: Digi real mark and topedge→Channels passed. Orange
homepage, official login handle, native keyboard, focused blank email field,
wvkbd Tab→blank password field, and auth pull→Media with keyboard cleanup all
passed. Both fields and labels were fully visible above the actual240px
keyboard; independent native screenshot review passed. No credentials entered.
Version1.4.5 uses the unchanged v8 worker; the existing profile was preserved.

At the final attempted login reopening, unrelated page and brightness changes
appeared between planned taps. Automated pointer actions were stopped and the
user was asked about concurrent device use; the newer preference was not
overwritten. This does not invalidate earlier observed login/control outcomes,
but the final page is not claimed to be the login form. Raw state stays private.

Scoped integration controls PASS. Actual Orange account login, subscription
entitlement, video/audio playback remain OPEN pending the user's own account.
Browser fixtures, synthetic/native input and screenshots do not certify
physical touch feel or full product acceptance; all30globalcriteria remainOPEN.
