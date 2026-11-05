# Digi Sport 1 oficial — integrare și verificare

## Decizie

Utilizatorul a furnizat [pagina oficială Digi Sport 1](https://www.digisport.ro/live/digisport-1)
și a confirmat conectarea prin rețeaua Digi. Clientul public al site-ului
folosește Shaka, DASH, Widevine și sesiuni DAI. PySH deschide playerul oficial
prin browserul deținut al serviciilor, cu aceeași pregătire protejată și meniu
de revenire ca pentru celelalte servicii. Nu extrage tokenuri/chei/licențe,
nu ocolește verificarea de rețea și nu oferă înregistrare IPTV pentru DRM.

Intrarea este în **Media → Servicii → TV**, în lista din stânga, etichetată
**Digi Sport 1 · Player oficial · Rețea Digi**. Este distinctă de canalele M3U;
programul și comenzile video aparțin site-ului oficial.

## Identitate și instalare

Runtime `f6385c202893`, cod GitHub
`d0a3fe7dcb48b744a4badcc1a3bf71cf56763293`; precedent `3ef6f627868a` păstrat.
228 fișiere și 29 preferințe verificate; Ethernet/gateway păstrate,
radio reluat. Backupul separat pe PC a fost verificat prin checksum și conținut:
`52320a510cf78706dae9a6d50450e027c3d2d750a051ce0b4d97d9250900387e`.
Nu au fost schimbate OS-ul, rețeaua sau driverele; profilurile cu conturi nu
au fost resetate.

Manifestul extensiei este 1.4.1, cu entry point nou
`background-digi-v5.js`. Senderul privilegiat Digi necesită HTTPS,
hostname exact `www.digisport.ro`, calea exactă `/live/digisport-1`, frame
principal și ID-ul propriu al extensiei. Subdomeniile, căile cu sufixe,
HTTP și frame-urile copil sunt respinse.

## Probe efectuate

941 teste Python PASS, 46 omise pe platformă, 11 subteste; 110 JavaScript,
TypeScript, Vite și structura repository-ului PASS. 44 regresii TV PASS,
inclusiv EN/RO × Ink/Noapte. Corecția Digi-only (fără mesaj fals „Niciun canal”)
a trecut alte 8 probe. Audit separat de sursă și audit vizual al capturilor:
fără blocaj pentru proba nativă.

Proba preliminară în profilul existent a decodat 1280×720 cu Widevine activ,
cadre 532→601, dar panoul de confidențialitate era încă vizibil. Nu a fost
prezentată drept acceptare a fluxului complet. După instalare, intrarea TV și
pregătirea protejată au deschis exact pagina oficială. „Respingeți toate” a
închis opțiunile suplimentare de confidențialitate fără „Accept toate”.
Meciul real a fost vizibil fără overlay, cu 1280×720, cadre și poziție în avans,
mediaKeys active și fullscreen funcțional. Workerul nou a fost observat în
profilul existent.

Proba finală instalată: **14 verificări PASS**. Intrarea TV a deschis pagina
oficială după pregătirea Widevine; 1280×720, 80 cadre, poziție și cadre în
avans, fără panou peste imagine. Fullscreen oficial PASS. Tragerea de la
marginea de sus a afișat meniul PySH peste containerul fullscreen DIV;
comanda Acasă a închis fereastra oficială prin mecanismul confirmat și a
afișat Acasă în Hub. Capturile private 03/04/05 documentează fullscreen,
meniul și revenirea, fără simularea playerului sau a poziției video.

Verificare finală: runtime și precedent verificate, Hub/recorder/gateway
active, zero convertoare/directoare temporare proprii, porturi debug închise.
Auditul separat al dovezilor native: scoped PASS.

Prima verificare locală a operatorului a refuzat un checksum de fixture
transcris greșit înainte de SSH; checksumul original a fost restaurat.
Prima probă a revenirii aștepta greșit ieșirea obligatorie din fullscreen:
Shaka folosește un container DIV unde meniul poate fi desenat deasupra.
Aceasta este o presupunere a instrumentului, nu o dovadă că meniul nu merge.
Proba a fost corectată să verifice meniul vizibil și închiderea confirmată.
Rapoartele și capturile brute, inclusiv tentativele, rămân private.

O repetare a pierdut elementul video în timpul încărcării paginii; testul a
fost schimbat să ceară două observații consecutive cu cadre și poziție în
avans, tolerând recrearea elementului. Încă o pornire a probei a găsit audio
deja indisponibil și boxa asociată deconectată; restaurarea nu a fost declarată
completă pentru sunet. Utilizatorul a cerut explicit continuarea fără boxă.
Operatorul a fost adaptat pentru această stare inițială și pentru a aștepta
separat disponibilitatea browserului, fără reconectări sau ieșiri forțate.
Ultima curățare a restaurat preferințele, volumul/mute, istoricul și starea
inactivă inițială a playerului, a eliminat numai fișierele proprii și a închis
debugul. Nu se pretinde reluarea radioului sau verificare acustică fără boxă.

## Limite și observații de UX

Nu se revendică acceptare tactilă/acustică nouă sau disponibilitate permanentă;
accesul, calitatea adaptivă, reclamele și condițiile serviciului aparțin Digi.
Rezoluția raportată este cea observată, nu o garanție a fiecărei sesiuni.
Acceptarea întregului produs rămâne OPEN.

Auditul a păstrat trei observații minore pentru o iterație TV ulterioară:
căutarea Digi-only poate lăsa detaliile canalului M3U anterior în dreapta;
culoarea scurtăturii oficiale seamănă cu selecția unui canal; numărul din
antet reprezintă canalele M3U și nu include scurtătura oficială. Titlurile
canalelor, eticheta „Player oficial” și săgeata rămân explicite; nu se prezintă
comanda Înregistrează ca aparținând playerului Digi.
