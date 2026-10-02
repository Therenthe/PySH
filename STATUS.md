# PySH status

Updated: 2026-10-02.

## Current milestone

Existing local application migrated and published to private GitHub repository https://github.com/Therenthe/PySH. GitHub is now the canonical source. Import commit: 6ff604b7ebb9c80b11765ea59917971071afba78; local main and origin/main are synchronized. A separate runtime preview is now staged and running on Pi; no OS or autostart changes performed.

## Verified locally

- Original functionality document identified and hash matched to the working copy.
- Legacy Git has no commits or remote; original source remains intact.
- React/TypeScript and Python implementation imported into app/ and services/.
- 39 Python tests pass against relocated sources using the existing Python 3.12 environment (one upstream deprecation warning).
- TypeScript check and Vite production build pass with Node 24.19.0 after materializing copied dependency packages. This is not a clean-install verification.
- GitHub CI run 37030198002 passed: frontend production build and backend tests/structure on Python 3.12 and 3.13, using clean runner dependency installs.
- See docs/MIGRATION.md and docs/evidence/migration-checks.md for scope and evidence.
- Runtime package 5a7b844f486f: 33 hashes and archive checksum verified; extracted backend serves the static index. Independent static migration review found no actionable regression.

## Acceptance and limitations

- All 30 product criteria remain OPEN. The repaired corrupt-file/recovery probe passes on candidate bfb3cdd16723; full product acceptance remains pending. The candidate runs as an isolated preview, not accepted for release.
- Historical preparation: 7 PASS in legacy ledger, preserved in docs/history. Active preparation entries are OPEN because private historical evidence was not imported.
- Existing runtime uses a graphical desktop session. The dedicated-session image builder is implemented on the experimental branch; actual appliance boot has not passed hardware acceptance.
- Wired SSH password authentication succeeded on 2026-10-02. Pi 4 / Debian 13.4 ARM64 confirmed, about 6 GiB disk space available. Both wired and wireless interfaces are up.
- Pi source checkout created at ~/PySH from verified GitHub history; Git integrity and repository checks passed. Origin points to Therenthe/PySH. Private GitHub authentication on Pi is not configured; source updates can be transferred as verified Git bundles over SSH.
- Legacy package 32d75c593e83 matches all 33 runtime manifest hashes. No current/previous links or installed launcher; hub/preview services inactive and no app process observed. These are the pre-preview observations; the isolated preview is now running, with no autostart activation.
- Saved Wi-Fi nested buttons and untranslated security labels corrected. Four browser regression tests cover EN/RO and both themes at 800×480; the full browser/product matrix and physical touch acceptance remain incomplete.
- Home/Radio translations, idle/end states and clipped radio controls corrected on the full-touch-ui branch. Twenty browser tests now cover EN/RO, both themes, all pages/settings, setup, dialogs, keyboard, pairing and failure/recovery. Newly found filter, shortcut and accessible-control defects corrected. See docs/evidence/ui-audit-2026-10-02.md; Pi candidate 1cc15fa4e625 is running; real Home capture, Bluetooth disconnect/reconnect and radio streaming checked. Full physical matrix remains pending.
- Real panel capture confirms the Romanian setup screen at 800×480. A generated local WAV played through mpv/PipeWire to the existing Bluetooth speaker; user confirmed audible output at 25% sink volume. See docs/evidence/pi-preview-2026-10-02.md.
- User confirmed first-run setup and Settings / Bluetooth via physical touch; real panel capture shows the connected speaker.
- Appliance service mode implemented behind an explicit launch flag, preserving desktop behavior. 43 Python and 24 browser tests pass, including EN/RO/themes and backend reconnection; device acceptance remains OPEN. See docs/evidence/service-mode-2026-10-02.md and ADR-0007.
- A separate experimental OS branch has produced an ARM64 image successfully in GitHub Actions (run 37040841447). Recovery provisioning, image inspection and real boot remain pending; it is NOT FLASH-READY.
- Complete touch, Bluetooth pairing/reconnect/radio/recovery, DRM/streaming accounts, cold boots, 8-hour stability, performance and clean install/rollback remain acceptance work.

## Next

1. Publish and verify the expanded UI candidate on Pi, then complete real radio and Bluetooth recovery checks.
2. Continue vertical product acceptance, beginning with setup and audio/Bluetooth recovery flows.
3. Keep PC/Pi source checkouts synchronized with verified GitHub commits; protect legacy releases and persistent data during deployment.
4. Follow docs/ROADMAP.md and accepted ADRs for appliance transition.

## Appliance build in progress

User requested autonomous full delivery and PySH OS flashing after verification. Experimental rpi-image-gen v2.8.0/Pi4/Trixie configuration and ARM64 CI build are prepared on feat/pysh-os-image. ADR-0006 records the build-only container exception and known gates. No image is accepted or flash-ready; no live OS changes. Recovery key provisioning, service-mode UX, target package provenance, actual boot and backup/restoration remain required.
## Real device audit and OS progress

48 real Pi screens inspected across EN/RO/themes, with 120 navigation samples. Service-mode media stop/return and preference preservation passed. Font/night contrast defects recorded as UX-03 FAIL; fixes and permanent browser checks prepared. See docs/evidence/pi-legibility-2026-10-02.md. An application backup is verified independently on PC; original card/desktop retained. Updated OS build and actual boot remain next.

## Content recovery candidate

Active isolated Pi preview: `24f207c79081`, from main `b853a5e`. Its 48-screen real audit no longer reproduces the font/night text contrast defects. Eight synthetic audio encodings decode on the real player; a corrupt MP3 incorrectly reports idle. A coherent repair covers mpv events and radio/weather/library/video retry, with 46 Python and 36 browser tests passing. See [content recovery evidence](docs/evidence/content-recovery-2026-10-02.md). The experimental OS branch has built and inspected a recovery-capable image; USB boot addressing and physical recovery/boot still require verification. No storage has been flashed.

Active preview advanced to `bfb3cdd16723`: corrupt file → visible error → valid WAV recovery → natural end passes on Pi. Main is `607496a`. The image branch incorporates this runtime and ADR-0008 UUID partition references, with actual filesystem inspection before packaging. Physical boot, recovery provisioning, target storage choice and complete DoD remain OPEN.
