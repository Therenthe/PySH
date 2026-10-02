# UI handoff, pairing and search — 2026-10-03

Candidate `df9d3777bdec`, based on main `b3a56b69d758d4b9fac0785658ebfcae394efdbc`.

Repairs: video waits for a successful Stop even when cached player state is idle; media mutations are serialized so a pending Play completes before that Stop. Failure prevents video opening; double taps do not open concurrent transitions. Bluetooth prompts wake an active screensaver and suppress its idle timer until answered. City search clears stale results, shows localized loading/empty feedback and discards an older response. mpv's URL-derived radio title (such as `128`) falls back to the selected station; genuine broadcast metadata remains visible.

Automated EN/RO × E-Ink/Night at 800×480: 72 browser tests passed, zero skipped/unexpected/flaky (71.847s). Includes delayed Play→video handoff, failed/delayed Stop and stale idle snapshot, prompt waking/suppressing/restarting idle timer, and delayed city A after empty city B. Python Windows 53 passed, five Linux-only skipped; TypeScript/Vite/repository/package checks passed. No hardware acceptance is inferred from fixtures. Real-device successor verification pending; required product criteria remain OPEN.
