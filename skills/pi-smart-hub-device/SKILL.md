---
name: pi-smart-hub-device
description: Audit, prepare, deploy and diagnose the Raspberry Pi used by Pi Smart Hub, including safe storage cleanup, audio/Bluetooth and network integration. Use only for this project's device operations.
---

# Pi Smart Hub device

Read project docs/ENVIRONMENT.md and docs/evidence before using remembered device facts. Refresh model, OS, disk, display, active user and service state after reconnecting. Obtain the current SSH target from local user configuration; reference hardware is Pi 4 4 GB, Debian 13 arm64, DSI 800x480. Do not store its password in scripts or docs.

## Changes and recovery

Show exact remote commands before execution and report outcomes afterwards. Use SSH/process tools rather than typing commands through desktop automation. Keep a dated record of mutations and exit codes. Preserve SSH, active networking, desktop, touch drivers, audio stack and boot firmware.

For cleanup, audit APT installation history and simulate first. "Manual" does not mean "extra": image builders mark many base packages manual. Remove only identified additions/unneeded generated artifacts in the authorized scope. Restrict dependency removal to evidenced additions; do not run broad autoremove when it includes unknown/base packages or kernels. Do not claim a factory baseline when original-image provenance is incomplete.

Back up prior project source, user modifications and relevant config before removal. Verify archive checksum AND readable contents on a separate local destination. For directory removals, validate canonical paths, reject symlinks/out-of-scope roots, check active processes and delete explicit allowlisted paths only. Keep personal media, SSH keys, browser profiles, credentials and unrelated data. Never format the card as a cleanup shortcut.

## Runtime integration

Use the existing NetworkManager, BlueZ, PipeWire and WirePlumber. Local service runs as the desktop user. Device APIs accept structured, allowlisted operations; never provide a generic root shell endpoint. Keep local endpoints loopback-only with origin validation and explicit protection for mutations before browser integration.

Bluetooth: inspect rfkill and Powered state, support app-driven enable/disable, bounded discovery, Agent1 prompts, pair/connect/disconnect/forget. A2DP output to a speaker differs from receiving phone audio. A connected BlueZ device is not yet an active PipeWire output. Verify actual routing and playback. Do not auto-accept unknown pairing requests.

Wi-Fi changes can break SSH. Use NetworkManager rollback/checkpoint behavior and ensure the touchscreen recovery path exists before testing disruptive changes. Do not disable the live connection merely to test an error state remotely.

Build UI on the PC. Keep Python virtual environments isolated; avoid global pip/system Python replacement. Stage a release separately and retain a working rollback target. Never enable autostart pointing at an absent/incomplete application. Validate after changes: SSH, network, graphical session, DSI/touch, BlueZ, PipeWire/WirePlumber, package consistency and disk headroom.
