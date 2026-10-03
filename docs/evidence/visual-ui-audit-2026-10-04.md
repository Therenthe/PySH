# Visual UI audit — 2026-10-04

Baseline: candidate `43bbb099a8b6`, source `22e7e46e72a5373111419f7ea90fb8bba45ddcd3`. This is an independent audit, not product acceptance or a numeric design score. Findings apply to this source, not to subsequent edits being implemented concurrently.

## Method and limits

Built an isolated Git archive under private `.runtime/audit-visual-22e7`, using production Vite assets and local headless Chromium at exactly 800×480 with touch enabled. No shared development server/HMR, device mutation, network change or real preference change was used. All API responses were intercepted with explicit fixture data; audio shapes used the same known nonuniform waveform and 16 amplitude bins. The local static server bound only 127.0.0.1 and was closed after each run.

Measured 72 combinations: EN/RO × E-Ink/night × six styles × three sizes. After initial render, measured expanded geometry; after 16 seconds of controlled browser time, measured collapsed geometry and actual SVG output. Ran four further settled captures and actual Arrange Home interactions to verify current toolbar colors, control rectangles and both languages/themes. Private results: `audit-output/measurements.json`, `focused-output/measurements.json`, source scripts `audit.mjs` and `audit-focused.mjs` inside the isolated directory. Initial broad-run screenshots can contain the retracting-rail transition; settled focused screenshots are the visual reference for that state.

Inspected the private native `free-layout-installed.png`. The private `owner-drag-current.png` shows an older toolbar; its white-on-white buttons are **not attributed to candidate43**. None of these private captures is published with this report.

This audit does not certify every application button end-to-end, physical touch, audio output, launch timing, eight-hour stability or current Pi rendering cost. It covers the requested visualizer geometry/style baseline, idle Home and current layout toolbar. The remaining full-button/hardware matrix needs separate evidence.

## Reproducible findings

| Priority | Finding | Evidence and action |
|---|---|---|
| High | Size appears ignored while playback is expanded. | All72 expanded visualizer containers were48px high regardless of Compact/Balanced/Large. Collapsed heights correctly became64/88/112px. `Home.tsx:42` explicitly forces48px while expanded. Apply the selected height in both states and budget the 422px content area; do not just increase height and clip transport. |
| High | Idle Home does not implement the new clock+signal+scene-only requirement. | At16s the weather card remains visible with location/temperature, the forecast remains visible as Today, and the topbar retains brand/network/settings. Only individual cards shrink. `Home.tsx:21-24`, `main.tsx` topbar and `ambient-home.css:126-128`. Add one coherent ambient state: hide card controls/content and secondary topbar content, preserve clock and genuine signal. First touch reveals compact cards without firing the underlying action. This is an unimplemented new requirement, not a failed claim that an existing feature had passed. |
| High | Bars and Mirror are nearly the same visual choice. | Actual SVG output contains16 vertically centered rectangles in both styles. Differences are rectangle width, corner radius, amplitude scale and opacity; their topology is identical. `AudioVisualizer.tsx:75,78`. Give Mirror a distinct reflected envelope around an axis, or consolidate the names. Avoid calling amplitude bins a frequency spectrum. |
| Medium | Wave and Ribbon have the same dominant outline. | Ribbon repeats the exact waveform path with a30%-opacity fill to the middle line. At48px expanded height, that fill is visually weak; both read as the same wave. `AudioVisualizer.tsx:74,77`. Use a genuinely distinct bounded ribbon/envelope derived from the real waveform; no arbitrary moving wave. |
| Medium | Circular styles are visually tiny despite a wide container. | Orbit and Rings use a320×80 viewBox with `xMidYMid meet`, leaving a central shape only a few tens of pixels wide in the48px expanded slot. The measured container size alone exaggerates their apparent prominence. `AudioVisualizer.tsx:72,76,79`. Fit circular styles to a square viewBox and measure occupied SVG shape bounds as well as container bounds. |
| Medium | E-Ink color treatment differs by SVG primitive. | `audio-visualizer.css` overrides path strokes and rectangle fills, but does not override circles or Ribbon fills. The actual E-Ink Rings screenshot retains a colored three-ring gradient while other styles become monochrome. Introduce an explicit theme-aware signal palette covering paths, fills and circles, including E-Ink over a nocturnal sky. |
| Medium | Meteor head/tail orientation is reversed. | Flight translates(-230,+130), toward the lower left. The horizontal gradient is transparent→bright toward positive X; after rotation(-30°), the bright end points upper right, trailing the movement. `ambient-home.css:71,143-144`. Reverse the gradient so the bright head leads the movement. Timings, starts, widths and burst counts already vary in `Meteors.tsx`; the current common direction, duration and angle still make the motion look uniform. |

## Verified improvements on this baseline

Arrange Home was opened using actual UI controls in EN/RO and both themes. Done/Reset/Cancel and the card-choice trigger were each48px high and within800×480. Computed toolbar button colors were E-Ink foreground(35,37,31)/background(225,233,223), contrast12.48:1; night foreground(244,247,251)/background(32,59,53), contrast11.24:1. The old white-on-white toolbar defect is repaired in this baseline. These opaque rendered colors permit a meaningful contrast calculation; gradient sky backgrounds require pixel-aware checks rather than treating CSS backgroundColor alone as the complete background.

The native installed capture shows a coherent city silhouette and a detailed illuminated lunar portion rather than the original three-circle moon. The lunar function is explicitly a low-precision illustration, not an ephemeris or true sky position. Do not present decorative sky events as observed or forecast astronomy.

## Restrained scene recommendation

Use an explicitly optional decorative atmosphere layer, separate from weather and low-precision lunar information. Meteors should have a leading bright head, tapered fading trail and modest variation in angle/duration/length, with bounded concurrency and sparse events. An occasional distant aircraft can use two tiny navigation lights and a subtle route; do not imply real flight tracking. A lunar flash/impact is fantasy decoration and should be clearly named as such in preferences; omit it from the default astronomically informed scene.

Animate transform/opacity on a small bounded number of elements. Stop generation when document hidden; remove all decorative motion under reduced-motion preferences. Avoid fullscreen blur, particle canvases, constant twinkling across every star or per-frame React state. Preserve legibility and never cover touch controls. Pi performance must be measured with real playback before accepting the scene.

## Required follow-up

Recheck the next immutable source after size/style/Home-idle fixes: all selected sizes in expanded/collapsed/free-placement states, occupied circular-shape bounds, E-Ink primitive consistency, first-touch reveal without unintended playback, keyboard/navigation access and reduced motion. Retest long RO labels and all transport capabilities. Browser geometry and fixture screenshots remain distinct from real-output sound and physical touch acceptance.
