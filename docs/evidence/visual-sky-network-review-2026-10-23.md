# Visual review: sky and network identity — 2026-10-23

This is a scoped review of the iteration after **Varianta Back**, not final
product acceptance or a visual score. The reviewer used the installed
`frontend-design`, `frontend-design-review` and `pi-smart-hub-touch-ux` skills.
No Figma/component-library source was supplied; the existing PySH source tokens,
owner references and 800×480 touchscreen contract are the design system for this
review. Desktop browser evidence does not prove panel touch feel or Pi cost.

## Direction before implementation

The distinctive element is the inhabited Gothic city under a quiet, readable
sky. The interface must leave that scene visible rather than add unrelated
decoration. Blender geometry, lighting and materials supply depth; static
atlases and small transformed layers keep runtime work bounded on Pi 4.

| Existing token | Role |
|---|---|
| `#080e19` | Night zenith; retain genuinely dark negative space |
| `#213747` | Upper atmospheric blue, not a photographic galaxy texture |
| `#142d39` | Night horizon transition behind the architecture |
| `#e7edf0` | Day sky, light enough for legible dark daytime details |
| `#f4f7fb` | Primary night text and icons |
| `#6edbb3` | Restrained active control accent |

Keep the installed DM Sans body family and Manrope clock rather than introduce
another font family. Body copy stays 16px, secondary labels 14px. The single
clock remains the quiet top anchor. Expanded cards retain readable surfaces;
collapsed/ambient mode reveals the scene. A connected radio may animate its
rooftop antenna, but decorative motion must not claim a measured audio level.

```text
48px controls       clock/date         real Wi-Fi / Ethernet
──────────────────────── sky ──────────────────────────────
        sparse stars       celestial body       cloud volume
                 clear negative space / rare aircraft
       collapsed cards remain user-positioned on waking
──────────────── Gothic city / lit windows ───────────────
                   quiet audio visualizer
```

The plan was checked against the brief: retain the owner's sparse stars, no
superheroes, no dense photographic star field, no extra profile greeting or
duplicated player. Use familiar monochrome network symbols rather than treat a
green decorative dot as evidence of Wi-Fi. A moon below the true horizon must
not be moved into view merely to make a sampled screenshot busier.

## Network component: local verification

`app/ui/src/NetworkStatus.tsx` replaces the ambiguous Connected dot with the
conventional three Wi-Fi arcs and a dot, plus a distinct Ethernet socket/plug.
Both link types can appear together in two compact rows inside one 48px-high
button. One touch opens network settings. Connection, pending, disconnected,
radio-off, unavailable and unknown states have separate EN/RO accessible names;
a slash distinguishes a disconnected link without relying on colour.

Signal comes first from the currently connected device's active AP reading.
An optional scan fallback requires both matching SSID and `in_use:true`; a
strong neighbour never supplies the connected indicator. Missing, invalid or
out-of-range values remain unknown. Link association is not a claim of internet
reachability. Radio-off requires an explicit genuine `wireless_enabled:false`;
an unavailable adapter does not imply its radio is switched off.

TypeScript and 12 focused browser cases passed after the final component
refinement, in EN/RO and Ink/Night. These exercise the actual application header
with both links, Android presence, expanded navigation, central clock and
power/settings controls, plus isolated link-state fixtures. All header touch
targets remain at least 48×48px, inside the 58px header, without clock overlap.
The idle night header keeps network icons bright even with the Ink theme.
Actual-app Ink/EN and Night/RO captures were visually inspected. Pi installation
and real network state are a separate root-agent verification step.

The backend companion change reads `device.signal` from the same active-AP
properties as its SSID, with no additional scan and no neighbouring AP lookup.
It includes the genuine NetworkManager radio-enabled boolean only when known;
the optional read is bounded. The separate 24-case backend suite passed for
active-AP strength, missing/invalid values and genuine/unknown radio state.

## Sky review checkpoints

The actual 800×480 Varianta Back panel capture at 20:11 was inspected. The city
has useful architectural layers and lit windows; the visible clouds resemble
two broad blurred horizontal smears. Stars, Moon and aircraft are not
discernible in that single sampled frame. Their absence alone cannot establish
a rendering defect: horizon, cloud cover and intermittent event timing matter.

The first new Blender composites were inspected at 800×480, including clear
night, winter night and summer day. Findings were sent directly to the artist
for another pass:

| Priority | Observed issue | Required improvement |
|---|---|---|
| Major | Star sprites downsample their cores below a useful pixel; clear night looks almost empty | Strengthen the central optical core while keeping the original170 centres; reserve glints for a few bright points |
| Major | Day cloud reads as dark soot/rounded domes; winter night forms a mottled smoky blanket | Cohesive irregular volume, softer edge, flatter base and restrained lit upper rim; remove grain and repeated puffs |
| Major | Crescent's unlit hemisphere is a perfectly black disc against atmospheric blue | Subtle earthshine/ambient fill preserving the computed phase and leaving the lit limb dominant |
| Checked | Plane has recognizable fuselage, tail and swept-back wings | Retain plausible silhouette; test actual event orientation and brief visibility |
| Checked | City retains depth and enough open sky without a photographic background | Preserve composition and sparse atmosphere while improving individual assets |

The subsequent refined day, night and overcast composites were inspected at
800×480. Star cores became plainly visible while retaining sparse placement;
clouds gained coherent volume without the first pass's obvious soot or noisy
edges; the aircraft and skyline retained readable depth. Two remaining issues
were returned to the artist: a dark/brown illuminated lunar crescent and a tan
Sun with a dark rim.

## Final desktop visual checkpoint

The final refreshed day, night, waxing-Moon and overcast previews were reviewed
at their exact 800×480 size. The artist neutralized lunar albedo, raised its lit
exposure while preserving a dim earthshine side, and removed the stochastic
corona from the Sun. The previously noted major issues are resolved in the
inspected fixtures:

- Sparse stars remain visible without a photographic galaxy background.
- Clouds have cohesive irregular volume; no soot, obvious render grain or
  clipped alpha edge is visible at the display size.
- The Moon reads as a neutral lit sphere. The above-horizon waxing fixture at
  `2026-10-20T17:00:00Z` has its right side illuminated; the waning fixture has
  the opposite orientation. The phase remains computed rather than forced full.
- The Sun has a pale luminous core without the prior dark rim/noisy halo.
- The airliner retains a recognizable fuselage, swept wings and tail. The
  original city remains layered and lit with substantial quiet sky space.

No additional major craft blocker was found in these four final fixtures. Minor
future refinements are possible: a repeated cloud silhouette is recognizable
between mirrored layers, and the daytime rooftop Bluetooth marker is faint.
Neither observation certifies the complete UI or its hardware operation.

The artist's final 24 EN/RO sky cases and 38 Blender render-prop gates passed.
The sky cases include actual Home CSS cascade checks, both Moon orientations,
asset pixels and Sun limb/alpha checks; this is broader than asserting filenames
or DOM attributes alone. The reviewer independently inspected the rendered
compositions, not merely the passing test counts.

Native Pi capture, sustained animation/media performance and physical touch
remain separate acceptance steps. No 10/10 judgment is assigned by the reviewer
or inferred from automated test counts.
