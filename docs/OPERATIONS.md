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

Înainte de schimbare, salvează runtime-ul precedent, manifestul sursă, preferințele și configurația afectată; verifică checksumul și conținutul lizibil pe PC. Păstrează originalul SD offline. O imagine CI verde sau un serviciu activ nu înlocuiește proba de boot, touch, audio și redare.

## Inventar și pregătire

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

`scripts/flash-experimental-image.ps1` defaults to inspection. Require the explicit USB disk number, serial, byte size, uncompressed image/hash, signed official Imager path, public key and an existing private log directory outside tracked files. No target defaults exist. The owner must explicitly select/authorize erasure before `-Write`; administrator access is required. Default Imager read-back verification remains enabled. Sources/logs cannot be on the target or traversed through reparse points; system disks and directory-mounted targets are rejected.

On success the writer identifies the verified FAT boot partition by offset/size, copies only the public recovery key, flushes and checks its hash. Use Windows safe removal before disconnecting the drive. Preserve the original SD card and test USB boot separately. A successful write does not certify boot, recovery, root expansion or product acceptance. Private logs and keys must not be committed.
