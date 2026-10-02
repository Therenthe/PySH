# Video controls and process recovery — 2026-10-02

Real preview `bfb3cdd16723` decoded five synthetic six-second fixtures through actual Chromium on Pi: MP4/M4V/MKV/MOV with H264/AAC, WebM with VP9/Opus. Each showed 640×360 decoded frames and increasing playback time. Invalid MP4 displayed its error overlay, retry and back worked in EN/RO and both themes. This proves the selected encodings, not arbitrary container/codec combinations or per-video audible acceptance.

Review of the actual 800×480 captures found native video controls hidden while playing and too small when visible. The repair uses a real HTML renderer with persistent app-owned controls, full 48px touch slider surfaces, play/pause/seek and actual system output volume/mute through the existing API. Both languages/themes remain covered.

The real API crash probe exposed orphan mpv processes: the old supervisor restarted API/kiosk but skipped cleanup of descendants of an exited API parent. REL-02 FAIL on bfb3cdd16723. The repair owns separate process groups for API/browser, adopts/reaps Linux orphan children, terminates even when a leader has died, escalates within a deadline and retains only current handles. Already-cleaned handles cannot signal a reused group. Four Linux subprocess regressions exercise real process trees and unrelated process safety.

Integrated local checks: 46 Python tests pass, four Linux-specific tests correctly skip on Windows, TypeScript and production build pass, 40 browser tests pass (no skipped/flaky cases), including real test-browser video decode/play/pause/seek with generated WebM and correct HTTP Range. Device audio is simulated only in those browser tests. Linux CI and repaired Pi deployment/probes remain pending. Neither new repair is hardware acceptance yet.
