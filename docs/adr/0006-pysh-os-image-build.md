# 0006 — Experimental PySH OS build

Date: 2026-10-02. Status: Accepted for experimentation; not release acceptance.

Context: user explicitly requests complete appliance delivery and a PySH OS image. PC is Windows without WSL; live Pi has only about 6 GiB free and must remain usable. ADR-0002/0003 remain proposals until boot validation. Upstream rpi-image-gen v2.8.0 is pinned to commit 262d4df5a9f9d4133370465399a7958a7c22cdc7. Its default trixie-minbase pulls networkd/iwd, while PySH requires existing NetworkManager adapters.

Decision: build an experimental Pi 4 Trixie ARM64 image with Raspberry Pi firmware/kernel layers, custom minimal suite, NetworkManager/wpasupplicant, BlueZ, PipeWire/WirePlumber, greetd/labwc, Chromium and the preserved Python/React application. This is a custom minimal image, not a claim that an official Lite binary image was installed. No desktop suite is included.

Use a standard GitHub ARM64 runner and an ephemeral privileged Debian build container. This container is build infrastructure only, never the product runtime or live Pi. It is justified by the absent Windows Linux builder; upstream does not formally support container hosts, so actual logs/build/boot evidence are required. Record the resolved host digest and installed target package manifest before release. Target APT inputs are not yet snapshot-pinned: reproducibility is not established by pinning the builder alone.

Consequences: first artifacts are marked NOT FLASH-READY. They do not yet provision recovery SSH access or implement the complete service-mode exit experience. A physical boot, panel/touch/audio/network checks, recovery provisioning, backup/restoration, five cold boots and product acceptance remain required. No live card is flashed or live OS changed by this build. No password, private key or user data is embedded in source/artifacts.

Sources: [upstream v2.8.0 documentation](https://github.com/raspberrypi/rpi-image-gen/tree/v2.8.0), [upstream custom layer example](https://github.com/raspberrypi/rpi-image-gen/tree/v2.8.0/examples/webkiosk), [GitHub runner reference](https://docs.github.com/en/actions/reference/runners/github-hosted-runners).
