# Oraș și animații — polish 2026-10-23

Implementarea v2 rafinează identitatea existentă. Nu introduce o lume vizuală
nouă, supereroi, fotografie de galaxie sau un motor 3D în runtime.

## Oraș Blender

- Coroane civice, mansarde și parapete variate înlocuiesc repetarea acoperișurilor.
- Glafuri, montanți și goluri de fațadă au adâncime; arcadele viaductului sunt
  volumetrice. Culorile pietrei și lumina laterală separă planurile.
- Ferestrele nocturne formează grupuri cu lumină caldă/rece reținută; ziua au
  reflexie mai rece și nu par iluminate ca noaptea.
- Metroul are articulație, rame și detalii mai clare, fără a deveni elementul
  dominant al scenei.

Camera 1600×570 și amprenta UI de 208px rămân neschimbate. Proiecțiile pentru
radio/Bluetooth și acoperișul Wi-Fi sunt păstrate exact. Sursele v1 rămân reper.
Fișierele v2, generatorul și procedura sunt în [proveniență](../../assets/blender/README.md)
și [build-report-v2.json](../../assets/blender/build-report-v2.json).

Trei PNG-uri: 1,162,333 bytes comprimați / 7,492,608 bytes RGBA decodați pentru
setul complet zi/noapte/metrou. Interfața folosește randări transparente ale
geometriei 3D Blender, fără un renderer ascuns care concurează cu redarea video.
Geometria procedurală este reproductibilă; randarea EEVEE poate varia în bytes
între rulări. Hashurile fixe identifică activele efectiv verificate și livrate.

Audit Blender: 2,744 componente închise verificate, 36 arhetipuri de componente
trec poarta render cu zero erori/avertismente; 50 plane deschise de geam sunt
intenționate. Fără fețe zero, elemente loose sau normale inversate; color audit
gol. Planșele orbitale, valori de gri, referință Cycles și comparațiile la
800×208 au fost inspectate. Nu este revendicat un model watertight sau export
de joc acceptat.

## Mișcare și lizibilitate

Metroul are un ciclu de 100s cu două treceri liniare de 18s în sensuri opuse,
separate de 32s de repaus. Schimbă orientarea numai în afara zonei vizibile.
Radio emite două unde mai discrete; Bluetooth conectat are un indicator stabil.
Wi-Fi emite numai când ruta reală este wireless; asocierea în rezervă rămâne
distinctă. Opacitățile și culorile sunt adaptate scenei diurne/nocturne.

Vizibilitatea documentului și IntersectionObserver condiționează împreună
animațiile orașului. Mișcarea redusă păstrează sensul static al conexiunii și
oprește deplasările decorative. Nu se schimbă condițiile/fazele meteo, Luna,
stelele, aeronavele, serviciile de rețea sau preferințele.

AUD-02 este remediat în candidatul instalat: doar eticheta postului și textele de stare/nivel
audio primesc un fundal stabil. Unda și restul scenei rămân transparente.
Se verifică contrastul și peste ziduri întunecate, și peste ferestre luminoase.
Celelalte opt rânduri ale [auditului](auditor-skills-2026-10-23.md) rămân în coadă.

## Verificări și stare

- 633 teste Python PASS / 32 omise pentru platformă; 80 verificări ale extensiei
  PASS. TypeScript, Vite și inventarul repository-ului PASS.
- 24 probe noi pentru etichete PASS: EN/RO × teme × zi/noapte × trei dimensiuni,
  inclusiv nivel static cu reducerea mișcării și revenire în card.
- 150 probe browser combinate PASS, apoi 52 probe afectate repetate după
  înghețarea definitivă a activelor. Există capturi EN/RO × teme la 800×480.

Acestea sunt probe locale, cu API-uri simulate. Rezultatele finale de mai jos
completează checkpointul sursei; nu transferă acceptarea hardware din fixture.

## Candidat final publicat și instalat

Runtime `1371bbff602e`, sursă
`6ad7ad51524f653c17818e5e06fb8151e09a17b8`, instalat cu backup citit și verificat
separat pe PC; precedentul `ca0bbb62a3d8` rămâne disponibil. Cele 106 fișiere runtime
și 29 de preferințe au hashurile așteptate; rețeaua, gatewayul și profilurile sunt
păstrate. Radioul curent a fost reluat și ieșirea audio rămâne pregătită.

Regresia finală pe sursa înghețată: **326 probe browser PASS** în EN/RO.
Auditul independent a inspectat 130 de capturi UI și 32 de capturi de contrast pereche,
în opt contexte limbă/temă/zi-noapte, plus cazuri meteo și de semnal. Minimul
măsurat al etichetelor: 13.669:1; fără erori de pagină, overflow global sau ținte
primare eșantionate sub 48px. S-au verificat restrângere/ambient/wake, aranjare,
mișcare redusă, pauza orașului ascuns și sensurile metroului.

Pe panoul real 800×480: oraș Blender v2, 208px, cele 12 active verificate și decodate
(3 oraș/metrou, 3 Wi-Fi, 6 cer), etichetă audio cu fundal stabil și contrast-limită
calculat 14.74:1. Home a trecut automat în ambient. O probă scurtă de 180 de cadre în
aproximativ 3s a avut rAF p95 de 16.7ms; aceasta nu este latență tactilă fizică sau
probă de performanță susținută. Cadrul de metrou a fost ales prin faza CSS pentru
inspecție, nu este declarat o observare a unei treceri programate în timp real.

Datele meteo reale ale probei nu au fost simulate sau schimbate: cod 45,
vizibilitate 5540m, nebulozitate 77%, stare proaspătă; scena păstrează haze 0.056 și
cer acoperit, fără Soare/Lună forțate. Acestea sunt estimări de furnizor, nu
observații directe din exterior. Stelele, faza Lunii și logica meteo sunt păstrate.

Preferințele, sursa audio și redarea au rămas identice. Diagnosticul loopback a
fost închis; Chromium normal și radioul au fost restaurate. Capturile și
jurnalele brute sunt private, fără tunel public sau încărcare în cloud.

## Restanțe păstrate

AUD-02 este închis în domeniul acestei remedieri; celelalte 7 defecte și recomandarea
APG din audit rămân OPEN. Auditorul a observat separat cinci animații de sclipire
preexistente care rămân `running` în inventarul DOM când `document.hidden` este
simulat. Orașul se oprește explicit; cerul nu a fost schimbat. Această observație
nu dovedește consum GPU/CPU în fundal și cere o probă de lifecycle real separată.

Nu se declară 10/10, acceptare fizică integrală, DRM, persistență după reboot,
memorie sau stabilitate de opt ore. Toate cele 30 de criterii complete rămân OPEN.
