# Radio replay regression — 2026-10-02

Candidate: `4049721e2f4b`, based on main `dc24dc25de5f61c701bcd45561752e4d87ece355`.

The mini-player previously attempted to resume an empty mpv source after Stop. It also exposed local-queue Previous for radio. Replay now loads the remembered station, while paused sources resume in place; retained radio error/end sources retry their URL. Connecting/buffering accepts Pause. Idle with no remembered station disables Play. Previous/Next remains specific to the local audio queue.

Regression covered EN/RO and E-Ink/Night at 800×480: 56 browser tests passed, no skips, failures or flaky tests (61.003 seconds). TypeScript/Vite/repository/package checks passed. Windows Python: 49 passed, five Linux-only skipped. Tests simulate API states and do not prove real stream transport. Actual Pi radio stream verification is pending. Required product criteria remain OPEN.
