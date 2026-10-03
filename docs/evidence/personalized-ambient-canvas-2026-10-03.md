# Personalized Ambient Canvas — 2026-10-03

## Scope and PC verification

Candidate ec6a0b1fbd3f adds a shared sky behind the idle header,10s transparency/interaction recovery, saved Home card visibility and positions, Compact/Balanced/Large output visualization, six real-signal styles, automatic matching-station artwork recovery, distinct cloud banks, illuminated city windows and irregular decorative meteor bursts. Card placement is explicit via Settings → Home → Arrange Home, with Save/Cancel/Reset and failure feedback. Relative coordinates are bounded by actual card size when the canvas changes. Deliberate user overlap is allowed.

Fresh complete browser run after the final CSS repair:224 passed in2.7min at800×480, EN/RO and both themes. Earlier intermediate run had16 failures:12 dock overflow cases and4 old positional shortcut selectors; those were corrected,16 affected tests passed, then the full fresh224 passed. The fresh run had no concurrent source edits. Backend284 passed,22 Windows platform skips. TypeScript, production Vite build, repository structure and separate toolchain fixture passed.41 runtime files packaged.

The new browser cases cover10s idle transparency and touch recovery, all three sizes, all four draggable elements, persistence across reload, card visibility, cancellation and failed saving. Output-signal tests cover six styles and paused/muted/invalid signal behavior. Artwork tests check stream matching and a playback-change race. Native device evidence is pending at this source commit. No10/10 score or product acceptance is inferred from these tests; all30 criteria remain OPEN.
