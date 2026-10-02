# PySH status

Updated: 2026-10-02.

## Current milestone

Existing local application migrated and published to private GitHub repository https://github.com/Therenthe/PySH. GitHub is now the canonical source. Import commit: 6ff604b7ebb9c80b11765ea59917971071afba78; local main and origin/main are synchronized. No device deployment or OS changes performed.

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

- 30 product criteria remain OPEN. No current Raspberry Pi candidate accepted.
- Historical preparation: 7 PASS in legacy ledger, preserved in docs/history. Active preparation entries are OPEN because private historical evidence was not imported.
- Existing runtime uses a graphical desktop session. Direct appliance boot, Lite base and image builder are not implemented.
- Wired SSH host identity matches the previously trusted Pi; batch user authentication failed. Live Pi state and installed build are not verified. Last local package: 32d75c593e83.
- Browser E2E suite absent. Wi-Fi list has nested button markup and at least two untranslated English labels; fix before claiming UI acceptance.
- Bluetooth audio, real touch, DRM/streaming accounts, cold boots, 8-hour stability, performance and clean install/rollback remain acceptance work.

## Next

1. Restore SSH user authentication for the wired Pi target (connection details remain local); perform read-only inventory before deployment.
2. Fix known UI issues and add real EN/RO browser flows.
3. Reconnect to Pi read-only, inventory active release and recover any device-only changes before deployment.
4. Follow docs/ROADMAP.md and accepted ADRs for appliance transition.
