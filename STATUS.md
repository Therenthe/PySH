# PySH status

Updated: 2026-10-04. GitHub is canonical: [Therenthe/PySH](https://github.com/Therenthe/PySH), branch `feat/pysh-os-image`, [draft PR #3](https://github.com/Therenthe/PySH/pull/3). The product is incomplete; no 10/10 or final release acceptance is assigned.

## Current identities

| Item | Verified state |
|---|---|
| Installed SD application | Runtime `32b5c92bbaf6`, source `296f3d75302167d3c161433d7d1d42b011318351`; previous `670c8155227b` retained |
| Published application source | Commit `296f3d75302167d3c161433d7d1d42b011318351` verified in GitHub |
| Superseded packages | `aa288e1a375f` and `358b4892b275`, never installed |
| Current update | Published and installed. All 48 runtime hashes and nine saved preferences verified; audio ready, radio resumed, no debug listener. UI-34/35 proposals remain private/unexecuted. |
| Device | Raspberry Pi 4 / 4 GB, Debian 13 ARM64, DSI 800×480, 180° display rotation; existing SD boot. USB and independently verified PC backups remain recovery assets. |
| Product acceptance | 30 complete product criteria OPEN for the new candidate. Prior HW-01 configuration PASS on670c is retained as historical evidence pending current viewport refresh. |

The installed application update is distinct from the OS image. There is no newly verified final successor image containing the ongoing correction. See [hardware evidence](docs/evidence/hardware-configuration-2026-10-04.md), [SD boot](docs/evidence/sd-boot-2026-10-03.md), [operations](docs/OPERATIONS.md) and [SSH flasher](docs/SSH_FLASHER.md).

## Latest evidence and its scope

- Previous installed 670c (historical): all 48 runtime hashes, activation identity, saved preferences, continuing radio and closed diagnostic endpoints were checked. Native local audio/video format and recovery probes passed within their stated scope; physical touch/audibility and complete media acceptance remain OPEN. [Media evidence](docs/evidence/media-missing-target-2026-10-04.md).
- Previous installed 670c (historical): five app service relaunches reached Home in 4.894–4.982 s; complete idle PSS at Home +120 s was 598.896 MiB across 15 processes, including diagnostic overhead. The 480 injected-touch navigation samples had zero failures; feedback style/frame proxy maximum 21.7 ms and worst navigation p95 146.8 ms. These do not establish physical display latency, all action types or graphical-session startup. [Performance evidence](docs/evidence/native-performance-2026-10-04.md).
- Earlier local audio correction: complete **594-case browser regression passed before the follow-on changes**; TypeScript/build/repository checks passed, with 347 Python cases /22 platform skips and 27 keyboard cases. Prepared aa288 belongs to that checkpoint. [Audio evidence](docs/evidence/audio-output-recovery-2026-10-04.md).
- Audio follow-on: **634 full browser cases passed before the final scoped Setup footer CSS adjustment**; 154 affected cases and 40 new cases passed at that checkpoint. Final footer adjustment reproduced four failures before repair; all eight new Setup cases passed afterward. **192 affected browser cases passed on the final source**, including Setup, product tour and both audio suites. TypeScript/build passed; Python 347 passed /22 platform skips and 27 keyboard cases retain their stated scope. [Audio evidence](docs/evidence/audio-output-recovery-2026-10-04.md).
- Setup long-label recovery now keeps the full primary navigation footer visible; all eight new cases verify complete 48px hit targets, touch scrolling and revisit. Video/service stress captures fit. This is browser fixture evidence, not native audio or touch acceptance.
- UI-34 Bluetooth confirmation/PIN/passkey handling has a private proposal ready for review, with static inspection only. Accept/cancel, failed replies, repeated taps and prompt withdrawal still require execution and acceptance; no implementation or runtime PASS is claimed from that proposal.
- Image provenance collector: eleven focused tests passed; a fresh Linux-generated image and actual read-only filesystem integration remain unverified. Experimental artifacts are NOT FLASH-READY. [Provenance evidence](docs/evidence/image-provenance-2026-10-04.md).

Every earlier UI request remains in [UI_DELIVERY_PLAN.md](docs/UI_DELIVERY_PLAN.md). Compact Arrange, exact edge anchors, overlap, personalization, ambient scene, station identity, both languages/themes and all older requirements must survive the new correction. The historical log is preserved in [the full status snapshot](docs/history/status-2026-10-04.md); its older “Current runtime” headings are historical, not competing current identities.

## Next work and release gates

1. Complete the native audio command/control tour and current-candidate viewport acceptance. Verified deployment preserved all nine preferences and resumed radio. Review and execute UI-34 Bluetooth prompt recovery and UI-35 favorites identity/recovery proposals separately; UI-36 solar theme and UI-37 actual language/theme switching remain OPEN.
2. Complete the current-candidate physical UI tour and remaining audio/Bluetooth/network/media recovery probes. Finish genuine Netflix movie/audio/resolution and YouTube checks, and resolve the approved music-service/account proof; the owner has Netflix, and Spotify Premium has not been supplied.
3. Complete per-action feedback/navigation performance, five actual graphical-session starts, required cold-boot/offline checks, media-load/system usability and eight-hour interactive stability on the accepted candidate.
4. Resolve runner/build-host admission, build and inspect the final image, retain software/license/source provenance and redistribution evidence, then prove clean installation, backup/restore, cold boot/offline behavior and all delivery requirements. Historical green CI/images do not accept the final candidate.

Use [acceptance.json](docs/acceptance.json) and [Definition of Done](docs/DEFINITION_OF_DONE.md) as the requirement-by-requirement release gate. Tests, source publication, successful deployment and product acceptance are separate states. Continue all open work; do not mark the project complete from a targeted test result.
