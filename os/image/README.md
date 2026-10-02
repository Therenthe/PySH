# PySH OS image candidate

Experimental Pi 4 Trixie ARM64 image definition; see ADR-0006. It has not passed a physical boot and is not flash-ready.

The config and layers use actual rpi-image-gen v2.8.0 metadata. `prepare-payload.py` accepts only committed source, stages the explicit runtime allowlist and records source/runtime/builder identities. `ci-build.sh` verifies the archive and each runtime file inside a new image chroot, installs isolated Python dependencies and builds the disk image. It never writes a block device.

The `Build experimental PySH OS` workflow runs on the experimental branch, using a standard ARM64 runner and ephemeral Debian container. Normal Windows development needs no container or system dependency changes. Generated payload/build/image files are ignored; checksums and manifests accompany successful private build artifacts.

Known gates: actual upstream build validation, target package inventory/snapshot provenance, recovery key provisioning, appliance service-mode UI, panel/touch/network/audio boot, backup/restoration and complete product acceptance. SSH intentionally does not start without a provisioned recovery administrator key. Current runtime and desktop on the existing Pi are preserved.

## Recovery provisioning for an experimental test card

After writing the candidate to a separately identified test card, copy exactly one public SSH key (OpenSSH ed25519 recommended) into the FAT boot partition as `pysh-recovery.pub`. Never copy a private key. First boot validates and installs it for `pysh-admin`, with a separate sudo recovery role; the everyday `pysh` account has no sudo rights. SSH accepts only public-key authentication for `pysh-admin`, never root/password login. With no valid key, SSH remains unavailable. Preserve the original working card until recovery login and a physical boot have passed.

The key file is renamed to `pysh-recovery.provisioned.pub` after provisioning; replacing it with a new `pysh-recovery.pub` on an offline test card rotates the authorized recovery key on the next boot. Invalid keys fail provisioning and require correcting the offline boot file. No keys are built into the generic image or committed.

The CI checks the actual generated ext4/VFAT and MBR files: runtime hashes, session/service assets, firmware listing, recovery policy and package inventory. This is image inspection, not a physical boot test. Compressed image parts are separate artifacts under 300 MiB, with per-part and joined-image SHA256 checksums; join the numbered parts in order before writing. The connector has a 512 MiB artifact download limit, so a single archive cannot be used for this image.
