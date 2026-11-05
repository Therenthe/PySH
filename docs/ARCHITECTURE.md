# Arhitectură

## Runtime-ul actual PySH OS

Sesiunea dedicată greetd/labwc pornește API și Chromium supravegheate de unitatea utilizatorului `pysh.service`. Runtime-ul este în `/opt/pysh/current`, venv-ul în `/opt/pysh/venv`, datele în `/home/pysh/.local/share/pi-smart-hub`; release-urile gestionate și rollback-ul sunt separate de date. Imaginea inițială instalează un director current real; actualizările verificate îl conservă înainte de trecerea la legături current/previous. USB-ul verificat rămâne mediu de recuperare după migrarea la SD; originalul SD are backup integral separat pe PC. Identitățile și rezultatele exacte sunt în STATUS, nu se deduc din HEAD.

Serviciile externe folosesc un profil Chromium separat de kiosk. Pagina loopback de pregătire cere EME/key creation reale înainte de Netflix/Spotify; component updater oficial și o repornire delimitată pregătesc profilurile noi. Extensia și host-ul nativ gestionează tastatura/revenirea. API-ul rămâne exclusiv loopback, cu verificarea originii și token pentru mutații. Profilul conturilor nu este sursă, diagnostic sau fixture de depanare.

Telecomanda Android cerută pe 2026-10-13 folosește un gateway opțional separat în `services/remote`, HTTPS pe IP-ul privat explicit al Pi-ului și portul 8766. Pairing-ul este autorizat prin cod local și pin SHA-256 al certificatului; telefoanele au tokenuri persistente revocabile. Gateway-ul transmite numai comenzile API permise către loopback și gestionează intern tokenul local; nu schimbă binding-ul sau validarea backendului. Nu există relay internet. [ADR-0010](adr/0010-android-lan-remote.md) și [procedura/contractul](ANDROID_REMOTE.md) separă această implementare de verificarea încă deschisă pe telefon/Pi.

Redarea video locală folosește elementul Chromium și o sesiune backend cu descriptor
read-only al fișierului aprobat; progresul provine din acel element, separat de
playerul mpv pentru radio/audio. `local_media`, `watch_history` și răspunsul de
streaming folosesc lockul Media existent. Istoricul privat este persistent,
metadatele/miniaturile au cache RAM limitat și extractor mpv separat. Lipsa lor
nu împiedică navigarea/redarea. [Dovezile P4](evidence/ui-ux-media-2026-10-25.md)
separă candidatul sursă de instalarea și verificarea efectivă.

## TV în Media și recorder independent

TV extinde lumea Media existentă, prin Media → Servicii → TV, cu aceleași
tokenuri Ink/Noapte, comenzi tactile și traduceri EN/RO. Nu adaugă o lume sau
o stivă grafică separată. [DESIGN](../DESIGN.md) descrie această continuitate;
[TV](TV.md) definește sursele și limitele, iar [ADR-0013](adr/0013-iptv-independent-recording.md)
consemnează decizia.

`iptv_catalog` importă cele patru liste M3U inițiale și XMLTV simplu/gzip,
asociază ghidul prin ID sau nume neambiguu și completează PRO TV/Antena 1 numai
din pagini oficiale cu dată/ore validate. Configurația/favoritele și cache-ul
limitat persistă în `DATA/iptv/config.json`, respectiv `cache.json`; datele
expirate au stare distinctă. Descărcările și fiecare redirect verifică DNS-ul
public și fixează socketul la adresa verificată. Dimensiunea, timpul și
decompresia XML sunt limitate; DTD/entitățile sunt refuzate.

HLS.js este încărcat dinamic numai la vizionare. Un singur element Chromium
decodează TV, prin resurse HLS rescrise de `iptv_stream` în URL-uri opace pe
același origin loopback; browserul nu primește URL-urile upstream ca surse de
redare. Sesiunea de vizionare are lease de 120 s, reînnoit inclusiv în pauză,
și este închisă explicit la revenire. Lockul Media arbitrează deținerea
playerului cu video local/mpv; descărcările nu blochează mutațiile dispozitivului.

`iptv_api` scrie comenzile/programările în SQLite privat,
`DATA/iptv-recordings/jobs.sqlite3`. Procesul separat `iptv_recorder` deține
exclusiv copiii FFmpeg și propriul relay HLS loopback pentru fiecare job;
schimbarea canalului vizionat sau restartul Hub nu schimbă înregistrarea.
FFmpeg copiază pistele audio/video în MKV fără recodare, printr-un descriptor
de fișier regulat, seekable, deschis exclusiv și verificat; ieșirea nu este un
pipe. Identitatea fișierului și stările active protejează ștergerea și în Media
local. Implicit, MKV-urile sunt în `~/Videos/MediaTool`, separat de release.

`pysh-recorder.service` este o unitate user independentă de `pysh.service`.
Continuitatea este față de UI/Hub, nu față de oprirea daemonului, suspendare
sau lipsa alimentării/rețelei. Restartul recorderului păstrează joburile și
marchează înregistrările întrerupte; nu promite reluarea lor fără pierderi.
Instalarea, backupul SQLite și coordonarea update/rollback sunt în
[OPERATIONS](OPERATIONS.md#tv-înregistrări-și-date-private).

## Implementarea desktop importată (istorică)

Chromium kiosk → assets React în `dist/` → API FastAPI pe `127.0.0.1:8765` → BlueZ/NetworkManager prin D-Bus, PipeWire/WirePlumber și mpv. UI se construiește pe PC. Python rulează ca utilizator al sesiunii grafice; API-ul nu este expus în LAN.

`app/ui` conține UI și traduceri; `app/browser-extension` controlul revenirii din servicii externe; `services/backend` conține API, dispozitiv, conținut, player și preferințe. `scripts/run-hub.py` supraveghează API/kiosk. `scripts/install-session.sh` generează serviciul utilizatorului și intrarea autostart. Pachetele se instalează în `~/pi-smart-hub/releases/<build>` cu legături current/previous. Datele persistente stau separat în `~/.local/share/pi-smart-hub`.

## Direcție appliance

Ramura experimentală OS implementează baza Lite cu rpi-image-gen 2.8, sesiunea labwc/greetd, mod de service și recuperare SSH prin cheie publică. Builderul și inspectorul sunt în `os/image/`. Boot-ul fizic USB și recuperarea au dovezi pentru imaginea corectată anterioară; o imagine nouă și un candidat nou au propriile probe, iar acceptarea finală rămâne deschisă. ADR-0006–0008 descriu detaliile. Nu se confundă pornirea kiosk după login cu imaginea appliance. ADR-0001–0004 consemnează această diferență.

Pentru migrare păstrăm recuperarea prin desktop a runtime-ului existent. Proiectarea unei sesiuni kiosk minimale și a unui mod de service precedă eliminarea desktopului. Nu schimbăm controlerele audio/rețea doar pentru noua structură de directoare.
