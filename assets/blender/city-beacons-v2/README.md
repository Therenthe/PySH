# Open rooftop beacons — v2

Original Blender geometry and materials for the installed Dark Deco city camera.
The Bluetooth lightbox and its solid glass rectangle have been removed entirely
from the rendered prop. A standalone extruded rune has a narrow sculpted metal
understroke and roof supports; there is no filled logo background or UI badge.
The existing radio lattice, dipoles and roof attachment are preserved.

The daytime palette is dark cobalt for Bluetooth and dark teal for radio waves,
so they remain legible against pale fog. Night uses cyan/sage emission with a
small localized baked halo. Day has no broad halo. These are separately rendered
Blender materials, not CSS recoloring or painted icon substitutes.

## Runtime assets

Twenty PNGs are split into five layers per prop and two lighting conditions:

`city-beacon-{bluetooth,radio}-{part}-{day,night}-v2.png`

`part` is one of `hardware`, `core`, `ring-1`, `ring-2`, `ring-3`.

- `hardware`: unlit physical rune/support or radio mast, without active waves.
- `core`: illuminated Bluetooth rune, or radio tip beacon only.
- `ring-1` through `ring-3`: independent inner/middle/outer paired wave bands.
  Each band contains the matching left/right wave tubes authored in Blender.

All layers share the exact previous crop, with no anchor or city movement:

| Prop | Crop x/y/w/h in1600×570 | CSS left/top/width/height |
|---|---|---|
| Bluetooth |290/45/114/105|18.125% /7.894736842% /7.125% /18.421052632%|
| Radio |908/9/119/151|56.75% /1.578947368% /7.4375% /26.491228070%|

`layout.json` is the machine-readable placement contract. Scale within the
existing208px city container. Geometry projection is checked to remain inside
these crops with at least2px padding. The wave tubes have been reauthored thick
enough to survive native800px-wide rendering.

Runtime must gate the layers by real powered/connected/playing state. It can
sequence ring opacity inner→middle→outer while retaining a visible low-opacity
baseline; inactive states must not imply a live connection. Reduced motion must
show a stable state, and hidden/offscreen animation must stop. These service
waves represent connection/playback status, not frequency measurements or an
invented audio signal. Radio facade PCM visualization remains a separate asset.

The editable source includes separate ring controls and a97-frame authoring
sequence demonstrating restrained staggered outward motion around each actual
signal origin. That source animation is intent evidence, not a runtime atlas or
an automatic claim of service activity. Browser opacity/state behavior requires
its own integration tests.

## Source and reproduction

Editable scene: `open-service-beacons-v2.blend`.

Run `scripts/blender/build_city_beacons_v2.py` through headless factory Blender
with `--python-exit-code 1`, followed by `-- --root <repository>`.
Default output uses64samples; `--preview` uses24. Optional `--audit-scripts`
selects the installed Blender expert skill's audit-helper directory.
The builder reuses the original radio-mast construction helper and the shared
straight-alpha PNG encoder; old source files, city, camera and v1 PNGs are kept.

Final geometry:54 closed render parts,4,072 vertices and6,296 triangles. Every
part passes the render delivery audit with zero errors and warnings. Separate
mounts and tubes are intentionally not a watertight assembly or print export.
The original city-v2 source hash remains unchanged. `build-report.json` records
exact runtime image hashes, palette, builder hash and budgets.

Twenty PNGs total58,690 encoded bytes and1,197,560 decoded RGBA bytes. No runtime
Blender, WebGL, texture atlas or expensive filter is required for these props.

## Review and limits

Author and independent reviewer inspected native800×208 day/night fog drafts:
the free-standing rune is recognizable and the three paired rings read without
a rectangular background. The final64sample iteration lifts day chroma slightly
and narrows the physical underline while preserving dark silhouette contrast.
Private review renders retain clear/fog, connected/idle and combined radio
facade/beacon compositions. Combined facade levels are controlled illustrative
inputs, not captured audio or actual Raspberry screenshots.

Actual application placement, animation sequencing, current weather composition,
physical touch and sustained Pi performance remain separate acceptance steps.
