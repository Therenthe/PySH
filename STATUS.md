# PySH status

Updated: 2026-10-03 (Europe/Bucharest). GitHub is canonical: https://github.com/Therenthe/PySH. Work is on draft PR3, branch feat/pysh-os-image; main remains the earlier desktop delivery. The product is not complete; all30 required criteria remain OPEN in [acceptance.json](docs/acceptance.json).

## Installed application and device

- Current physical SD application53c750ceab68, source912040b136ebc18bbe8d63d040d5ff7ab8feef99, all41 installed hashes independently verified. Previous5c174880ca5b retained. Backup/activation verified; active radio resumed and progressing. [Wi-Fi evidence](docs/evidence/wifi-profile-recovery-2026-10-03.md).
- Metadata/navigation follow-up5db8b9b0bdb6:162 complete browser tests passed, build/typecheck passed; native activation pending.
- Ambient Canvas/Radio candidate53c750ceab68 contains41 runtime files.154 browser tests and260 backend tests passed; native activation and real output-monitor proof passed (60 distinct PCM samples). [Redesign evidence](docs/evidence/ambient-canvas-2026-10-03.md).
- Pi4/4GB, Debian13 ARM64, DSI800×480, rotation180 with identity touch calibration. Active SD root UUID4d41b42c-d61a-4052-8898-94191aaa18fc, expanded root15,685,627,904 bytes. Original SD has a complete verified PC backup; corrected USB is retained separately for recovery. [SD boot evidence](docs/evidence/sd-boot-2026-10-03.md).
- Dedicated greetd/labwc session, user pysh.service, /opt/pysh/current and /opt/pysh/venv. API is loopback8765. Administrative SSH uses the provisioned key; secrets, profiles and backups stay outside Git. Desktop deployment scripts do not operate this appliance.

## Current evidence

Full application CI37125060631/37125062942 passed on Python3.12/3.13 and frontend. Protected preparation on an empty native profile reached real EME/key readiness in69.781s with one browser restart; prepared profile3.271s; cancel completed. RO/E-Ink preparation fits800×480. Actual compositor live inspection found and then verified removal of Chromium's translation prompt. Retained owner profile reopened without CDP/account inspection: checking→ready2.573s, actual panel shows Netflix Home without error. Film playback/resolution remains OPEN. [Preparation/activation evidence](docs/evidence/protected-playback-preparation-2026-10-03.md).

Pre-activation backup is separately verified on PC: SHA256880dc725418a0161713caf4643b5e4b4b84e53bc4365b2d61a6f19400016fc02,40 readable regular members and35 previous-runtime hashes. Earlier keyboard,48-screen UI surveys, cold boots, audio and performance results are historical evidence and are not cumulative PASS for the current candidate.

## Earlier verified image (superseded)

Image source20f19b907359da5aede58b933888c0eb7a5f5be6/runtime4ce1a5fe6390 built in run37125060698. Downloaded parts, gzip and raw image verified independently on PC:4,571,791,360 bytes, SHA256dcc40256ff08ee195bc39616a3829d7773c1402bfb0409ee680f973f347790eb. Independent ext4 inspection checks39 runtime hashes and session/touch/native-host/immersive settings. Three font/license files differ from installed934 only by CRLF/LF. Recovery provisioning, writing and physical boot of this image remain OPEN. [Image evidence](docs/evidence/os-immersive-image-2026-10-03.md).

## Current delivery work

The934 observer is authoritatively inactive after candidate change:2291.115s/76 samples, zero observation errors, incomplete observation. It supplies no eight-hour acceptance for4a133. The final same-candidate observation remains OPEN.

Public appliance update/rollback is now natively exercised; all six application CI jobs37128431057/37128428420 passed. New notice asset is installed and independently verified inside successor imagec8ac9c709acb/source3ca7e4e. Its4,571,791,360-byte raw SHA256 is de085cdcae326cfafba7ef93c2bf4956efd33aaf650ccdbb4a5cd311f3db5979. This image has now been written/read back on the physical SD and provisioned with the recovery public key; first SD boot has been verified. [Latest image/procedure evidence](docs/evidence/appliance-update-and-sd-image-2026-10-03.md), [dependency inventory](docs/DEPENDENCIES.md).

Owner priority: complete flasher/SD installation first, then remaining functionality and major UI/UX improvement. Current owner assessment UI3.5/10, UX5/10 is unsatisfactory; visual/product acceptance remains OPEN. [Roadmap](docs/ROADMAP.md).

SSH console flasher is implemented: [procedure](docs/SSH_FLASHER.md). All18 focused tests passed; full local suite153 passed/22 Windows/Linux-platform skips, one existing deprecation warning. Native loop proof, full original SD backup, physical write/readback and recovery-key provisioning passed; first SD boot also passed the scoped installation checks.

Native Linux loop/provisioning proof passed, including exact raw readback, separate public-key proof and all owned mappings detached; [evidence](docs/evidence/ssh-flasher-linux-2026-10-03.md). Original SD backup is independently verified on PC; [backup evidence](docs/evidence/sd-backup-2026-10-03.md). Physical SD flash finished15:25:30Z, exit0, exact image hash before provisioning and separate public-key hash verified. Controlled shutdown was requested after rechecking USB root and both new SD UUIDs; SSH disconnected during shutdown and a subsequent connection timed out. Owner removed USB and started SD; first boot was independently verified; [physical flash evidence](docs/evidence/sd-flash-2026-10-03.md). Product acceptance remains OPEN. [First SD boot evidence](docs/evidence/sd-boot-2026-10-03.md).

New SD Bluetooth audio is now observed: owner confirmed the local tone and is listening to radio. Six read-only samples over40 seconds showed progressing radio playback and active Bluetooth output. Original image has no preloaded Bluetooth pairing or checked home preferences/profile. [Scoped audio/radio evidence](docs/evidence/sd-audio-radio-2026-10-03.md); complete media/Bluetooth acceptance remains OPEN.

## Remaining release gates

- Complete EN/RO physical touch, theme and error-state inventory on one current candidate; native preparation timeout/retry.
- Real Netflix movie/audio/resolution, YouTube route and the approved music-service decision/account proof. Owner has Netflix; Spotify Premium has not been supplied.
- Complete Bluetooth pair/connect/disconnect/forget/reconnect and radio/local audio routing/volume; real network failure/authentication/forget/recovery.
- Current-candidate recovery, five physical cold boots, graphical-start/per-action performance, complete idle PSS and eight-hour interactive stability.
- Public appliance update/rollback, clean successor-image installation, backup/restore, dependency/license deliverables and full requirement-by-requirement audit.

[Roadmap](docs/ROADMAP.md), [operations](docs/OPERATIONS.md), [Definition of Done](docs/DEFINITION_OF_DONE.md). The detailed prior ledger is preserved in [historical status](docs/evidence/status-history-through-2026-10-03.md); it is not a current-state checklist.

## UI polish in progress

Candidateadb2f3a42a42 is packaged and locally verified:114 browser,164 backend and26 extension tests passed;3 weather mapping tests, TypeScript, build and structure passed. Home duplication/source/weather icons, hidden bars with real touch scrolling and screensaver transport are implemented. Native activation passed with radio resumed and compositor Home inspected. The forecast/attribution correction ebd9af386290 is installed;16 affected browser checks passed, all40 native hashes passed, no pending update and advancing radio playback verified in4 samples; audio visualizers and full UI acceptance remain OPEN. [Evidence](docs/evidence/ui-polish-2026-10-03.md).

## Saved Wi-Fi profile recovery

Candidate5c174880ca5b fixes explicit saved-profile credential updates, recovery errors and touch profile selection/Forget confirmation.200 backend and122 browser tests passed;12 network tests rerun after a translation correction. Native preflight: NetworkManager1.52.1, LAN active, zero saved Wi-Fi profiles. Activation/validation pending; full physical Wi-Fi acceptance remains OPEN. [Evidence](docs/evidence/wifi-profile-recovery-2026-10-03.md).
