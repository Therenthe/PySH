# Ambient material — 2026-10-04

Local candidate `7d525cef84cb` contains42 manifest files. Publication and device activation are recorded separately; this document does not certify hardware acceptance.

The sky uses150 stars with varied opacity/radius, two city layers with83 building-specific windows and soft overlapping clouds without an SVG blur filter. Moon material is the unchanged NASA image documented in `docs/licenses/moon-surface-nasa.md`; computed approximate phase still determines the illuminated mask. The static texture does not imply current libration or a live observation.

Optional aircraft and lunar dust have bounded, randomized scheduling. Aircraft are decorative; lunar dust defaults off and is limited to a visible Moon under clear night skies. Reduced motion, leaving Home and hidden document state stop encounters. EN/RO settings describe their decorative nature.

Independent usability review found duplicate pending saves for these two switches. The integrated fix uses a synchronous lock, disabled controls, bilingual Saving feedback, authoritative preferences and deliberate retry after failure. Its dedicated pending state also prevents idle entry independently of another operation clearing generic busy state.

Before the pending fix: full UI326/326 passed; backend314 passed with22 Windows platform skips. After the fix: TypeScript and production Vite build passed;20 targeted browser tests passed in46.5s including pending/retry/idle, settings persistence, Home customization and artwork. Further anchor/Home idle/recovery results are appended after completion.

Independent visual review covered20 Moon phase cases and eight800×480 captures across EN/RO and both themes, with the local image loaded and no external texture requests. The root reviewer inspected the RO night capture. Disc/terminator area was within1% of computed illumination. A decoded1024² RGBA texture is at most4MiB; this estimate does not establish GPU/RSS or native animation performance.

Compact Arrange, edge anchoring, deliberate overlap and forecast1↔5 semantics are retained. All30 product acceptance criteria remain OPEN. Native performance, physical touch and final image acceptance require their own evidence.

Post-fix anchor/Home ambient/action recovery/idle guard suite:68/68 passed in38.8s, EN/RO and both themes. Repository structural check passed; extension keyboard suite26/26 passed after enabling its child-process execution.

Installed source cd1ff4282ebd0142639978b82d110040cbef4d45 on SD as7d525cef84cb; previous98385a22787c retained. Before activation, readable PC backup verified:SHA25610f8b5024f2f232cb9d4ddb099f4ee7785d4674b0fb6e6c179170e0e306cc513. After activation all42 hashes matched, no pending transaction; radio/audio ready at1.520,4.551,7.579,10.596s. Actual private800×480 compositor capture inspected. This verifies deployment/integrity/continuing playback, not a full physical acceptance tour.
