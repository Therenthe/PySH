# Functional recovery fixes

After the physical SD milestone, source review identified four bounded defects:

- Manual weather refresh reused recent cache. It now forces a provider request; failure retains the original timestamp/data marked stale, and successful retry refreshes the cache. Scheduled requests retain normal caching.
- Unreadable selected media directories appeared empty. They now return a safe retryable error. Mixed libraries retain readable entries and expose a localized partial warning/retry; all unavailable roots do not pretend to be empty.
- Setup could only advance and could not be revisited. Back is present at steps1–3; settings can reopen it with confirmation and leave confirmation, preserving saved preferences and setupComplete.
- HTML local video kept playing after audio-output loss. It now pauses, explains loss, and requires explicit Play after reconnection. Decode Retry remains available without audio; it does not bypass audio gating to start playback.

Reviewed implementation: full backend160 passed/22 platform skips, existing Starlette warning; TypeScript and production build passed; extension26 passed; complete browser suite102 passed in43.4s across EN/RO and both themes at800×480. Initial Windows sandbox test-runner spawn failures were rerun under the owner; initial Retry regression found by the broader product tests was corrected before the final full suite.

Packaged runtime5aef8c81c90b,40 allowlisted files, source803b09734eb4171d35942ba923704e71e29529fe. Controlled native activation on SD completed with exit0; previousc8ac9c709acb remains available. Backup was independently read and verified on PC, SHA2562769c54cb6d7ddbb7c16d64eda6f780fc19ab3f347e833d57527949c7b5f9637. The public update tool verified installed files and protected preferences/configuration. The owner radio was playing before activation and resumed afterwards with progressing playback and audio ready. Actual compositor capture showed Home on the new release. Complete physical acceptance of the four flows remains OPEN.
