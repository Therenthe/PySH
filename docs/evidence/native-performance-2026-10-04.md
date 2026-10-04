# Current-candidate scoped native performance

Runtime670c8155227b, sourcebeab133f81aa3de7d09c4901faef64efb952c0bb. Five measured relaunches of the user app service within the existing graphical session reached visible native Home with fonts loaded at800x480 in4.929185,4.894435,4.904389,4.981712 and4.941366seconds. These are app relaunches, not graphical-session starts or cold boots.

At fifth Home+120.000122seconds, complete whole-tree PSS was613270KiB /598.896484MiB across15processes, including verified same-UID descendants in Chromium sibling scopes and diagnostic overhead. Collection ended at+120.182964seconds; no unreadable members, membership changes or zombies were observed. Playback was stopped for idle. This satisfies the measured idle<=700MiB subcondition; it does not accept all PERF-02 media/system usability requirements.

Each phase verified the48current runtime files, activation source, SD UUID and absence of an update transaction. The kiosk-only debugger listened exclusively on loopback. Unknown playback was rejected before preparation. The original preferences, audio volume/mute/output and radio state were restored. The independent original diagnostic teardown completed with preferences/audio/radio restored and ports closed; subsequent preflight reconfirmed48hashes, audio ready, playing radio and no diagnostic listener.

Private report `.runtime/perf670c-output-3/report.json` SHA256`c6c5c148c9c7daa58a493e88b47ab667115bcc11abfd38649d038c05d878bd28`; terminal run exit0. Private runner SHA256`3c7930bae2b14a791932d581cbf069a1904fb11e2115d2908cf3b4a84572f5ee`; native phase SHA256`e75d517adfb234a573b6feadccf3ba6629670596197a6d0c20874064efde87de`. Canonical collector SHA256`22c0eeaf4f5cd7e71b5d0177591e4e81aa6d3893d6cbb093498261f4abf42676` was unchanged. Raw preferences and reports remain private.

Two earlier attempts failed baseline before measured launches: unreadable descriptors in an unrelated nondumpable same-UID process. Each was followed by independently verified teardown/restoration. The harness now skips inaccessible unrelated descriptors while still rejecting an unidentified diagnostic owner or owner outside the app tree. Six local synthetic tests passed, including the owner-found and fail-closed cases. Failed attempts are not measurements.

At this earlier checkpoint, interaction timing was unmeasured. The following scoped navigation probe supersedes that statement; PERF-01 remains OPEN for the complete action inventory and five actual graphical-session starts. PERF-02 remains OPEN pending complete media-load/system usability evidence. REL-01 requires eight hours plus periodic interaction evidence. No final image, physical touch latency or product completion is claimed.

## Native injected-touch local navigation follow-up

Runtime `670c8155227b`, source `beab133f81aa3de7d09c4901faef64efb952c0bb`, native Chromium at 800 × 480. The root-operated probe completed 480 genuine CDP-injected touch interactions: 30 valid transitions to each of Home, Radio, Media and Settings in EN/RO × E-Ink/Night. All 16 groups had 30 valid samples, zero failed attempts and zero timeouts. The original radio remained playing and advanced during each context; audio settings were preserved. These are injected browser touch events, not physical panel touches.

Browser `performance.now` capture-handler timing measured pointerdown → changed computed pressed box-shadow at a requestAnimationFrame opportunity. This is a **style/frame opportunity proxy**, not actual pixel paint; device delivery and pre-handler scheduling delay are excluded. Navigation measured trusted click → active destination, visible owned local shell, loaded fonts and two subsequent animation frames. Radio/catalog and media/library fetch completion are excluded. Touch dwell was 120 ms and recorded separately, excluded from click-based navigation.

Each group independently met all-sample feedback proxy ≤100 ms and local-navigation p95 ≤300 ms. Worst feedback proxy maximum was 21.7 ms; worst navigation p95 was 146.8 ms. The following values are milliseconds rounded to one decimal; p95 uses nearest rank `ceil(.95*n)`. Raw samples and unrounded statistics are retained privately.

| Language | Theme | Destination | Valid/attempts | Failed | Feedback max | Feedback p95 | Navigation p95 |
|---|---|---|---|---|---:|---:|---:|
| EN | E-Ink | Home | 30/30 | 0 | 15.3 | 10.4 | 101.1 |
| EN | E-Ink | Radio | 30/30 | 0 | 21.7 | 13.2 | 146.8 |
| EN | E-Ink | Media | 30/30 | 0 | 8.4 | 8.3 | 70.2 |
| EN | E-Ink | Settings | 30/30 | 0 | 13.6 | 11.0 | 59.2 |
| EN | Night | Home | 30/30 | 0 | 11.8 | 10.8 | 81.4 |
| EN | Night | Radio | 30/30 | 0 | 21.1 | 20.3 | 132.0 |
| EN | Night | Media | 30/30 | 0 | 10.1 | 9.9 | 60.7 |
| EN | Night | Settings | 30/30 | 0 | 15.1 | 10.1 | 57.2 |
| RO | E-Ink | Home | 30/30 | 0 | 11.0 | 10.4 | 87.0 |
| RO | E-Ink | Radio | 30/30 | 0 | 14.0 | 12.7 | 132.6 |
| RO | E-Ink | Media | 30/30 | 0 | 9.1 | 8.7 | 59.0 |
| RO | E-Ink | Settings | 30/30 | 0 | 9.9 | 9.7 | 48.5 |
| RO | Night | Home | 30/30 | 0 | 10.3 | 10.2 | 81.9 |
| RO | Night | Radio | 30/30 | 0 | 13.7 | 11.2 | 143.8 |
| RO | Night | Media | 30/30 | 0 | 13.7 | 8.6 | 64.8 |
| RO | Night | Settings | 30/30 | 0 | 11.8 | 10.3 | 55.2 |

Each guarded context verified the exact current source/release, all 48 runtime file hashes, SD identity, unit/owned kiosk process and loopback-only diagnostic listener. Unknown playback or an external service process would have blocked the probe. Preferences were restored exactly LAST, after returning Home; audio volume/mute/output and the original radio identity/state were restored. The root operator subsequently ran independent diagnostic teardown and preflight successfully: normal service and original preferences/audio/radio restored, diagnostic ports closed, all 48 hashes verified. No private endpoint, key, radio identity, account data or profile contents are included here.

Private latency report SHA256: `5def91f81a53e7bff4658322f2f7d1ac34f70d0b5d959d58d3d41c0ca277dd89`. Probe terminal status was `SCOPED_MEASUREMENTS_COMPLETE`; all samples and timeout/failure fields remain in the private report. Seven local statistics-contract tests passed before execution, including individual feedback outliers, failure completeness, duplicate-context rejection and invalid/untrusted samples.

This supersedes the earlier statement that current-candidate local-navigation timings were entirely unmeasured. **PERF-01 remains OPEN**: this measures only the four-destination navigation family, not 30 samples for every product action type, physical visual feedback, or five actual graphical-session starts. The preceding five service relaunches remain scoped app relaunches. PERF-02/REL-01 are not accepted by this latency result; no final image, physical-touch latency or product completion is claimed.

Separately, the root-run browser regression baseline completed **546 PASS before the subsequent audio changes**. That result is not a regression verdict for those new changes, and the latency evidence above belongs specifically to the installed 670c/source beab candidate. Native timing and browser-fixture regression evidence have distinct scopes.
