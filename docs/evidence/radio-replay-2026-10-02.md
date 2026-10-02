# Radio replay regression — 2026-10-02

Candidate: `4049721e2f4b`, based on main `dc24dc25de5f61c701bcd45561752e4d87ece355`.

The mini-player previously attempted to resume an empty mpv source after Stop. It also exposed local-queue Previous for radio. Replay now loads the remembered station, while paused sources resume in place; retained radio error/end sources retry their URL. Connecting/buffering accepts Pause. Idle with no remembered station disables Play. Previous/Next remains specific to the local audio queue.

Regression covered EN/RO and E-Ink/Night at 800×480: 56 browser tests passed, no skips, failures or flaky tests (61.003 seconds). TypeScript/Vite/repository/package checks passed. Windows Python: 49 passed, five Linux-only skipped. Tests simulate API states and do not prove real stream transport. Actual Pi radio stream verification is pending. Required product criteria remain OPEN.

## Real Pi verification

Published source `5eafe6e49a66fbf166790225b385fcc53741cfae` (merged main `b3a56b69d758d4b9fac0785658ebfcae394efdbc`), candidate `4049721e2f4b`: checksum and all 33 runtime file hashes verified before isolated launch; previous release and a private 52 MB backup retained. Two official Radio Swiss streams passed real mpv progress, row Pause/Resume preserving position and mini-player Stop→Play in EN/RO × ink/night (eight flows). Invalid reserved-DNS stream showed localized error and recovered to valid playback in four flows. No JavaScript errors. Source URLs are documented by [Radio Swiss Classic](https://www.radioswissclassic.ch/en/reception/internet) and [Radio Swiss Jazz](https://www.radioswissjazz.ch/en/reception/internet). These checks used temporarily muted output and restored preferences/audio; they do not certify acoustic quality or actual network-disconnection recovery.

Five selected video encodings again played in real Chromium; 48px controls and invalid-file recovery passed all four language/theme combinations. Auxiliary browser was explicitly stopped after tests. Images and raw reports remain private `.runtime/` artifacts. One visible problem was discovered: absent radio metadata made mpv display the URL tail `128` instead of station identity. Follow-up repairs only the URL-derived fallback while preserving actual broadcast metadata. Further UI repairs cover video/audio handoff, pairing prompt vs screensaver, and empty city search; successor hardware revalidation is required.
