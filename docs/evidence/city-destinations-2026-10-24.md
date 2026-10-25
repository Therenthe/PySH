# Grounded city, destinations, clock and alerts

## Reported and reproduced defects

The previous city PNG had34 fully transparent bottom rows, leaving roughly12px
of sky below its foundation at the native208px height. Side rail continuity and
metro entry/exit lacked occluding structure. Architecture haze and manual-night
opacity also let the sky bleed through otherwise solid geometry.

Independent clock measurements in16 EN/RO/theme/rail/idle states found343.414px
center with the rail retracted, versus the required viewport400px. The first
fixed-center iteration exposed right-control overlap; intrinsic end-aligned
controls and a compact network label when Android is present corrected it.
Thirty-two subsequent development captures kept clock center399.992px, with
at least25px date/control separation. Final frozen-source coverage is separate.

Meteoalarm transport was independently reproduced on the installed Pi: explicit
XML Accept returned406, wildcard Accept returned a genuine fresh Atom feed200.
The narrowly scoped repair retains all source, XML, geometry/time and cache
guards. See [alert evidence](weather-alerts-2026-10-24.md).

An open warning dialog also allowed Home's30s ambient timer to activate. The
new regression failed in both languages before the fix, then passed after the
dialog joined recovery/idle tracking. The shared modal focus/inert helper now
isolates the warning dialog and restores its trigger. A legacy folding test
now waits for that observable focus restoration before moving focus elsewhere;
updated unavailable copy explicitly says automatic retry, never verified clear.

## Visual iterations and implementation

Original Blender Platform and Retaining variants were compared at800×208 inside
800×480. The Retaining version was selected, then signs/door clearances and
nighttime lettering were polished. A real ground mass, railbed, sleepers, piers
and retaining wall continue beyond the view; a foreground abutment layer hides
the metro at either edge. The trimmed genuine Blender vehicle preserves visible
RGBA and has a measured wheel/rail baseline; traversal uses viewport distance.

Five distinct portals and camera journeys open existing canonical destinations:
Cinema→Media, Audio→Sound and speakers, Wi-Fi→Internet and phone, central
tower→Settings, Radio→Radio. The editable master preserves all five cameras and
door actions. Ten silent transparent-sky movies contain60 frames at24fps,
800×480/2.5s.405 new closed parts,300 camera-segment collision checks and70 late
portal rays pass authoring gates; every movie is separately decoded and alpha
checked. Original city-v3 geometry and original runtime assets are retained.

The application uses one bounded lifecycle for all destinations: Cancel,
Skip, timeouts, media failure, hidden/unmount and reduced motion. Canonical
destination focus waits through navigation autosave; settings return Home.
Media retains the existing Home navigation, avoiding a redundant extra arrow.
Whole-facade touch regions remain available without playback or Wave. A measured
Cinema clipping defect with the rail open was corrected by a bounded target
clamp; Audio shifts only enough to retain a disjoint1px gap. Both original
door centers remain inside their targets and expose48×48 under default cards.

Architecture/support stay opaque; real fog uses its existing overlay and manual
night retains brightness dimming. No new weather, beacon state or celestial
events are recorded into the movies. Additional visual ideas remain proposals.

## Checks before exact-source delivery

654 Python PASS /32 platform skips and82 extension PASS. Initial new-flow run:
69/72 PASS, with all46 destination/clock/ground checks passing; warning-copy and
focus-restoration harness expectations were updated and the complete26-case
warning retest passed. These development results do not replace final frozen
browser/device gates. Raw previews, scripts, captures and backups remain private.

Final source/build, independent browser audits and native installation outcomes
are recorded after their gates. All30 complete product criteria remain OPEN.

## R1 independent gates and R2 focus repairs

R1 source `d43b0606d5021353c239a3acdc67581ac47a869e`, runtime `baea5fbaf1c3`:
32 strict clock states,208 visual captures,84 flow captures and an independent
76-capture usability pass accepted the bounded scene/destination behavior.
A suspected missing-clock paint issue was disproved by identical395 glyph pixels
across original and repeated PNGs; no speculative clock code change was made.

The separate accessibility reviewer passed140 entry groups and16 warning-modal
groups but found two focus defects:16 canonical Home returns left focus on BODY,
and four verified-clear refresh observations lost focus when the warning trigger
disappeared. R2 restores the originating building after returning Home and waits
through navigation autosave, while automatic warning clear returns focus to the
weather heading only if its own trigger is gone. Shared dialog logic is unchanged.
The clear-refresh public regression reproduced failure in EN/RO before the fix.
A connected network lacking a profile name now says Connected rather than Offline;
the earlier advisory came from partial fixture data, not a proven native outage.

The first full1516-case browser launch stopped after20 fixture failures: the test
runner resolved standalone fixture paths from the development checkout while Vite
correctly restricted serving to the frozen source (HTTP403). This environment
failure is not counted as product PASS. The corrected launch uses the immutable
export as its working directory, with the expanded R2 regression tests.

R2 source `a52138674b0f290d6ae93643c796639fa0ddb35f`, runtime `4ca0c38e0753`:
176/176 independent accessibility groups pass, including all20 prior focus
instances, with212 captures. Independent usability repeats76 captures and
explicitly verifies20 building-focus returns, four warning-heading recoveries
and four connected-but-unnamed network captions. Layout/scene assets and150
relevant files remain identical to R1; representative visual/clock/flow gates
are separately attributed. No remaining scoped focus defect was observed.

The corrected full browser launch then exposed legacy expectations still naming
city-v3 rather than the new city-v4; its first269 cases passed before the20-fail
cap. R3 updates those three callers and adds explicit asset decoding before
scene assertions. Warning failure copy is generalized to unverifiable data,
covering transport, parsing and unsupported coverage without claiming no hazard.
The final complete regression is rerun on that exact export.

R3's broader run retained1097 passes before the20-failure cap. Fourteen failures
used floating-placement expectations with radio Wave's fixed facade, four still
expected the superseded radio movie URL, and two exposed keyboard focus missing
when collapsing the facade's playback card. A stronger four-context regression
reproduced the latter before repair. R4 directs that collapse to the real Radio
building command; floating styles keep their prior visualizer focus behavior.

The placement fixtures now explicitly use Bars, with a non-building precondition;
all drag, anchor, edge, overlap and persistence assertions remain byte-identical.
An independent12-case retest passed before the full rerun. The valid Wave tests
for Arrange's temporary placeholder and local audio remain unchanged. Legacy
movie expectations now address the actual city-entry-radio asset. Runtime layout
preferences are neither rewritten nor reset by these test-only changes.

## R4 complete regression and follow-up

Pinned local source `8ae90254ced74f7f14e73027635b86dcc049454d`, tree
`603a335707c394ddc5a233cabe54cfaf6af2c8f3`, runtime `ca9ff15300c7`.
The complete1520-case run finished:1512PASS,8FAIL,0skipped,0flaky, zero retries.
It is not reported as a clean full-suite pass. Independent focused follow-up
classifies each failure and retains the original results.

One ambient-home failure attempted to expand a card after the legitimate30s
idle phase had hidden it. A test-only blank touch now explicitly returns to
interactive before that action; every original assertion remains unchanged.
All48 cases pass against the identical frozen R4 runtime, without retries.
Two solar cases used a running fixture clock seeded only two seconds before
sunset; setup consumed that margin. A save-recovery case lacked initial
navigation readiness. Original10 bounded cases pass; six controlled-delay
negative probes reproduce those errors. Test-only explicit clock/readiness
preconditions then pass all10 cases and all six delayed probes, without
changing any behavioral assertion. The three media failures reached the existing2.5s load guard: their Range
requests received no response headers under the concurrent suite burst and
were canceled. Captures show usable Radio after bounded fallback, rather than
a stranded transition. The fourth trace shows Quick Controls already open
while the input driver exceeded its5s acknowledgement budget. All four original
cases pass unchanged in a single-worker, zero-retry bounded run (21.1s).
These separate results do not turn the original1512/8 ledger into1520/1520.

The candidate's published source is `aa2f5e07db7fe2debd9c3ea942632a7ebab7501e`,
verified public tree `bba2bba52dd64f19f785195122fc8f405f5ec39c`:722 blobs,
including719 nonexcluded local files and three retained operational documents.
Five existing private operational-document exclusions remain unchanged.
The180-file archive is staged and the separate PC backup is checksum/content
verified; staging does not certify installation or native behavior.

## Installed R4 candidate

The source branch was advanced with an expected-head lease, without force.
Preparation verified archive bytes, exact180 runtime files, and a readable
checksum/content-verified backup on the separate PC before activation.
Activation installed `ca9ff15300c7` with published source `aa2f5e07db7fe2debd9c3ea942632a7ebab7501e`.
The previous `eaa8c82585e4` is retained. All180 installed hashes and29 preferences
match; Ethernet identity, gateway pointer/files and both services are unchanged.
The previously playing radio was resumed and its progress/output readiness
verified. This is runtime delivery, not flashing or a full product release.
Native destination/decoder/provider proof is recorded separately below.

## Native kiosk verification and restoration

All five actual day movies completed naturally on the installed Raspberry,
with the original real weather and saved preferences. Synthetic CDP touch
verified canonical destination focus and focus on the originating building
after returning Home. All20 natural/Cancel/Skip/reduced-motion route checks
preserved radio identity/state, volume, mute and output readiness. Reduced
motion opened directly with no new movie. A separately paused approach
capture avoids screenshot overhead inside natural decoding measurements.

| Destination | Elapsed ms | Frames | Dropped | Corrupt |
| --- | ---: | ---: | ---: | ---: |
| Media |2652.4|60|1|0|
| Sound |2647.6|60|4|0|
| Internet |2615.6|60|4|0|
| Settings |2599.1|60|2|0|
| Radio |2607.3|60|2|0|

The physical viewport clock center measured399.992px. The bottom four native
source rows are fully opaque, with both architecture/scenery computed opacity1.
Actual provider state was `available`, no error/partial result, with zero
applicable warnings and an update timestamp13:35:53UTC. This is a genuine empty
snapshot, not certification of a live severe-weather alert; active warnings
and night/movie combinations retain their separately labelled browser coverage.

The first native attempt passed Media decoding/arrival but rejected the rounded
48px navigation button because its transparent corners failed an overly strict
rectangular hit probe. Original evidence is retained. The private harness now
uses center/cardinal probes for rounded controls, while preserving48px bounding
measurements and the original five-point facade probes. No product code changed.
The subsequent complete native run passed.

Cleanup restored the exact original preferences and radio, removed its owned
service override and closed temporary browser debugging/SSH forwarding ports.
A fresh Wayland frame after restoration was inspected at800×480. The preexisting
read-only live viewer remains bound only to PC127.0.0.1:18765, without a public
relay. Native CDP touch is not a new physical-finger/acoustic acceptance.

## Proposals only

Not implemented: weather-driven wet-road reflections; gradual window lighting
at dawn/dusk; a short reverse camera journey when returning to the originating
building. Each requires user agreement before a separate implementation.
All30 complete product criteria remain OPEN; this bounded delivery does not
claim a global10/10 visual score or completed product acceptance.

A separate reviewer inspected the actual original Home, paused Media approach,
finished Home and fresh post-restoration Wayland PNGs, all800×480, together
with the native report/cleanup receipt. The bounded scene, edge/rail continuity,
clock, no Home-layer leakage during approach, decoder and restoration checks
were accepted. This does not certify new physical finger/audio observations
or the complete application's unrelated open criteria.
