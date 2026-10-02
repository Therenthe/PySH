# UI handoff, pairing and search — 2026-10-03

Candidate `df9d3777bdec`, based on main `b3a56b69d758d4b9fac0785658ebfcae394efdbc`.

Repairs: video waits for a successful Stop even when cached player state is idle; media mutations are serialized so a pending Play completes before that Stop. Failure prevents video opening; double taps do not open concurrent transitions. Bluetooth prompts wake an active screensaver and suppress its idle timer until answered. City search clears stale results, shows localized loading/empty feedback and discards an older response. mpv's URL-derived radio title (such as `128`) falls back to the selected station; genuine broadcast metadata remains visible.

Automated EN/RO × E-Ink/Night at 800×480: 72 browser tests passed, zero skipped/unexpected/flaky (71.847s). Includes delayed Play→video handoff, failed/delayed Stop and stale idle snapshot, prompt waking/suppressing/restarting idle timer, and delayed city A after empty city B. Python Windows 53 passed, five Linux-only skipped; TypeScript/Vite/repository/package checks passed. No hardware acceptance is inferred from fixtures. Real-device results follow below; full required product acceptance remains OPEN.

## Real Pi successor verification

Published source `74a006e54c38f2b54c531f61345ed3a46f1f411e`, merged main `4d28e523e87bb71b83614c53903d629f0e48757b`, preview `df9d3777bdec`. Archive SHA256 `f58848785266983c7764b82ae6d8d70cf8d4feceae33d5c3a3000f0194f53fbf` and all 33 file hashes verified; previous release/private 53 MB backup retained.

Eight actual radio/local-audio→video handoffs (EN/RO × themes) stopped mpv and progressed Chromium video. All radio observations showed Radio Swiss Jazz rather than URL tail 128. Four actual geocode searches showed the localized empty-result state; captures inspected at 800×480, zero JavaScript errors. Temporary mute and original preferences/audio restored; auxiliary browser stopped. Bluetooth screensaver tests remain synthetic until a real pairing prompt is observed.

Controlled owned-process SIGKILL recovered API in 2.425s and kiosk in 0.979s. Preference SHA256 unchanged; complete supervisor descendant tree had zero zombies and one live mpv after cleanup grace. Saved output/27%/mute restored after forced PipeWire state change and API restart in 3.235s; original values restored finally. Administrative journal filter for the exact preview unit showed API/Kiosk exited code=-9 and corresponding restart messages without credentials. REL-02 passes on this original desktop/card preview; no dedicated OS boot/recovery acceptance is implied. Raw reports/captures remain private. GitHub run 37064480391 succeeded for frontend and Python 3.12/3.13.

## Repeated complete preview audit

On the same df9d3777bdec preview: 48 actual 800×480 screens across EN/RO and E-Ink/Night had zero measured touch targets below 48px, sampled fonts below 14px, sampled text-contrast failures or JavaScript errors. This survey does not certify every graphical boundary or every hardware state. Two-animation-frame navigation observations: 30 per action, Home p95 67.9ms, Radio 178ms, Media 66.4ms, Settings 47.1ms; overall 120 samples p95 137.4ms. This is auxiliary-browser observation, not proof of native visual feedback or OS boot timing.

All four actual local-audio transport/seek/EOF-replay flows passed. Five selected video encodings (MP4/M4V/MKV/MOV H264+AAC and WebM VP9+Opus) progressed, with actual 48px controls and invalid-file recovery in all four combinations. Eight actual audio decoders (WAV, MP3, AAC, M4A, FLAC, OGG, OGA, OPUS) progressed through mpv; missing-file rejection, invalid-stream error, valid-file recovery and natural EOF passed. Muted decoder tests do not certify audible quality per codec. Preferences/audio restored and auxiliary browser stopped.

Actual diagnostics export passed attachment name and exact field allowlist checks; all three service probes were available. The 1,462-byte hub log had no sampled secret/SSID/MAC/external-URL patterns. Rotation was not forced; full DIAG-01 remains OPEN. Raw local reports stay private.

## Native preview performance probe

Five controlled launches of the actual native kiosk from the existing desktop session reached visible Home with fonts loaded at 800×480 in 3.9044, 3.9243, 4.0401, 3.9130 and 3.9411 seconds. Anchor was systemd ActiveEnterTimestampMonotonic, not graphical-session startup. Fifth observed Home +120.0001s: full stable same-user supervisor descendant tree (14 processes including Chromium main, children and crashpads) had combined PSS 463.739MiB; sample ended at +120.1469s; zero zombies, one API and one kiosk. Exact native-profile ownership was checked even outside its cgroup. Debugger overhead included; no auxiliary browser used.

First attempt failed before mutation on unrelated inaccessible descriptors. Second measured five launches but rejected its PSS result because Chromium rewrites argv into a single process-title field; no PSS PASS claimed for that incomplete attempt. Corrected ownership/parser probe passed and restored normal non-debug launch, preferences and audio in finally. Private successful report retained. This qualifies preview app launches and idle memory only: PERF-01/02 remain OPEN for full feedback/media scenarios and dedicated OS acceptance, and it is not five cold boots or eight-hour stability.
