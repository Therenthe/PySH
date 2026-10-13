# PySH Remote

Aplicație nativă Android Studio, Kotlin / Jetpack Compose / Material3, Android8+
(minSdk26, target/compile36). JDK21 din Android Studio, Gradle9.4.1, AGP9.2.1.

## Conectare

Instalează APK-ul și conectează telefonul la Wi-Fi-ul PySH. Pe hub deschide
**Setări → Android App Control** și activează serviciul. Aplicația caută automat
huburile locale; alege PySH și confirmă **Da** pe ecranul hubului pentru numele
telefonului tău. Cererea expiră după două minute. Nu introduci IP, certificat
sau cod de asociere. Poți refuza cu **Nu** și elimina telefoane din același meniu.
Clientul folosește numai IPv4 RFC1918, port8766, rețeaua Wi-Fi/Ethernet Android și
HTTPS cu pinning; refuză adresele publice/DNS și redirecturile. Tokenul este
criptat cu Android Keystore, fără backup/transfer automat. Telefonul nu descarcă
sigle sau conținut de pe internet; sursele media/meteo folosesc conexiunea hubului.

| Ecran | Control |
|---|---|
| Acasă | Stare reală, sigle radio prin gateway, volum/mute, transport, seek local, vreme, repaus/activare |
| Radio | Căutare țară/limbă, favorite comune, fluxuri proprii, redare pe hub |
| Media | Pi/USB, directoare aprobate, filtrare, audio/video, ștergere confirmată, servicii oficiale/status/retry/cancel |
| Dispozitiv | Ieșiri audio; Bluetooth power/scan/pair/connect/disconnect/forget/PIN; Wi-Fi scan/connect/editare/eliminare |
| Setări | Luminozitate reală; repaus după 15/30/60/90/120 min și anulare; program zilnic în fusul hubului; limbă/temă telefon și hub; noapte/ceas/vizualizator; carduri/poziții/ancore/straturi/scurtături; locație/fus; service/revenire/setup/diagnostic/revocare |

Radio anterior/următor parcurge favoritele; fișierele folosesc coada backendului.
YouTube/Netflix/Spotify se deschid pe PySH. Autentificarea și comenzile interne
ale site-urilor rămân pe ecranul hubului. Aplicația nu pretinde comenzi OS fără
suport în backend (reboot/shutdown), control universal al paginilor terților ori
acceptare DRM. Wi-Fi poate întrerupe legătura; recuperarea este pe ecranul PySH.
După schimbarea IP-ului, descoperirea locală regăsește același hub și verifică
identitatea și certificatul deja salvat, păstrând tokenul. O cheie înlocuită
cere asociere nouă. Căutarea funcționează în prim-plan; izolarea Wi-Fi sau
blocarea multicastului poate împiedica descoperirea.

Citirea se reia la2s în prim-plan. Starea veche este marcată la deconectare și
comenzile se dezactivează. Mutațiile cu rezultat incert nu se repetă automat.
Răspunsul PIN Bluetooth poate trece simultan cu cererea pairing în așteptare.

Controlul permanent din antet oprește ecranul și redarea prin standby; nu taie
alimentarea și permite activarea din aceeași aplicație. `state.power` furnizează
starea reală, disponibilitatea luminozității, temporizatorul și programul zilnic.
Luminozitatea se trimite numai când utilizatorul termină deplasarea sliderului;
valoarea confirmată este recitită. În repaus se afișează luminozitatea dorită la
activare, distinctă de ecranul stins. Lipsa controlului hardware este explicată.

Siglele folosesc exclusiv `GET /api/radio/artwork?station=current|uuid` cu aceleași
rețea LAN, pin și token; răspunsurile PNG/JPEG/WebP/GIF/ICO sunt limitate la256KiB.
Imaginile obișnuite sunt limitate la4096×4096 și decodare512px. ICO acceptă cadre
PNG și DIB32 necomprimat, maximum256×256, maximum64 intrări; validează limitele
și aplică transparența alpha/AND. Cache-ul are limita4MiB. Lipsa siglei păstrează
inițialele postului și declanșează o reîncercare la60s numai cât este vizibilă.
GETstate menține prezența telefonului; ieșirea în fundal
trimite DELETE `/remote/heartbeat`, ordonat înaintea revenirii în prim-plan.

## Build

Deschide acest director în Android Studio. `local.properties` rămâne local.

```powershell
$env:JAVA_HOME='C:\Android Studio\jbr'
.\gradlew.bat :app:assembleDebug :app:assembleDebugAndroidTest :app:testDebugUnitTest :app:lintDebug
```

APK: `app/build/outputs/apk/debug/app-debug.apk`, candidat semnat pentru instalare
locală, fără publicare GooglePlay. Varianta release este minificată și necesită
cheie proprie de semnare pentru distribuție publică.

`LanPolicyTest` verifică IP/pin/cod/rute. `IcoArtworkTest` verifică directoare și
dimensiuni nevalide, PNG inclus, DIB32, orientare și transparență alpha/AND.
`LiveLanTest` cere hub real, pin și cod nou
în argumentele instrumentării `host`, `pin`, `code`; asociază, citește starea,
trimite volumul existent și capturează ecranele. Păstrează asocierea pentru turul
manual. Capturile se salvează în `files` privat. Preview-urile debug au date de
exemplu și nu pornesc polling; nu certifică LAN sau hardware.

`PowerLanTest` conține decodare ICO nativă, citirea contractului/artwork real și turul UI înRO/EN×teme.
Testul de mutații cere explicit `power_mutations=true`, hub fără redare activă
și fără temporizator existent; salvează și restaurează repausul și programul,
iar luminozitatea este trimisă cu valoarea existentă. Testul artwork citește primul
favorit configurat chiar când playerul este inactiv. Turul UI păstrează ecranul
activ numai pe durata testului; telefonul trebuie deblocat manual. Compilarea testelor nu le
execută pe telefon. Candidatul acestei modificări:0.1.3/versionCode4.

`OnboardingLanTest` verifică identitatea salvată, descoperirea NSD reală,
recuperarea unei adrese salvate nevalide și 28 de prezentări ale configurării.
Testul `fresh_pairing=true` cere aprobarea locală și restaurează asocierea inițială,
revocând numai asocierea creată de test. Nu schimbă IP-ul real al hubului.

[Gateway și instalare](../docs/ANDROID_REMOTE.md) ·
[Dovezi candidat0.1.2](../docs/evidence/standby-remote-2026-10-13.md).
