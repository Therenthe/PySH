# PySH status

Updated: 2026-10-02. GitHub is the canonical source: https://github.com/Therenthe/PySH.

## Current candidate and acceptance

The isolated Pi preview is `9648250fa63f`, from main `9c2b66fe9ca93b1bbe543c35c4d0bca488b4f588`. It runs on the original desktop/card; no storage has been flashed and appliance autostart has not been activated on that installation. Product acceptance is incomplete: REL-02 FAIL, the other 29 criteria OPEN. Historical observations are retained in docs/evidence/ and docs/history/; they do not accept a later candidate automatically.

User confirmed physical setup/Bluetooth touch and audible local WAV output through ML-DAC-SPKBT-QC15. Real Pi audits captured 48 screens across EN/RO/themes and 120 navigation samples. Font/night text defects were repaired and rechecked on an earlier preview. Eight selected audio encodings and five selected video encodings decoded on Pi; this does not guarantee arbitrary container/codec combinations.

Current preview recovered from API/kiosk crashes in 1.909s/1.128s, preserved preferences and left one live mpv. Two exited detached crashpad children remained zombies. A follow-up reaps adopted exited children without stealing leader exit codes; merged main `a4a3e34bac5424a3281d332d83e13c718342dd13` includes it. GitHub run `37056786164` passed: 51 backend tests on Linux and the frontend/browser suite. Deployment and real recovery revalidation of that follow-up remain pending. See [video/process evidence](docs/evidence/video-process-recovery-2026-10-02.md).

Persistent 48px video controls pass 40 browser regressions; actual Pi play/pause/seek/volume/mute revalidation is pending. A complete later idle descendant-tree sample measured 545.45 MiB. The earlier 258.26 MiB sample omitted Chromium's main process and is invalid for acceptance. The later sample is not the required exact two-minute measurement or an eight-hour stability result.

## Experimental PySH OS

Source `47a943c4b73b88de92f2f9e26a0430a5f6ac3f9c` passed ARM64 image build `37053903436` and application CI. This branch now integrates main's detached-child cleanup for a new image. Builder, UUID-addressed boot/root layout, dedicated labwc/greetd session, service mode and public-key-only recovery provisioning are implemented as an experimental candidate; physical boot, recovery and USB root expansion remain unverified. ADR-0006–0008 and os/image/ describe the implementation.

Earlier UUID image `a9fdf3d` had its metadata ZIP independently verified on PC; image inspection matched 33 runtime hashes and actual ext4/VFAT UUIDs against fstab/cmdline. This evidence does not replace downloading/checking the latest complete image or booting it. The original card and desktop remain intact; an application backup is independently verified on PC.

Windows flash preparation includes a reviewed wrapper defaulting to inspection, signed official Imager 2.0.11.1 and a private local recovery key. No target disk has been authorized for erasure. Exact target selection, complete artifact transfer/checksum, public-key provisioning and physical boot/recovery remain required before an experimental flash. No flash performed.

## Remaining work

1. Deploy the merged recovery follow-up as a checksum-verified candidate and repeat recovery/video-control checks on Pi.
2. Build/check the corresponding OS artifact, then test physical boot and recovery on an explicitly selected destination while preserving the original card.
3. Complete the EN/RO/theme hardware flow matrix, Bluetooth pairing/forget/reconnect, offline recovery, performance, five cold boots, eight-hour stability and clean installation/rollback.
4. Validate external services on the exact target with authorized accounts or an explicitly approved product alternative. Shortcuts are not proof of playback.

Automatic approval review blocked the privileged local browser audit because the Codex usage limit was reached; the audit did not run. This was an approval-review failure, not a safety decision. Unaffected source/CI work continues; resume that audit when review capacity is available. The delivery goal remains active.
