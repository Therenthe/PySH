# Grounded city and destination entrances

Original PySH geometry, derived from the preserved `city-v3/pysh-city-v3.blend`.
No downloaded models, textures or copied scene imagery. Blender5.2.2 LTS;
offline EEVEE renders keep a live3D context off the Pi. The editable master is
`city-destinations.blend`; the portable builder is
`scripts/blender/build_city_destinations.py`.

## Architecture and image contract

The orthographic camera and existing radio/Bluetooth/Wi-Fi anchors are unchanged.
The district continues beyond both viewport edges. A real ground mass, street
deck, railbed, sleepers, retaining wall and piers occupy the old transparent
foundation strip. Foreground side abutments are separate renders so the moving
train passes behind actual masonry, instead of appearing through an edge.

`gothic-city-{day|night}-v4.png` and
`gothic-city-rail-front-{day|night}-v4.png` are1600×570 transparent-sky renders.
At runtime both use the same800×208 city rectangle; paint rail-front after the
train. Bottom eight source rows are fully opaque. The selected retaining-wall
iteration follows comparison against a simpler platform treatment; raw previews
and controlled native-scale comparisons remain private.

`metro-v4.png` trims empty padding from the prior genuine Blender vehicle render,
preserving every visible RGBA pixel and the complete alpha channel. Fully
transparent RGB is normalized to zero. Its449×60 crop preserves the old visible
vehicle size,82.690833×11.05px at800×480. Use width10.33635417% of the viewport and
track bottom14.99378383% of the208px city. The visible front wheel baseline is
448.81293px down the full480px viewport, aligned with the closest rail. The old
21 transparent bottom rows must not be counted as wheel height. Travel uses
the full viewport distance rather than600% of the narrower trimmed image.

## Entrances and motion

Five portals lead into the existing destinations: Cinema/Media, Audio/Bluetooth,
central control tower/Settings, Radio and Wi-Fi/Internet. Their3D annexes stand
in front of the preserved shop awnings. Each has keyed double doors, a distinct
canopy/pilaster treatment and a recognizable sign or a closed3D gear. No device
connection or audio-state signal is recorded into a movie.

A final material pass makes AUDIO/RADIO/Wi-Fi lettering softly ivory at night.
Home lights all three architectural signs; a doorway journey favors its selected
sign. These are steady building materials, separate from live rooftop emissions.
Day lettering retains the original brass inputs. Other night journeys and all
day clips remain byte-identical through that bounded refinement.

`city-entry-{media|audio|settings|radio|network}-{day|night}-v1.webm` contains
60 Blender frames,24fps,2.5seconds,800×480, VP8 alpha and no audio. The perspective
camera approaches the correct doorway with moving cars, metro and walkers.
Transparent sky preserves the actual live weather/celestial scene. The ending
is an opaque dark vestibule; destination UI supplies its own short release.
Native decoder/navigation acceptance remains a separate application gate.

The master contains `JourneyCamera_<id>` cameras and preserved door actions.
Its `journey_actions_json` scene property maps each camera/door recipe. The main
camera is left orthographic for Home review; animated actors are hidden there
to avoid recording a second stationary train into the Home image. The builder
enables the actors and selects the matching door recipe during movie exports.

## Rebuild

Run an existing Blender executable in factory/headless mode with
`--python-exit-code 1 -P scripts/blender/build_city_destinations.py -- --root <repo>`.
Use `--preview-only --variant platform` and then `--preview-only --variant retaining`
for comparison. Final export uses `--variant retaining --ffmpeg <existing-full-ffmpeg>`.
The encoder needs PNG/image2 decoding and libvpx VP8 alpha; no encoder is bundled.
`--destinations media,audio,network,settings,radio` can limit a regeneration.
After the initial complete export, `--destinations audio,radio,network --palettes night`
rebuilds only those three night clips and the night city while retaining every
camera recipe and the complete manifest. The master uses portable `//renders/`
output paths.

Then run `review_city_destinations.py` in factory/headless Blender with the same
`--root` and `--ffmpeg` arguments. It reopens the saved master, verifies all five
camera trajectories against the scene BVH and target-door rays, gates the closed
parts, and force-decodes all ten clips with libvpx to inspect actual alpha.

`mesh-audit.json` records newly authored closed-prop gate results. The original
city's independent architectural audit remains in `city-v3/`. `build-report.json`
records hashes, camera trajectories, measured anchors and the runtime alignment
contract; raw render frames, full per-part checks and machine paths stay private.
