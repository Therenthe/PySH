# PySH status

Updated: 2026-10-03 (Europe/Bucharest). GitHub is canonical: https://github.com/Therenthe/PySH.

## Current candidate

Main `4d28e523e87bb71b83614c53903d629f0e48757b` includes radio replay and media handoff/search/pairing-prompt repairs (PRs #10/#11). Original-desktop preview `df9d3777bdec` is deployed with all 33 runtime hashes verified; previous release and private backup retained. TypeScript/Vite/repository/package checks pass; 72 browser regressions pass with zero skips/failures/flaky tests; Windows Python 53 passed, five Linux-only skips. GitHub frontend/Python 3.12/3.13 run37064480391 passed.

Actual Pi revalidation passed eight media handoffs, four city-empty states, 48-screen EN/RO/theme survey, selected audio/video encodings and media error recovery with no JavaScript errors. API/kiosk recovery took 2.425s/0.979s with unchanged preferences and zero owned zombies; saved audio restored in 3.235s. REL-02 passes for this preview. See [UI evidence](docs/evidence/ui-handoff-2026-10-03.md). Original SD/desktop unchanged; no appliance autostart enabled there.

## Experimental PySH OS

Draft PR #3 integrates main above. Image source `59fcd319fadf133295cabd0443b13c5060430c12`, successful run37066609253, Linux runtime `1e2918ca798f`. Complete image verified on PC: raw SHA256 `4c99dc0b6f9b812fec4d291b3e34347642289211dc65b8b77fa00fead870e6c4`, 4,571,791,360 bytes. Includes UUID addressing, dedicated labwc/greetd session, key-only administrative recovery and guarded first-boot root expansion. Sixteen disposable Linux growth checks passed, including actually mounted online growth. [Image evidence](docs/evidence/os-image-2026-10-03.md), [growth evidence](docs/evidence/root-expansion-2026-10-03.md).

Windows wrapper passed inspection-only for the intended USB inventory. Explicit erase-target approval remains pending; no flash performed and original SD preserved. This is an experimental image, not physical product acceptance.

## Remaining delivery work

Physical boot/recovery login/root growth on actual storage; five cold boots and eight-hour stability; complete Bluetooth pair/forget/reconnect and real network-disconnection recovery; native resource/performance acceptance; external-account playback and DRM support; clean installation/rollback. Known paired-speaker appearance and a previously heard WAV are evidence of those observations only. Full product acceptance remains OPEN and the project is not complete.
