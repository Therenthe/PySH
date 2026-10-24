# Rooftop service beacons

Original Blender 5.2.2 geometry for the fixed PySH city camera. These props replace
the small flat Bluetooth symbol and tiny radio roof point. They do not change
the city, radio facade neon, sky, weather or saved Home arrangement.

The radio transmitter is a tapered four-legged steel mast with five levels of
cross-bracing, two crossarms/dipoles and an obstruction-lamp housing. It mounts
at world 3.0/0.64/z6.09 and reaches z8.28, giving roughly44px native height above
its crown attachment. A localized cool rooftop practical makes the steel and
cross-braces legible at night without washing the skyline. Transmission arcs
are closed Blender tube geometry, rendered independently from hardware.

Bluetooth is a physical beveled dark lightbox with an extruded bind-rune,
rooftop bracket/posts and separate blue/cyan glyph, status practical and arcs.
The dark housing provides contrast against pale daytime fog. The housing reads
approximately28px wide at the native city scale; it is geometry, not a web UI
badge or SVG. Its mounting follows the unchanged Bluetooth landmark roof.

## Placement and runtime contract

All six PNGs share the original1600×570 camera and transparent alpha. Each prop
has one shared crop for its day, night and emission images; `layout.json` is the
exact placement contract. Scale it within the existing208px-high city container.

| Prop | Crop x/y/w/h | CSS left/top/width/height |
|---|---|---|
| Bluetooth |290/45/114/105|18.125% /7.894736842% /7.125% /18.421052632%|
| Radio |908/9/119/151|56.75% /1.578947368% /7.4375% /26.491228070%|

Runtime assets are `city-beacon-{bluetooth,radio}-{day,night,emission}-v1.png`.
The parent must gate Bluetooth emission by real powered/connected status and
radio emission by actual radio playback. Powered idle and connected must remain
distinct, and Off/unknown must not invent a connection. Emission images support
a slow, restrained opacity pulse; source material keys show that animation
intent over97frames at24fps. There is no baked automatic playback state.
Reduced motion must remain static, hidden/offscreen animation must stop, and
decorative props must remain pointer-transparent and hidden from screen readers.

These service indicators are composited after the foreground weather veil by
the UI integration. Heavy fog still affects the architecture behind them.
Do not apply the city's haze opacity to these independent signal layers again:
that was the original observed visibility failure. The source does not invent
different weather or erase the meteorological scene.

## Reproduction and review

Run `scripts/blender/build_city_beacons.py` with headless factory Blender and
`--python-exit-code 1`, then `-- --root <repository>`. Optional `--audit-scripts`
selects the installed expert skill's audit helper directory. Default is64samples;
`--preview` uses32samples. Original city source and its hash are checked unchanged.

Editable source: `city-service-beacons.blend`. Every separately mounted closed
prop is audited with the render delivery profile:55parts,3200vertices,
4612triangles, zero errors or warnings. Independent parts intentionally remain
separate; this is not a watertight assembly or a3D-print export.

Six PNGs total45,008 encoded bytes and359,268 decoded RGBA bytes. PNG data retains
rendered straight alpha through the shared lossless encoder. A small localized
halo is baked offline; no runtime Blender, WebGL or blur is introduced.

The author and independent visual reviewer inspected native800×208 night/day
and strong-fog composites. First night review found dark mast edges; the local
rooftop practical corrected this before final64sample output. Final night-clear
and night-fog review found cross-braces readable, a mounted BT housing and no
blocking asset defect. Fullcity/native composites are retained privately in the
dated build review folder; they are controlled asset composites, not actual
Raspberry screenshots. Final integrated browser/device evidence remains separate.
