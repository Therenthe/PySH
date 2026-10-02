# Service mode regression — 2026-10-02

Scope: `feat/appliance-service-mode`, application changes accompanying ADR-0007. These checks are automated PC evidence, not physical OS acceptance.

- Python 3.12: 43 tests passed, including authenticated return, unchanged preferences, cancellation boundary and failed media stop.
- TypeScript compilation and Vite production build passed.
- Browser: 24 tests passed, zero skipped/flaky, EN/RO × E-Ink/night at exactly 800×480 with touch input. Four new cases cover confirmation cancellation, service entry, diagnostics/return controls and backend outage/reconnection. Existing full-page/setup/settings/media regression passes.
- The initial service recovery test failed in all four variants: backend reconnection left the connection error visible. Corrected state refresh to clear only `backend_unavailable` after a successful response; unrelated errors remain visible. Full matrix passed after the repair.
- Romanian night service capture visually reviewed: readable labels, controls inside viewport, diagnostic and return targets ≥48px. Screenshot fixtures remain in ignored test results.

BOOT-02 remains OPEN until this mode and the separate administrative recovery channel are tested on the OS candidate. Desktop exit is preserved for ordinary sessions. No existing Pi boot configuration was changed.

Related OS progress: experimental image build [37040841447](https://github.com/Therenthe/PySH/actions/runs/37040841447) passed for source `925d7e85de91fcd5498a682dcbdebad746e98edc`, runtime `da4dcbe4055b`, pinned builder `262d4df5a9f9d4133370465399a7958a7c22cdc7`. Archive size 662307425 bytes, artifact ZIP digest `a7f27734a069bf7cd373be8dc687ae24110cb7c040a42bda8726682b94336b9a`. Build logs confirm the PySH customization hook, Python runtime installation and image partition creation. This proves construction only. Image inspection, recovery provisioning and physical boot remain pending; NOT FLASH-READY.
