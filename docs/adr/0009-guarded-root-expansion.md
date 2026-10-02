# 0009 — Guarded first-boot root expansion

Status: Accepted for the experimental image; Initial Linux offline integration passed; extended mounted-loop integration and physical online growth acceptance pending.
Date: 2026-10-03.

The UUID image has a fixed 4GiB ext4 root, wasting remaining capacity on larger SD/USB/NVMe devices. Upstream's by-slot mount assumptions were replaced by ADR-0008; expansion must not guess device names or tolerate failed resize as success.

Install a dedicated root-only first-boot service in newly built images. Resolve the actual mounted root and boot through findmnt kernel MAJ:MIN and explicit lsblk fields. Require plain partitions 2/1 on the same canonical physical disk, exact ext4/VFAT UUID fstab entries and the expected DOS/512-byte-sector geometry (boot start16384/size524288, root start540672/size≥8388608). Reject custom/mapped/RAID/GPT/loop production targets. No CLI target override exists.

Grow only the verified final partition with growpart, synchronize udev/kernel size, then resize2fs and verify filesystem bytes before atomically writing a root-owned success record. An error leaves no stamp. Only genuine growpart NOCHANGE proceeds to retry an unfinished filesystem resize. UUIDs, first partition, starting sectors and disk identity must remain unchanged. The success record never bypasses target guards.

Order growth after local filesystems and recovery provisioning, before the graphical session. Failure must not become a Requires dependency of recovery SSH or greetd. A five-minute service timeout bounds first graphical startup. Recovery may start while growth proceeds. No existing Pi/card is modified by this source/build change.

A required CI job creates only its own sparse loop images. It tests wrong UUID, foreign boot disk untouched, wrong partition, production loop rejection, growth errors, ambiguous NOCHANGE, failed resize without stamp, actual retry, idempotency and boot preservation. Extended cases reject extra/GPT layouts, resolve actually mounted root/boot, grow a private loop backing file 6→7GiB and resize mounted ext4 while preserving a file and UUIDs. Its test-only internal loop exemption is never selected by the installed entrypoint. The image inspector compares installed script/unit bytes to source; the builder verifies systemd units.

The runner's unmounted ext4 growth does not prove mounted first-boot expansion or real mmc/sd/nvme kernel partition refresh. Those require the experimental physical boot, preserved original SD and administrative recovery. No product PASS is implied by implementation.

Alternatives: keep fixed4GiB (insufficient long-term capacity); generic cloud-init (unnecessary broader provisioning); copy upstream best-effort `|| true` (could stamp failed growth as success); raspi-config device assumptions (not our explicit UUID/layout contract).

Primary tool semantics: [growpart](https://manpages.debian.org/trixie/cloud-guest-utils/growpart.1.en.html) and [resize2fs](https://manpages.debian.org/trixie/e2fsprogs/resize2fs.8.en.html).
