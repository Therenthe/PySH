# PySH status

TV recovery R2 candidate88efb8ce5f6e: compact guide/fullscreen controls and bounded recovery, plus no-store entry and versioned kiosk URL. R1 installed files were correct but native browser showed old UI; HTTP index matchednewpackage,cacheheaderabsent. R2 has952Python/46platformskips/11subtests and11entry/launcher checksPASS, warm-profile fixturePASS. Existing113JS,20newTV,40+4TV,76shared,visual8+8 andkeyboard12+4 PASS; unchangedUIassets. R2 installation/native verification pending; acoustic testing excluded by user. See docs/evidence/tv-recovery-ux-2026-11-06.md.


## Official Digi Sport1 installed —5November2026

TV now opens exact official DigiSport1 URL via protected owned browser and trusted Return. Runtimef6385c202893/code d0a3fe7dcb48b744a4badcc1a3bf71cf56763293,previous3ef6f627868a retained.228hashes/29preferences/separate PCbackup verified; network/gateway preserved.

941Python/46platform skips/11subtests,110JS,44TVfixtures+8search retests,TS/Vite/repository PASS.14native existing-profile checks PASS:1280x720/80frames,Widevine,unobstructedplayer,officialfullscreen,newMV3worker,topedgegesturemenu and acknowledgedHomeReturn. Independent scoped audit PASS. Final services active,zero owned converters/tempdirectories,debugports closed; prefs/volume/mute/history restored. User explicitly continued without disconnected speaker; no acoustic acceptance or radio-resumption claim without audio. No M3U/DRM recording claim. Full product acceptance remains OPEN.

See docs/evidence/digi-official-2026-11-05.md and docs/plans/digi-official-2026-11-05.md.


## PRO TV HD installed — 5 November2026

Runtime3ef6f627868a, code10ae036022ea21e13268032088878d7fb88abfec; previous5131fbbab94a retained. Bounded stdin-only MPEG-TS to HLS remux, no recoding or new dependencies.227 hashes/29preferences/separate PC backup verified; network/gateway unchanged and original radio restored.

940Python/46platform skips/11subtests,96JS,80UI fixtures,TS/Vite/repository PASS.27 actual existing-profile Chromium checks PASS: PRO TV1920x1080 with89 decodedframes,pause/resume/back,actual recording/save,1080pMKV18frames,owned deletion.10 independent-service checks PASS: recording advances with whole Hub stopped,same recorderPID,automatic end,oneH264/oneAAC track and restored userstate. Final services active,zero owned converters/tempdirectories,debugports closed. Independent scoped audit passes.

Second simultaneous upstream PRO TV connection interrupted; simultaneous viewing/recording reliability for that source remains unaccepted. Prima Sport1/Digi Sport1 now accept SD too; HD is preferred. Five further public candidates were checked without a resolution threshold: four unavailable,one decodable subscription-payment placeholder confirmed visually on Pi (no channel programme/audio). No new favorite or source was saved; radio/preferences preserved. Full product acceptance remains OPEN.

See docs/evidence/iptv-direct-ts-2026-11-05.md and docs/plans/iptv-direct-ts-2026-11-05.md. Prior IPTV evidence: docs/evidence/iptv-2026-11-05.md; cloud drift: docs/plans/cloud-drift-2026-11-05.md. Historical status is retained in Git history.
