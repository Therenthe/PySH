# Blender ambient scene — scoped local verification, 2026-10-23

This is implementation/browser evidence. It does not establish installation,
physical touch acceptance, Pi resource budgets or a numerical design score.

## Authored assets and scene behavior

- Blender 5.2.2 LTS authored the editable gothic/art-deco city, the metro prop,
  raindrop, snow crystal, ice, three warning-funnel frames and flood ripple.
  No downloaded models, photographic textures, logos or superheroes were used.
- Ten transparent runtime PNGs total approximately 1.5 MB; two city images are
  1600×570. The editable `.blend`, deterministic builder, build report and
  regeneration/review instructions are in `assets/blender/` and `scripts/blender/`.
  The UI composites flat assets; no runtime WebGL engine is introduced.
- Three architectural depth layers, stepped towers, pointed windows, clock tower,
  water tanks, stone edge catches, procedural material variation, varied storefronts,
  lamps and an elevated metro replace the old silhouette/facade-photo city layer.
- The original 170 SVG stars and existing calculated Sun/Moon position/phase are
  retained. Day/night-only celestial visibility is unchanged.
- The antenna emits only while the actual player is playing radio. Bluetooth
  powered/disconnected and connected have different markers; an unavailable/off
  adapter has no Bluetooth marker. Camera-projected roof anchors keep them on the
  corresponding buildings. These are supplemental decorative cues, not controls.
- Rain uses individual differently sized, staggered, slightly tilted falling
  Blender sprites instead of repeating full-screen gradient stripes. WMO intensity
  controls 18/38/64 particles. Snow/ice, wind drift, fog, distant low-contrast thunder
  illumination and cold roof haze use real weather fields. Actual temperature
  at least 35°C enables a warmer daytime sky and a small rising heat haze.
- Reduced motion disables the train, falling motion, heat shimmer and lightning;
  sparse static precipitation has varied vertical positions. Hidden-page city
  animations pause. Decorative elements do not intercept pointer events.

## Warning truth and usability

Weather codes never manufacture a flood, tornado or warning. Warning eligibility
requires explicit provider/source, current onset/expiry and an available report.
Only explicit severe/extreme flood/rain-flood or tornado warnings enable the
corresponding illustration. A visible caption and warning dialog explain that it
is a warning illustration, not live footage or a confirmed disaster at the address.

The 48px EN/RO warning control remains available on a folded weather card, is
absent during Arrange, and opens a bounded scrolling dialog with human-readable
provider/expiry. Raw feed URLs are not displayed or linked. Known verified alerts
remain visible with an explicit partial-coverage disclaimer. Missing/stale data
does not claim an all-clear. Expiry closes the old dialog; a later warning does
not reopen it without another user action.

## Checks performed

- TypeScript check passed on the final scene source.
- **68 final browser cases passed** in EN/RO at 800×480, covering both themes,
  ten seasonal weather scenarios, all supported WMO condition mappings,
  northern/southern hemisphere seasons, bounded particles and actual CSS movement,
  reduced motion, real player/Bluetooth state transitions, warning dialog geometry,
  folded/Arrange behavior, stale/unavailable/expired/future/source-less alerts,
  partial coverage, human source labels, explicit flood/tornado illustrations and
  expiry/replacement recovery. The hazard cases are isolated fixtures, not live
  warnings or device state.
- A preceding **128-case affected regression passed**, including existing
  Ambient Home and celestial tests. The final heat-background refinement and
  warning-dialog expiry reset were subsequently covered by the 68-case run.
- First local runs exposed two test-harness problems: JavaScript fake-clock
  advancement does not advance compositor animation frames, and isolated TSX
  module import lacked Vite's React preamble. The tests now observe real CSS
  frames and import a separate pure warning model. An obsolete English Arrange
  label was also corrected. No failed run is counted as passing evidence.
- Blender's installed expert `bx_review` produced front/three-quarter/side
  silhouette and matcap sheets, which were inspected. `bx_light.color_audit`
  returned no issues. City mesh audits reported no zero-area faces, loose
  vertices/edges or flipped faces. The separate closed rain and ice props passed
  the render-profile delivery gate. Disconnected architecture and open detail
  planes are intentional offline-render scenery, not printable/exported game
  meshes.
- Full-size day/night and seasonal browser captures were inspected, including
  visible individual rain drops, metro/roof-marker alignment, heat haze,
  snow/ice and sourced warning illustrations. The existing photographic
  starfield/facade files remain unused; no photographic sky layer was restored.

Private local artifacts are under `.runtime/city-final-frozen-20261023`,
`.runtime/city-acceptance-playwright-20261023` and `.runtime/blender-city-review`.
They are not runtime assets and are not published with user/device state.

## Still required

Verify the exact packaged candidate on the Raspberry at 800×480, inspect the
physical display in day/night conditions, confirm actual state changes, and
measure CPU/GPU/frame timing and total Chromium memory during media playback.
These checks and complete product acceptance remain OPEN.
