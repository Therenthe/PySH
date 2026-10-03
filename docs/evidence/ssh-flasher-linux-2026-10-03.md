# SSH flasher — Linux kernel/FAT proof

2026-10-03. The18 focused flasher tests passed; full local suite153 passed/22 platform skips. These are not physical SD acceptance.

First owned-loop fixture failed at topology validation before formatting or writing. `lsblk --json` with PATH and no NAME was flat on the target; the helper/fixture had expected a tree. Both now request `--tree` explicitly, preserving mounted-descendant checks. The one leftover loop mapping was separately verified against the exact owned source file and confirmed unmounted before detach. No physical disk was used by either fixture.

Repeated fixture completed on two newly created private sparse files,277,872,640 bytes each, with exact PySH FAT offset/size and a synthetic1MiB Linux root partition. Real block-device exclusive open, streaming write, fsync/BLKFLSBUF and independent full raw readback succeeded. A syntactically valid fixture-only public key was written to the FAT boot partition, unmounted/synced, remounted read-only and hash-verified. All owned loops detached; no cleanup errors.

Helper SHA256b97c25158e5d0cff849e5f6a8b724dde8b6973fcb58259071acc617d6a46e78d. Raw readback before provisioning SHA256f2fe43054e319b71f99db56ef87960ef64297b6db2b7133a038dd8e97c31a894. Fixture public-key SHA25691da3274dc5d8573eb3882d43b638f8010d8d9cb5b23de98dd739f5a2fc59af8. Raw after provisioning SHA2561efab6198762ab6906d111f0beb6fb63702eb08e99f1d730d1a3181b6046953c. The different raw hash is intentional: public-key provisioning changes FAT bytes, so exact image verification and key verification are separate proofs.

Production policy still permits only inactive physical `/dev/mmcblkN` disks with explicit CID/capacity and separately verified full PC backup; the fixture's snapshot override accepts only its exact owned loop backing files and does not change production policy. Its synthetic root is not an OS and is not boot-tested.

Owner inserted the original SD while USB continued running. Read-only inspection confirmed root remains `/dev/sda2`, UUID5610e056-221b-46c9-8046-65c9adb6a5c1, while `/dev/mmcblk0` is15,962,472,448 bytes with two unmounted partitions. CID is recorded privately, not published. The PC console whole-card backup started; independent verification and actual image write/readback/provisioning/physical boot remain pending. No SD erasure is claimed by this evidence.
