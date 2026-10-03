# Personalized Ambient Canvas — 2026-10-03

## Scope and PC verification

Candidate ec6a0b1fbd3f adds a shared sky behind the idle header,10s transparency/interaction recovery, saved Home card visibility and positions, Compact/Balanced/Large output visualization, six real-signal styles, automatic matching-station artwork recovery, distinct cloud banks, illuminated city windows and irregular decorative meteor bursts. Card placement is explicit via Settings → Home → Arrange Home, with Save/Cancel/Reset and failure feedback. Relative coordinates are bounded by actual card size when the canvas changes. Deliberate user overlap is allowed.

Fresh complete browser run after the final CSS repair:224 passed in2.7min at800×480, EN/RO and both themes. Earlier intermediate run had16 failures:12 dock overflow cases and4 old positional shortcut selectors; those were corrected,16 affected tests passed, then the full fresh224 passed. The fresh run had no concurrent source edits. Backend284 passed,22 Windows platform skips. TypeScript, production Vite build, repository structure and separate toolchain fixture passed.41 runtime files packaged.

The new browser cases cover10s idle transparency and touch recovery, all three sizes, all four draggable elements, persistence across reload, card visibility, cancellation and failed saving. Output-signal tests cover six styles and paused/muted/invalid signal behavior. Artwork tests check stream matching and a playback-change race. Native device evidence is pending at this source commit. No10/10 score or product acceptance is inferred from these tests; all30 criteria remain OPEN.

## Native installation and visual findings

Application ec6a0b1fbd3f/source4bb708bdeb63e648fcc6811ccffbfa1e46edd952 activated on the verified SD after a separate readable PC backup, SHA2562d7a3cdb0919cb96b88469434ab6e4861d0e6587a1e45afe10a8a6dfae4c3ed4. Previous54a31cd7e182 retained. Independently checked all41 file hashes, absence of pending transaction and advancing radio35.91→44.95s with ready output.

44 native functional records: EN/RO × two themes × header/decoded logo, three sizes, six changing real-signal styles, and one distinct persisted placement per combination (all four elements covered). Sizes measured380×64,520×88 and660×112px; default forecast clearance exceeded16px. Actual captures exposed dark E-Ink signal over the nocturnal sky despite these functional passes. A targeted contrast correction b180f17fb355 is prepared and requires separate native visual verification. Private captures and raw device proofs stay outside Git. Temporary Chromium debug listener and SSH tunnel were closed; saved preferences restored and radio resumed. All30 acceptance criteria remain OPEN.

Targeted contrast regression run:36 affected cases passed in36.8s after correcting a test expectation for the distinct night-palette text. TypeScript/production build passed; backend runtime files are unchanged from the284-test run.
