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

AUD-02 are remediere locală: doar eticheta postului și textele de stare/nivel
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

Acestea sunt probe locale, cu API-uri simulate. Auditul independent al
snapshotului final, publicarea sursei/pachetului și instalarea cu backup verificat
sunt următoarea poartă; nu sunt declarate realizate de acest checkpoint.
Acceptarea fizică, performanța susținută și toate cele 30 criterii de produs
rămân OPEN. Rezultatele instalării se adaugă separat, cu identitatea candidatului.
