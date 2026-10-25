# Common command surface —25October2026

P1 is installed as runtime34f8210d72fe, code source
887fc97f70c289650b3763d4c5b19d7497ddc332. Previous runtime8778974040f4 is
retained. Scoped native verification passed; full product acceptance remains OPEN. This follows delivered N0 and P5; proposals
2/3/4/7 remain planned and proposal6 is excluded.

## Resulting behavior

The Hub and supported official service views share a top pull-down surface:
Home, Radio, Media, volume/mute, brightness and current audio output. The Hub
retains its own player, device settings and Standby entry. Official services
retain Keyboard and never pretend to control protected service playback.
Controls remain48px at800x480, EN/RO, Ink/Night, with reduced-motion support.
Existing radio, preferences, account profiles and network identity are preserved.

The extension uses a fixed owner-native bridge with bounded typed messages.
Only a reduced controls projection is returned. Authentication/documentation
pages cannot mutate device controls. No account contents or owner token are
exposed to service pages. Output identity is revalidated before mutation.

## Reproductions and corrections

- Ambiguous HTTP408/409/429/5xx after integration require readback before retry.
  Four native-bridge unit regressions failed before correction and pass after.
  Hub409-after-write failed in all four language/palette cases before the fix.
- Return retries share an operation. Only queued destination intent can change;
  dispatched/closing intent cannot redirect the Hub later. Full Return cancels
  its own legacy keyboard request promptly but lets a device write settle.
  Six original race cases failed, followed by another keyboard-cancel regression;
  the complete extension regression now passes94tests.
- Opening owned controls no longer hides the keyboard before its toggle can be
  used. Outside focus, submission and navigation still dismiss typing normally.
- A visual review found the Hub volume slider narrowed by inherited alignment;
  both columns now stretch equally. Mute has a crossed-speaker icon and accent.
  Power is visually separated from transport; Radio/dismissal icons are aligned.

Earlier failed runs are retained privately. Geometry checks now wait for the
finite opening animation before comparing settled bounds; timeout tests await
queued dispatch before firing an installed timer. These harness corrections are
not reported as product fixes. A keyboard scenario now explicitly exercises
Hide then Show after automatic focus-based opening, matching actual state.

## Verification so far

701Python tests PASS,32platform-specific skips;94extension tests PASS.
TypeScript, production build and repository structure checks PASS. Focused
browser regression:72scoped checks PASS (24command-panel,16volume-recovery,
32drawer). Another50navigation checks passed
in the preceding bounded regression. These are not a whole-app acceptance claim.
Raw traces, screenshots, device state and backups remain private.

Full product acceptance, physical-finger use, speaker audibility and protected
stream playback are not established by these scoped checks.

## Pinned delivery and native result

Frozen local74779eecc3172237b44c17df7ac915e34fb6792f/tree646a3e6f and public
code887fc97f/treeac568174 were compared across all804public source files.
The five documented private-document exclusions remain unchanged. Runtime214files,
all29preferences, separate PCbackup contents/checksum, unchanged Ethernet and
unchanged gateway were verified. ArchiveSHA256:
01181198355f7434e93a59813a3cd2ba2d9cd2ac044ba0701a9ffad7c8405da4.

The current English/night800x480 native run passed three acknowledged external
Return journeys (Radio, Media, Home). Actual worker1.4.0/background-commands-v4.js
and six loaded extension resources matched the pinned source in the existing
service profile. Owned closed-shadow controls retained48px targets. Hub and
external volume/brightness changed by one point and were restored; mute toggled
and was restored. Manual Keyboard Show/Hide retained prior focus and restored
fullscreen size. The selected radio stayed paused after Return, then resumed
through the actual Hub Play control. No account content, field values, cookies
or profile contents were inspected; external captures contain only PySH controls.

One earlier native attempt stopped while waiting for external volume UI to
settle, after genuine backend readback. Its generic failure record does not
establish the underlying cause. The harness now can follow the existing
read-only Check status recovery instead of replaying a write; the successful
repeat required zero such recoveries. The first cleanup also read the output
list too soon after restart; a bounded readiness wait and idempotent explicit
cleanup restored all state. Both attempts and the manual cleanup receipt are
retained privately. No claim is made that the intermittent first failure is a
proven resolved product defect or a completed stability test.

Final cleanup confirmed exact preferences/audio/original radio restoration,
closed debug ports and closed owned service windows. Three legitimate auto-hide
navigation preference writes were admitted by the browser guard and restored;
zero unexpected writes and zero owner page errors occurred. A fresh ordinary
Wayland frame is inspected after cleanup. Physical touch, audible output, all
language/theme hardware combinations and DRM playback remain separate criteria.
