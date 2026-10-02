# PySH status

Updated: 2026-10-02. GitHub is the canonical source: https://github.com/Therenthe/PySH.

## Current candidate and acceptance

The isolated Pi preview is `41a17d9b69e8`, from merged main `dc24dc25de5f61c701bcd45561752e4d87ece355`. It runs on the original desktop/card; no storage has been flashed and appliance autostart has not been activated on that installation. Product acceptance is incomplete: REL-02 passes on the isolated preview; 29 criteria remain OPEN. All required criteria must still be validated on the dedicated OS release candidate. Earlier failures and partial repaired observations are preserved in the evidence. Historical observations are retained in docs/evidence/ and docs/history/; they do not accept a later candidate automatically.

User confirmed physical setup/Bluetooth touch and audible local WAV output through ML-DAC-SPKBT-QC15. Real Pi audits captured 48 screens across EN/RO/themes and 120 navigation samples. Font/night text defects were repaired and rechecked on an earlier preview. Eight selected audio encodings and five selected video encodings decoded on Pi; this does not guarantee arbitrary container/codec combinations.

Previous preview recovered from API/kiosk crashes in 1.909s/1.128s but left two detached crashpad zombies. The new preview recovered in 2.384s/1.007s, preserved preference bytes, had one live mpv and zero zombies in the complete owned tree. A follow-up reaps adopted exited children without stealing leader exit codes; merged main `a4a3e34bac5424a3281d332d83e13c718342dd13` includes it. GitHub run `37056786164` passed: 51 backend tests on Linux and the frontend/browser suite. That follow-up is now deployed and the real recovery probe passed. The subsequent candidate adds explicit exit-code logging and requires affected revalidation. See [video/process evidence](docs/evidence/video-process-recovery-2026-10-02.md).

Persistent 48px video controls passed real Pi play/pause/seek/volume/mute, five selected encodings and invalid-file recovery across EN/RO/themes with no JavaScript errors on c0b1e35b77a9. Browser regressions also passed. A complete later idle descendant-tree sample measured 545.45 MiB. The earlier 258.26 MiB sample omitted Chromium's main process and is invalid for acceptance. The later sample is not the required exact two-minute measurement or an eight-hour stability result.

## Experimental PySH OS

Source `2cde9da2bd0078c290fdb7b9c52c59c03274b54a` includes detached-child cleanup and passed ARM64 image build `37057546408`. The next image must incorporate audio controls/persistence and weather race repairs. Builder, UUID-addressed boot/root layout, dedicated labwc/greetd session, service mode and public-key-only recovery provisioning are implemented as an experimental candidate; physical boot, recovery and USB root expansion remain unverified. ADR-0006–0008 and os/image/ describe the implementation.

Earlier UUID image `a9fdf3d` had its metadata ZIP independently verified on PC; image inspection matched 33 runtime hashes and actual ext4/VFAT UUIDs against fstab/cmdline. This evidence does not replace downloading/checking the latest complete image or booting it. The original card and desktop remain intact; an application backup is independently verified on PC.

Windows flash preparation includes a reviewed wrapper defaulting to inspection, signed official Imager 2.0.11.1 and a private local recovery key. No target disk has been authorized for erasure. Exact target selection, complete artifact transfer/checksum, public-key provisioning and physical boot/recovery remain required before an experimental flash. No flash performed.

## Remaining work

1. Deploy the merged recovery follow-up as a checksum-verified candidate and repeat recovery/video-control checks on Pi.
2. Build/check the corresponding OS artifact, then test physical boot and recovery on an explicitly selected destination while preserving the original card.
3. Complete the EN/RO/theme hardware flow matrix, Bluetooth pairing/forget/reconnect, offline recovery, performance, five cold boots, eight-hour stability and clean installation/rollback.
4. Validate external services on the exact target with authorized accounts or an explicitly approved product alternative. Shortcuts are not proof of playback.

Automatic approval review initially blocked the browser audit due to usage capacity. Later transfer and browser actions received fresh approvals; the c0b1e35b77a9 real video audit completed. No bypass was used. The auxiliary browser was explicitly stopped afterwards.

## Audio and weather follow-up

Source audit found missing local audio transport controls, active radio pause reloading the stream, saved audio values not applied on restart, and a late old-city weather response overwriting a new city. Repairs add queue-aware touch transport, persistent output/volume/mute restoration on availability and a weather request/location guard. Synthetic regressions pass; updated device/media/persistence checks remain pending. See [audio/weather evidence](docs/evidence/audio-weather-controls-2026-10-02.md).

Real audio transport matrix passes on41a17d9b69e8 across EN/RO/themes, including seek/queue/EOF replay/48px targets; recovery1.903s/0.998s, no zombies, preference bytes unchanged. Device persistence, journal visibility and final OS acceptance remain pending. This branch integrates that merged main for the next image.

Audio device preference restoration passed after forced volume71%/unmute/alternate output and API restart; saved27%/mute/output returned in3.458s. Admin journal confirms exit=-9/restart messages. Latest OS image sourcee19b48c29ff2ea703b6f4365d5ebd9e0aa05acfe passed run37059900737; runtime1f4842e63876 is distinct from the desktop preview. Metadata verified on PC; complete image verification and exact write destination remain next. Versioned Windows writer defaults to inspection and requires explicit target identity.
