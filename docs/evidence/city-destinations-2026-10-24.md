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
