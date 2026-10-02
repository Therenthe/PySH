# Pi inventory and source checkout — 2026-10-02

SSH password authentication succeeded against the wired target supplied by the owner. Host key matches the previously trusted Pi. Credentials, interface addresses and raw session logs are excluded from this report.

Observed: Raspberry Pi 4 Model B Rev 1.5, aarch64, Debian 13.4 trixie; kernel 6.12.75+rpt-rpi-v8; approximately 3.7 GiB RAM and 6 GiB free on root storage. Wired and wireless interfaces both active. Touch input device path is present; panel resolution and physical operation were not retested.

Installed packages: git 2.47.3, Chromium 146.0.7680.80, mpv 0.40.0, BlueZ 5.82, NetworkManager 1.52.1, PipeWire 1.4.2, WirePlumber 0.5.8 (distribution revision suffixes omitted here).

Legacy state: two release directories, 44ceeed1b8e7 and 32d75c593e83. The latter matches all 33 files of its preserved local runtime manifest, with zero missing or changed files. The former is an older, incomplete package relative to the latest manifest. Root source folder contains only the previous environment declaration. No Git repository, current/previous links or installed launcher existed in the legacy runtime directory. Hub and preview services are inactive; no matching hub/player/browser process was observed.

Created a separate source checkout at ~/PySH from a complete Git bundle built from the verified GitHub main history. Bundle SHA-256 b234fb64bba0b227096d718bf22911d1b235d08506dfc910560a16be3ce1426e verified before clone. Initial checkout commit 45db30fabe5ee5e704f3d2a1b2939db3b1bd27bc, identical to GitHub at creation. Origin changed from the local bundle to https://github.com/Therenthe/PySH.git. Working tree clean; git fsck and scripts/check_repository.py passed on Pi.

The existing runtime environment is kept separate from this source checkout. No service activation, dependency replacement or alteration of existing releases was performed. Repository checks and source import do not prove physical product acceptance.

Relocated services.backend.app imports successfully using the preserved Pi Python 3.13.5 venv with isolated PI_HUB_DATA and bytecode writes disabled. No API or kiosk process was started by this check.
