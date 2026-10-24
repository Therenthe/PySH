# Solar windows, wet roads and outward city journeys

## Scope and baseline

Approved on24October2026 after the prior grounded-city delivery. Add only
weather-driven wet pavement, gradual solar window illumination and cinematic
return from the five entered buildings. Baseline installed ca9ff15300c7,
production source aa2f5e0; documentation HEAD26660b5. No OS/network/audio/account
migration. Existing layout/recovery and private viewer are preserved.

## Implementation and development gates

Windows use separate warm emission banks on always-opaque unlit Blender
baseplates. The existing fully lit nighttime image is not merely faded: doing
so would leak sky or keep the windows lit at noon under a manual Night theme.
Current selected-local-date sunrise/sunset epochs must be finite, ordered and
belong to that same local day. Three staggered banks fade over30minutes around
rise/set. Missing/stale/invalid timing falls back only to the existing location
ephemeris, from solar altitude+6° to−6°; absent valid coordinates means unlit
unknown. UI theme choice does not supply astronomical evidence.

Wet reflection layers require validated nonstale rain/drizzle/showers/thunder
precipitation and follow intensity. Snow, ice, dry, unknown and stale weather
remain dry; reflections never imply a hazard or official warning. No new
weather provider or permission is introduced.

Outward movies pull the camera back from the original portal while actors
continue forward. The existing bounded modal lifecycle handles Cancel, Skip,
media failure, hidden state, timeout and reduced motion. The original task
remains mounted until completion; Cancel returns to its launching control.
Completed Home return restores the original building. Navigation to another
page clears the journey; ordinary Home navigation remains direct.

Development TypeScript passes;654 Python PASS/32 platform skips and82 extension
PASS. First80-case development browser attempt retained16PASS/8FAIL/56notrun.
The eight failures occur at initial reduced-motion arrival before any return
action: the paused fixture had not advanced the animation frame used for focus.
Independent classification corrected only fixture sequencing, including a fresh
retry network gate and a focus frame after asynchronous Home arrival. The
bounded48-case recovery probe passes, zero retries/skips/flaky; all original
behavior/focus/state assertions remain. No failed attempt is counted as a
clean full-suite result.

Final source identity, independent reviews, publication, installed hashes and
native results are recorded only after their own gates. Full product acceptance
remains OPEN; fixtures do not certify physical finger, acoustic or DRM behavior.

Blender reflection iterations R1/R2 were too quiet at native size because the
raised railway occluded reflected practical lights. R3 retains all visible
geometry and uses a standard glossy-ray visibility cheat on the rail occluders
so the actual warm/cool city lights reflect on the existing wet pavement.
The camera, opaque foundation, rail support and weather mask are unchanged.
Independent native-size asset comparison accepted the improved readability;
final browser composition is a separate gate.

## Frozen R1 findings

Source c330d00d68628f57565f815658b0202e6a1c5621/tree d2b6a7a12a70fbc6c67e965fbbae063b33c3127a,
runtime b4c4cc8cf96e/197 files: independent targeted80/80 EN/RO cases pass with
zero retry/skip/flaky, including40 genuine ended entry/exit movies.208 relevant
source/assets and all197 package hashes were independently verified unchanged.
The broader affected regression retained234PASS/4FAIL; all four failures are
one legacy celestial test still expecting the superseded fully-lit baseplate
filename. Its expectation is updated to the actual unlit baseplate; behavior
and astronomy assertions are unchanged.

The separate visual reviewer found a real R1 blocker: the final perspective
return frame put the central tower roof aroundy240 while Home puts it around
y297, causing a57px scale jump at handoff. Passing navigation tests did not
accept this visual defect. R1 is not installed or published as the candidate.
A corrected Blender projection is reviewed before a new immutable source gate.

While awaiting the corrected movies, the previous documentation HEAD's GitHub
CI completed: one full frontend run passed1520/1520, the parallel run passed
1518 and failed two hour-boundary confetti fixtures. Both use a running clock
seeded only31s before the target minute, while setup plus30s idle can consume
the boundary before ambient begins. A private2.5s setup-delay reproduction
failed2/2 with the same signature. Holding only the initial fixture clock at
the seed then passed the same delayed2/2 and all22 existing confetti cases,
without changing any product code or behavioral assertion. Evidence remains
private; previous CI failure is not relabelled green.

Read-only device preflight confirms the original ca9ff15300c7 is still active
on Pi4Rev1.5, Debian13aarch64, DSI800×480, graphical UID1000. Both services
active, Ethernet/radio playing, real alerts available and10.5GiB disk headroom.
No new runtime has been activated during these development iterations.

The independent keyboard reviewer found a second real R1 defect: in four
language/theme contexts, a Bluetooth confirmation prompt safely cancels the
outward movie and owns focus, but provider withdrawal then leaves focus on
BODY. The prompt had remembered the removed movie's Cancel button. The local
city focus-pending mechanism now retains the canonical return launcher during
that safety preemption and waits until the prompt/modal/keyboard owner is gone.
The shared dialog-stack helper is unchanged. Regression and R2 review follow.

Aligned Blender movies retain a constant anamorphic render projection and a
continuous perspective dolly/lens approach to the Home projection, without a
late frame warp or camera-type switch. All five journeys at frames59/60 match
17,819 static vertices per check: maximum0.680px error. All60 frames of each
movie decode; seven window/reflection PNGs remain byte-identical. The failed
authoring save guard and portable local-overlay recovery are recorded separately.

## R2 verification and final prompt ownership repair

R2 source a3cb77eae38fb4deb6179abdee2d96c6e39ddf0c/runtime4f1bec99d75e:
80/80 targeted usability cases,72/72 focus/celestial/confetti regression cases,
44/44 keyboard groups plus four public BT regressions and12 alternate-branch
smokes pass, no retries/skips/flaky. The visual reviewer passes52 captures and
all10 actual encoded final-frame/Home pairs: skyliney296/y296, sampled-column
mean error0.025px, maximum1px. VIS-ATM-01 is closed on that observed scope.
Seven PNGs and five visual UI modules remain identical; main's focus change is
explicitly reviewed rather than incorrectly claimed identical.

Additional Android safety-prompt probing found four cases where the outgoing
movie's cleanup restored focus behind the visible Android approval dialog.
Four new public negatives reproduce that exact gate on R2. R3 reuses the
existing dialog focus/isolation hook for Android approval, with No initially
focused and Escape unable to decide a pairing request. The local city pending
focus now waits for either Bluetooth or Android prompt ownership to end.
The shared hook implementation and all17 atmosphere resources remain unchanged.
Existing four BT public tests are preserved and four Android tests extend them.
