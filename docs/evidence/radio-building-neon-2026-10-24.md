# Radio facade visualizer — 24 October2026

## Behavior

On Home, Wave follows the existing radio landmark while a radio source is
selected. Eight separately rendered light circuits trace studio-floor waves,
corner returns and art-deco cornices. Actual night/day determines brightness;
changing the interface theme does not invent a nocturnal scene.

The shared output reader supplies16 temporal PCM amplitude samples. Each pair
drives one circuit; these are not frequency bands. Pause, mute, zero volume,
missing output and unavailable/invalid/silent samples extinguish the lights.
There is no automatic party loop. Hidden/offscreen work stops; reduced motion
uses the existing1Hz signal cadence without opacity transitions.

Touch or keyboard activation of the building expands/collapses the existing
player. The first ambient touch only wakes Home. Decorative geometry remains
pointer-transparent and hidden from assistive technology; its separate Home
control has a localized name and a target of at least48px.

Other styles and local media retain their floating visualization, size and
saved position. Radio and rest views retain their waveform. Arrange retains
the existing movable Wave preview and stored anchors; no preference migration.
Settings explains the difference between building-mounted Wave and other styles.

## Blender delivery

Original source: `assets/blender/radio-neon/radio-neon-wrap.blend`.
Reproducer: `scripts/blender/build_radio_neon.py`.
Eight runtime PNGs:32,097 bytes encoded /1,061,056 bytes decoded RGBA.
Same118×281 crop at909/136 within the original1600×570 city camera.
45 closed tube props,4,784 vertices,7,948 triangles; all45 render-profile gates
pass with zero errors/warnings. City source, raster architecture and sky unchanged.
Night low/mid/high and subdued day inspected at native800×208 city size by both
author and independent visual reviewer. Local baked halo approximates spill;
the Pi does not run Blender, WebGL or a per-frame blur for these circuits.

## Iteration and verification

Independent usability and visual reviewers execute complementary browser probes.
R1 found an18px facade/control displacement. Further compact/ambient review
exposed state-dependent grid origins and inherited floating sizes. Integration
now uses Home's measured origin, explicit automatic grid area, and excludes the
building control from floating sizing rules. Delivery requires retest after
these corrections, not the earlier passing subset.

TypeScript/build and repository check pass.650 Python tests pass;32 platform
skips.82 extension tests pass. Final browser, canonical publication and actual
Raspberry verification are recorded below when complete.

This scoped feature is not full product acceptance, a numeric quality score or
a sustained Pi performance certification. All30 product criteria remain OPEN.


## Final delivery

Installed runtime `bf33d3e87322`, GitHub production source
`112c7c906ad2f775b6051e46b134c701b5ca0d03`, public tree
`5537d9e3250cead1c958fe04738fc83814eff881`. Local canonical source
`982625dddb779dfaaefd3b4ca3970f0e151acf9e`, tree
`6ff5bf9011d44de445a3461a31c4d772cb582f2b`.
Subsequent documentation/test-fixture changes do not change this runtime.

- Final cold-load browser gate:146/146 PASS (20 new +126 retained), EN/RO at800x480;
  zero failures/skips/flaky cases. Three test fixtures then adopted the backend's
  real local-audio kind; all14 affected retests PASS against the same frozen
  runtime. This is a targeted follow-up, not160 unique cases.
- Independent visual R4:60 captures across native-size night/day, languages,
  folded/expanded/ambient, sizes and reduced motion. Two geometry/sizing defects
  corrected and independently retested.
- Earlier working-tree regression:125/126 then isolated unchanged case PASS.
  Development hot reload invalidated that batch; the final146 run starts cold
  and supersedes it. Failed iterations remain in private evidence.
- GitHub publication verified577 public blobs/modes, including Blender source
  and every PNG. Five previously excluded operational documents stay excluded.
- PC backup contents/checksum verified before activation;115 installed hashes
  and29 preferences verified. Previous runtime `dd9a018bf755` retained; gateway
  and Ethernet unchanged; originally playing radio resumed.
- Actual Raspberry Chromium R2 PASS: 19 native800x480 screenshots, twelve
  theme/size/rail combinations, eight decoded118x281 images, changing measured
  radio signal, facade touch, Play button, pause/mute darkness and first ambient
  touch consumed. Control59x102.53px; x matched, y differed0.016px. Actual weather
  was fog and was not replaced for these captures.
- First native run passed geometry/signal/pause, then its API probe sent `play`
  instead of supported `resume`; the UI already maps that correctly. R2 uses the
  real Play button; no production fix required. Both runs restored preferences
  and original playback, closed debug listeners and retained raw private evidence.

Paused/muted/unavailable Wave has no floating caption: the facade darkens while
its target and global Quick controls retain player access. The accessible name
includes station, playback state and Expand/Collapse. This is an explicit
immersive-scene discoverability tradeoff.

Native CDP touch is injected input, not physical-finger/acoustic acceptance.
Approximately1.01MiB decoded assets is a bounded budget, not a sustained Pi
CPU/GPU/frame-rate certification. All30 complete product criteria remain OPEN.
