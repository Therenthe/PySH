# PySH status

Updated: 2026-10-03 (Europe/Bucharest). GitHub is canonical: https://github.com/Therenthe/PySH. Work is on draft PR3, branch feat/pysh-os-image; main remains the earlier desktop delivery. The product is not complete; all30 required criteria remain OPEN in [acceptance.json](docs/acceptance.json).

## Installed application and device

- Application4a133daa7278, source dda57f080de2f9d03eae01947594a159fae887f6; all40 installed file hashes verified. Previous934d0d338e66 retained. Public update→rollback→return succeeded, each with separately verified PC backup; no pending transaction. Preferences, display/touch configuration and native host unchanged. [Native procedure evidence](docs/evidence/appliance-update-and-sd-image-2026-10-03.md).
- Corrected physical USB image source d61ec8d, original runtimea32c29065d6d. Pi4/4GB, Debian13 ARM64, DSI800×480, rotation180 with identity touch calibration. Root UUID5610e056-221b-46c9-8046-65c9adb6a5c1. Original SD is kept offline for recovery.
- Dedicated greetd/labwc session, user pysh.service, /opt/pysh/current and /opt/pysh/venv. API is loopback8765. Administrative SSH uses the provisioned key; secrets, profiles and backups stay outside Git. Desktop deployment scripts do not operate this appliance.

## Current evidence

Full application CI37125060631/37125062942 passed on Python3.12/3.13 and frontend. Protected preparation on an empty native profile reached real EME/key readiness in69.781s with one browser restart; prepared profile3.271s; cancel completed. RO/E-Ink preparation fits800×480. Actual compositor live inspection found and then verified removal of Chromium's translation prompt. Retained owner profile reopened without CDP/account inspection: checking→ready2.573s, actual panel shows Netflix Home without error. Film playback/resolution remains OPEN. [Preparation/activation evidence](docs/evidence/protected-playback-preparation-2026-10-03.md).

Pre-activation backup is separately verified on PC: SHA256880dc725418a0161713caf4643b5e4b4b84e53bc4365b2d61a6f19400016fc02,40 readable regular members and35 previous-runtime hashes. Earlier keyboard,48-screen UI surveys, cold boots, audio and performance results are historical evidence and are not cumulative PASS for the current candidate.

## Earlier verified image (superseded)

Image source20f19b907359da5aede58b933888c0eb7a5f5be6/runtime4ce1a5fe6390 built in run37125060698. Downloaded parts, gzip and raw image verified independently on PC:4,571,791,360 bytes, SHA256dcc40256ff08ee195bc39616a3829d7773c1402bfb0409ee680f973f347790eb. Independent ext4 inspection checks39 runtime hashes and session/touch/native-host/immersive settings. Three font/license files differ from installed934 only by CRLF/LF. Recovery provisioning, writing and physical boot of this image remain OPEN. [Image evidence](docs/evidence/os-immersive-image-2026-10-03.md).

## Current delivery work

The934 observer is authoritatively inactive after candidate change:2291.115s/76 samples, zero observation errors, incomplete observation. It supplies no eight-hour acceptance for4a133. The final same-candidate observation remains OPEN.

Public appliance update/rollback is now natively exercised; all six application CI jobs37128431057/37128428420 passed. New notice asset is installed and independently verified inside successor imagec8ac9c709acb/source3ca7e4e. Its4,571,791,360-byte raw SHA256 is de085cdcae326cfafba7ef93c2bf4956efd33aaf650ccdbb4a5cd311f3db5979. This image is not provisioned or written. SSH console flasher is being implemented; SD is offline, while USB remains the current/recovery medium. [Latest image/procedure evidence](docs/evidence/appliance-update-and-sd-image-2026-10-03.md), [dependency inventory](docs/DEPENDENCIES.md).

Owner priority: complete flasher/SD installation first, then remaining functionality and major UI/UX improvement. Current owner assessment UI3.5/10, UX5/10 is unsatisfactory; visual/product acceptance remains OPEN. [Roadmap](docs/ROADMAP.md).

SSH console flasher is now implemented: [procedure](docs/SSH_FLASHER.md). All18 focused tests passed; full local suite153 passed/22 Windows/Linux-platform skips, one existing deprecation warning. Linux loop/provisioning proof, SD identity/whole-card backup, physical write/readback and SD boot remain pending. No SD has been erased.

## Remaining release gates

- Complete EN/RO physical touch, theme and error-state inventory on one current candidate; native preparation timeout/retry.
- Real Netflix movie/audio/resolution, YouTube route and the approved music-service decision/account proof. Owner has Netflix; Spotify Premium has not been supplied.
- Complete Bluetooth pair/connect/disconnect/forget/reconnect and radio/local audio routing/volume; real network failure/authentication/forget/recovery.
- Current-candidate recovery, five physical cold boots, graphical-start/per-action performance, complete idle PSS and eight-hour interactive stability.
- Public appliance update/rollback, clean successor-image installation, backup/restore, dependency/license deliverables and full requirement-by-requirement audit.

[Roadmap](docs/ROADMAP.md), [operations](docs/OPERATIONS.md), [Definition of Done](docs/DEFINITION_OF_DONE.md). The detailed prior ledger is preserved in [historical status](docs/evidence/status-history-through-2026-10-03.md); it is not a current-state checklist.
