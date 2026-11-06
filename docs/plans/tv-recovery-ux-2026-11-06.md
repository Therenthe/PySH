# Recuperare PySH și TV tactil — 6 noiembrie

Scop activ cerut de utilizator: (1) diagnostic și recuperare a stării inutilizabile;
(2) TV lizibil la 800×480, ghid utilizabil și volum în fullscreen.

- [x] Captură inițială și identificare runtime/OS/servicii, fără modificări.
- [x] Probă nativă delimitată: navigare și Antena 1/PRO TV, revenire TV.
- [x] Restaurare preferințe/istoric/volum și închidere diagnostic.
- [x] Recuperare explicită pentru flux fără progres și izolarea repausului TV.
- [x] Toolbar compact, ghid curent/următor vizibil, descrieri la cerere.
- [x] Controale SVG, schimbare canal și volum în fullscreen.
- [x] Regresii EN/RO × Ink/Noapte; erori/pending/anulare/focus.
- [x] Auditori independenți, remedieri și repetarea probelor afectate.
- [x] Publicare GitHub verificată, backup PC verificat, instalare reversibilă.
- [x] Verificare nativă pe noul candidat, restaurare și raport final.

## Diagnostic observat

Captura curentă inițială arată ceasul de repaus, radio oprit. API și trei servicii
active. Relansarea controlată pentru diagnostic a recuperat navigarea. În aceeași
instalare, Antena 1 și PRO TV au decodat câte peste30 cadre la1920×1080 și au
revenit în TV. Eșecul inițial nu a fost reprodus; nu atribuim o cauză nedovedită.
Auditul sursei identifică separat lipsa unei limite de progres la TV și lipsa
notificării vizionării către mecanismul de repaus.

## Charter și limite

Mediu: Chromium800×480, candidat identificat, backend/fixture separat și apoi Pi.
Datele fixture sunt sintetice și nu certifică sursele externe. Scenarii: navigare,
curent/următor și programare, favorite/căutare, surse/înregistrări, flux indisponibil,
conectare fără progres, pauză, reluare, închidere și răspuns întârziat, schimbare
canal, volum/mute și repaus exclus în vizionare. Capturi la fiecare stare utilă.

Acceptare UI: două emisiuni complete cu acțiuni în viewport, ținte48px, fără
suprapuneri sau scrollbar vizibil, ambele limbi/teme și navigare extinsă/retrasă.
Acoustică exclusă conform cererii „Continuă fără boxă”. Fără conturi/profiluri,
rețea, OS, surse, favorite sau înregistrări personale modificate. Livrarea globală
a produsului rămâne OPEN. Dovezile brute rămân private în `.runtime/`.

## Candidat pregătit

Runtime `fda00541134a`, 228 fișiere. Sursa și pachetul vor fi publicate și
verificate înaintea instalării. Etapele de instalare și verificare nativă rămân
PENDING până la dovezile lor.

## R2 după proba nativă

R1 instalat, dar proba nativă a respins UI vechi rămas în browser. API-ul servea
indexul nou, identic cu manifestul; lipsea no-store, iar kiosk folosea același URL.
R2 `88efb8ce5f6e`: GET/HEAD pentru index nu mai răspund 304, kiosk folosește hashul
indexului în URL. Nu se șterge cache/profilul și nu se resetează conturi.
Cele 11 probe noi HTTP/launcher PASS; noua livrare și retestarea nativă rămân PENDING.

## Încheiere

R2 `88efb8ce5f6e` / cod GitHub `09162997ea1ac878bf77fa0c306c8fcc07bb4e82`
instalat și verificat. 20 probe native PASS: index/URL/script curent, ghid,
PRO TV și Antena 1 1920×1080, pauză27s, reluare, comenzi/revenire și schimbare
canal cu ghid sincron. Cleanup și verificarea finală servicii/resurse PASS.
Preferințe/istoric/volum/mute și starea inițială idle restaurate. Sunetul fizic
nu a fost verificat la cererea utilizatorului. Cele două obiective sunt închise
în acest domeniu; acceptarea completă a produsului rămâne OPEN.
