# Native local-media probes and immediate decoder recovery

The native probes used installed runtime `6676b558fe06`, source `204ff1b2117fcf4b07394ad660912edbf5e7acd6`, with all48runtime hashes and the active SD identity checked before mutation. Seventeen explicitly owned synthetic fixtures were generated on the Pi. Their actual codec, duration and content hashes were verified; no personal media was used. The authenticated Raspberry Pi FFmpeg package was extracted into an isolated staging directory, without installing packages or changing the system decoder stack.

## Observed native results

- API/mpv played eight20-second audio encodings: WAV PCM16, MP3, AAC ADTS, M4A AAC, FLAC, OGG/OGA Vorbis and Opus. Position advanced for each. Pause, seek, resume, listing-derived next/previous queue, natural EOF, missing-file rejection and valid-file recovery after corrupt media passed. These probes were muted; they do not certify speaker audibility or physical touch.
- Actual kiosk Chromium decoded MP4/M4V/MKV/MOV H264+AAC and WebM VP9+Opus fixtures. EN/RO×Ink/Night video Retry, Back, valid recovery, pause, touch-sized slider seek and resume passed. The four contexts had controls within800×480 and at least48px targets.
- The separate1280×720 H264/AAC resource fixture decoded, with zero reported dropped frames in the bounded sample. Complete application-tree PSS was723.701MiB across16verified processes. This is a media scenario, not the idle700MiB gate, an8-hour stability result, or a physical latency measurement.
- Eight native video captures were inspected. They exposed an unwanted Chromium Cast tile over valid playback and generic duplicated invalid-file wording.

The first native video harness stopped before any decoder probe because it attempted navigation through a collapsed rail. Navigation/wake and preference restoration ordering were corrected in the private harness; the second run completed with no page errors and verified restoration. This is not recorded as a product decoder failure.

## Confirmed audio UI defect

The first native audio UI probe failed on the first corrupt MP3 selection. The backend can return HTTP200 containing an already-failed audio player snapshot (`state:error`, `error:stream_failed`). The UI request wrapper treated its `error` field as a failed API operation, producing generic text and suppressing the useful local-audio notice. No audio UI format/control/missing-file matrix is claimed to have passed. The failed run restored exact preferences, audio/output and the previously playing radio; cleanup reported no errors.

Prepared runtime `3e4e9d6d1b07` corrects only that HTTP200 local decoder snapshot handling; non-success HTTP statuses still produce the existing exact-target API retry. A new regression exercises immediate failure, repeated Replay, actual409missing-file feedback, exact retry identity and healthy-file recovery. Local video opts out of remote playback controls and explains retry/return to library in EN/RO without claiming a codec cause.

Forty-four affected browser cases passed at800×480. TypeScript/build,336backend cases (22Windows platform skips) and27keyboard/extension cases passed. All eight affected recovery captures were reviewed; text and actions fit in both languages/themes. Full526case UI regression passed (10.9minutes); native verification of the prepared candidate is still pending. Native Cast suppression must be checked on a valid frame, not inferred from the attribute test or invalid-video capture.

Kiosk diagnostics were restricted to Pi loopback and a PC-loopback SSH tunnel, without accessing the service/account profile. They were removed after the probe. Native cleanup verified restoration of preferences, volume/mute/output and radio, and closure of the diagnostic listener; the PC tunnel was terminated. Raw reports, screenshots, fixtures and backups remain private.

MEDIA-02 and all remaining complete product criteria remain OPEN. The next step is publication, guarded activation of the corrected candidate and a full native audio UI/video retest, followed by physical audibility/touch acceptance. A container extension alone does not promise all codecs supported by that container.

## Corrected candidate installed and retested

Installed `3e4e9d6d1b07`, source `84618b3de5d2b73442e78fc00ee03d7ec49bde2f`. Archive SHA256 `10108a86df1514864e0a9973af7ba7de6702294745b5a4d5338ac3306832cdd0`; manifest SHA256 `01918d188401b28d1d334a29c5f3835f31f564074b4db3fd3ba3f46a5df3bcc4`. The previous6676runtime and PC backup SHA256 `2a4feb2fb2e71407951f9dc309971dc53d2537be7db390897e2613f161ff783c` are retained. Independent checks verified all48native files, no pending transaction, radio35.333→44.389seconds and all nine saved preference hashes, including layout/visualizer/location/navigation.

Fixtures were reused without rewriting their original6676/source204provenance. A separate read-only guard verified the current48runtime files and all17original fixture sizes/hashes; the original native manifest and normalized content digests remained unchanged.

Actual audio UI passed all32encoding/context selections (eight encodings×EN/RO×Ink/Night), four pause/seek/resume/next/previous sets, four corrupt-file Retry flows, four real missing-file409Retry/restore flows and four naturalEOF/replay flows. A missing-file navigation-away/back scenario also passed with a fresh listing omitting the temporarily hidden owned WAV and recovery after restoration. Current native corrupt responses were asynchronous decoder states; the immediate HTTP200error-response branch is covered by the new browser regression and is not described as independently reproduced on the new native runtime. Twelve native audio captures were reviewed; actions and recovery text fit. The auditor noted a remaining clarity gap: missing-file banners do not name the failed basename. This is tracked as UI-32.

Actual Chromium video passed all five encoding fixtures, four EN/RO/theme control/error recovery contexts and the bounded720p sample. Both disableRemotePlayback and disablePictureInPicture were true in the actual video element; valid native captures show the former Cast tile absent. Root inspected the RO Night control capture. The720p sample advanced0.606→5.370seconds with133total/0dropped frames reported at the end; complete whole-application PSS736.703MiB across16processes. This is a media measurement, not idle acceptance, sustained frame-rate acceptance or physical latency.

The visual auditor independently inspected all eight corrected native video recovery/control captures: Cast absent in all valid frames; recovery text and controls readable and inside800×480. Both harness reports had no page errors or cleanup errors and verified exact preferences/audio/output/radio restoration. Final diagnostic teardown independently confirmed restored preferences/audio/radio and closed Pi debugger listener; the PC tunnel was terminated. Speaker audibility and physical gestures are still not proved by muted CDP-injected tests. Full MEDIA-02 and all30mandatory final product gates remain OPEN.
