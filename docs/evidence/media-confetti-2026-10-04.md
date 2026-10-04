# Media and ambient celebrations — 2026-10-04

Installed SD runtime `c1e2e6049fec`, application source `4de7386dac7a1f51c4eb955844e178af1b6d0503`, source tree `79678651c734cea21d2f5670de29d7c4efac2443`. GitHub branch `feat/pysh-os-image` is canonical. Previous runtime `536e1332a260` retained. Documentation-only successor commits do not alter this installed source. All 30 complete product criteria remain OPEN.

## Implemented behavior

Home heart confetti observes selected-timezone HH:00 or HH:HH boundaries only while Home is already ambient. Lifetime is capped at five seconds. Hidden/reduced-motion state, wake and leaving Home cancel it; returning mid-minute never catches up. Hearts fall with varied delay/drift and fade. The operating-system clock was never changed.

Media separates device files and official services. Search opens the existing touch keyboard on demand, matches case and diacritics, and preserves the applied filter on cancellation. Parent navigation appears only where meaningful; return to the merged library is available from approved roots. Three service cards fit above transport controls with radio active.

Deletion requires explicit filename confirmation and the original list fingerprint. Only eligible regular owned single-link files under approved roots are offered. Linux nofollow directory handles and atomic private quarantine prevent replacement/symlink races. Active/paused local playback is excluded and requests serialize against playback. Acknowledged writes followed by failed reads retry only the read; ambiguous responses require an authoritative complete listing before any new deletion. Changed identity requires reselection. Failed quarantine restoration preserves the captured file and offers recovery rather than repeated deletion. Serialized local selection remains possible behind a pending transport command.

## Source verification

- 970 complete browser cases passed in 14.5 minutes on the frozen corrected source. Includes 22 Home/confetti and 48 Media layout/deletion cases plus earlier requirements.
- 176 affected cases passed after the queued-selection correction. The earlier 122-case result belongs to the preceding checkpoint.
- 349 backend cases passed with 32 Windows platform skips. Twelve deletion cases ran on Raspberry Linux against substituted temporary roots: all passed, zero skips. Application dependencies and pre-existing user files were untouched.
- 92 extension/astronomy cases passed. TypeScript, production build, repository structure and runtime packaging passed. No current green CI is claimed.
- Early service clipping, toast interception and blocked queued selection were reproduced and corrected before the final complete regression.

## Activation and recovery evidence

Package archive SHA256 `2e2320e783ba40373ddb94005b2b1ecc2cd24ef8ee8920f3bd512e6a3be2abfa`. Pre-activation backup was fully read and independently verified on PC: SHA256 `137cf525f60fe8a3dc7dceaef102362a98e0a659832c258012676c932aa901ea`. Private backups/profiles/raw captures are excluded from Git.

All 51 installed runtime files matched the package hashes after activation and again after the native audit. Nine saved preference comparison keys matched the backup: homePositions, homeCards, visualizerStyle, visualizerSize, theme, language, location, navigationCollapsed and navigationAutoHide. Previous536e retained. This was an application update on the existing SD, not a new final OS image or a demonstrated restore.

## Native tour at 800×480

Actual Raspberry Chromium tour used injected user actions, not physical-finger acceptance. All four contexts EN/RO × Ink/Night passed source navigation, parent/root navigation, search apply/cancel/clear with keyboard closure, confirmation cancellation and exact owned-file deletion. Four temporary WAV files created exclusively for this audit were deleted through the UI/API; no pre-existing user media was deleted. The audit directory was removed only after verified empty.

Thirteen native screenshots were collected (Services, Files and Delete in four contexts, plus confetti). Key service/file/dialog/confetti captures were visually inspected; independent fixture service captures were also reviewed. Service controls were enabled and hit-testable, but external services were not launched: this does not establish streaming/DRM acceptance.

Native confetti appeared as visibly falling hearts, expired within the 5.5-second observation tolerance and first-touch wake restored compact cards. The implementation cap is exactly five seconds. This native probe simulated an hourly boundary only inside the Chromium renderer; normal Chromium was restarted afterward to erase the simulation. Browser cases separately cover matching digits, hourly boundaries and absence of catch-up. No real OS clock or wall-hour scheduling claim is made.

All fourteen preferences temporarily controlled by the audit were restored. Final normal-session verification confirmed the same radio URL still playing, audio ready, all nine backup comparison keys matching, no diagnostic listeners on 9222/9223 and no external window. The audit-owned SSH tunnel was closed. The final restored Home screenshot was inspected. The live viewer remains private through SSH/PC loopback; no public exposure was introduced.

## Remaining acceptance

These checks establish the scoped implementation, installation and native Media behavior. Physical touch, full preference restart/cold-boot persistence, actual external streaming/audio, complete Bluetooth/network recovery, performance/stability, clean final image and restore acceptance remain OPEN. See [acceptance inventory](../acceptance.json), [UI delivery plan](../UI_DELIVERY_PLAN.md) and [Definition of Done](../DEFINITION_OF_DONE.md).
