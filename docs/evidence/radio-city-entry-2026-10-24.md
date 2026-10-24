# Blender radio entry and service motion

## Candidate scope and authorship

The radio-building command is now a separate permanent touchscreen target,
independent of playback, Wave style and enabled Home cards. Its bounds cover
the mast, facade and entrance while staying beneath user-positioned cards.
Ambient first-touch wake remains consumed; playback has its own existing card.
Other buildings have no new interaction and are suggestions only.

The genuine perspective Blender shot approaches the modeled Art Deco entrance,
with two cars, a moving metro, two walking figures, hinged doors and a small
rightward camera arc. Its two transparent VP8 WebM clips are800×480,24fps,
60 frames /2.5s, no audio. Combined encoded size1,231,809 bytes;117 new closed
props pass render gates with zero errors/warnings. Sky stays transparent for
the actual live weather/celestial scene. The existing city source is unchanged.
An early long dark tail was rejected and retimed before full rendering.

Bluetooth uses32 genuine Blender vertical-axis poses,3.2s per occasional turn,
with fixed supports and separate connected-state wave bands. Four1600×77 atlases
hold50×77 tiles. Wi-Fi has only three independent wave bands per palette; no
router or association dot is rendered. Twelve motion PNGs total357,158 bytes
encoded /2,222,888 decoded RGBA; nine closed props pass render gates. Old source
and runtime assets remain intact. The full first/last BT frames are identical.

The initial BT turn is scheduled18–28s after an eligible mount; later turns
45–75s apart. Hidden/offscreen/reduced-motion states reset the rune to its front
pose, and state/palette changes select matching idle/connected material. Only
the actual Wi-Fi route transmits; connecting has a separate search progression.

## Interaction and recovery

The dialog loads a local silent movie with Cancel and Skip commands. Ended media
hands off to the existing Radio page after a short160ms release. Rejected play,
missing media or bounded loading/stall timeout also reaches usable Radio.
Cancel/Escape and hidden/unmount discard late completion. Reduced motion opens
Radio directly. Scene dimming, precipitation and fog are separate from actual
day/night selection. The shot never calls playback/network/device operations.

Authors and independent reviewer inspected key poses, full continuity sheets,
BT front/quarter/edge/rear views and day/night city compositions. These authoring
gates do not establish actual browser alpha, hardware decoding or touch feel.
Exact frozen browser/native verification will be added after its gates finish.

The first frozen candidate passed all30 new interaction cases. Its legacy scene
run passed178/180; two tests retained the superseded building→expand-card gesture.
Those test-only expectations were migrated to the existing Quick controls and
Radio navigation, with isolated EN/RO retest2/2 PASS on unchanged runtime.

Independent full-UI inspection then rejected Home-card/header leakage behind
the transparent movie: the hide rule targeted direct topbar/content children,
but the actual UI is inside main-area. R2 hides that container while preserving
the live-sky sibling, explicitly outranks the manually dark daytime city layer,
and releases the movie against the destination theme background rather than
flashing the Home sky. The prepared first candidate was never activated.

R2's independent usability and keyboard/modal reviews found no blocker. Their
minor observations were polished before device delivery: loading now clears
the old Home header beneath its action row, and successful/error/skip/reduced
handoff moves focus into Radio without opening the keyboard. Cancel still
restores the building trigger. The remaining legacy geometry assertion sampled
an intermediate rail/ResizeObserver frame; R3 waits for settled containment,
retaining exact facade bounds and minimum48px checks instead of weakening them.

Cold TypeScript/Vite, structure/package checks PASS;650 Python PASS /32 platform
skips and82 extension PASS. No global quality score or full product acceptance
is claimed. Raw frames, probes, captures and device operations remain private.
