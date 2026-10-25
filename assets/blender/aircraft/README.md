# Ambient aircraft miniatures

Five original meshes authored in Blender 5.2.2 LTS and rendered with EEVEE/AgX.
No downloaded models, airline logos or live aircraft tracking. These are decorative
miniatures, not representations of traffic near the selected weather location.

| Variant | Identifying geometry | Mesh vertices / polygons |
| --- | --- | --- |
| Airliner | Slender pressure fuselage, swept low wings, two underwing turbofans, conventional fin | 6,744 / 7,204 |
| Turboprop | High straight wing, twin propellers, tall T-tail, shorter regional cabin | 4,414 / 4,620 |
| Business jet | Narrow cabin, swept wings, rear engines, compact T-tail and winglets | 4,552 / 4,836 |
| TV helicopter | Compact saffron/white cabin, slung gyro camera, microwave dish, skids | 2,632 / 2,598 |
| Police helicopter | Larger blue/white cabin, blue beacon, warm searchlight lens, sensor gimbal | 2,866 / 2,868 |

The models are intentionally three-dimensional render assemblies with intersecting
closed parts. They are not watertight printable or optimized game-engine exports.
Each part **and each complete aircraft assembly** passed `bx_audit.deliverable`
with the `render` profile: zero errors and zero warnings. Side/top/three-quarter
silhouette and matcap review sheets were inspected, followed by day/night sprites
at 160 and 96 pixels. Independent review of actual 800×480 browser scenes led to
stronger police livery/lens contrast and a larger TV camera before final rendering.
This is visual evidence, not a claim of physical Pi or performance acceptance.

## Rebuild

```sh
blender -b --factory-startup --python-exit-code 1 \
  -P scripts/blender/build_ambient_aircraft.py -- --root . --review
```

The review/audit helpers are from the locally installed
`scenario-blender-expert` skill under the current user's `.codex/skills` directory.
Review images stay in private `.runtime/aircraft-blender-review/`.
The script saves `pysh-aircraft-v1.blend`, the reproducible build report, PNGs under
`app/ui/public/ambient/aircraft/`, and generated synchronous projected light anchors
in `app/ui/src/aircraftAnchors.ts` (also available as `anchors-v1.json`).

## Raster contract and budget

- All canvases: transparent RGBA, **160×80**, nose facing **right**, top facing up.
- Reverse travel with a horizontal mirror only. Never rotate the entire craft 180°.
- Aircraft: `{airliner,turboprop,business-jet}-{day,night}-v1.png`.
- Helicopters: `{tv-helicopter,police-helicopter}-{day,night}-{0,1,2}-v1.png`.
  Three discrete physically modeled rotor orientations are baked into each craft.
  They suggest rotor motion; they are not a real rotor RPM simulation.
- **18 PNGs**, **921,600 decoded bytes** (900 KiB), about **175 KB encoded**.
  The builder asserts five variants, 18 sprites, no clipping, and less than 1 MiB
  decoded pixel storage. Exact hashes, byte sizes and alpha bounds are in the report.
- The Pi composites these Blender renders; it does not load Blender, meshes,
  WebGL, a 3D engine or per-frame lighting. Runtime motion remains separately tested.
