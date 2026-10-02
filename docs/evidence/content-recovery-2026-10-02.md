# Content recovery and real audio audit — 2026-10-02

## Observed candidate

Pi preview `24f207c79081`, derived from main `b853a5e62a5d40920f7ca8fee8a7709fdb3439b7`, remains isolated from desktop boot and persistent legacy data.

The real Chromium/Pi audit inspected 48 screens at 800×480 across EN/RO and E-Ink/night. Visible text below 14 px, text contrast failures and touch targets below 48 px: zero in this sampled matrix. 120 local navigation samples had aggregate p95 163.5 ms. This does not establish the complete control contrast, physical touch, first-feedback or five-launch criteria. Private captures and raw measurements remain outside Git.

Eight generated five-second audio fixtures (WAV PCM16, MP3, AAC, M4A/AAC, FLAC, OGG/Vorbis, OGA/Vorbis and Opus) reached real mpv `playing` with increasing position and selected PipeWire output ready. Missing local file returned HTTP 409 `media_not_found`. This demonstrates these particular encodings, not arbitrary files or audible acceptance for each codec. Prior audible WAV confirmation is recorded separately.

An intentionally invalid MP3 returned idle without an error: MEDIA-02 FAIL on this candidate. mpv JSON IPC emits end-file fields at the top level; the adapter incorrectly expected only nested data. Reference: https://github.com/mpv-player/mpv/blob/master/DOCS/man/input.rst (event fields and reasons).

## Repair under test

- Consume flattened mpv failure/EOF events, retain visible failure until recovery, distinguish natural end from stop, and avoid clearing a new source when the previous source emits stop. Reset position tracking for each new load. Existing nested adapters remain compatible.
- Radio cancels superseded requests, ignores stale results, reuses the recent catalog on re-entry and gives retry for the failed catalog operation.
- Weather and media-library failures retry their own operation. Local video errors appear inside the video overlay with retry and a usable back control.
- Service mode suppresses the idle screensaver and clears a latent overlay on return. Radio/media subtitles describe their actual page.

Validation: 46 Python tests, 36 Playwright tests (EN/RO × themes, including stale catalog responses, weather/library/catalog retry, invalid video retry and service idle/return), TypeScript, production build and repository structure pass. Browser failures are simulated only in tests. The repaired runtime still requires deployment and a repeat of the real corrupt-file/recovery probe; no product acceptance is inferred from unit/browser results.
