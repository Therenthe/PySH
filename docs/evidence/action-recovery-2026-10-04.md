# Bluetooth and location recovery — 2026-10-04

Runtime candidate `98385a22787c`; installation is not claimed by this source verification.

Bluetooth power, scan, pair, connect, disconnect and forget retain the exact failed action for explicit retry. Pending locks duplicate actions. Errors and pending status remain visible in the active dialog/settings; after closing that context, an accessible band returns to it. If the mutation succeeded but its state read failed, retry reads state only, without repeating the mutation.

Location save failure retains search results and the selected location for retry. Geocoding failure retains the query. Accepted location PATCH followed by failed state read preserves the accepted preferences; backend recovery only repeats GET. Pending and unacknowledged errors block both Home ambient and other-page screensaver, including after navigation. Error dismissal is explicit; pending cannot be dismissed.

Independent isolated audit:52 distinct EN/RO, Ink/night,800×480 recovery and guard cases passed. Buttons in the off-context band measured at least48px, keyboard foreground checked, captures inspected. Root integrated regression:316/316browser cases passed in5.5minutes. TypeScript and production build passed;41allowlisted runtime files packaged. Fixtures do not prove hardware association, physical touch or speaker output.

The previous-source GitHub run37157162597 passed253browser cases and failed one immediate weather/forecast spacing read. An isolated auditor subsequently passed48Arrange edge cases and8spacing cases across languages/themes, including64reloads; settled spacing was exactly16px. The negative CI value was not reproduced. The spacing probe now advances its virtual clock400ms and reads both DOMRects atomically within expect.poll, retaining the strict16px requirement. Application layout was not changed for that test correction.

All product criteria remain OPEN until same-candidate native acceptance.
