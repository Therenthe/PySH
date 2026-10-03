# Roadmap

## Current delivery work

Migration, CI and a corrected physical USB boot are evidenced in STATUS; the numbered stages below describe the original sequence. The remaining release loop uses one identified candidate, not cumulative PASS results from different runtimes.

Owner priority clarified2026-10-03: finish the SSH console flasher, full separate SD backup, image write/readback/recovery provisioning and SD physical boot first. Then finish functional gaps and undertake a major UI/UX improvement, before final same-candidate acceptance. Owner rates the current UI3.5/10 and UX5/10; these are explicitly unsatisfactory, not release acceptance. Preserve EN/RO,800×480 touch and the agreed product scope during the redesign. Do not divert the current flash milestone into cosmetic work.

1. Revalidate the complete physical EN/RO touch inventory and affected keyboard/fullscreen flows on the current candidate. Earlier native keyboard fixtures remain scoped evidence.
2. Complete native timeout/retry and failure recovery for protected preparation. Current empty/prepared profiles, actual EME/key creation, one component-loading restart and cancel have native evidence. Component metadata cannot authorize ready; official updater timing cannot be promised ([installer](https://raw.githubusercontent.com/chromium/chromium/main/chrome/browser/component_updater/widevine_cdm_component_installer.cc), [updater configuration](https://raw.githubusercontent.com/chromium/chromium/main/components/component_updater/configurator_impl.cc)). See [evidence](evidence/protected-playback-preparation-2026-10-03.md).
3. Verify real external playback/resolution and the final music-service decision; complete network/Bluetooth touch flows, current-candidate recovery/resources and the eight-hour interaction session.
4. Publish and repeat generic appliance update/rollback and fresh-image installation, then audit every required criterion before release.

## Original sequence

1. **Acum — conservare și migrare:** import verificabil, documentație coerentă, structură GitHub, verificări automate, publicare privată și CI.
2. **Stabilizarea aplicației:** corectarea structurii butoanelor Wi-Fi și a textelor netraduse; teste UI reale la 800×480 EN/RO; verificarea tuturor resurselor din pachet.
3. **Reconectare și inventar Pi:** starea reală, build activ și diferențe față de GitHub; backup înaintea oricărei actualizări. Apoi candidat unic și probe Bluetooth/audio/radio/media/rețea.
4. **Tranziție appliance:** validarea bazei Lite, compositor/sesiune kiosk, recuperare de service; builder reproducibil numai după ADR-uri acceptate. Nu suprascriem cardul de dezvoltare fără plan de restaurare.
5. **Acceptare/release:** 30 de criterii, inclusiv servicii externe, cinci porniri, opt ore stabilitate, performanță, instalare și rollback. Nicio funcție externă nu devine PASS prin simpla deschidere a unui site.
