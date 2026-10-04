# Public appliance update/rollback and next SD image

2026-10-03. Public tool `scripts/appliance-release.py` from3ca7e4ef4ec71f84c1510cef20099c73c079baab was used on the real USB appliance. Target root remained UUID5610e056-221b-46c9-8046-65c9adb6a5c1. Each operation prepared a distinct backup, copied it to PC, verified the full outer checksum and every inner runtime/protected-state hash, issued a separate-computer receipt and activated only after that verification.

| Operation | Result | Separately verified backup SHA256 |
|---|---|---|
| Update934d0d338e66→4a133daa7278 | Success; source dda57f080de2f9d03eae01947594a159fae887f6 |9bc485d3afcb294ca830fee8f714eee41812bc5e2ea640191ee5332c9fa095f6|
| Voluntary rollback4a133daa7278→934d0d338e66 | Success; source20f19b907359da5aede58b933888c0eb7a5f5be6 |44f95eac8dce4f2a51736f72d48e61aff27bc8f211d57a335fb5835d0355fed8|
| Return934d0d338e66→4a133daa7278 | Success; source dda57f080de2f9d03eae01947594a159fae887f6 |418597d4662c2c17f20889785fcd609e4a169eb9df54045ba5707eb9007e8804|

Activation independently checked the runtime inventory, protected preference/config hashes, real unit cwd and API readiness. Live whole-compositor inspection saw the Romanian Home screen after update and rollback; a frame captured immediately after rollback was temporarily black before Home appeared. This is rendered UI evidence, not a new physical-touch or audio acceptance result. Runtime4a133daa7278 has40 files; its39 earlier hashes are unchanged, with only the full browser MIT notice asset added. Current previous is934d0d338e66. `recover` after all operations returned current4a133daa7278 with `pending:false`, without a restart. No browser profile, display, network, audio or boot configuration was modified by the tool. Full DEL-01 still needs clean SD-image installation and remaining recovery/restore/hardware proofs.

Application CI37128431057/37128428420: all six backend3.12/backend3.13/frontend jobs completed successfully for dda57f0. Observer native smoke on that source:60.197s, three samples, zero API/observation errors, unchanged candidate/unit identity; one memory sample remained explicitly incomplete. Telemetry was correctly not accepted as complete. Earlier934 eight-hour observation stopped successfully on candidate change:2291.115s,76 samples, zero observation errors, `candidate_changed:true`, `complete_observation:false`. No eight-hour or idle-memory PASS is claimed.

## Verified candidate for SD installation, not written

Image run37127898986 succeeded for source3ca7e4ef4ec71f84c1510cef20099c73c079baab, runtimec8ac9c709acb. All five artifact ZIP digests, the ordered gzip parts and joined gzip were independently verified on PC. Raw image:4,571,791,360 bytes, SHA256de085cdcae326cfafba7ef93c2bf4956efd33aaf650ccdbb4a5cd311f3db5979. Gzip SHA25609a9a4cd6629bbd579dbca0cd540219c1b70bc397d5ad30509b4aea91ca6b776. MBR FAT12 partition starts16384/sectors524288; Linux131 starts540672/sectors8388608. Root UUID4d41b42c-d61a-4052-8898-94191aaa18fc; boot8C78-31C4.

Independent read-only ext4 inspection verified all40 runtime hashes, three complete MIT notices, user-unit/native-host/touch/session and immersive browser settings. Compared with installed4a133daa7278, only the same three font/license stylesheet texts differ by CRLF/LF; code and notice asset match. Metadata remains experimental and full product acceptance OPEN. Recovery-key provisioning, SD write/readback, first physical boot and acceptance on this image remain OPEN.

Live block-device inspection found only the running256087425024-byte SanDisk USB drive; no SD device. Owner confirmed SD is removed and retained separately. Bootloader config has no explicit BOOT_ORDER; official [Raspberry Pi documentation](https://www.raspberrypi.com/documentation/computers/raspberry-pi.html#BOOT_ORDER) defines SD→USB as the default. No EEPROM changes or storage write were performed. The planned SSH flasher must run from USB, identify an unmounted SD explicitly, verify a full separate backup, expose write/readback progress and provision only a public recovery key. Whole-panel viewer remains PC-loopback only, not a public stream.
