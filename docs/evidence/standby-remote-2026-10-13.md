# Standby, screen controls and Android refinement — 2026-10-13

## Candidate under verification

Owner requests: remove routine Android success notices and the REMOTE subtitle;
show actual radio logos; put active Android presence immediately before the
network dot; software ON/OFF on both interfaces; display brightness; countdown
and daily automatic standby; refine both interfaces and reopen Android Studio.

RO/EN and ink/night touchscreen power flows: **12 browser cases PASS** on an
800×480 fixture. Cases cover indicator order/expiry, full-sized power target,
touch wake with no second action, brightness write/readback, countdown start and
cancel, daily toggle and in-app keyboard HH:mm input, unavailable brightness,
rejected writes and failed post-write reads without an automatic repeated command.
Screenshots are local `.runtime/power-ui` fixture evidence, not physical acceptance.

Read-only Pi inventory: Raspberry Pi4 Rev1.5, Debian13.7 ARM64, ~12GiB free,
prior hub runtime5c76b8aff50d and sidecarafcc33f88ac8 both active. DSI backlight
`10-0045`, maximum255 and current255. logind SetBrightness255 as userpysh on
active Wayland seat session succeeded, preserving the existing level. No new
privileges, policy, networking, boot, storage or browser profile changes.

Android Studio failed before initialization because its stale `.port` UNIX
socket reparse point could not be accessed by Windows. Only failed launch
processes were stopped. The entire Local cache directory was retained as
`AndroidStudio2026.1.1.recovery-20261013`; Roaming settings/plugins were preserved.
Studio reopened the existing project and recognized the authorized Samsung.
Existing cache/build logs and Compose classloader warnings are separate from
the installed app; final updated-source build and device checks are recorded below.

Deployment, final candidate hashes and physical checks are pending in this draft.

## Final source checks

Runtime candidate33c3cb8361ac,57 allowlisted files.445 Python cases PASS /32
Windows hardware skips;74 extension cases PASS; TypeScript/Vite and repository
checks PASS. Android0.1.2/code3 APK SHA256
`63ec90bcca2fd9ccb49f24f33c11e5e4119f78463b13a837f59fa679db9cd982`,
10 policy / artwork methods and lint PASS.22 affected browser cases PASS.
Complete browser run:974 PASS /8 initial failures in15.4minutes. Six failures
were stale header/exit selectors after adding power controls; these were changed
to identify the intended buttons.22 affected Home/power cases and8 service/tour
cases then passed. The two unrelated external-service/documentation timing cases
passed in an isolated4-case rerun. All982 browser cases are thus covered by the
complete run plus affected reruns; a single green982-case rerun is not claimed.
Actual RADIO BOB homepage fallback returned a103136-byte PNG on PC; the current
favorite's empty favicon remains unchanged. Real-phone logo proof is pending.
