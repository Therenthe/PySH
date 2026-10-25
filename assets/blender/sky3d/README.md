# Blender sky source

The editable `pysh-ambient-sky-v1.blend` and `scripts/blender/build_ambient_sky.py`
author the Moon, Sun, cloud volumes, aircraft, star glints and meteor streak in
Blender 5.2.2 LTS. The browser displays transparent rendered sprites; it does not
run Blender, WebGL or volumetric ray marching on Raspberry Pi.

The established 170 sparse star centres, real weather selection, astronomical
positions, day/night gates, random event scheduling and reduced-motion preference
remain application responsibilities. No photographic star field is added. The
source models and cloud noise are original project work, with a fixed seed 231127.

## Moon reference and phase precision

The sphere reuses the existing NASA SVS / Ernie Wright Moon surface reference.
Source: [NASA SVS 4537](https://svs.gsfc.nasa.gov/4537/), with the exact original
image, SHA-256 and NASA usage terms recorded in
[the repository credit](../../../docs/licenses/moon-surface-nasa.md).
The reference image is packed in the `.blend`. This is a projected surface
reference, not a measured lunar topography or libration model.

The atlas contains 128 rendered lighting phases, 16 columns by 8 rows, 144px per tile.
Frame 0=new, 32=waxing half, 64=full, 96=waning half. Application metadata keeps the
existing continuous phase; sprite selection rounds the lighting angle with a
maximum illuminated-fraction error below 1.23 percentage points. Dim earthshine
keeps the unlit limb dark blue-grey. It does not change the phase calculation.

## Runtime budget and rendering

The Moon atlas is 2304×1152; each cloud sprite 768×256; aircraft 256×128;
the four star sprites share 96×96; Sun 192×192; meteor 256×32. Ten PNG files are
shared between repeated instances, with about 13MiB of total decoded RGBA pixel
data. Render dimensions and projected aircraft anchor coordinates are recorded in
`build-report.json`; the source `.blend` is an authoring artifact, not shipped to
the device's browser bundle.

Clouds use asymmetric three-dimensional water-droplet volumes, a flattened base,
smooth radial density falloff, procedural density variation and separate Sun/sky
and Moon/sky lighting. Cycles 96 samples with denoising and a small offline alpha
finish produce the two sprites. Their runtime motion uses slow transforms only.
The airliner has swept wings, engines and separate tail surfaces; the glider has
longer wings and no engines. Wingtip lights use camera-projected mesh anchors.

## Rebuild and review

Run from the repository root, using an installed Blender 5.2 binary:

```text
blender -b --factory-startup --python-exit-code 1 -P scripts/blender/build_ambient_sky.py -- --root ABSOLUTE_REPO
blender -b --factory-startup --python-exit-code 1 -P scripts/blender/review_ambient_sky.py -- --root ABSOLUTE_REPO --skills-root ABSOLUTE_SKILLS
```

The renderer requires access to the existing local NASA reference. The review writes
per-prop render gates, topology/color audits and multi-view aircraft review sheets
to `.runtime/blender-sky-review`. These private artifacts are not release assets.
The browser tests in `tests/e2e/blender-sky.spec.ts` capture seasonal 800×480
fixtures and check the real Home CSS cascade. Aircraft/celestial/meteor tests also
sample the actual rendered pixel geometry, not only filenames or metadata.
