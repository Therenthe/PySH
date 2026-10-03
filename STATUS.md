# PySH status

Updated: 2026-10-03 (Europe/Bucharest). GitHub is canonical: https://github.com/Therenthe/PySH. Work is on draft PR3, branch feat/pysh-os-image; main remains the earlier desktop delivery. The product is not complete; all30 required criteria remain OPEN in [acceptance.json](docs/acceptance.json).

## Installed application and device

- Application934d0d338e66, source20f19b907359da5aede58b933888c0eb7a5f5be6; all39 installed file hashes verified. Previous8ede2b86f53a retained. Preferences, display/touch configuration and native host unchanged on activation.
- Corrected physical USB image source d61ec8d, original runtimea32c29065d6d. Pi4/4GB, Debian13 ARM64, DSI800×480, rotation180 with identity touch calibration. Root UUID5610e056-221b-46c9-8046-65c9adb6a5c1. Original SD is kept offline for recovery.
- Dedicated greetd/labwc session, user pysh.service, /opt/pysh/current and /opt/pysh/venv. API is loopback8765. Administrative SSH uses the provisioned key; secrets, profiles and backups stay outside Git. Desktop deployment scripts do not operate this appliance.

## Current evidence

Full application CI37125060631/37125062942 passed on Python3.12/3.13 and frontend. Protected preparation on an empty native profile reached real EME/key readiness in69.781s with one browser restart; prepared profile3.271s; cancel completed. RO/E-Ink preparation fits800×480. Actual compositor live inspection found and then verified removal of Chromium's translation prompt. Retained owner profile reopened without CDP/account inspection: checking→ready2.573s, actual panel shows Netflix Home without error. Film playback/resolution remains OPEN. [Preparation/activation evidence](docs/evidence/protected-playback-preparation-2026-10-03.md).

Pre-activation backup is separately verified on PC: SHA256880dc725418a0161713caf4643b5e4b4b84e53bc4365b2d61a6f19400016fc02,40 readable regular members and35 previous-runtime hashes. Earlier keyboard,48-screen UI surveys, cold boots, audio and performance results are historical evidence and are not cumulative PASS for the current candidate.

## Verified successor image, not installed

Image source20f19b907359da5aede58b933888c0eb7a5f5be6/runtime4ce1a5fe6390 built in run37125060698. Downloaded parts, gzip and raw image verified independently on PC:4,571,791,360 bytes, SHA256dcc40256ff08ee195bc39616a3829d7773c1402bfb0409ee680f973f347790eb. Independent ext4 inspection checks39 runtime hashes and session/touch/native-host/immersive settings. Three font/license files differ from installed934 only by CRLF/LF. Recovery provisioning, writing and physical boot of this image remain OPEN. [Image evidence](docs/evidence/os-immersive-image-2026-10-03.md).

## Work in progress

Read-only eight-hour stability observation started2026-10-03T13:33:16Z on934. User unit pysh-stability-observation.service, invocation ef9abc7ace0e473990a453c04a6d502c, was confirmed active with PID75679. It records30-second safe API/process/memory samples and stops if the candidate changes. Initial Netflix-open sample:27 processes, API available, zero zombies,1,113,752KiB PSS, all members readable. This is media-load observation, not idle PERF-02 or REL-01 acceptance; periodic touch/media response is still required. Recheck the actual unit handle before treating it as running.

The observer unit was rechecked active at1175.801s:40 samples, zero observation errors, unchanged invocation/PID. This partial observation is not eight-hour acceptance.

Public appliance update/rollback and reproducible read-only stability tools are implemented with local regression coverage; Linux CI and relevant native procedure proofs are required before acceptance. Dependency/license inventory covers569 OS packages. Local successor package4a133daa7278 adds the three complete browser MIT notices as a40th runtime file; all39 previous file hashes remain unchanged. It has not been installed or checked in a successor image. [Dependency inventory](docs/DEPENDENCIES.md).

## Remaining release gates

- Complete EN/RO physical touch, theme and error-state inventory on one current candidate; native preparation timeout/retry.
- Real Netflix movie/audio/resolution, YouTube route and the approved music-service decision/account proof. Owner has Netflix; Spotify Premium has not been supplied.
- Complete Bluetooth pair/connect/disconnect/forget/reconnect and radio/local audio routing/volume; real network failure/authentication/forget/recovery.
- Current-candidate recovery, five physical cold boots, graphical-start/per-action performance, complete idle PSS and eight-hour interactive stability.
- Public appliance update/rollback, clean successor-image installation, backup/restore, dependency/license deliverables and full requirement-by-requirement audit.

[Roadmap](docs/ROADMAP.md), [operations](docs/OPERATIONS.md), [Definition of Done](docs/DEFINITION_OF_DONE.md). The detailed prior ledger is preserved in [historical status](docs/evidence/status-history-through-2026-10-03.md); it is not a current-state checklist.
