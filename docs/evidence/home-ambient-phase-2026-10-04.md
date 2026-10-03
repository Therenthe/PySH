# Home ambient rest — 2026-10-04

Candidate runtime: `c425ad0475dc`. This record covers source and browser verification; installation and physical acceptance require separate observed evidence.

Home enters an ambient phase after 30 seconds of eligible inactivity, retaining clock, audio signal and sky in their existing positions. Navigation, cards, metadata and transient chrome fade away. Automatic ScreenSaver remains available on other pages; explicit preview remains available. Setup, dialogs, editing, keyboard, pending operations and errors block the transition.

The first pointer or keyboard gesture wakes compact cards without executing the covered control. The full originating gesture is consumed. Header becomes solid, then returns to its normal idle transparency after ten seconds. Layout and preferences are not rewritten.

Verification on the same application source: 240 cases passed in the full 264-case suite; the remaining 24 audio cases initially failed because their virtual-clock jump overtook asynchronous Unmute completion. With chronological `clock.runFor(62000)`, all 24 passed in 31.3 seconds. This is 264 covered cases, not one clean full-suite run. TypeScript and production Vite build passed; archive contains 41 allowlisted runtime files.

Independent usability audit: four EN/RO playing/paused cases held Unmute pending for 15 seconds, below its 20-second timeout. No saver while pending; absent at 58 seconds after completion; present at 62 seconds. Playback polling does not reset idle time.

Independent visual audit: eight exact 800×480 captures across EN/RO and both themes; compact wake without mutations or dialogs; three manual right anchors stable within two pixels; twelve weather/sky checks; reduced-motion transition duration zero. Representative pixel contrast: clock 15.06:1, Ink signal 10.56:1, night purple signal 7.00:1. Browser fixtures do not prove physical touch or native rendering performance.

All product acceptance criteria remain OPEN. Optional aircraft/lunar effects and recovery defects are separate tracked tasks.

## Observed native installation

Source `06b5cf5f999f51257980b734b78e9cb998aa0ddf`; runtime `c425ad0475dc` activated on the existing SD, retaining `94ca6c6baf22` for rollback. Separate PC backup SHA256 `8e7ebc2b4ce717533b2339024eb99910d8690cf04cbd4e3ad5a6e235d8648dea`, archive and receipt verified before activation. All41 runtime file hashes matched; no pending transaction. Radio resumed, audio-ready true throughout four samples with playback position16.116→19.120→22.149→25.137seconds. Actual800×480 private compositor capture inspected: Home idle shows clock, signal and sky, with navigation/cards absent. No physical wake/Arrange gesture or native performance acceptance is claimed from this capture.
