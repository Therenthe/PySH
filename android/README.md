# PySH Remote

Aplicație nativă Android Studio, Kotlin / Jetpack Compose / Material3, Android8+
(minSdk26, target/compile36). JDK21 din Android Studio, Gradle9.4.1, AGP9.2.1.

## Conectare

Instalează APK-ul și conectează telefonul la Wi-Fi-ul PySH. Introdu IP-ul privat,
amprenta certificatului SHA256 DER și codul local de8cifre (unic, valabil5minute).
Clientul folosește numai IPv4 RFC1918, port8766, rețeaua Wi-Fi/Ethernet Android și
HTTPS cu pinning; refuză adresele publice/DNS și redirecturile. Tokenul este
criptat cu Android Keystore, fără backup/transfer automat. Telefonul nu descarcă
sigle sau conținut de pe internet; sursele media/meteo folosesc conexiunea hubului.

| Ecran | Control |
|---|---|
| Acasă | Stare reală, volum/mute, transport, seek local, vreme |
| Radio | Căutare țară/limbă, favorite comune, fluxuri proprii, redare pe hub |
| Media | Pi/USB, directoare aprobate, filtrare, audio/video, ștergere confirmată, servicii oficiale/status/retry/cancel |
| Dispozitiv | Ieșiri audio; Bluetooth power/scan/pair/connect/disconnect/forget/PIN; Wi-Fi scan/connect/editare/eliminare |
| Setări | Limbă/temă telefon și hub; noapte/ceas/vizualizator; carduri/poziții/ancore/straturi/scurtături; locație/fus; service/revenire/setup/diagnostic/revocare |

Radio anterior/următor parcurge favoritele; fișierele folosesc coada backendului.
YouTube/Netflix/Spotify se deschid pe PySH. Autentificarea și comenzile interne
ale site-urilor rămân pe ecranul hubului. Aplicația nu pretinde comenzi OS fără
suport în backend (reboot/shutdown), control universal al paginilor terților ori
acceptare DRM. Wi-Fi poate întrerupe legătura; recuperarea este pe ecranul PySH.
Adresa salvată se poate schimba păstrând pinul/tokenul.

Citirea se reia la2s în prim-plan. Starea veche este marcată la deconectare și
comenzile se dezactivează. Mutațiile cu rezultat incert nu se repetă automat.
Răspunsul PIN Bluetooth poate trece simultan cu cererea pairing în așteptare.

## Build

Deschide acest director în Android Studio. `local.properties` rămâne local.

```powershell
$env:JAVA_HOME='C:\Android Studio\jbr'
.\gradlew.bat :app:assembleDebug :app:assembleDebugAndroidTest :app:testDebugUnitTest :app:lintDebug
```

APK: `app/build/outputs/apk/debug/app-debug.apk`, candidat semnat pentru instalare
locală, fără publicare GooglePlay. Varianta release este minificată și necesită
cheie proprie de semnare pentru distribuție publică.

`LanPolicyTest` verifică IP/pin/cod/rute. `LiveLanTest` cere hub real, pin și cod nou
în argumentele instrumentării `host`, `pin`, `code`; asociază, citește starea,
trimite volumul existent și capturează ecranele. Păstrează asocierea pentru turul
manual. Capturile se salvează în `files` privat. Preview-urile debug au date de
exemplu și nu pornesc polling; nu certifică LAN sau hardware.

[Gateway și instalare](../docs/ANDROID_REMOTE.md) ·
[Dovezi candidat](../docs/evidence/android-remote-2026-10-13.md).
