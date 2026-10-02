# Audio transport, persistence and weather races â€” 2026-10-02

Source review found local audio directory queue existed but the UI exposed only pause/stop, active radio pause reloaded a stream, saved audio settings were persisted but not reapplied, and old weather requests could overwrite a new selected city's results.

Repairs expose queue availability, previous/next, progress and touch seek; use pause/resume for the same radio URL; restore saved available output/volume/mute once per availability cycle; and discard stale weather results using request generation plus location identity. Audio snapshots retain actual device values and hardware errors do not become success. No automatic unknown Bluetooth pairing is introduced. Supervisor recovery now logs role and exit code without process arguments or credentials.

Automated asynchronous cases delay the old city request, replace/remove the location, and finish the old request last. Audio tests restore saved values from another default, avoid repeating writes on each poll, pause on device loss and restore on return; preference bytes survive a new store. Queue boundaries are returned for local sources only. Device acceptance remains pending on the candidate produced after these changes.

Local checks: 49 Python tests passed, five Linux cases skipped on Windows; TypeScript and production build passed. Full browser suite: 52 passed, zero skipped/flaky/unexpected, 56.042s. New tests cover EN/RO/themes, local queue boundaries, seek/pause/replay after EOF/error, and same-title/different-URL radio identity. These synthetic checks do not prove device acceptance.

## Real Pi follow-up

Runtime 41a17d9b69e8 from published source0bc1740c8333d3042a1bda6c41dc7df1726fff1f (merged main dc24dc25de5f61c701bcd45561752e4d87ece355), archive SHA256 04ae2c80d1ef7da9262bcf81976943a5067be19351f31b2a986b2d963e38592f: 33 hashes verified before isolated launch. Backup1b4895aa1685902b657531b0025739b15d8c9b286dbbebc6df23d699ddb296b0 retained.

Actual Pi Chromium EN/RO x ink/night passed pause/resume, touch seek within a 45-second WAV, next/previous across two files with correct boundary disabling, natural EOF replay, stop and 48px targets. No JavaScript errors. Private panel captures reviewed; preferences/audio restored and auxiliary browser stopped. This verifies real selected-file playback and controls, not audible acceptance for every encoding.

API/kiosk SIGKILL recovered in1.903s/0.998s, preference bytes unchanged, zero zombies and one live mpv in full descendant tree. User journal query returned no entries; visibility/cause evidence and final OS revalidation remain open. Actual audio preference restoration is the next probe. GitHub run37059200971 passed backend/frontend/browser checks.

Actual persistence probe forced volume71%, unmute and another available default output, then restarted the owned API. In3.458s it restored the saved output, volume27% and mute; original actual/preference values restored afterwards. Administrative journal query confirmed API/Kiosk exitcode=-9 restart messages with no arguments or credentials. Normal user journal query lacks visibility; physical OS recovery/admin access is still untested.
