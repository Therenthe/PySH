# Blender sky refinement — 23 October 2026

Scope: the visible sky elements above the Blender city, following the preserved
VariantaBack baseline. The source is
`assets/blender/sky3d/pysh-ambient-sky-v1.blend`; rebuild/review instructions and
NASA attribution are in that directory's README. No device clock, location,
weather data, account profile, preference or radio state was changed for fixtures.

## Delivered source and runtime contract

- Actual Blender geometry/material/light renders for Moon, Sun, asymmetric cloud
  volumes, airliner, glider, star optical cores/glints and the tapered meteor.
- 128 Moon lighting phases, retaining continuous application phase metadata and
  existing astronomical position/horizon/day-night gates. Maximum phase-atlas
  illumination rounding below 1.23 percentage points. The surface reference is
  projected NASA imagery, not measured lunar topography/current libration.
- Exactly 170 original sparse star centres retained. Five bright glints; no dense
  photographic star texture. Daytime continues to exclude Moon/stars.
- Correct aircraft sweep and projected wingtip navigation lights. All glider tips
  fit inside the raster. Random scheduling and direction remain application-owned.
- Weather-dependent cloud coverage; no cloud visibility claimed for clear/unknown
  weather. Slow transforms only; reduced-motion disables cloud/glint/light motion.
- Ten PNGs total 2,170,363 bytes; decoded RGBA pixel upper bound 12,931,072 bytes
  (12.33MiB), shared between repeated instances. No runtime WebGL or live volumes.

## Verification

`scripts/blender/review_ambient_sky.py` used the installed Blender expert and
lighting review tools against Blender 5.2.2 LTS.38 independent render-prop gates
passed. Audits found zero zero-area faces, loose vertices, flipped faces or color
space flags. Aircraft silhouettes/matcaps were inspected from top/front/three
quarter views. Earlier inward-facing mirrored wings were corrected before this
result; Moon relief uses a separate Non-Color texture input.

`tests/e2e/blender-sky.spec.ts`:24 passed in EN/RO at 800×480. This includes seven
seasonal/celestial fixture captures, waxing and waning Moon orientation/metadata,
the continuous-to-atlas illumination bound, a real Sun limb/alpha pixel check,
reduced-motion handling and actual integrated Home styles. The latter caught and
now protects against legacy `.ambient-moon{background:none}` hiding the new atlas.
The new selector wins the real application cascade.

Direct PNG reviews initially rejected round cloud chains, sooty daylight fill,
grainy transparent edges and a stochastic Sun halo. The final cloud uses outdoor
sky fill and a premultiplied offline Blender alpha finish; the Sun has a quiet
deterministic alpha corona. Independent review requested neutral/brighter lunar
illumination and a pale Sun core; both were revised and recaptured. The auditor
then found no remaining major visual blocker in the final day/night/waxing/
overcast fixtures. Minor future polish: repeated mirrored cloud silhouettes can
still be recognized; daytime city Bluetooth marker contrast remains subtle.

Private local evidence (not release assets): `.runtime/blender-sky-review/`,
`.runtime/blender-sky-refined-20261023/`, and the shortened 800×480 previews
`.runtime/sky3d-preview-{night,day,waxing,overcast}.png`.

This is browser/source verification. Native Raspberry performance, final physical
display approval and whole-product acceptance remain separate checks. No numeric
quality score or complete product acceptance is claimed here.
