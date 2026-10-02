# PySH OS image candidate

Experimental Pi 4 Trixie ARM64 image definition; see ADR-0006. It has not passed a physical boot and is not flash-ready.

The config and layers use actual rpi-image-gen v2.8.0 metadata. `prepare-payload.py` accepts only committed source, stages the explicit runtime allowlist and records source/runtime/builder identities. `ci-build.sh` verifies the archive and each runtime file inside a new image chroot, installs isolated Python dependencies and builds the disk image. It never writes a block device.

The `Build experimental PySH OS` workflow runs on the experimental branch, using a standard ARM64 runner and ephemeral Debian container. Normal Windows development needs no container or system dependency changes. Generated payload/build/image files are ignored; checksums and manifests accompany successful private build artifacts.

Known gates: actual upstream build validation, target package inventory/snapshot provenance, recovery key provisioning, appliance service-mode UI, panel/touch/network/audio boot, backup/restoration and complete product acceptance. SSH intentionally does not start without a provisioned recovery administrator key. Current runtime and desktop on the existing Pi are preserved.
