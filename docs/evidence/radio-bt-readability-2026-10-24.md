# Radio and Bluetooth readability

The actual morning capture showed a black Bluetooth plate, faint radio arcs and
no discernible facade visualization. Read-only diagnosis confirmed Wave and all
three Home cards enabled, radio playing, output ready and unmuted. Measured PCM
was healthy: peak about0.63–0.69, RMS0.22–0.28 and maximum temporal bin0.35–0.39.
This was not missing data or an output-volume normalization problem.

Day Wave multiplied square-root amplitude by0.22 and reused pale night colors.
At these measured levels, opacity was only about13%, against fog and stone.
The correction keeps true measured pair amplitudes and all zero/silence/output
gates, removes only that extra day attenuation, and uses a Blender daylight
palette with contrasting teal/cobalt/plum/brass materials. Night assets remain
unchanged. Eight day PNGs total18,704 encoded bytes /1,061,056 decoded RGBA;
45 original closed tube props pass render gates.

Bluetooth's solid housing and dark face are removed from the Blender model.
The mounted3D rune has a thin physical understroke, not an opaque rectangle.
Bluetooth and radio now each have hardware, core and three separate wave-band
layers in day/night palettes.54 closed parts pass render gates;20 PNGs total
58,690 encoded bytes /1,197,560 decoded RGBA. Roof mounts and crops are unchanged.

Wave bands light in sequence over3.6s with1.2s offsets. A visible baseline and
stable core prevent the connected/playing cue from disappearing between pulses.
Powered idle has no Bluetooth emission; off has no illuminated rune. Pausing
radio removes its emission while retaining the physical mast. Existing hidden,
offscreen and reduced-motion rules cover all child bands, without new JS timers.

Palette follows the actual composited surface: actual night or a dark UI uses
the night material; a light daytime surface uses day material. Actual weather,
celestial state and the data-neon-night flag remain independent of UI theme.
Card retreat/ambient wake and saved arrangements are unchanged: missing cards
in the baseline were deliberately hidden by the requested idle behavior.

The first exact-source browser run passed180 functional regressions, but its
independent visual review rejected manual Night UI over actual daytime fog:
the legacy whole-sky brightness filter still dimmed every emitted signal. A
temporary inverse filter was also rejected. Sky/background and city scenery
now have separate dimming layers; mounted service lights and measured neon
remain outside them. Actual weather and day/night determination stay unchanged.
The rejected runtime20e2ab5ceade was prepared only, never activated.
The second candidate restored readable lights but put rain behind the city in
manual Night UI. Precipitation and warning illustrations remain direct sky
siblings with their original foreground order, dimmed independently of scenery.
That prepared candidate9817e3d98a39 was also superseded without activation.

Asset previews were independently reviewed at native size. Runtime/frozen-source
checks and final actual-device evidence follow below after their gates complete.
This scoped change does not certify a global score or complete product release.
