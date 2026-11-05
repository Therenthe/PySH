# PySH status

R03 candidate: clarify the integrated TV entry and theme badge; align stale regression fixtures. R06 48/48 and R07 96/96 PASS. Installed R02 remains documented below until R03 activation is verified.


## IPTV installed and verified — 5 November 2026

Media → Services → TV now provides the four requested M3U lists, eight requested
favorites, XMLTV with dated official PRO TV/Antena 1 supplements, and independent
MKV recording. Installed runtime `1a9b625f7452`, code
`c8369a3ae47b1f2df364d7892cd453b4e5ebaea8`; previous `a300cbeda2ba` retained.

903 Python PASS/46 platform skips, 108 JavaScript PASS, 36 R05 TV UI cases and
44 affected Media/TV retests PASS. Isolated Linux: 15 multi-rendition FFmpeg
checks PASS. Installed existing-profile Chromium: 22 checks PASS, current-first
guide, actual HLS and saved 1920×1080 MKV playback/delete confirmation. Independent
service: 10 checks PASS with the entire Hub stopped, growing file, unchanged
recorder PID, automatic end and exactly one H.264 video/AAC audio pair.

226 runtime hashes/29 preferences and a separate PC backup verified; network and
gateway preserved. Original preferences/audio/radio/watch restored, only owned
test files/jobs removed, diagnostic ports closed. Independent scoped visual
review: ship. Native EN/Night and synthetic pointer are distinguished from the
EN/RO/theme fixture matrix and physical acceptance. Public streams can change;
not every listed channel or codec has been certified. Full product acceptance
remains OPEN.

[User guide](docs/TV.md) · [Plan](docs/plans/iptv-2026-11-05.md) ·
[Evidence and limits](docs/evidence/iptv-2026-11-05.md)

## Previously delivered UI baseline

Installed runtimef0b140892a9e/codeeb899025. The approved N0/P5/P1/P2/P3/P4/scopedP7
UI batch is delivered: Radio neon, subtle floating Blender Explore names, common
commands, Radio library, Home arrangement assistance and real local Media details
with Continue watching/recovery. Five real20minute label experiments complete.

P4:64distinct native current-language/theme checks PASS with actual JPEG, natural
video progress, exact Resume, Continue Start over, history removal and guarded
copy deletion.219runtime hashes/29preferences/PCbackup verified. Original watch
bytes, radio/audio/preferences restored, synthetic fixtures removed and diagnostic
ports closed.755Python/44platform skips,108JavaScript,84focused Media/audio and
52command/Radio PASS;30Linux component and53isolated API checks PASS. Earlier
failures/corrections and limits are retained in the evidence.

- [Media evidence](docs/evidence/ui-ux-media-2026-10-25.md)
- [Home evidence](docs/evidence/ui-ux-home-2026-10-25.md)
- [Label experiments](docs/plans/label-autoresearch-2026-10-24.md)
- [Approved plan](docs/plans/ui-ux-2026-10-24.md)

Full product acceptance remains OPEN: physical/native matrix, DRM/media compatibility,
phone and stability criteria require their own evidence. Proposal6 excluded; no21:30
automation/public stream. Raw state/accounts/backups remain private.
