# Android / LAN candidate — 2026-10-13

Owner requested native Android LAN control using installed Android Studio. This
companion scope does not accept the complete PySH product or external streaming.

## Checks

Android Studio2026.1.1/JBR21 project sync PASS. APK and opt-in instrumentation APK
compile PASS; 3 LAN policy test methods PASS; lint zero errors. Advisory warnings
cover installed version upgrades, style and deliberate custom certificate pin
validation. Final APK SHA256:
`6e0f55bd9031c3525e010d8e11f90df8f53eeece843f0a5f265500e1221faec5`.
Installable copy: `2026-10-13/PySH-Remote/PySH-Remote-0.1.0.apk` in the PC workspace.
Final app/instrumentation build, policy tests and lint passed after correcting
the clock/header widths and initial audio slider value. Android signature uses
the PC's development certificate; production-store signing is not claimed.

Full backend regression **401 PASS / 32 Windows platform skips** includes
39 gateway cases: temporary real TLS, pairing expiry/persistence/revocation,
method/body/transport limits, hidden session, pending Bluetooth-like request and
concurrent reply. TypeScript/Vite build,74 extension tests, repository check PASS.
No current hub frontend/backend UI was replaced on Pi.

## Actual LAN sidecar

`scripts/install-remote-sidecar.py` installed four verified source/unit files in
`/opt/pysh-remote/releases/afcc33f88ac8`; independent `pysh-remote.service` active.
Archive SHA256 `afcc33f88ac8672b8938b5c6a4449782cfe7f042f37f93d9372d0bf8b4470352`.
Existing runtime `/opt/pysh/releases/5c76b8aff50d` and `pysh.service` retained.
Read-only inventory: Debian13.7 ARM64, about12GiB free. Installation-specific SD
SSH trust record used; older generic records retained. No storage, networking,
browser-profile or audio-stack changes.

PC→actual Pi HTTPS probe verified the certificate against the fingerprint from
trusted SSH. Observed: health200, unauthenticated state401, one-use pairing200,
state200, theme change/readback/restoration, same-volume audio command200,
media/diagnostics200, loopback session404, self-revocation200 followed by401.
Audit identity revoked and original theme restored. Raw script/results private
under `.runtime`; tokens, keys, codes and certificates excluded from Git/APK.

## Visual/device gates

Native Studio Compose rendering exposed heading/header/clock intrinsic-width
defects; explicit widths applied. Interactive preview reached form/footer and
translated app-owned text to English. Debug previews contain sample data; they
cannot prove actual Android LAN or hardware operation.

Official Android36/API29 x86_64 project AVDs were prepared because none existed.
Multiple software-rendering runs remained ADB offline before kernel boot; no
active hypervisor driver on this PC. No Windows security/virtualization/boot
changes. Emulator testing is OPEN; Studio sync/preview are separate evidence.
Owner offered a physical USB Android phone; discovery/install/LAN tour remains
pending until recorded below.

Physical APK launch, pairing/persistence, Wi-Fi HTTPS, command feedback, EN/RO
light/dark layouts, keyboard/rotation/font scaling and real media/Bluetooth
recovery remain OPEN. Router forwarding/DMZ was not inspected; port8766 must stay
local. Updating Android target37 will require Android17 LAN runtime permission
and a new acceptance run. Third-party sign-in/site controls stay on PySH.
