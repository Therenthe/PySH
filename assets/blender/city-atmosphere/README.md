# City atmosphere and return journeys

Original scene work in Blender5.2.2 LTS, derived from the preserved
`../city-destinations/city-destinations.blend`. Existing city/entry/metro assets
are not overwritten. These are offline assets for Chromium on Raspberry Pi;
there is no live Blender or WebGL scene on the appliance.

## Runtime assets

- `gothic-city-{day,night}-unlit-v1.png`:1600×570 baseplates, exact city-v4
  orthographic camera and opaque support/ground, with occupied windows unlit.
- `city-window-bank-{0,1,2}-v1.png`: three aligned transparent emission passes
  containing153 connected original window-pane components (47/61/45). The
  original warm/cool occupancy palette is retained. Foreground city holdouts
  prevent light leaking through other buildings. Runtime solar time controls
  each bank; neither an arbitrary UI theme nor a baked timer invents sunset.
- `city-road-wet-{day,night}-v1.png`: aligned physical asphalt/water reflections,
  rendered in Cycles and clipped by an actual Blender visibility mask to the
  existing deck footprint. No sky, structural geometry or service state is
  painted into these layers. Maximum encoded alpha is0.70; runtime precipitation
  intensity further attenuates it. A thin foreground pavement needs a motivated
  lighting cheat: raised transit objects remain camera-opaque but are excluded
  only from glossy rays, and existing practical/window reflection strength is
  favored1.8× at night. This reveals narrow warm/cool streaks rather than a mirror
  of whole buildings or a global glow. R1/R2 were too quiet; the selected R3
  uses the same geometry/mask with this controlled reflection-ray treatment.
- `city-exit-{media,audio,settings,radio,network}-{day,night}-v1.webm`: ten local,
  silent VP8-alpha clips,800×480,24fps,60 frames/2.5seconds. The camera returns through the matching portal and its door hinges close;
  cars, train and walk cycles advance forward in time.
  Each starts inside its opaque vestibule, pulls out of the matching entrance
  and ends with transparent sky and solid ground. The initial near-black
  vestibule lasts at most5 frames (208ms), not a long black loading scene.

The editable master preserves five return camera actions plus the original
entry actions. `return_actions_json` records the corresponding camera and door
recipes; the Home camera remains the unchanged city-v4 orthographic view.
Geometry-only illumination demo layers are hidden by default. Return renders
use a constant1:1.3701923 pixel aspect throughout the shot, matching Home’s
1600×570→800×208 display mapping; FFmpeg normalizes encoded SAR to1:1.
The final far-perspective projector settles onto the exact Home camera basis,
with a6.661875-unit camera-up offset. Lens/distance increase together; animated
near/far planes retain depth precision. There is no last-frame projection-type
switch or late vertical image warp. The initial return iteration exposed a
57.72px skyline jump; the corrected projection is checked against Home geometry
at both frames59 and60 for every destination (maximum tolerance2px). Camera/door
selection is explicit when authoring; selecting a camera alone does not select
all matching door actions.

## Rebuild and verify

Run from the repository root using installed Blender and a full FFmpeg build
with PNG sequence input, libvpx VP8-alpha encoding and decoding. The reduced
Playwright FFmpeg binary does not accept PNG sequence input. No download or
runtime dependency is required by this authoring recipe.

```powershell
& '<Blender>/blender.exe' -b --factory-startup --python-exit-code 1 -P scripts/blender/build_city_atmosphere.py -- --root . --mode preview --destinations media --palettes day,night --samples 12
& '<Blender>/blender.exe' -b --factory-startup --python-exit-code 1 -P scripts/blender/build_city_atmosphere.py -- --root . --mode exits --samples 24 --ffmpeg '<FFmpeg>/ffmpeg.exe'
& '<Blender>/blender.exe' -b --factory-startup --python-exit-code 1 -P scripts/blender/build_city_atmosphere.py -- --root . --mode plates --samples 32
& '<Blender>/blender.exe' -b --factory-startup --python-exit-code 1 -P scripts/blender/build_city_atmosphere.py -- --root . --mode audit --ffmpeg '<FFmpeg>/ffmpeg.exe'
```

The preview stage is reviewed before the full export. `exits` deliberately
requires all five destinations and both palettes so it cannot silently replace
a complete editable master with a partial one. `plates` adds/replaces only its
owned overlay geometry in that saved master. Sources, settings and files from
other Blender projects remain untouched. Raw frames, review comparisons,
encoding logs and per-part evidence remain private in `.runtime/`.

`build-report.json` records final asset hashes, fully decoded frames/alpha,
all300 saved camera-position comparisons, full-scene Home handoff geometry
checks, forward-world-time actor checks, per-pane/new-floor
render gates and preserved source identity. It is not native touchscreen,
Raspberry decoding or whole-product acceptance; those gates belong to delivery.

Each emission bank is intentionally an atlas of detached panes. The mesh gate
checks153 connected original panes separately plus the one closed wet-road
solid; treating all windows as one watertight building would misclassify the
intentional spacing as floating fragments. The first aggregate probe and its
classification are retained privately.

The aligned export’s first master assembly hit Blender’s library overwrite
guard; completed full-render frames and encodes were retained. Assembly now
imports overlay geometry from an owned private copy, asserts fully local IDs
and removes the empty source-library metadata before saving. The recovered
master and every retained movie were then independently gated from disk.
