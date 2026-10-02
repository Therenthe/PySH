# UI handoff, pairing and search — 2026-10-03

Candidate `df9d3777bdec`, based on main `b3a56b69d758d4b9fac0785658ebfcae394efdbc`.

Repairs: video waits for a successful Stop even when cached player state is idle; media mutations are serialized so a pending Play completes before that Stop. Failure prevents video opening; double taps do not open concurrent transitions. Bluetooth prompts wake an active screensaver and suppress its idle timer until answered. City search clears stale results, shows localized loading/empty feedback and discards an older response. mpv's URL-derived radio title (such as `128`) falls back to the selected station; genuine broadcast metadata remains visible.

Automated EN/RO × E-Ink/Night at 800×480: 72 browser tests passed, zero skipped/unexpected/flaky (71.847s). Includes delayed Play→video handoff, failed/delayed Stop and stale idle snapshot, prompt waking/suppressing/restarting idle timer, and delayed city A after empty city B. Python Windows 53 passed, five Linux-only skipped; TypeScript/Vite/repository/package checks passed. No hardware acceptance is inferred from fixtures. Real-device successor verification pending; required product criteria remain OPEN.

## Real Pi successor verification

Published source `74a006e54c38f2b54c531f61345ed3a46f1f411e`, merged main `4d28e523e87bb71b83614c53903d629f0e48757b`, preview `df9d3777bdec`. Archive SHA256 `f58848785266983c7764b82ae6d8d70cf8d4feceae33d5c3a3000f0194f53fbf` and all 33 file hashes verified; previous release/private 53 MB backup retained.

Eight actual radio/local-audio→video handoffs (EN/RO × themes) stopped mpv and progressed Chromium video. All radio observations showed Radio Swiss Jazz rather than URL tail 128. Four actual geocode searches showed the localized empty-result state; captures inspected at 800×480, zero JavaScript errors. Temporary mute and original preferences/audio restored; auxiliary browser stopped. Bluetooth screensaver tests remain synthetic until a real pairing prompt is observed.

Controlled owned-process SIGKILL recovered API in 2.425s and kiosk in 0.979s. Preference SHA256 unchanged; complete supervisor descendant tree had zero zombies and one live mpv after cleanup grace. Saved output/27%/mute restored after forced PipeWire state change and API restart in 3.235s; original values restored finally. Administrative journal filter for the exact preview unit showed API/Kiosk exited code=-9 and corresponding restart messages without credentials. REL-02 passes on this original desktop/card preview; no dedicated OS boot/recovery acceptance is implied. Raw reports/captures remain private. GitHub run 37064480391 succeeded for frontend and Python 3.12/3.13.
