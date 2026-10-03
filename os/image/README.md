# PySH OS image candidate

Experimental Pi 4 Trixie ARM64 image definition; see ADR-0006. The corrected image source d61ec8d/runtime a32c29065d6d passed physical USB boot, recovery SSH, root growth, display/touch and five cold boots including offline use. These are historical results for that exact image, not acceptance of every subsequent source build. See [current status](../../STATUS.md) and [cold-boot evidence](../../docs/evidence/os-cold-boots-2026-10-03.md). Full product acceptance remains OPEN.

The config and layers use actual rpi-image-gen v2.8.0 metadata. `prepare-payload.py` accepts only committed source, stages the explicit runtime allowlist and records source/runtime/builder identities. `ci-build.sh` verifies the archive and each runtime file inside a new image chroot, installs isolated Python dependencies and builds the disk image. It never writes a block device.

The `Build experimental PySH OS` workflow runs on the experimental branch, using a standard ARM64 runner and ephemeral Debian container. Normal Windows development needs no container or system dependency changes. Generated payload/build/image files are ignored; checksums and manifests accompany successful private build artifacts.

Current gates include fresh-image first-use DRM preparation, complete media/network/Bluetooth flows, sustained stability and acceptance on one final candidate. CI builds and offline image checks, provisioning, physical boot and product acceptance are distinct evidence. SSH intentionally does not start without a provisioned recovery administrator key. The original SD remains the owner's offline recovery medium; the installed appliance boots from the USB drive.

## Recovery provisioning for an experimental test card

After writing the candidate to a separately identified test card, copy exactly one public SSH key (OpenSSH ed25519 recommended) into the FAT boot partition as `pysh-recovery.pub`. Never copy a private key. First boot validates and installs it for `pysh-admin`, with a separate sudo recovery role; the everyday `pysh` account has no sudo rights. SSH accepts only public-key authentication for `pysh-admin`, never root/password login. With no valid key, SSH remains unavailable. Preserve the original working card until recovery login and a physical boot have passed.

The key file is renamed to `pysh-recovery.provisioned.pub` after provisioning; replacing it with a new `pysh-recovery.pub` on an offline test card rotates the authorized recovery key on the next boot. Invalid keys fail provisioning and require correcting the offline boot file. No keys are built into the generic image or committed.

The CI checks the actual generated ext4/VFAT and MBR files: runtime hashes, session/service assets, firmware listing, recovery policy and package inventory. This is image inspection, not a physical boot test. Compressed image parts are separate artifacts under 300 MiB, with per-part and joined-image SHA256 checksums; join the numbered parts in order before writing. The connector has a 512 MiB artifact download limit, so a single archive cannot be used for this image.

## Partition identity

ADR-0008 replaces upstream by-slot mount references with the UUIDs used when creating each filesystem. CI probes ext4/vfat UUIDs and matches fstab and root cmdline before packaging. Physical USB boot and mounted root expansion were verified on the corrected image and documented in [first-boot evidence](../../docs/evidence/os-first-boot-2026-10-03.md). That observation does not prove other storage models or a newer image. The image starts with a 4096M root. ADR-0009 adds guarded first-boot growth for this exact mounted UUID-backed DOS layout, with a throwaway loop-image CI gate before building. Failures do not produce a success stamp and leave recovery/kiosk available at the original capacity where boot is intact.
