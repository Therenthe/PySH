# PySH — Pi Smart Hub

Hub tactil EN/RO pentru Raspberry Pi 4 (4 GB), LCD DSI 7″, 800 × 480: ceas, vreme, radio, media locală și conectivitate.

Ultimul lot instalat: `ca9ff15300c7`, sursă `aa2f5e0` — oraș cu bază și șine
continue, cinci intrări Blender spre Media, Sunet, Internet, Setări și Radio.
Ceasul este centrat pe ecran, iar alertele oficiale meteo răspund din nou.
Pe Pi: toate cele cinci intrări, revenirea, Anulează/Omite și mișcarea redusă
verificate; preferințele și radioul păstrate. Animații2,6s,60 cadre,1–4 pierdute,
fără cadre corupte. Regresia completă1512/1520 PASS are opt eșecuri clasificate
și retestate separat; nu este declarată1520/1520.
[Dovezi și limite](docs/evidence/city-destinations-2026-10-24.md) ·
[Conceptul vizual Home pentru specialist](docs/HOME_VISUAL_CONCEPT.md).

Vizualizatorul Undă este acum integrat în clădirea radio: circuite neon Blender
conduse de semnalul audio, cu intensitate nocturnă. Comenzile redării sunt în
Comenzi rapide și Radio; atingerea clădirii este acum intrarea cinematică.
[Plan și verificări](docs/plans/radio-building-neon-2026-10-24.md) ·
[Dovezi](docs/evidence/radio-building-neon-2026-10-24.md).

**Stare: PySH OS experimental instalat pe dispozitiv; acceptarea produsului rămâne incompletă.** Pentru iterația curentă citește [planul activ](docs/PLAN_2026_10_23.md), [dovezile cerului Blender](docs/evidence/blender-sky-2026-10-23.md), [conexiunea activă și clădirea Wi-Fi](docs/evidence/network-rooftop-2026-10-23.md), [aeronavele ambientale](docs/evidence/ambient-aircraft-2026-10-23.md), [atmosfera meteo](docs/evidence/weather-atmosphere-2026-10-23.md) și [inventarul integral UI/UX](docs/UI_DELIVERY_PLAN.md), împreună cu [STATUS.md](STATUS.md). Probe ale unui candidat anterior nu certifică o versiune nouă. Cele30 criterii complete rămân OPEN.

- [Produs](docs/PRODUCT.md), [arhitectură](docs/ARCHITECTURE.md), [hardware](docs/HARDWARE.md)
- [Dezvoltare și verificări](docs/DEVELOPMENT.md), [operare/recuperare](docs/OPERATIONS.md), [securitate](docs/SECURITY.md)
- [Plan](docs/ROADMAP.md), [decizii ADR](docs/adr/README.md), [auditul migrării](docs/MIGRATION.md)
- [Criterii de acceptare](docs/DEFINITION_OF_DONE.md), [registru](docs/acceptance.json)

Cod: `app/ui/` și `app/browser-extension/`; servicii: `services/backend/`; integrare sistem: `os/`; particularități placă: `hardware/`; automatizare: `scripts/`; teste: `tests/`.

GitHub este sursa canonică. Copiile de dezvoltare și artefactele instalate își păstrează explicit commit-ul și build-ul; un runtime instalat nu este automat identic cu ultimul HEAD al documentației. Fișierele sincronizate din ChatGPT Project sunt referințe, nu directorul de dezvoltare.

Codul proiectului nu are încă o licență de redistribuire aleasă. Licențele componentelor terțe, inclusiv fonturile, sunt păstrate.
