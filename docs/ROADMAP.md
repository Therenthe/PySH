# Roadmap

## Current delivery work

Migration, CI and a corrected physical USB boot are evidenced in STATUS; the numbered stages below describe the original sequence. The remaining release loop uses one identified candidate, not cumulative PASS results from different runtimes.

1. Finish external-service keyboard lifecycle and reliable touch access to PySH controls during video fullscreen; repeat the affected native flows.
2. Implement first-use protected-playback preparation in the same persistent service profile before opening Netflix/Spotify. An owned loopback page must perform real EME access and key creation. Waiting for Chromium's official component updater needs truthful EN/RO progress, cancellation, retry and offline recovery. Component presence alone may trigger a bounded full browser restart, but cannot authorize a successful-ready state. Preserve credentials and do not use production CDP. Validate empty/prepared profiles, stale callbacks, duplicate launches and cancellation during restart. Linux requires a browser restart to load a newly installed component ([Chromium installer](https://raw.githubusercontent.com/chromium/chromium/main/chrome/browser/component_updater/widevine_cdm_component_installer.cc)); updater delays prevent promising an exact first-use duration ([updater configuration](https://raw.githubusercontent.com/chromium/chromium/main/components/component_updater/configurator_impl.cc)). This flow is planned, not implemented.
3. Verify real external playback/resolution and the final music-service decision; complete network/Bluetooth touch flows, current-candidate recovery/resources and the eight-hour interaction session.
4. Publish and repeat generic appliance update/rollback and fresh-image installation, then audit every required criterion before release.

## Original sequence

1. **Acum — conservare și migrare:** import verificabil, documentație coerentă, structură GitHub, verificări automate, publicare privată și CI.
2. **Stabilizarea aplicației:** corectarea structurii butoanelor Wi-Fi și a textelor netraduse; teste UI reale la 800×480 EN/RO; verificarea tuturor resurselor din pachet.
3. **Reconectare și inventar Pi:** starea reală, build activ și diferențe față de GitHub; backup înaintea oricărei actualizări. Apoi candidat unic și probe Bluetooth/audio/radio/media/rețea.
4. **Tranziție appliance:** validarea bazei Lite, compositor/sesiune kiosk, recuperare de service; builder reproducibil numai după ADR-uri acceptate. Nu suprascriem cardul de dezvoltare fără plan de restaurare.
5. **Acceptare/release:** 30 de criterii, inclusiv servicii externe, cinci porniri, opt ore stabilitate, performanță, instalare și rollback. Nicio funcție externă nu devine PASS prin simpla deschidere a unui site.
