# Video controls and process recovery — 2026-10-02

Real preview `bfb3cdd16723` decoded five synthetic six-second fixtures through actual Chromium on Pi: MP4/M4V/MKV/MOV with H264/AAC, WebM with VP9/Opus. Each showed 640×360 decoded frames and increasing playback time. Invalid MP4 displayed its error overlay, retry and back worked in EN/RO and both themes. This proves the selected encodings, not arbitrary container/codec combinations or per-video audible acceptance.

Review of the actual 800×480 captures found native video controls hidden while playing and too small when visible. The repair uses a real HTML renderer with persistent app-owned controls, full 48px touch slider surfaces, play/pause/seek and actual system output volume/mute through the existing API. Both languages/themes remain covered.

The real API crash probe exposed orphan mpv processes: the old supervisor restarted API/kiosk but skipped cleanup of descendants of an exited API parent. REL-02 FAIL on bfb3cdd16723. The repair owns separate process groups for API/browser, adopts/reaps Linux orphan children, terminates even when a leader has died, escalates within a deadline and retains only current handles. Already-cleaned handles cannot signal a reused group. Four Linux subprocess regressions exercise real process trees and unrelated process safety.

Integrated local checks: 46 Python tests pass, four Linux-specific tests correctly skip on Windows, TypeScript and production build pass, 40 browser tests pass (no skipped/flaky cases), including real test-browser video decode/play/pause/seek with generated WebM and correct HTTP Range. Device audio is simulated only in those browser tests. Linux CI and repaired Pi deployment/probes remain pending. Neither new repair is hardware acceptance yet.

## Real repaired preview and follow-up

Published source `1fb013f0e44ad321094905d783a58e8efea9bba1`, merged main `9c2b66fe9ca93b1bbe543c35c4d0bca488b4f588`, produced runtime `9648250fa63f`, archive SHA256 `70803024101be1687f69c0afba45bd4b3ff6fe4828ff1b211b0aa037fcf12eac`; 33 files verified before launch. Both GitHub runs 37052967647/37052981090 passed, including four Linux process-tree regressions.

Real API SIGKILL recovered in 1.909s; kiosk SIGKILL recovered in 1.128s. Preference file hash remained identical; only one live mpv remained. Two exited crashpad children detached from the browser process group remained adopted zombies. The follow-up reaps exited adopted children without signalling processes or stealing the current API/browser Popen exit status; a fifth Linux regression covers that case.

The first resource probe (258.26 MiB at two minutes) omitted Chromium's main process because it moves to a sibling app scope. It is incomplete and must not be used to accept PERF-02. A complete descendant-tree observation later, after closing the auxiliary audit browser, measured 545.45 MiB across 16 processes, including two zero-memory zombies, with one live mpv. This is a corrected later idle observation, not the required exact two-minute release measurement or an eight-hour stability result. PERF-02 stays OPEN.

The final video-control device audit was not executed: automatic approval review failed because of the Codex usage limit, not a safety rejection. Browser regression remains valid but cannot replace the pending real-control validation. No workaround of that approval check was attempted.
