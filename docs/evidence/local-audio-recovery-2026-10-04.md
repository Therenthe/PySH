# Local audio recovery notice — prepared, not installed

The local audio error now identifies the file by basename, explains that playback failed without guessing a codec cause, and offers Replay using the existing single-intent selection flow. Failed Replay uses one existing API error notice. Radio errors remain separate. All app-owned text is EN/RO.

The usability and visual auditors reviewed the recovery flow and both themes at 800×480. Body/identity text is 16px, secondary text 14px; measured contrast was 12.72/13.44 for primary text and 5.33/7.83 for secondary text. These are browser measurements, not physical touch acceptance.

Root validation after integration: 474 Playwright cases passed; TypeScript, production Vite build and repository structure checks passed; 336 backend tests passed with 22 platform-dependent skips; 27 browser-extension keyboard tests passed. The initial sandbox Node spawn restriction was resolved by running that local test with approved process permissions.

Installed runtime remains `9424277cdab1`, source `060d57be00472fa7c1c81b77ad87ab7473e01e44`. This notice is not installed yet. A fresh read-only native check verified all 48 runtime files, no pending transaction and radio progress 1700.438→1709.473 seconds. Home, HomeLayout and ambient-home.css have no changes relative to that installed source. No saved user layout or radio preference was modified.

Native local-file decode/control/error probes and physical touch remain OPEN. The official cached Raspberry Pi APT signature and Packages hash were independently verified with the installed sqv default policy; the retained FFmpeg package hash matches that authenticated index. No package was installed and no test media was played during this check. This authenticates the current cached index, not an unavailable historical download receipt.
