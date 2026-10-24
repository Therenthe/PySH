# Rooftop Wi-Fi access point

Original Blender 5.2.2 geometry, authored for the pitched roof at world
`(6.3, .4, 4.58)` in `../pysh-gothic-city-v1.blend`. The city camera and lighting
are reused; architecture and existing renders remain unchanged. The cabinet,
ventilation, aerials, mounting feet, three extruded signal arcs and association
lamp are editable in `pysh-city-wifi-v1.blend`. No downloaded models or add-ons.

Rebuild from the repository root:

```powershell
& '<Blender path>/blender.exe' -b --factory-startup --python-exit-code 1 -P scripts/blender/build_city_wifi.py -- --root .
```

Three transparent 73×89 RGBA crops use the source camera's exact raster bounds.
Combined decoded texture budget is 77,964 bytes (about 76 KiB); no runtime 3D
engine, continuous scripting loop, image request to a third party or new package.
Crop position and association-lamp coordinates are recorded in `build-report.json`.
All 16 prop meshes have zero loose vertices/edges, degenerate faces, flipped faces
or non-manifold edges in the installed Blender expert audit. Intentional assembled
parts are not a manifold printable whole. The exact 800×480 day/night scene is
reviewed through `tests/e2e/city-wifi.spec.ts`.

The roof shows **association**, separately from the current route: connected
standby is a steady lamp, actual Wi-Fi route adds gentle emissive arcs, connecting
uses a slow search cycle, disconnected/off/unknown never emit. These are decorative
local interface states, not a claim of Internet reachability or observed packets.
Reduced motion is static and hidden documents pause all decorative animation.
