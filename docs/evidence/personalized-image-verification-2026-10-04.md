# Personalized OS image verification — 2026-10-04

GitHub source 1cda67c67fa36a5ac984f64f4342e140b79fe07e passed the complete application workflow 37152452942 (frontend including Playwright, backend Python3.12/3.13). OS image workflow37152450359 succeeded using builder262d4df5a9f9d4133370465399a7958a7c22cdc7. The image's runtime is17afa59162cc; installed runtime remainsb180f17fb355.

All five downloaded artifact ZIP digests were checked. Ordered image parts matched PART-SHA256SUMS, gzip SHA256 ebb7859a8fca9cc44192f7ec3cacbd59866c046fe0ea10a91545778dc17245ed, decompression CRC passed. Raw image is4571791360bytes with SHA2566a4ecffe5af4f283b8dab90416f63531f75ee14a9fa2474b76a04605f851fdb4. MBR partition types/offsets/sizes match build metadata.

An independent read-only ext4 inspection on the PC verified root UUID8656c1a0-3323-451f-ac3d-eaf6e745e00e, build-source marker and all41 runtime-file SHA256 values. Comparison with the installed release found only CRLF/LF differences in dist/THIRD_PARTY_NOTICES.txt and the three font CSS/license files; each normalized byte sequence matched. Application unit cwd/appliance flag, native keyboard origin, touch identity matrix, server-decoration setting and Chromium Translate disabling flags were checked directly inside the image.

Private evidence: .runtime/ui-image-1cda/verification.json and independent-root-verification.json. No disk was flashed. Physical clean-image boot and full product acceptance remain OPEN; the artifact retains its EXPERIMENTAL, NOT FLASH-READY label. These checks do not prove performance, streaming service playback or hardware installation acceptance.
