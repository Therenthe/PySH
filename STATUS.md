# PySH status

Live sliders R2 candidate: reuse actual preview audio readback, avoid waiting for player status on each preview, and keep regular network/Bluetooth polling outside the audio ownership lock. Final persistence and uncertain-operation recovery retained. See docs/plans/live-levels-2026-11-06.md and docs/evidence/live-levels-2026-11-06.md. New native verification pending.


Live volume/brightness candidate: immediate numeric drafts, bounded serial previews without preference writes, final persistence, stale-poll protection and explicit uncertain-write recovery in all app/external controls.983Python/46platformskips/11subtests,192JS,64TV,28newlive and80legacy/error checksPASS; final16retests and4pending-video-close checksPASS.Independentvisual/focus4x9 andexternal4contextsPASS. Worker1.4.2/scalars-v6. New runtime installation/native validation pending. See docs/plans/live-levels-2026-11-06.md and docs/evidence/live-levels-2026-11-06.md.


TV recovery and touchscreen UI installed and verified: runtime88efb8ce5f6e/code09162997ea1ac878bf77fa0c306c8fcc07bb4e82. Versioned kiosk URL/no-store and loaded script equality verified in existing profile.20nativechecksPASS: actual Antena1/PROTV1920x1080,27spause/resume,compact guide,controls,stop/focus,next/return guide.228runtimehashes/29preferences and PCbackup verified; previous retained; network/gateway preserved. Originalidle/preferences/history/volume restored;3servicesactive,0ownedconverters/tempdirs,debugclosed.952Python/46platformskips/11subtests,113JS,20newTV,40+4TVretets,76shared,independentvisual8+8/keyboard12+4 andnativevisualreviewPASS. Physicalaudio excluded byuser; all30fullproductcriteriaOPEN. Initialreportedblockage not reproduced; nativeR1staleUI and R2harnessfailure are retained honestly in evidence. See docs/plans/tv-recovery-ux-2026-11-06.md and docs/evidence/tv-recovery-ux-2026-11-06.md.


## Official Digi Sport1 installed —5November2026

TV now opens exact official DigiSport1 URL via protected owned browser and trusted Return. Runtimef6385c202893/code d0a3fe7dcb48b744a4badcc1a3bf71cf56763293,previous3ef6f627868a retained.228hashes/29preferences/separate PCbackup verified; network/gateway preserved.

941Python/46platform skips/11subtests,110JS,44TVfixtures+8search retests,TS/Vite/repository PASS.14native existing-profile checks PASS:1280x720/80frames,Widevine,unobstructedplayer,officialfullscreen,newMV3worker,topedgegesturemenu and acknowledgedHomeReturn. Independent scoped audit PASS. Final services active,zero owned converters/tempdirectories,debugports closed; prefs/volume/mute/history restored. User explicitly continued without disconnected speaker; no acoustic acceptance or radio-resumption claim without audio. No M3U/DRM recording claim. Full product acceptance remains OPEN.

See docs/evidence/digi-official-2026-11-05.md and docs/plans/digi-official-2026-11-05.md.


## PRO TV HD installed — 5 November2026

Runtime3ef6f627868a, code10ae036022ea21e13268032088878d7fb88abfec; previous5131fbbab94a retained. Bounded stdin-only MPEG-TS to HLS remux, no recoding or new dependencies.227 hashes/29preferences/separate PC backup verified; network/gateway unchanged and original radio restored.

940Python/46platform skips/11subtests,96JS,80UI fixtures,TS/Vite/repository PASS.27 actual existing-profile Chromium checks PASS: PRO TV1920x1080 with89 decodedframes,pause/resume/back,actual recording/save,1080pMKV18frames,owned deletion.10 independent-service checks PASS: recording advances with whole Hub stopped,same recorderPID,automatic end,oneH264/oneAAC track and restored userstate. Final services active,zero owned converters/tempdirectories,debugports closed. Independent scoped audit passes.

Second simultaneous upstream PRO TV connection interrupted; simultaneous viewing/recording reliability for that source remains unaccepted. Prima Sport1/Digi Sport1 now accept SD too; HD is preferred. Five further public candidates were checked without a resolution threshold: four unavailable,one decodable subscription-payment placeholder confirmed visually on Pi (no channel programme/audio). No new favorite or source was saved; radio/preferences preserved. Full product acceptance remains OPEN.

See docs/evidence/iptv-direct-ts-2026-11-05.md and docs/plans/iptv-direct-ts-2026-11-05.md. Prior IPTV evidence: docs/evidence/iptv-2026-11-05.md; cloud drift: docs/plans/cloud-drift-2026-11-05.md. Historical status is retained in Git history.
