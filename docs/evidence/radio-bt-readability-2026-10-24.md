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

## R3 installation and verification

Installed runtime `016160798d6f`, GitHub production source
`7db433b4a388b2d2d43147dfa5b096fa05b1ace7`, public tree
`6662a61f03c292a6911c1d0f861d511195682427`. Canonical local source is
`1e224abd0006ec32ce99f2c724618e39d00eeaa6`; later documentation/test commits
do not change the installed runtime.

- Exact frozen production:204/204 browser cases PASS, no failures, retries or
  skips. Late test-only warning-layer assertion:8/8 against the same runtime.
- Independent full UI review:46 captures /16 contexts, EN/RO, Ink/Night,
  actual-scene day-fog, night-fog, night-clear and day-rain. Zero page errors,
  overflow or API writes. Three phase probes retain visible cores and sequence
  all six rings. Controlled-night frames retain stars, Moon and a naturally
  scheduled meteor; those fixtures do not represent actual Pi weather.
- Real installed Chromium:14 captures at800×480, actual daytime WMO45 fog,
  connected Bluetooth and measured radio output. All six rings change opacity;
  facade amplitude changes reach0.702. Both themes keep the signal outside
  ancestor dimming. Facade touch opens controls; pause and mute extinguish
  visualization; UI Play resumes; first ambient touch wakes without also
  activating the underlying control. Card arrangements remain unchanged.
- PC backup contents/checksum verified before activation;151 installed hashes
  and29 preferences verified. Previous runtime40d0bedaf3fb retained. Gateway and
  Ethernet unchanged; original radio resumed. Diagnostic browsers/listeners
  closed; all preferences and playback restored. Final private Wayland frame
  captured through the existing PC-loopback viewer after restoration.
- TypeScript, Vite, repository structure and package checks PASS;650 Python
  cases PASS /32 platform skips and82 extension cases PASS.

The independent review rejected two prepared candidates before installation;
their functional PASS did not override the observed visual defects. A private
visual fixture had encoding artifacts in location/track text; production
translations were not changed, and actual native text/captures are the final
comparison. Raw frames, recordings, operator scripts and backups remain private.

## Post-restoration daylight finding

The final original-preference Ink/day-fog image exposed a remaining visual
blocker: day circuits merged with the dark radio facade. The earlier native
Night view could not certify this context. A second read-only observation of
the unchanged original preferences sampled eight states: visible document,
loaded day PNGs, ready/active signal, and maximum opacity0.56–0.68. Healthy
PCM and DOM state exclude a missing reader or lifecycle problem. Independent
review found nearly-black tube pixels against dark masonry, whereas night
tubes had much higher luminance. All preferences/playback were restored again.

The day Blender material is corrected with porcelain/icy-cyan/warm-gold tube
cores, without amplitude normalization, fake animation or a global filter
workaround. An authored0.65-opacity composition over the actual Ink/day-fog
capture is visibly clearer; this preview does not certify an installed result.
R3's scoped visual
gate remains OPEN for this daylight context until new actual native proof.
Native CDP touch does not establish physical-finger/acoustic acceptance or
sustained Pi performance. All30 complete product criteria remain OPEN.
