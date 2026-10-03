# PySH — Pi Smart Hub

Hub tactil EN/RO pentru Raspberry Pi 4 (4 GB), LCD DSI 7″, 800 × 480: ceas, vreme, radio, media locală și conectivitate.

**Stare: implementare existentă importată; acceptarea produsului este incompletă.** Nu există încă o imagine PySH OS construită și validată. [STATUS.md](STATUS.md) indică rezultatele și următorul pas.

- [Produs](docs/PRODUCT.md), [arhitectură](docs/ARCHITECTURE.md), [hardware](docs/HARDWARE.md)
- [Dezvoltare și verificări](docs/DEVELOPMENT.md), [operare/recuperare](docs/OPERATIONS.md), [securitate](docs/SECURITY.md)
- [Plan](docs/ROADMAP.md), [decizii ADR](docs/adr/README.md), [auditul migrării](docs/MIGRATION.md)
- [Criterii de acceptare](docs/DEFINITION_OF_DONE.md), [registru](docs/acceptance.json)

Cod: `app/ui/` și `app/browser-extension/`; servicii: `services/backend/`; integrare sistem: `os/`; particularități placă: `hardware/`; automatizare: `scripts/`; teste: `tests/`.

GitHub este sursa canonică. Copiile de dezvoltare și artefactele instalate își păstrează explicit commit-ul și build-ul; un runtime instalat nu este automat identic cu ultimul HEAD al documentației. Fișierele sincronizate din ChatGPT Project sunt referințe, nu directorul de dezvoltare.

Codul proiectului nu are încă o licență de redistribuire aleasă. Licențele componentelor terțe, inclusiv fonturile, sunt păstrate.
