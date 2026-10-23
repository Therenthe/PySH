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
