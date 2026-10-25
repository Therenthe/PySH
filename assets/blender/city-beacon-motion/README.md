# Bluetooth turn and router-free Wi-Fi waves

The Bluetooth rune performs a genuine Blender rotation around its vertical
world-Z axis. Its closed tubes, bevel, depth and lighting turn through front,
quarter, edge and reverse views; this is not a flat image scaled or mirrored
with CSS. A second rear luminous tube makes it a designed double-sided sign.
The roof foot and posts remain fixed. There is no solid rectangle behind it.

The Wi-Fi prop contains only three closed, curved wave-band meshes above the
existing roof. No router cabinet, aerial hardware or association dot/lamp is
rendered in these new assets. Existing city geometry and old assets are retained.

## Bluetooth runtime contract

- Unchanged full-city resolution: **1600 × 570**.
- Unchanged wrapper crop: **x290, y45, width114, height105**.
- Glyph-only tile: **x322, y56, width50, height77** in the full city.
- Tile offset within that wrapper: **x32, y11**.
- Four horizontal atlases: **1600 × 77**, with **32 columns × 1 row**.
- Duration: **3.2 seconds**, using **31 steps** from the first to final frame.
- First and last tiles are the exact same front image; the angular path eases
  into and out of a complete 360° turn.

Atlas files are `city-bluetooth-turn-{day,night}-{idle,connected}-v1.png`.
Fixed-support files are `city-bluetooth-support-{day,night}-motion-v1.png`.
The latter retain the complete114 × 105 wrapper crop.

Within the wrapper, the tile occupies left28.07017544%, top10.47619048%,
width43.85964912%, height73.33333333%. A horizontal atlas background sized
3200% × 100%, with x-position0%→100% in31steps, traverses the32poses. Alternatively
select the corresponding integer tile by explicit frame index. `layout.json`
records exact integer bounds, angular poses and filenames.

Use frame0 as the normal front poster. The integration owner schedules an
occasional turn only while powered and visible, resets safely on state/palette
change, and keeps frame0 for reduced motion. Idle and connected atlases must
follow the real service state. Off/unknown must not invent an active connection.

Replace the old hardware/core images when using these atlases: the old hardware
includes a static rune that would otherwise ghost behind the turning glyph.
The existing three BT wave-band layers remain independent and can continue
their state-dependent progression while the physical rune turns.

## Wi-Fi runtime contract

The existing crop is preserved: **x1116, y153, width73, height89**, within
1600 × 570. The original roof anchor is world6.3/0.4/z4.58; wave center remains
world6.3/0.295/z5.24.

Six files: `city-wifi-wave-{1,2,3}-{day,night}-motion-v1.png`.
Each contains one closed Blender wave band, allowing inner→middle→outer opacity
sequencing. Day uses dark teal for pale sky/fog contrast; night uses restrained
sage emission. Router hardware and the old CSS association dot must be removed
by integration. A saved association without the active Wi-Fi route must not
emit transmission waves; connecting/search is a separate optional state.

## Source, budget and review

Editable source: `bluetooth-turn-wifi-waves.blend`.
Reproducer: `scripts/blender/build_city_beacon_motion.py`, run with headless
factory Blender and `--python-exit-code 1`, then `-- --root <repository>`.
Default render quality is64samples. Optional `--preview` uses24; optional
`--audit-scripts` selects the installed expert skill's audit-helper directory.

The source keys32 angular poses over78 scene frames at24fps, with a nominal
3.2-second runtime. The geometry itself is rendered at each pose. The duplicate
360° endpoint is locked to the identical first rendered tile to eliminate small
temporal anti-aliasing differences on return to rest. The supports have no
animated transform. The source's independent state meshes have no account or
live service data and do not imply a real connection by themselves.

Twelve runtime PNGs total **357,158 encoded bytes** and **2,222,888 decoded RGBA
bytes**. Four atlases contribute1,971,200 decoded bytes. Atlas width stays below
2048px. No runtime Blender, WebGL or mesh renderer is required.

Nine individually closed props contain **708 vertices / 1,220 triangles**.
All render-profile delivery gates pass with zero errors and zero warnings.
`build-report.json` records image hashes, source/build hashes and budgets;
`mesh-audit.json` retains the per-part gates. The original open-beacon source's
bytes are checked unchanged after generation.

Author review includes full800 × 480 compositions using the original city-v3
day/night raster and unchanged object scale: front, quarter, near-edge, reverse,
opposite quarter and exact returned-front poses, with clear and controlled fog
variants. Review images are retained privately. These are asset compositions,
not actual app screenshots, actual weather claims or physical-device acceptance.

Root integration must independently verify schedule, state gates, hidden/offscreen
lifecycle, reduced motion, palette changes, final full UI and actual Pi behavior.
