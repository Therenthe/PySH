# Original PySH ambient assets

`pysh-gothic-city-v1.blend` is editable Blender 5.2.2 LTS source. All geometry and
materials are authored by `scripts/blender/build_ambient_city.py`, seed 231026;
there are no downloaded meshes, photographic textures, logos or external files.
The visual reference is an original nocturnal gothic/art-deco metropolis, not a
reproduction of licensed movie artwork. No superheroes are present.

The model uses 12 city material batches, 10,667 base vertices and 7,583 base
polygons. Stone has small authored bevels and procedural material variation.
Day/night illumination is baked into transparent 1600×570 PNGs. A separate
Blender-authored metro prop has linear passage keys at 24 fps; the UI composites
that prop along the same quiet 43-second presentation beat. The radio and
Bluetooth markers are anchored to camera-projected roof coordinates in
`build-report.json`; their states come from the real hub API.

Weather drop, six-arm snow crystal, ice, three warning-funnel frames and flood
ripple are independently rendered Blender scenes in the same `.blend`. The
frontend moves the flat sprites; it does not run a 3D engine on the Pi.

Regenerate from the repository root (substitute your Blender executable):

```sh
blender -b --factory-startup --python-exit-code 1 \
  -P scripts/blender/build_ambient_city.py -- --root /absolute/repository
```

For the installed Scenario Blender expert/lighting skills, the optional review
script produces a front/three-quarter/side silhouette and matcap review sheet,
mesh audits, color audit and independent closed weather-prop delivery gates:

```sh
blender -b --factory-startup --python-exit-code 1 \
  -P scripts/blender/review_ambient_city.py -- \
  --root /absolute/repository --skills-root /absolute/installed/skills
```

The source does not include a sky or stars. PySH's original 170 SVG stars, Moon
phase and celestial position calculation remain separate and unchanged.

Severe weather graphics are **warning illustrations**, not a live view or an
assertion that a disaster is happening at the selected address. Only an explicit
current, sourced severe/extreme warning for flood/rain-flood or tornado enables
them. Ordinary WMO rain/wind codes never imply a flood, tornado or alert. Missing,
stale, future and expired warnings cannot enable these illustrations.

Observed local QA: Blender color audit empty; city mesh audit found no zero-area
faces, loose vertices/edges or flipped faces. The independent closed rain/ice
props passed the render-profile delivery gate. Architectural islands and open
window/viaduct planes are intentional for this offline scene; the city is not
claimed to be a watertight print or exported game asset. Runtime resource and
physical display acceptance must be measured on Raspberry separately.
