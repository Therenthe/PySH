# Arhitectură

## Implementarea importată

Chromium kiosk → assets React în `dist/` → API FastAPI pe `127.0.0.1:8765` → BlueZ/NetworkManager prin D-Bus, PipeWire/WirePlumber și mpv. UI se construiește pe PC. Python rulează ca utilizator al sesiunii grafice; API-ul nu este expus în LAN.

`app/ui` conține UI și traduceri; `app/browser-extension` controlul revenirii din servicii externe; `services/backend` conține API, dispozitiv, conținut, player și preferințe. `scripts/run-hub.py` supraveghează API/kiosk. `scripts/install-session.sh` generează serviciul utilizatorului și intrarea autostart. Pachetele se instalează în `~/pi-smart-hub/releases/<build>` cu legături current/previous. Datele persistente stau separat în `~/.local/share/pi-smart-hub`.

## Direcție appliance

Ținta este pornirea direct în PySH fără desktop expus utilizatorului obișnuit. Baza Lite și rpi-image-gen rămân propuneri de validat; `os/` nu conține încă un builder. Nu se confundă pornirea kiosk după login cu imaginea appliance. ADR-0001–0004 consemnează această diferență.

Pentru migrare păstrăm recuperarea prin desktop a runtime-ului existent. Proiectarea unei sesiuni kiosk minimale și a unui mod de service precedă eliminarea desktopului. Nu schimbăm controlerele audio/rețea doar pentru noua structură de directoare.
