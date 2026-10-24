# Daylight radio facade

This is a separate Blender material variant of the existing radio neon facade.
All 45 original tube meshes, their positions, the city camera and the common
118×281 crop at 909/136 in the 1600×570 source image are retained. The eight night
PNGs and original `radio-neon-wrap.blend` are protected by hashes during every
build and are never written by this builder.

Dark teal, cobalt, plum and brass materials replace the pale night emission for
daylight. A soft area key exposes the physical tube surfaces. Emission is only
0.28, with a 0.7px local alpha halo capped at 0.12; there is no large bloom cloud,
backing rectangle or new signboard. This allows the mounted wave and corner
fixtures to contrast with stone and fog without a second day opacity reduction.

The eight runtime PNGs total **18,704 bytes encoded** and **1,061,056 bytes decoded**.
Runtime selects either these eight layers or the existing eight night layers;
it does not need to decode both sets for simultaneous display. Material changes
do not alter audio semantics: each zone remains one adjacent pair of the 16 real
temporal PCM samples. Pause, silence, mute, stale/unavailable signal, scene
visibility and reduced-motion behavior remain application responsibilities. No
synthetic audio values or automatic light cycle are baked into these files.

Rebuild with `scripts/blender/build_radio_neon_day.py` under Blender 5.2.2 LTS,
headless, factory startup and `--python-exit-code 1`, passing `--root REPO`.
The optional `--audit-scripts` points to the installed Blender expert audit tools.
Only this source directory, the eight runtime PNGs and private ignored evidence
directories are written. The two measured 800×208 inspection images remain here;
other authoring previews are routed to the ignored
`.runtime/radio-bt-20261024/day-authoring-review` directory.

The editable source is `radio-neon-day.blend`; `build-report.json` records
palette, exact hashes, original-source protection, geometry counts and budget.
`mesh-audit.json` contains all 45 separate closed-prop render gates: zero errors
and warnings, with 4,784 vertices and 7,948 triangles retained.

Review images use the current city-v3 day raster and documented sample levels.
The `measured` name denotes illustrative opacity values around the square root
of the observed 0.35–0.39 PCM amplitudes, rather than a captured device frame.
The fog image uses a documented illustrative veil; it does not claim a current
weather observation. The native-sized 800×208 reviews are inspection evidence,
not runtime assets. Actual browser/device signal visibility requires a separate
runtime check with the current provider weather and live PCM data.
