# Working on PySH

Read STATUS.md first, then docs/PRODUCT.md, docs/ARCHITECTURE.md, docs/DEVELOPMENT.md, docs/WORKFLOW.md and docs/DEFINITION_OF_DONE.md. Use docs/adr/ for decisions and docs/OPERATIONS.md before device work.

- GitHub is the canonical source once publication is verified; commit code, decisions and status together. Never leave the only copy of a change on the Pi.
- Preserve the imported application. The current runtime still requires a graphical user session; direct appliance boot is a target, not an implemented fact. Do not remove desktop/recovery on the existing device during migration.
- Keep UI in app/, local API/adapters in services/, system configuration in os/, board-specific material in hardware/. Build UI on the PC; no Node runtime on Pi.
- Do not introduce Electron, containers, cloud accounts or replacement network/audio managers without a reasoned ADR. Never relax device permissions globally.
- Run the verification commands in docs/DEVELOPMENT.md before committing. Update STATUS.md and docs/acceptance.json with real evidence. Automated unit tests do not prove hardware acceptance.
- All app-owned UI and accessible names must support EN/RO at 800x480. A shortcut is not proof of streaming/DRM playback.
- Show exact remote commands before execution and useful results afterwards. No secrets, private logs, browser profiles or device backups in Git.
- Apply the versioned skills under skills/ when relevant. Current STATUS and accepted ADRs override historical phase/architecture statements in imported references or skills.
- Do not replay historical cleanup scripts. Do not flash storage, alter active networking or activate autostart as part of a repository migration.
