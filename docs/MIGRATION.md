# Audit și migrare — 2026-10-02

## Proveniență

Documentul original identificat este `Pi_Smart_Hub_Functionalitati.md` din Downloads. Copia din vechiul proiect, `docs/SOURCE_FUNCTIONALITIES.md`, este identică byte cu byte: SHA-256 `2f35969e43efb03296675c8374da811bd160feca2defc64f464e300c3b83f307`.

Proiectul local a fost găsit în directorul `outputs/pi-smart-hub` al conversației „Identifică dispozitivul USB” (01a0e8dd-376e-7950-9df6-3feb807edf5a). Conversația „Instalare Omarchy Raspberry Pi” (6abd3109-2c20-83eb-9b82-9e352fb6ef4f) propune structura appliance/GitHub. La audit, `sources/` din mirror-ul Project era gol. Nicio sursă sincronizată nu a fost modificată.

Vechiul director are `.git`, dar fără commit-uri și fără remote. Importul păstrează fișierele sursă selectate; [manifestul de proveniență](migration-source-manifest.json) consemnează calea veche, calea nouă și hashul original înaintea adaptărilor. Originalul rămâne intact.

## Ce exista efectiv

React/TypeScript/Vite, Python/FastAPI, adaptoare BlueZ/NetworkManager/PipeWire, mpv IPC, meteo, radio, media, preferințe, lansator kiosk, activare și rollback. Ultimul pachet local identificat este `32d75c593e83`; hashurile runtime corespund manifestului său. Asta nu demonstrează versiunea activă acum pe Pi.

README/PRODUCT/WORKFLOW și registrul erau în urmă față de cod. Registrul avea 7 PASS pentru pregătirea din 29 septembrie și 30 OPEN pentru produs. Snapshotul istoric este în `history/acceptance-prep-2026-09-29.json`; probele brute private au rămas în directorul original. Registrul activ nu preia PASS-uri cu probe absente.

Playwright indica un director `e2e/` inexistent. Probele vechi de browser privesc un fixture, nu întreaga aplicație. Revizia statică a observat butoane imbricate în lista Wi-Fi și texte englezești fără traducere; acestea sunt restanțe ale aplicației, înregistrate în STATUS.

## Transformări

- `src`, `public`, `index.html` → `app/ui`; extensie → `app/browser-extension`.
- `backend` → `services/backend`; importurile, rădăcina assets și pachetul runtime sunt actualizate împreună.
- Lockfile-urile și testele existente sunt păstrate. Nu s-au actualizat versiuni de dependențe.
- Excluse: backupuri, profiluri, medii virtuale, arhive de release, cache-uri, loguri/audit brut și scripturile punctuale de ștergere.
- ADR-urile separă runtime-ul actual de direcția appliance. Niciun deploy, flash sau schimbare de rețea nu face parte din migrare.

## Închiderea migrării

Verificări locale → commit inițial → repository privat → push → verificare remote/commit → CI → actualizare STATUS. Până la confirmarea push-ului, migrarea GitHub nu este finalizată. Repository-ul privat `Therenthe/PySH` a fost creat de utilizator și accesul de scriere prin conector a fost verificat. Commit-ul inițial al utilizatorului este păstrat ca părinte al importului.

Închisă publicarea inițială: commit `6ff604b7ebb9c80b11765ea59917971071afba78`, 109 fișiere cu tree identic copiei locale; main local sincronizat. CI 37030198002 a trecut frontend și backend pe Python 3.12/3.13. GitHub este sursa canonică; inventarul live Pi așteaptă autentificarea SSH.
