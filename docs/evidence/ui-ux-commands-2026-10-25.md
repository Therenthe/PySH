# Common command surface —25October2026

P1 is a local candidate. Installed runtime remains8778974040f4; native
verification and delivery are OPEN. This follows delivered N0 and P5; proposals
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
32drawer); native verification remains OPEN. Another50navigation checks passed
in the preceding bounded regression. These are not a whole-app acceptance claim.
Raw traces, screenshots, device state and backups remain private.

Full product acceptance, physical-finger use, speaker audibility and protected
stream playback are not established by these scoped checks.
