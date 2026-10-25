# City v3 — Dark Deco massing

Original Blender architecture for PySH's800×480 Home scene; the city is displayed
at800×208 when the navigation rail is retracted. The user asked for the Dark Deco
visual direction of *Batman: The Animated Series*: monumental1930s silhouettes,
angular setbacks, charcoal/maroon masonry, cool steel and restrained warm windows.
This is a style reference, not a downloaded city, copied geometry or texture pack.
DC identifies that visual direction as Dark Deco in its
[official anniversary article](https://www.dc.com/blog/2022/12/12/dc-shop-releases-exclusive-batman-the-animated-series-30th-anniversary-merchandise-and-apparel).

## Architecture and framing

The repetitive equal-width tower rhythm is replaced by a chamfered cinema palace,
asymmetric buttressed office, taller flat-capped civic lantern, stepped maroon
office, sawtooth factory, industrial chimneys/water tank and chamfered exchange.
Lower storefront blocks have different footprints and setbacks, with planted
gaps instead of a continuous repeated mansard row. Seven small motivated street
practicals support the foreground at night without turning the windows into a
uniform glowing grid. The civic lantern contains no fake frozen-time clock.

The source retains the original1600×570 orthographic camera:
position`(0,-42,14)`, target`(0,0,3.7)`, ortho scale`28.6`.
The existing radio body/cornices/crown dimensions remain compatible with the
eight mounted neon zones. Bluetooth keeps its original rooftop mount while
asymmetric lower shoulder wings distinguish its footprint from the slender radio
tower. The Wi-Fi roof and its mounted hardware remain in place.

- Radio anchor:60.490%,18.001%.
- Bluetooth anchor:21.678%,20.945%.
- Wi-Fi roof world position:`(6.3,.4,4.58)`.
- Original landmark indices3,10,12 are preserved; camera/anchor assertions run on
  every build. Separate beacon geometry is authored by its own builder.

## Reproduction

```sh
blender -b --factory-startup --python-exit-code 1 \
  -P scripts/blender/build_ambient_city_v3.py -- \
  --root /path/to/PySH \
  --audit-scripts /path/to/scenario-blender-expert/scripts
```

Verified with Blender5.2.2 LTS. Optional`--preview` emits half-resolution review
renders into the private runtime evidence directory. The full build writes
`pysh-city-v3.blend`, the two production PNGs and provenance reports. Legacy v1/v2,
metro and sky source/assets are not overwritten. The editable`.blend` is the
authoring master; production exports are lossless display-referredRGBA8 PNGs.

## Budgets and delivery gate

-15,609 vertices,23,940 triangles,23 material-batched city objects.
-1,774 actually authored closed primitives checked individually by the installed
  Blender expert render-profile delivery gate: zero errors, zero warnings.
-26 intentional open ornamental/window planes are identified separately. The
  city is a collection of mounted architectural parts, not a watertight solid,
  3D-print asset or real-time game mesh export. Parts are not falsely treated as
  floating defects solely because neighboring buildings do not touch.
- Two1600×570 PNGs:1,050,211 encoded bytes /7,296,000 decodedRGBA bytes, matching
  the previous two-layer decoded footprint. Browser loads the selected day/night
  layer; it does not run Blender or a WebGL city renderer.

`build-report.json` records exact source/builder/PNG hashes and camera anchors.
`mesh-audit.json` summarizes every closed-part gate by material. Full per-part
results and stage renders remain in the private builder evidence directory.

## Review and limits

Both author and independent visual reviewer inspected blockout, native800×208
night/day and the final Dark Deco revision. Initial European church/dome/clock
features were rejected and replaced before production. Final refinement adds
the asymmetric Bluetooth shoulders and raises the central civic lantern by0.5
world units. The reviewer found no blocking form/value defect in those final
asset renders; that judgement is not a whole-application quality score.

Low-alpha antialias pixels can carry saturated RGB in isolation: for example,
one reviewed day pixel wasRGBA`(0,0,255,1)`. Compositing over the actual sky before
downsampling produces a neutral one-level edge change, not a visible cobalt
outline. The author inspected sky-composited night/day native-size reviews and
retained pixel/alpha measurements. No production bitmap cleanup or lossy palette
quantization was used. Actual UI/fog composition, native interaction, sustained
Pi performance and complete product acceptance remain separate integration gates.

All geometry, procedural materials and lighting are original PySH authoring.
No external models, textures, online renderer or account data are used.
