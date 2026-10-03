# Arhitectură

## Runtime-ul actual PySH OS

Raspberry pornește de pe USB în sesiunea dedicată greetd/labwc, cu API și Chromium supravegheate de unitatea utilizatorului `pysh.service`. Runtime-ul este în `/opt/pysh/current`, venv-ul în `/opt/pysh/venv`, datele în `/home/pysh/.local/share/pi-smart-hub`; release-urile gestionate și rollback-ul sunt separate de date. Imaginea inițială instalează un director current real; actualizările verificate îl conservă înainte de trecerea la legături current/previous. Originalul SD rămâne mediu separat de recuperare. Identitățile și rezultatele exacte sunt în STATUS, nu se deduc din HEAD.

Serviciile externe folosesc un profil Chromium separat de kiosk. Pagina loopback de pregătire cere EME/key creation reale înainte de Netflix/Spotify; component updater oficial și o repornire delimitată pregătesc profilurile noi. Extensia și host-ul nativ gestionează tastatura/revenirea. API-ul rămâne exclusiv loopback, cu verificarea originii și token pentru mutații. Profilul conturilor nu este sursă, diagnostic sau fixture de depanare.

## Implementarea desktop importată (istorică)

Chromium kiosk → assets React în `dist/` → API FastAPI pe `127.0.0.1:8765` → BlueZ/NetworkManager prin D-Bus, PipeWire/WirePlumber și mpv. UI se construiește pe PC. Python rulează ca utilizator al sesiunii grafice; API-ul nu este expus în LAN.

`app/ui` conține UI și traduceri; `app/browser-extension` controlul revenirii din servicii externe; `services/backend` conține API, dispozitiv, conținut, player și preferințe. `scripts/run-hub.py` supraveghează API/kiosk. `scripts/install-session.sh` generează serviciul utilizatorului și intrarea autostart. Pachetele se instalează în `~/pi-smart-hub/releases/<build>` cu legături current/previous. Datele persistente stau separat în `~/.local/share/pi-smart-hub`.

## Direcție appliance

Ramura experimentală OS implementează baza Lite cu rpi-image-gen 2.8, sesiunea labwc/greetd, mod de service și recuperare SSH prin cheie publică. Builderul și inspectorul sunt în `os/image/`. Boot-ul fizic USB și recuperarea au dovezi pentru imaginea corectată anterioară; o imagine nouă și un candidat nou au propriile probe, iar acceptarea finală rămâne deschisă. ADR-0006–0008 descriu detaliile. Nu se confundă pornirea kiosk după login cu imaginea appliance. ADR-0001–0004 consemnează această diferență.

Pentru migrare păstrăm recuperarea prin desktop a runtime-ului existent. Proiectarea unei sesiuni kiosk minimale și a unui mod de service precedă eliminarea desktopului. Nu schimbăm controlerele audio/rețea doar pentru noua structură de directoare.
