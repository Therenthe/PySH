# PySH status

## Orange: control DRM reușit, redarea Orange rămâne blocată

Firefox 159 Raspberry Pi cu Widevine Google 4.10.3112 nemodificat redă controlul
criptat Sintel: 2,9→15,5 secunde, 68→371 cadre. Modulul încărcat este verificat.
În aceeași configurație, Kanal D marcat Free în Orange dă W813 în cinci observații,
zero cadre. Utilizatorul raportase aceeași eroare la un videoclip gratuit și
login Firefox care dispare; autentificarea Firefox nu este certificată.
Problema Orange nu este remediată și nu se deduce cauza politicii DRM.
Probe închise, port închis, trei servicii active, preferințe păstrate; captura
finală arată playerul TV PySH. Nicio înlocuire a browserului de producție.
[Dovezi și limite](docs/evidence/orange-w813-2026-11-07.md).

Orange native follow-up: Prima Sport1 still fails without extensions. Hash-verified passive inspection found 3video representations with supported codecs and all3marked undecipherable. User confirms same-account playback on Windows and Android. Official signed Google Chrome157 ARM64 was prepared side by side with a separate profile; keyboard/native viewport and Radio return passed trial readiness. After user login Prima Sport1 still raised W813/fatalvideo NO_PLAYABLE_REPRESENTATION,0decodedframes across8observations. Both account profiles retained; diagnostic browser/tunnel closed; existing runtime96764525dbc5/code42ac4d908b9285e72d43155e0182f7a5bc940290 remains unchanged. Chrome is not selected for production; its DevTools-loaded extension is temporary. Official RaspberryPi Firefox candidate evaluation is underway, no playback success or delivered fix claimed. See docs/evidence/orange-w813-2026-11-07.md.


Orange authenticated playback follow-up: runtime96764525dbc5/source42ac4d908b9285e72d43155e0182f7a5bc940290 unchanged. Existing member selection authorized; Prima Sport1 and2 reproduce fatal video NO_PLAYABLE_REPRESENTATION/W813 with zero decoded frames. User confirms Prima Sport1 works with same account on another device. Official Chromium Widevine update reports4.10.3112.0 Up-to-date. Precise cause and supported compatibility remedy remain OPEN; no successful playback or app fix claimed. Temporary loopback diagnosis cleaned, settings/account preserved,3services active; normal Media Services available. See docs/evidence/orange-w813-2026-11-07.md.


Digi and Orange TV Go installed: runtime96764525dbc5 / code42ac4d908b9285e72d43155e0182f7a5bc940290; previous917de2f7f36e retained. Official Digi mark and acknowledged Channels return verified on the final runtime. Orange TV Go under Media Services, official login keyboard and Media return, focused blank email/password visible above the actual keyboard. Independent native visual review passed. 991Python/46platformskips/11subtests,199JS,176initial and70final browser cases passed. 233runtime hashes/29preferences, separate PC backup checksum and readable contents verified; network/gateway preserved. 3services active,0temporary touch devices,no debug ports opened. Existing account profile retained; no credentials entered. Final pointer actions stopped after unrelated interactive changes; newer preferences not overwritten. Scoped integration controls PASS; real Orange account login/subscription playback and all30fullproductcriteria remainOPEN. See docs/plans/tv-services-2026-11-07.md and docs/evidence/tv-services-2026-11-07.md.


Video command drawer installed: runtime6314da69ecce/code479361d0af8dc7d64d139122150ace6de2564d17; previous40e96fcc7f76 retained. Topedgepull,48pxHUDbutton andAltShiftP inTV/localvideo; existingQuickControls layeredaboveplayer withactualtitle. Scopedfocus/Escapeandknown-sessionnavigationcleanup; prolongedTVHUDtimerdefect corrected.986Python/46platformskips/11subtests,192JS,final68browsercasesPASS; independentvisual/focus8+8andaffectedtimer4retestsPASS. Native ENnight800x480: actualAntena1 andVP8localvideo, menus/heldhardwarepreviews/persistence/dismiss/HUDbutton/MediaandHome verified; independentnativevisualPASS. 229runtimehashes/29preferences andPCbackup verified; network/gateway preserved. Ownfixture/historyremoved;3servicesactive,0temporarytouchdevices/transportdirs,debugclosed. FinalAntena1Bluetooth,brightness10%,preprobevolume restored. Nativeinput synthesized,notphysicalgesturecertification; knowninitialpendingTVsession retainslatecleanup; separateTV-START-20261106 andall30fullproductcriteriaOPEN. See docs/plans/video-command-drawer-2026-11-06.md and docs/evidence/video-command-drawer-2026-11-06.md.


Bluetooth audio follow-up,6November: saved speaker reconnected/selected; user explicitly confirmed audible radio and Antena1TV. Selected-output PCM and active Chromium-to-Bluetooth links verified. Requested finalstate: Antena1favorite fullscreen,actual/saved volume15%,unmuted,radioidle,3servicesactive,0temporarytouchdevices,debugclosed. Runtime40e96fcc7f76/code c9ac5e2927f9c77a69f07a6d98d1e79bef01dbde unchanged. InitialTVstart stayedConnecting/black withoutChromiumaudio; reopening restored playback. Causeunresolved,TV-START-20261106 remainsOPEN in docs/UI_DELIVERY_PLAN.md. Follow-up certifies audible playback at15%,not continuous-slider acoustic latency. Evidence: docs/evidence/live-levels-2026-11-06.md.


Live volume and brightness installed and verified: runtime40e96fcc7f76/code c9ac5e2927f9c77a69f07a6d98d1e79bef01dbde; previous9897df27e389 retained. Immediate visible percentages and bounded serial live previews in all app-owned sliders and the external drawer; preferences persist at gesture end. Fresh hardware readback reused; regular network/BT polling no longer holds the audio lock. 986Python/46platformskips/11subtests,192JS and140browserchecksPASS; independentvisual/focus auditPASS. 44nativechecksPASS at800x480: actual volume/backlight changes while held, unchanged saved preference until release, worker1.4.2/scalars-v6 in existing profile, keyboard and trusted Home return.229runtimehashes/29preferences and separate PCbackup verified. Originalpreferences/history/volume-mute/playback restored;3servicesactive,0ownedconverters/tempdirs,debugclosed. Initialsliderprobe had no acoustic acceptance: originaloutput unavailable, existinganalog endpoint temporarily selected for software readback only, no playback or pairing. R1diagnostic timings were not hardware latency measurements; R2 evidence distinguishes them. Fullproductacceptance remainsOPEN. See docs/plans/live-levels-2026-11-06.md and docs/evidence/live-levels-2026-11-06.md.


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
