---
name: pi-smart-hub-delivery
description: Define, implement and verify Pi Smart Hub against its complete product Definition of Done. Use for this project's delivery and release work, including EN/RO and hardware acceptance; not for unrelated Raspberry Pi tasks.
---

# Pi Smart Hub delivery

Locate the project using the current workspace, then read AGENTS.md and docs/PRODUCT.md, docs/DEFINITION_OF_DONE.md, docs/WORKFLOW.md. If using the installed personal copy, do not assume a fixed workspace path. Project docs own feature scope; this skill owns the execution discipline.

- Respect the active phase. Preparation is not a finished app; a frontend shell is not complete multimedia integration.
- Maintain docs/acceptance.json with criterion IDs, status OPEN/FAIL/PASS, candidate build identity, evidence paths and blocking conditions. PASS requires observed evidence; source inspection or a mock response alone cannot prove a hardware flow.
- Work in closed loops: choose a failing/open criterion, implement the smallest coherent flow, run focused checks, inspect the real outcome, repair, rerun affected checks, record evidence. Broaden regression only after a coherent milestone or a changed shared dependency.
- For release, validate all required criteria on the same candidate. Any relevant change invalidates affected results. A known external dependency stays OPEN until supplied or the user explicitly accepts a changed requirement. Do not silently convert unsupported playback into a completed feature.
- EN/RO covers every app-owned visible state and accessible name, including pairing, errors, offline and recovery. Third-party sites retain their own language support; label the boundary honestly.
- Prefer a small local architecture. Do not add accounts, cloud services, containers or a custom OS solely to satisfy a workflow preference.
- Use inexpensive subagents for bounded work/review when useful; reserve serial ownership for real-device changes. Review their evidence, not only their completion claims.
- Before remote execution show the exact command or link the full script and show its invocation; after execution report useful output. Never include secrets in saved command logs.
- Finish the active preparation milestone when its own checks pass. Finish the product only when the full product DoD passes. If physically absent hardware or an account is needed, state that concrete limitation without claiming completion and continue independent work.
