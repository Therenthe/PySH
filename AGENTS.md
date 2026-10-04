# Working on PySH

Read STATUS.md first, then docs/PRODUCT.md, docs/ARCHITECTURE.md, docs/DEVELOPMENT.md, docs/WORKFLOW.md and docs/DEFINITION_OF_DONE.md. Use docs/adr/ for decisions and docs/OPERATIONS.md before device work.

- GitHub is the canonical source once publication is verified; commit code, decisions and status together. Never leave the only copy of a change on the Pi.
- Preserve the imported application and original SD recovery medium. The live corrected USB image uses a dedicated labwc/greetd graphical session with direct appliance boot; this implementation is experimental and full product acceptance remains OPEN. Desktop migration scripts and appliance operations are different workflows: read current STATUS and OPERATIONS before choosing one.
- Keep UI in app/, local API/adapters in services/, system configuration in os/, board-specific material in hardware/. Build UI on the PC; no Node runtime on Pi.
- Do not introduce Electron, containers, cloud accounts or replacement network/audio managers without a reasoned ADR. Never relax device permissions globally.
- Run the verification commands in docs/DEVELOPMENT.md before committing. Update STATUS.md and docs/acceptance.json with real evidence. Automated unit tests do not prove hardware acceptance.
- All app-owned UI and accessible names must support EN/RO at 800x480. A shortcut is not proof of streaming/DRM playback.
- Show exact remote commands before execution and useful results afterwards. No secrets, private logs, browser profiles or device backups in Git.
- Apply the versioned skills under skills/ when relevant. Current STATUS and accepted ADRs override historical phase/architecture statements in imported references or skills.
- Do not replay historical cleanup scripts. Do not flash storage, alter active networking or activate autostart as part of a repository migration.

## Unpacked Chromium extension updates

When background.js or its imported scripts change, migrate the manifest service_worker entry URL as well as its version. The appliance existing profile retained an old MV3 worker after file-path and version changes; a fresh profile concealed that failure. Verify the actually loaded worker and trusted Return in the existing service profile. Never reset browser profiles or inspect accounts to repair this. See docs/evidence/external-return-2026-10-04.md.
