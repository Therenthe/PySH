# Ambient aircraft refinement

## Scope and defect

The previous westbound aircraft rotated the entire asymmetric render by almost
180 degrees. Its nose led the path, but the aircraft was upside down. Existing
tests checked forward direction and swept wings without checking uprightness.
The replacement must mirror the horizontal direction while preserving its up
axis, with a small pitch derived from the actual scene aspect ratio.

The requested fleet comprises an airliner, turboprop, business jet, television
helicopter and police helicopter. They are original Blender3D models and lighting,
delivered as compact pre-rendered transparent assets for the Raspberry Pi.
Helicopters use a short baked rotor cycle and slower, lower flight paths.
Appearances are decorative; they do not indicate tracked flights or emergencies.

## Delivery gates

- Inspect each model from multiple angles and at the actual800×480 display scale.
- Distinct silhouettes, both travel directions upright, nose leading motion;
  neither mirrored day/night assets nor changed names count as different models.
- Verify geometry/render gates, encoded and decoded asset budgets, transparent
  frames and consistent rotor framing.
- Verify enabled/disabled, hidden/reduced-motion lifecycle, bounded scheduling,
  no immediate variant repeats, both themes and independent lunar effects.
- Publish and verify the candidate source before installing it; retain a readable
  checksummed PC backup, prior release, all preferences and network policy.
- Verify native asset hashes/decode, actual Home presentation and radio state;
  distinguish deterministic presentation fixtures from naturally scheduled events.

## Implemented and reviewed

Five original aircraft,18transparent160×80PNG renders:175082encoded bytes and
921600decoded bytes. Individual closed parts and all five complete assemblies
passed the Blender render delivery gate with zero errors and zero warnings.
The review found and repaired a T-tail joint gap, low police night contrast and
an insufficiently visible TV camera. Editable source, reproducible builder and
projected light/fin/rotor anchors are included alongside the renders.

The integration mirrors only the horizontal axis when reversing direction. Pitch
uses the current scene aspect ratio. A selected variant cannot immediately repeat;
at most one aircraft is scheduled, with a35–95second quiet gap after it exits.
Helicopters fly lower and slower with three baked rotor orientations and a subtle
vertical drift. Existing preference keys, lunar phase and lunar dust stay compatible.
RO now labels the shared aircraft option “Aeronave decorative”.

An independent auditor inspected20initial full800×480scenes and8revised helicopter
scenes, and passed23independent browser tests. The small ambient scale naturally
limits equipment detail; role is communicated chiefly by airframe and livery.
This is scoped visual evidence, not a numeric quality score or physical motion test.

## Installed candidate

Runtime`07493a5a387f` / canonical source`f91f4f9cd37c6c6bc36137ecaef6ef5bb5463b71`.619Python cases passed with32
platform skips;236affected browser cases passed on the frozen candidate in EN/RO.
TypeScript, Vite, repository inventory and runtime package passed. The integrated
fleet/settings checks and independent review also passed before freezing.
121extension/policy checks and3weather-icon checks passed on that same source.

After a separately verified readable PC backup, all103installed runtime hashes
and29preferences were verified. Native800×480 Home observed a naturally scheduled
upright airliner; all18fleet PNG hashes and decodes matched.
The genuine scheduled flight was paused at its CSS midpoint only for capture;
weather, time, variant and direction were not replaced with fixture values.
During that native flight,180requestAnimationFrame samples over roughly3seconds
had a16.7ms p95 interval. This measures brief browser scheduling, not physical
touch latency, sustained frame delivery or the full performance acceptance budget.
Radio/audio, selected source, preferences, prior release and gateway/network
were preserved; normal Chromium was restored and diagnostic listeners closed.
The native observation covers one randomly scheduled type. The full five-model,
two-theme, two-direction matrix is browser presentation evidence, not a claim of
every combination physically observed on the Pi. Long-term motion/performance
and full hardware/product acceptance remain OPEN.
This scoped iteration does not close the full product acceptance inventory.
