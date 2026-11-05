# Operare, update și recuperare

Procedura pentru desktop de mai jos descrie runtime-ul importat. Pentru appliance-ul instalat pe USB, folosește secțiunea PySH OS; comenzile și directoarele celor două moduri diferă. Starea candidatului și dovezile sunt în [STATUS](../STATUS.md).

## PySH OS instalat pe USB

Imaginea și procedura de provisioning sunt în [os/image](../os/image/README.md). Runtime-ul appliance este în `/opt/pysh/releases/<build>`, cu `current` și `previous`; venv-ul este `/opt/pysh/venv`. Utilizatorul grafic este `pysh`, iar recuperarea administrativă folosește `pysh-admin` și cheia publică provisionată. Profilul serviciilor și preferințele rămân separat în `/home/pysh/.local/share/pi-smart-hub`; nu le publica și nu le înlocui la update.

Unitatea `pysh.service` aparține utilizatorului, nu managerului de servicii de sistem. Din SSH administrativ, verificarea read-only este:

```sh
readlink -f /opt/pysh/current
findmnt -no UUID /
sudo -u pysh env XDG_RUNTIME_DIR=/run/user/1000 DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/1000/bus systemctl --user is-active pysh.service
```

O relansare autorizată folosește aceeași invocare cu `restart pysh.service`; închide și ferestrele media deținute de aplicație. Nu folosi aici scripturile desktop `activate-release.sh` sau `rollback.sh`: acestea operează în `~/pi-smart-hub` și asupra altei unități. Activările appliance documentate până acum folosesc scripturi administrative private, verificate pentru UUID, release curent, manifest, backup separat și preferințe, cu revenire la precedent dacă API-ul nu se restabilește. O procedură generică de update/rollback appliance publicată și repetată rămâne necesară pentru DEL-01.

Înainte de schimbare, salvează runtime-ul precedent, manifestul sursă, preferințele și configurația afectată; verifică checksumul și conținutul lizibil pe PC. La migrarea la SD, păstrează USB-ul verificat și backupul integral original pe PC. O imagine CI verde sau un serviciu activ nu înlocuiește proba de boot, touch, audio și redare. Pentru scrierea unui SD inactiv de pe USB, folosește [flasherul SSH](SSH_FLASHER.md); nu rescrie root-ul activ.

## Update și rollback runtime PySH OS (procedură publică)

`scripts/appliance-release.py` operează exclusiv pe appliance-ul identificat prin `/etc/pysh-build.json`, în `/opt/pysh`, cu unitatea **utilizatorului** `pysh.service`. Nu folosi comenzile desktop de mai jos. Tool-ul nu modifică partiții, pachete, venv, SSH, rețea, drivere, configurația touch sau profiluri browser. Schimbarea `requirements.lock` este refuzată: necesită o procedură separată pentru imagine/dependențe. Sursa GitHub trebuie verificată de operator înainte de transfer; SHA-ul transmis identifică sursa, nu este o semnătură a publisher-ului.

Pe PC, construiește din commit-ul verificat cu `python scripts/package-release.py`. Transferă arhiva, manifestul și tool-ul către directorul administrativ privat; folosește valori reale în locul `<build>` și `<commit>`:

```sh
sudo python3 /home/pysh-admin/appliance-release.py prepare \
  /home/pysh-admin/pi-smart-hub-<build>.tar.gz \
  /home/pysh-admin/<build>.manifest.json --source <commit>
```

`prepare` verifică checksum, inventarul exact și hash-urile runtime-ului, refuză traversal, linkuri și fișiere necunoscute, extrage într-un release nou și **nu oprește serviciul**. Dacă imaginea are inițial un director real `current`, îi verifică identitatea față de markerul imaginii și păstrează o copie verificată în `releases`. Runtime-ul, preferințele și configurațiile relevante intră într-un backup privat (profilul browser nu este copiat sau modificat). Ieșirea conține calea backupului și SHA-256.

Directoarele administrative trebuie să fie deținute de root și să nu fie inscriptibile de alți utilizatori. `update` este creat privat `0700`; un director existent accesibil altor utilizatori este refuzat, fără modificarea automată a permisiunilor. Fișierul backup este creat exclusiv `0600` înainte de scrierea oricăror preferințe/configurații, inclusiv cu umask permisiv.

Copiază backupul pe **alt PC** într-un director privat și verifică-l acolo cu același tool:

```sh
python appliance-release.py verify-backup <backup-copiat.tar.gz> \
  --sha256 <sha256-din-prepare> --receipt <receipt.json>
```

Verificarea citește integral arhiva și compară fiecare fișier cu hash-ul salvat, nu doar listarea tar. Receipt-ul leagă build-ul, digestul backupului și identitatea dispozitivului de PC-ul verificator. Transferă **numai receipt-ul** înapoi. Acesta este o confirmare administrativă verificabilă, nu o atestare criptografică independentă; operatorul trebuie să păstreze copia separată și să nu fabrice receipt-uri.

```sh
sudo python3 /home/pysh-admin/appliance-release.py activate /home/pysh-admin/receipt.json
```

Activarea refuză receipt-ul emis pe același host, schimbări între prepare/activate și preferințe/configurații modificate între timp. Oprește numai `pysh.service`, comută atomic `current`, înregistrează build/commit/hash-uri în `runtime-source.json`, pornește și verifică API-ul appliance plus cwd-ul procesului real. La eșec revine la runtime-ul precedent. Directorul real inițial se păstrează ca `image-current-<build>`; toate release-urile și backupurile rămân. Nu se fac ștergeri de procese globale sau cleanup automat.

Pentru **rollback voluntar**, pregătește release-ul `previous`, exportă și verifică noul backup pe PC, apoi activează cu noul receipt:

```sh
sudo python3 /home/pysh-admin/appliance-release.py prepare-rollback
# copiere backup pe PC, verify-backup, transfer receipt: aceiași pași de mai sus
sudo python3 /home/pysh-admin/appliance-release.py activate /home/pysh-admin/receipt-rollback.json
```

Pentru o tranzacție întreruptă după prepare/comutare, `sudo python3 /home/pysh-admin/appliance-release.py recover` revine la identitatea salvată în jurnal și verifică pornirea. Operațiile administrative sunt serializate prin lock; un eșec lasă dovezile pentru diagnostic, nu le șterge. Dacă prepare a refuzat un pachet, nu edita manual jurnalul pentru a forța activarea.

Aceste verificări dovedesc integritatea și recuperarea procesului, nu acceptarea hardware. După update și rollback verifică SSH, LAN, panoul/touch, audio, preferințe și redarea efectivă pe același candidat; notează build/commit și rezultate. Proba repetată pe appliance-ul real și restaurarea backupului rămân necesare pentru DEL-01.

## Date Media locale

În afara runtime-ului, backupul descris mai sus salvează numai inventarul
`PROTECTED` din `scripts/appliance-release.py`: configurația labwc, host-ul tastaturii,
`pysh.service` și cele două fișiere de preferințe. Nu este backupul întregului
director de date: istoricul Media, datele TV și MKV-urile cer o copie privată
separată.

Progresul video este păstrat separat de release, în directorul privat de date
`local-media/watch.json`. Include-l în backupul privat al datelor aplicației;
conține căi locale și nu se publică în Git. Maximum40înregistrări sunt persistate,
iar „Continuă vizionarea” arată maximum12fișiere validate și disponibile.
Un volum deconectat ascunde temporar intrările; citirea nu șterge istoricul.
„Elimină din istoric” nu șterge fișierul. Ștergerea fișierului păstrează confirmarea
și verificarea identității, fiind refuzată cât timp este redat.

Metadatele și miniaturile reale sunt un cache RAM limitat, regenerat la nevoie
prin procesul mpv separat și limitat; lipsa lor păstrează numele și pictograma
tipului de fișier. Acest cache Media nu necesită ffmpeg/ffprobe, conturi sau un
scanner nou; recorderul TV are separat dependența FFmpeg de mai jos.
La ieșire se salvează observația video și se închide sesiunea. În caz de eroare,
utilizatorul poate reîncerca sau alege explicit revenirea fără salvare. Dacă hubul
nu confirmă închiderea, ieșirea locală cere o alegere distinctă; curățarea remote
rămâne neconfirmată până la expirarea/înlocuirea sesiunii. Expirarea logică este
120s, cu eliberare fizică la următoarea accesare/curățare periodică.

## TV, înregistrări și date private

Utilizarea, sursele M3U/XMLTV și limitele sunt în [TV](TV.md). Recorderul necesită
pachetul OS `ffmpeg` (care furnizează și `ffprobe`) din distribuția țintă;
instalarea sa este o operație de dependențe separată de update-ul runtime.
Definiția imaginii include acum această dependență, dar imaginea modificată nu
a fost construită sau flash-uită. Proba Linux izolată cu FFmpeg real 7.1.5 a
trecut 14 verificări după corectarea ieșirii MKV seekable pentru AAC; aceasta
nu certifică redarea HLS/MKV în Chromium pe panou sau instalarea noului runtime.
Starea candidatului și acceptarea completă, încă OPEN, se urmăresc în STATUS.

După activarea unui release verificat care conține recorderul și unitatea,
instalarea explicită pe appliance este:

```sh
sudo python3 /opt/pysh/current/scripts/install-recorder.py
```

Scriptul cere Linux/root, release versionat activ și markerul existent
`/opt/pysh/runtime-source.json` cu build/hash-ul unității corespunzător. Nu
fabrica markerul. Instalează `/etc/systemd/user/pysh-recorder.service` numai
dacă lipsește; acceptă copia identică și refuză o unitate existentă diferită.
Refuză actualizarea serviciului dacă baza are joburi `starting`, `recording`
sau `stopping`. Apoi rulează daemon-reload și enable/start în managerul user
`pysh`; nu restartează Hub și nu certifică pornirea după un reboot.
[Detaliile unității](../os/systemd/README.md) includ verificarea read-only.

Unitatea recorderului nu este `PartOf=pysh.service`. Închiderea UI sau restartul
Hub nu oprește recorderul; dispozitivul trebuie să rămână pornit, nesuspendat,
online și cu spațiu liber. Oprirea/restartul recorderului întrerupe joburile
active, păstrează fișierele parțiale și marchează întreruperea. Joburile al
căror interval a trecut sunt marcate ca ratate; nu se promite reluare continuă.

Înainte de update/rollback care schimbă codul recorderului, așteaptă terminarea
sau oprește și salvează explicit toate înregistrările active; verifică și
programările apropiate. Oprește recorderul înainte de comutarea `current`, apoi
repornește-l cu release-ul compatibil și verifică starea reală. Tool-ul
`appliance-release.py` comută/repornește numai Hub; nu coordonează automat
daemonul separat. Înainte de rollback la un release fără recorder, oprește și
dezactivează `pysh-recorder.service`, pentru a nu porni cu un modul absent.
O unitate schimbată cere migrare explicită: installerul refuză suprascrierea ei.

`DATA` este `PI_HUB_DATA` dacă este configurat, altfel
`~/.local/share/pi-smart-hub`; pe appliance implicit este
`/home/pysh/.local/share/pi-smart-hub`. API și daemonul trebuie să folosească
același director. Datele private sunt:

- `DATA/iptv/config.json`: surse și favorite; `DATA/iptv/cache.json`: catalog,
  ghid și starea ultimei actualizări, regenerabile din surse.
- `DATA/iptv-recordings/jobs.sqlite3`: programări, stări și identități de
  fișiere, cu SQLite WAL. Include URL-uri și titluri private.
- `~/Videos/MediaTool`: MKV-uri, implicit `/home/pysh/Videos/MediaTool`.
  Directorul de ieșire este reținut în SQLite; nu îl muta independent de bază.
- `DATA/local-media/watch.json`: istoricul privat al vizionării locale.

Păstrează copiile în afara repository-ului, cu acces privat și ownership-ul
`pysh`. Pentru baza live folosește API-ul Python SQLite
`source_connection.backup(destination_connection)` către un fișier nou privat,
apoi verifică acea copie cu `PRAGMA integrity_check` și checksum pe PC separat.
API-ul de backup produce o copie tranzacțional consistentă chiar cu daemonul
activ. Nu copia independent `jobs.sqlite3`, `-wal` și `-shm` în timp ce sunt
scrise și nu considera backupul runtime o copie a acestor date.

Copiază separat configurația, istoricul și MKV-urile finalizate; un backup al
bazei nu conține imaginile/audio din MKV și nu fixează un fișier încă în creștere.
Pentru un set comun de restaurare, oprește și salvează joburile, oprește Hub și
recorderul, apoi salvează baza prin API-ul SQLite și restul fișierelor. La
restaurare păstrează mai întâi copia stării existente, ține ambii scriitori
opriți și restaurează baza prin API-ul SQLite plus fișierele asociate în căile
lor originale, cu aceleași permisiuni. Verifică integritatea și disponibilitatea
MKV-urilor înainte de repornire; restaurarea bazei nu recuperează emisiuni
pierdute. Proba completă backup/restaurare pe candidat rămâne necesară.

## Inventar și pregătire (desktop importat)

Auditul live din 2026-10-02 este consemnat în [pi-source-checkout-2026-10-02.md](evidence/pi-source-checkout-2026-10-02.md). Copia sursă este ~/PySH; runtime-ul și release-urile istorice sunt separate în ~/pi-smart-hub.

Înainte de operații: reconfirmă model/OS, disc liber, display/touch, sesiune, versiune activă, servicii audio/rețea și orice schimbări locale. Folosește scripturile read-only `scripts/pi_preflight.py` și `scripts/probe-application.py` numai după afișarea comenzilor exacte. Nu publica rezultatele brute fără redactare.

Ținta necesită Python, Chromium, mpv, BlueZ, NetworkManager, PipeWire/WirePlumber și sesiune Wayland. `scripts/bootstrap-pi.sh` este o operație separată de pregătire, nu un pas implicit de migrare. Dependențele Python se instalează din requirements.lock într-un venv dedicat.

## Deploy al aplicației

1. Rulează verificările DEVELOPMENT și `python scripts/package-release.py` pe PC. Arhiva și manifestul din releases/ sunt artefacte generate, excluse din Git.
2. Identifică commit-ul sursă și build-ul din manifest; transferă arhiva și verifică SHA-256 pe destinație.
3. Extrage într-un director nou `~/pi-smart-hub/releases/<build>`. Nu suprascrie release-ul activ. Venv-ul runtime rămâne `~/pi-smart-hub/.venv`.
4. După review și probe, invocarea `bash ~/pi-smart-hub/releases/<build>/scripts/activate-release.sh <build>` păstrează previous, schimbă current și instalează/pornește serviciul `pi-smart-hub.service` și autostart-ul sesiunii. Aceasta modifică dispozitivul.
5. Verifică sănătatea API, UI reală, touch, audio și preferințe. Înregistrează commit/build și probele în registru. Un simplu `is-active` nu dovedește experiența finală.

## Recovery

`systemctl --user stop pi-smart-hub.service` oprește aplicația; runtime-ul curent păstrează desktopul. `systemctl --user restart pi-smart-hub.service` repornește serviciul. `bash ~/pi-smart-hub/current/scripts/rollback.sh` revine la previous dacă există. Primul deploy nu are versiune precedentă.

Preferințele sunt în `~/.local/share/pi-smart-hub/preferences.json` și copia `preferences.backup.json`. Oprește serviciul înainte de backup/restaurare; păstrează ownership și permisiuni. Nu publica profilurile browser sau cache-ul de conturi. Verificarea completă a restaurării rămâne criteriu de acceptare.

Nu se reflashează cardul sau schimbă conexiunea SSH activă în această etapă. Pentru appliance se va documenta separat recuperarea fără desktop, înainte de activarea noului boot.

## Sincronizarea surselor fără credențiale GitHub pe Pi

Conectorul GitHub poate publica modificările de pe PC. Când Pi nu are autentificare la repository-ul privat, se transferă un Git bundle care conține main verificat față de GitHub. Se verifică checksumul înainte de import; numai cu working tree curat se execută `git fetch /cale/bundle main`, apoi `git merge --ff-only FETCH_HEAD`. Se confirmă HEAD față de commit-ul GitHub și se actualizează origin/main la același SHA verificat. Acesta este un transfer de surse; nu activează aplicația. Nu copia tokenuri personale pe Pi pentru a evita acest pas.

## Windows experimental writer

Pentru scrierea unui SD inactiv din Raspberry pornit pe USB, folosește [flasherul SSH cu progres în consolă](SSH_FLASHER.md). Acesta păstrează o copie integrală verificată separat pe PC, refuză discul activ și verifică imaginea prin recitire înainte de provisioning. Nu folosi fluxul SSH pentru a rescrie SD-ul de pe care rulează Raspberry. Flash/readback, provisioning și primul boot sunt probe distincte.

`scripts/flash-experimental-image.ps1` defaults to inspection. Require the explicit USB disk number, serial, byte size, uncompressed image/hash, signed official Imager path, public key and an existing private log directory outside tracked files. No target defaults exist. The owner must explicitly select/authorize erasure before `-Write`; administrator access is required. Default Imager read-back verification remains enabled. Sources/logs cannot be on the target or traversed through reparse points; system disks and directory-mounted targets are rejected.

On success the writer identifies the verified FAT boot partition by offset/size, copies only the public recovery key, flushes and checks its hash. Use Windows safe removal before disconnecting the drive. Preserve the original SD card and test USB boot separately. A successful write does not certify boot, recovery, root expansion or product acceptance. Private logs and keys must not be committed.
