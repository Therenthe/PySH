# PySH status

Updated: 2026-10-03 (Europe/Bucharest). GitHub is canonical: https://github.com/Therenthe/PySH.

## Historical weather candidate

Previous application `4b56d5150640`, source `75bda82e0d58bb0786664e9c3281c7baf5d1a947`, was tested on the USB-booted corrected image (image source d61ec8d, original runtime a32c29065d6d). All33 runtime hashes and real update→rollback→update verified with unchanged preferences. Native five-day weather overflow is repaired: eight actual Home captures and48-screen survey pass the measured layout checks. API/kiosk recovery1.905/1.182s; complete idle PSS586.819MiB at native Home+120s; usable local WAV/radio/720p video resource probes passed. Five physical cold boots and offline tactile use were verified on the earlier image runtime a32; they are historical evidence, not five cold boots of4b. [Weather evidence](docs/evidence/home-weather-layout-2026-10-03.md).

## Current installed candidate

Installed application6012a2bda401/sourceb1ac75d8195c129c1e948ca54f5ed1b65f6782e9 adds an external browser keyboard and immersive controls.35 installed hashes, exact preferences and rollback targetcfb129d12e91 verified. Native isolated fixture proves real keyboard visible at800×240, automatic hide and restored800×480, no window frame or visible scrollbars, four-second control retraction/top-right48px reveal and Return/owned-child cleanup.22 extension regressions, Python86 (six Linux-only skips), unchanged frontend76 browser regressions and build checks pass.

Official Chromium component updater downloaded Widevine4.10.3057.0. Native isolated EME access and key creation pass for H.264/AAC and VP9/Opus after browser restart. The user's retained service profile has the same component and Netflix was reopened without changing account data; owner-confirmed film playback/resolution is pending. Debug fixture/tunnel closed. [Keyboard/DRM evidence](docs/evidence/service-keyboard-2026-10-03.md). Fresh-image component download/relaunch UX, full touch inventory, current-candidate recovery/resources, eight-hour stability and the remaining product criteria are still OPEN. Original SD and previous releases are retained.

## Previous desktop candidate

Main `4d28e523e87bb71b83614c53903d629f0e48757b` includes radio replay and media handoff/search/pairing-prompt repairs (PRs #10/#11). Original-desktop preview `df9d3777bdec` is deployed with all 33 runtime hashes verified; previous release and private backup retained. TypeScript/Vite/repository/package checks pass; 72 browser regressions pass with zero skips/failures/flaky tests; Windows Python 53 passed, five Linux-only skips. GitHub frontend/Python 3.12/3.13 run37064480391 passed.

Actual Pi revalidation passed eight media handoffs, four city-empty states, 48-screen EN/RO/theme survey, selected audio/video encodings and media error recovery with no JavaScript errors. API/kiosk recovery took 2.425s/0.979s with unchanged preferences and zero owned zombies; saved audio restored in 3.235s. REL-02 passes for this preview. See [UI evidence](docs/evidence/ui-handoff-2026-10-03.md). Original SD/desktop unchanged; no appliance autostart enabled there.

## Historical experimental PySH OS (superseded)

Draft PR #3 integrates main above. Image source `59fcd319fadf133295cabd0443b13c5060430c12`, successful run37066609253, Linux runtime `1e2918ca798f`. Complete image verified on PC: raw SHA256 `4c99dc0b6f9b812fec4d291b3e34347642289211dc65b8b77fa00fead870e6c4`, 4,571,791,360 bytes. Includes UUID addressing, dedicated labwc/greetd session, key-only administrative recovery and guarded first-boot root expansion. Sixteen disposable Linux growth checks passed, including actually mounted online growth. [Image evidence](docs/evidence/os-image-2026-10-03.md), [growth evidence](docs/evidence/root-expansion-2026-10-03.md).

Windows wrapper passed inspection-only for the intended USB inventory. Explicit USB erase approval received; candidate written with full Imager read-back and independent MBR/root/428 boot-file checks. Public recovery key provisioned; original SD preserved. Physical USB boot occurred; findings are recorded below. This is an experimental image, not physical product acceptance.

## Remaining delivery work

Netflix account playback/resolution and first-use DRM preparation; eight-hour stability; complete Bluetooth pair/forget/reconnect and real network-disconnection recovery; native resource/performance acceptance; external-account playback and DRM support; clean installation/rollback. Known paired-speaker appearance and a previously heard WAV are evidence of those observations only. Full product acceptance remains OPEN and the project is not complete.

## Historical first physical USB boot

Recovery SSH login and real mounted USB root growth passed (255,810,580,480 filesystem bytes). Initial GUI startup exposed tty1 getty/greetd conflict; live repair now runs Labwc/API/Chromium at800Ãƒâ€”480. Output rotation180 physically confirmed. Native Chromium tracing identified doubled touch rotation; identity calibration with DSI rotation180 restored native touch. Trusted button events and user-confirmed Continue Ã¢â€ â€™ Connectivity passed. Full touch-navigation acceptance remains OPEN. Temporary browser debugging removed; four source assets installed with matching hashes. Normal OS reboot passed with automatic UI/API/SSH startup, persisted DSI rotation and zero failed units. See [first-boot evidence](docs/evidence/os-first-boot-2026-10-03.md). Base runtime1e2918ca798f plus documented live session patches; product acceptance remains OPEN.

## Native OS UI survey

Actual existing-kiosk EN/RO and E-Ink/night survey passed48 screens, zero measured target/font/text-contrast defects or JavaScript errors;120 navigation samples p95=65.9ms. Initial setup completed, choices deferred, preferences restored. Network display exposed active loopback selection; corrected primary-route selection has seven regressions and read-only live D-Bus verification. Runtime115cb4173f52/sourcea6f61ec is deployed with all33 hashes verified; original runtime and verified readable PC backup retained. See [native OS UI evidence](docs/evidence/os-native-ui-2026-10-03.md).

## OS network/audio integration

Network primary-route correction is deployed; real Wi-Fi scan found three networks without disrupting Ethernet. Bluetooth connect exposed missing PipeWire Bluetooth plugin; installed isolated plugin1.4.2-1+rpt3 and five codec dependencies after simulation, zero upgrades/removals. Known speaker now connected with selected Bluetooth output and actual WAV playback; human audible confirmation is pending. Image package/inspection repair is prepared. Acceptance target115cb4173f52; dedicated-OS REL-02 revalidated after reopening. See [network/audio evidence](docs/evidence/os-network-audio-2026-10-03.md).

## Dedicated OS performance/recovery

Five installed app relaunches reached native Home in4.04–4.23s. Complete15-process idle PSS563.487MiB at Home+120.0001s, below700MiB, zero zombies. Owned API/kiosk crash recovery2.396s/1.179s with exact preferences unchanged and administrative exit-code causes logged. REL-02 passes for115cb4173f52. These are app launches, not cold boots; full graphical-start and media-load/stability acceptance remain OPEN. See [OS performance/recovery evidence](docs/evidence/os-performance-recovery-2026-10-03.md).

## Historical OS media and successor image

Runtime115cb4173f52 passed a repeated48-screen native survey (120 navigation samples, p95=67.8ms), eight local audio formats, five video containers with the tested encodings, video controls/error recovery, and service cancel/entry/return in EN/RO × both themes. Temporary kiosk debugging removed after these probes; original preferences restored. New-OS speaker audibility remains pending.

Successor image d61ec8d/runtimea32c29065d6d built successfully (run37104486072), downloaded and fully verified on PC: 4,571,791,360 bytes, raw SHA256 `d34aef22890cc0b1f767b39cc46d60ca1f811e18c1c89d7f38dc75a1ef16dcbd`. Includes startup/touch, network-route and Bluetooth-plugin fixes. This fresh image is not installed or physically accepted; recovery provisioning remains required. Live inventory sees only the mounted USB, no SD. See [media/service/image evidence](docs/evidence/os-media-service-image-2026-10-03.md).

## Corrected USB installation history (physical boot now verified)

Owner moved the original SD back to Raspberry and USB to PC. Exact SanDisk identity reconfirmed; 2,596 files from old USB user/runtime/config paths backed up to PC with all member hashes/readability verified. Corrected d61ec8d image written to USB, full Imager read-back passed, public recovery key provisioned. Independent MBR/root/428 boot-file/key checks passed. Windows eject requested and boot-volume path unavailable. Awaiting physical move/boot of the corrected USB; original SD remains the recovery medium. Candidate acceptance remains scoped to the previous runtime until fresh boot is verified. See [corrected USB flash evidence](docs/evidence/os-corrected-usb-flash-2026-10-03.md).
