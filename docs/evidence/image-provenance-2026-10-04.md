# Prepared final-image provenance collector

Repository validation:347Python tests passed,22platform-specific skips; TypeScript and Vite build passed;27extension keyboard tests and repository structure passed. The first keyboard test invocation was blocked by Windows child-process EPERM in the sandbox; the identical approved invocation passed. No shell/image integration or full product acceptance is inferred from these results.

The final OS image must identify its actual software and retain evidence instead of borrowing the inventory of a running, updated appliance. `os/image/collect-provenance.py` is integrated after image inspection and before packaging in `ci-build.sh`. It reads generated ext4/VFAT files through read-only debugfs/mtools commands; it does not access the live Pi or flash storage.

Required source/builder/build identities, the image source marker and every manifest runtime hash are checked. The artifact records OS package/source versions and architectures, retained copyright hashes, Python distribution metadata and nested license files, cached APT index/Release hashes and available checksums, and boot file hashes with observed package ownership. Relocated firmware ownership requires equal complete bytes. An invalid checksum or different architecture cannot close the installed-package checksum gap.

Root reviewed the implementation and integration; eleven focused tests passed. Cases cover changed runtime and source identities, missing inputs/notices, nested Python notices, firmware byte mismatch, unauthenticated APT metadata, invalid checksum/foreign architecture, path injection and symlink escapes/cycles. These fixture tests do not prove the Linux filesystem reader on a generated image. No new image build, CI execution, device operation or flash was performed for this change.

The artifact remains EXPERIMENTAL, NOT FLASH-READY. Signature verification, package/source download provenance, corresponding source obligations, license choice/redistribution rights, reproducibility, fresh boot and all remaining product acceptance remain separate open gates. Installed runtime670c8155227b/sourcebeab133f81aa3de7d09c4901faef64efb952c0bb is unchanged.
