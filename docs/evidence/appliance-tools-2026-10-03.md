# Appliance tooling and observation — partial evidence

2026-10-03. Installed candidate934d0d338e66/source20f19b907359da5aede58b933888c0eb7a5f5be6 remains active. No activation, rollback or storage write was performed for this milestone.

Public `scripts/appliance-release.py` handles identified PySH OS runtime updates, separate-computer backup verification, guarded activation, recorded rollback and interrupted-transaction recovery. Local tests cover unsafe archives, protected preference changes, backup member corruption, dependency-lock changes and refusal before service stop. POSIX-only tests additionally cover real pointer changes, restart/readiness failure, interrupted switches, private backup creation and insecure existing state. These require Linux CI and a separate native procedure proof; passing filesystem fixtures does not accept DEL-01.

Public `scripts/observe-stability.py` verifies runtime hashes/source identity, guards candidate changes before/after each sample, observes only the application cgroup and records explicit incomplete/unreadable samples. Unit restarts, sampling gaps and interrupted observations remain visible. API evidence is a boolean projection without accounts, preferences or URLs. Output is private. Telemetry completion never automatically accepts REL-01.

First native smoke run refused before creating output: `unit_supervisor_mismatch`. The unit invokes `/opt/pysh/current/scripts/run-hub.py`, while the guard compared its text to the resolved release path. The corrected guard resolves the actual script argument against the verified candidate, accepts the owned current alias/relative script and rejects an unrelated script carrying a matching extra argument. No production process or configuration was changed. A repeated native probe is required.

Local full Python regression:132 passed,21 skipped on Windows, one existing Starlette/httpx deprecation warning. TypeScript and repository checks passed. Linux-specific checks and native public-tool execution remain OPEN.

The earlier private read-only eight-hour observer was rechecked against its actual user-unit handle: active, same invocation/PID;1175.801 elapsed seconds,40 samples and zero observation errors. This partial measurement is neither an eight-hour result nor an idle-memory claim. Netflix was left open. Full-panel live view is available privately via loopback on the development PC, with compositor snapshots through SSH approximately once a second; no continuous recording or browser-account instrumentation.

Local successor package4a133daa7278 has40 files. Independent archive verification reads every member/hash, compares all39 earlier hashes unchanged and checks that `dist/THIRD_PARTY_NOTICES.txt` contains the full React19.3.0, react-dom19.3.0 and scheduler0.28.0 MIT notice texts. This successor is not installed or verified in a new OS image. DEL-01/DEL-02, REL-01 and full product acceptance remain OPEN.
