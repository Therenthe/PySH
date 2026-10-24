# Radio facade neon

Original Blender geometry for the existing city-v2 radio landmark (building 10,
world center 3.0/0.64, width 1.7, height 5.3). The city scene, raster city, camera,
roof/antenna anchors and all sky assets are preserved. No downloaded geometry,
textures or web fonts are used.

Three continuous tubular waves are mounted across studio-floor bays. Corner
returns, lower/upper cornices and the three art-deco crown setbacks attach the
illumination to the building. Cyan/mint carry most of the facade, with restrained
violet and amber. The PNGs bake a short local halo; they do not require live blur
or 3D rendering on Raspberry Pi. That halo approximates practical spill, rather
than dynamically relighting the unchanged city raster.

## Runtime contract

`layout.json` specifies the common 118×281 crop at 909/136 in the existing
1600×570 city image. All eight zone PNGs share that exact crop, so independent
opacity changes cannot shift their architectural alignment. Scale both axes
with the existing city container, including its 208px native height.

- `radio-neon-zone-01.png` through `radio-neon-zone-08.png` are the runtime assets.
- Each zone represents one adjacent pair of the 16 measured temporal audio bins.
  These are waveform-envelope samples, **not frequency bands**.
- Runtime intensity must come from fresh real playback data. These assets do
  not contain an automatic motion cycle. Silence, unavailable data, paused
  playback and reduced motion are integration responsibilities.
- Suggested night gain 1.0 and day gain 0.20 are recorded in the layout. They are
  presentation gains; they must not invent activity when signal is absent.
- Encoded total 32097 bytes; decoded RGBA 1061056 bytes (approximately 1.01MiB).
  No runtime filter, animated texture atlas or WebGL context is needed.

The source contains eight separately named zone collections, 45 closed mounted
tubes, 4784 vertices and 7948 triangles, eight authored emissive materials and eight
local practical lights. Its 25-frame light-energy keys are **authoring intent
samples only**, not a runtime animation or an audio-analysis claim.

## Reproduction and evidence

Run the repository builder through Blender 5.2.2 LTS with factory startup and
`--python-exit-code 1`, passing `--root` with the repository directory. The script
opens the unchanged `pysh-gothic-city-v2.blend`, creates its own overlay scene,
renders every zone, bakes the local alpha halo and saves editable source here.
The final PNG encoder preserves straight alpha and the rendered display RGB;
Blender generated-float image saving otherwise unpremultiplied low-alpha pixels
a second time in this version, whitening the original trial output. That trial
was corrected before delivery.

`build-report.json` records exact asset/source/builder hashes and crop budgets.
`mesh-audit.json` contains the render-profile delivery results for each separately
mounted closed tube: all 45 passed, with zero errors and zero warnings. The
separate-part gate is deliberate: architectural spacing between independently
mounted light fixtures is not a watertight assembly requirement.

`facade-review.png` and `city-neon-review.png` are full-intensity inspection
renders, not additional runtime downloads. `all-zones-overlay.png` is a review
composite. Both author and independent visual reviewer inspected low/mid/high
night and subdued day composites at 800×208, plus full 1600×570 and facade crop.
The review found no blocking asset defect: stone/window detail and skyline remain
legible; light stays attached to the facade without a large glow cloud. Browser,
actual measured-signal behavior and sustained/native performance are separate
integration acceptance steps.
