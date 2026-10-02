# PySH status

Updated: 2026-10-03 (Europe/Bucharest). GitHub is canonical: https://github.com/Therenthe/PySH.

## Current candidate

Main `b3a56b69d758d4b9fac0785658ebfcae394efdbc` includes verified radio replay (PR #10). Isolated preview `4049721e2f4b` runs on the original Pi desktop/card, with the previous release and a private 52 MB backup retained. All 33 runtime hashes were verified before launch. SSH, NetworkManager, Bluetooth, PipeWire and WirePlumber remain active; no storage has been flashed and no appliance autostart activated on the existing card.

Successor candidate `df9d3777bdec` adds confirmed, serialized audio-to-video handoff, Bluetooth pairing prompts that wake/suspend the screensaver, city-search loading/empty states with stale-response protection, and radio URL-title fallback repair preserving genuine metadata. TypeScript/Vite/repository/package checks pass; 72 browser regressions pass with zero skips/failures/flaky tests (71.847s); Windows Python: 53 passed, five Linux-only skips. Successor hardware revalidation is pending. Full product acceptance remains OPEN.

## Observed device checks

On `4049721e2f4b`, two real radio streams passed Pause/Resume without position reset and Stop→Play in EN/RO × E-Ink/Night, plus invalid-stream recovery in all four combinations. Five selected video encodings and 48px touch controls/invalid-file recovery passed again with no JavaScript errors. Preferences/audio were restored and the auxiliary browser stopped. These muted transport tests do not certify acoustic quality or actual network-disconnection recovery. See [radio evidence](docs/evidence/radio-replay-2026-10-02.md).

Earlier `41a17d9b69e8` passed local audio touch transport/EOF replay, eight selected audio encodings, saved output/volume/mute restoration, API/kiosk recovery with unchanged preferences and zero owned zombies, and administrative restart-cause logs. Historical evidence is retained; a changed candidate requires affected revalidation. User previously confirmed physical setup/Bluetooth touch and audible WAV output. Full hardware flow matrix and resource/stability acceptance remain incomplete.

## Experimental PySH OS

PR #3 contains the experimental ARM64 image builder, UUID boot/root addressing, dedicated labwc/greetd session and public-key-only administrative recovery. Image source `e19b48c29ff2ea703b6f4365d5ebd9e0aa05acfe` built successfully in run `37059900737`; the complete PC copy was joined/decompressed and its raw SHA256 verified as `e98791fc99bcae5ab34def71c5f7f0bbbce47c9cb88b0f4c85a7f8de134b2c69` (4,571,791,360 bytes). CI inspected partition/UUID/runtime/recovery content. New application changes must be incorporated in a successor OS image.

A reviewed Windows flash wrapper passed inspection-only against the intended USB inventory. Explicit erase-target confirmation is still pending; no flash performed. Original SD is retained. Physical boot, recovery login, root expansion, five cold boots, eight-hour stability, clean installation and rollback are still OPEN. Detailed current OS evidence lives on PR #3; an image build is not physical acceptance.

## Remaining delivery work

1. Publish/deploy the successor and repeat affected real-device media/UI/recovery checks.
2. Integrate verified app changes into PySH OS, inspect the resulting artifact, then perform authorized experimental installation and physical boot/recovery.
3. Complete Bluetooth pair/forget/reconnect, real offline recovery, all EN/RO/theme hardware flows, exact resource/performance measurements, cold boots and stability.
4. Validate external services with authorized accounts and target playback support; shortcuts are not proof of streaming or DRM playback.
