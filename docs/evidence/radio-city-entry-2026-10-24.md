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

## Exact R3 browser and first native gates

R3 runtime `b115fcdaa2c7`, production source
`024ee82eb90eca86799db20643a387b0c09f19a0`, passed210/210 browser cases,
144 captures across16 EN/RO/theme/weather contexts,40 accessibility cases and
10 usability groups. No viewport overflow, page errors or unintended API writes.
Browser decoding confirms transparent sky and opaque ground/threshold; the live
sky remains visible while the old Home UI and original city are cleared.

Installation verified165 runtime hashes and29 preferences against a PC backup;
the gateway, Ethernet and original radio selection were preserved. Native BT
sampling confirms the running Blender atlas through more than12 distinct poses.
The first sampling probe interleaved slow screenshot requests with the3.2s turn;
in-page RAF sampling removed that measurement limitation on unchanged runtime.

Native first-touch wake passed after removing Playwright's actionability trial
click: an independent local reproduction showed that trial emitted trusted mouse
input before the intended CDP touch. A separate probe received physical touches
while awaiting idle and timed out; it is not counted as a product pass.

Actual native playback opened Radio with sound preserved and decoded60 frames
over approximately2.6s. Focus instrumentation then found a real R3 defect: Radio
Search was briefly disabled by navigation auto-hide's preference save when the
one-shot focus attempt ran. Later enablement never retried it. R4 retains the
pending intent through that save/audio busy interval, verifies successful focus,
cancels on departure and bounds readiness retries. Exact R4 browser and native
results follow after verification; R3's native delivery gate was not accepted.

## Final R4 browser and installation gate

Runtime `eaa8c82585e4`, production source
`79830a4d9a5ec830b6298089118cae01a6740af2`, local source
`9551127352c98aefde7b99ae7d62bdab16a3e101`.
214/214 complete scoped regression PASS, no skips/flaky results. Independent
72-capture review covers8 EN/RO/theme/weather contexts; zero page errors,
overflow or unintended API writes and seven source hashes unchanged. The R3
144/16-context review remains separately attributed. Delayed navigation autosave
is covered by28 independent accessibility groups/48 captures: disabled Search
waits for enablement, then receives focus; Enter/Escape and leaving-page
cancellation pass. The code/runtime in that audit is identical to final R4;
the later source commit corrects only the test's PATCH expectation.

The first R4 regression used a static server where six tests require Vite module
imports. Its new request assertion also expected POST rather than PATCH. Those
harness faults and two asset-readiness failures were retained, then the exact
final frozen source was run cleanly on Vite. No failed run is counted as PASS.

685 public source blobs were verified with five existing operational-document
exclusions retained. Canonical LF sources were packaged,165 file hashes checked,
and a fresh PC backup downloaded and verified before activation. Original29
preferences, Ethernet and gateway were preserved; the radio resumed. Previous
runtime `b115fcdaa2c7` remains available for recovery. Documentation HEAD is
separate from the installed production source above.

Native R4 confirms the occasional Blender BT turn and first-touch ambient wake.
It also confirms enabled Search gains focus after autosave. A serial Node/CDP
opacity assertion arrived after the short movie had already ended; its failure
is retained. Native inspection is therefore separated from natural decoder
measurement, with diagnostic paused frames explicitly labelled. Further results
are recorded below when the independent native gate completes.

## Native R4 completion and restoration

On unchanged installed `eaa8c82585e4`/`79830a4`, the supplemental native gate
passes: paused-frame composition clears Home UI and the original city while
preserving the live sky; Cancel prevents late navigation; Skip reaches Radio;
natural completion focuses enabled Search after autosave; reduced motion opens
Radio without creating a movie. Original player identity/state, volume, mute and
audio readiness remained unchanged through all five navigation/control checks.
The unheld, screenshot-free decoder pass reports60 frames,3 dropped,0 corrupted,
duration2.5s and measured2627ms. This is separate from paused diagnostic captures.

The earlier exact-build probe already confirmed the real BT atlas turn and
consumed first ambient touch. An early paused-frame assertion sampled the normal
180ms fade before it settled; the final visual check waits for settled opacity.
A diagnostic tunnel-start timeout was also retained and its bounded allowance
extended before the successful run. These harness attempts are not product PASS.

Native conditions were actual daytime weather and original Ink preferences;
nighttime was not fabricated on the device. Synthetic CDP touch and API state
checks do not establish new physical-finger/acoustic or whole-product acceptance.
Original29 preferences and radio were restored; owned diagnostic browsers,
listeners and PC test servers closed. The existing read-only viewer remains only
on PC127.0.0.1:18765. A fresh guarded whole-Wayland capture after restoration was
visually inspected. Raw scripts, frames, profiles and backups remain private.

Cinema→Media, Bluetooth→Sound and speakers, Wi-Fi→Internet and phone and central
tower→Settings are proposals only. No other building interactions were added.
All30 complete product criteria remain OPEN.
