# Reglaje live — volum și luminozitate

## Problemă și soluție

Sliderul comun și cel extern transmiteau numai la pointerup, iar numerele
veneau din starea confirmată ulterior. Acum draftul afișează imediat poziția,
iar un owner persistent coalescează preview-urile: un request în zbor, o singură
valoare în așteptare, interval minim120ms (125ms extern). Commit-ul final este
distinct, inclusiv când ultima valoare coincide cu un preview deja aplicat.
Polling-ul și răspunsurile vechi nu modifică draftul activ.

Preview-urile schimbă hardware-ul, fără PreferenceStore.update sau fsync.
Volume-only preview păstrează verificarea ieșirii reale și lockul cu polling-ul,
fără scanări de rețea/BT ori restart de vizualizator pe ieșire stabilă. Commit-ul
păstrează persistența și readbackul. Luminozitatea are endpoint typed separat,
minim1%, folosind implementarea existentă de backlight.

Cancel/blur/navigarea finalizează ultima intenție când proprietarul o poate
confirma. O scriere incertă oprește coada: verificarea stării nu repetă mutația,
iar salvarea neconfirmată cere reîncercare explicită. Return extern își păstrează
prioritatea; nu se ascunde o salvare neconfirmată în spatele valorii hardware.

Protocolul extern acceptă flagul strict persist numai pentru volum/luminozitate;
originile, frame-ul și mesajele rămân allowlisted. Worker1.4.2, URL nou
background-scalars-v6.js. Profilurile și conturile nu sunt resetate.

## Verificări înainte de instalare

- 983Python PASS,46skip de platformă,11subteste;192JavaScript PASS.
- 64regresii TV PASS, inclusiv fullscreen și sesiuni/închidere.
- 28probe noi live slider PASS în EN/RO × Ink/Noapte, API mock separat de
  persistență: preview înainte de eliberare, numeric, serializare, polling vechi,
  keyboard/cancel/blur și șapte destinații UI.
- 80probe legacy/recuperare PASS:48audio,24command panels și8erori noi. Au fost
  actualizate așteptările vechi commit-only; nu au fost șterse teste.
- Ultima corecție separă închiderea video de indisponibilitate: finalizează
  intenția de volum la ieșire, dar nu auto-repetă preview-ul eșuat.39/40probe
  inițiale au trecut; o probă apăsa Escape înainte de încheierea operației mock.
  Retest16/16 PASS, inclusiv8erori cu pointer încă apăsat;4închideri video cu
  preview pending PASS. Fără eroare de produs rămasă în aceste scenarii.
- Extern:13teste focalizate,4contexte browser,20capturi; numeric și hardware
  mock diferite de valoarea persistentă, final true și recuperare explicită.
- Audit vizual/focus independent:4contexte ×9suprafețe,36capturi și măsurători,
  plus36capturi existente inspectate. Numeric≥14px, input≥48px după derulare,
  focus păstrat și vizibil. Observație neblocantă: sliderul Ecran din Setări
  începe parțial sub fold; derularea/focusul îl dezvăluie integral.

TypeScript/build și verificarea structurii PASS. Fixture-urile nu sunt probe
acustice sau de backlight. Instalarea și proba nativă R2 sunt consemnate mai jos.
Datele brute rămân private în `.runtime/`; acceptarea globală rămâne OPEN.

## Prima probă nativă și corecția de latență

R1 runtime `9897df27e389`, sursă `03dcb266f37e3d700adb6f8105246637895bb816`,
a trecut 44 verificări: volum și backlight modificate înainte de pointerup,
numeric corect, preferințe neschimbate în timpul glisării și salvate la final,
comenzi rapide și meniul extern YouTube, worker1.4.2/scalars-v6 în profilul
existent și revenire Acasă. Rețeaua, gateway-ul și preferințele au fost păstrate;
backupul PC a fost verificat prin checksum și conținut lizibil. La final,
preferințele/istoricul/volum-mute/starea media au fost restaurate, diagnosticul
închis, trei servicii active și zero convertoare/directoare temporare proprii.
Ieșirea era indisponibilă înaintea probei; a fost selectat temporar endpointul
analog deja enumerat, fără redare, apoi restaurată configurația inițială.
Aceasta nu reprezintă acceptare acustică sau dovada unei boxe conectate.

Timpii R1 includeau mișcarea pointerului, citirea completă `/api/state` și
așteptări IPC ale playerului. Nu sunt latențe de actuație sau măsurători p95.
Inspecția a identificat totuși citiri audio duplicate și polling de rețea/BT
ținând lockul audio. R2 reutilizează observația reală din aceeași secțiune
critică, păstrează readbackul după scriere și scoate polling-ul regulat lent
din lock. Generația refreshului explicit împiedică publicarea stării de rețea
vechi. UI consumă răspunsul audio real al preview-ului, fără a aștepta playerul;
commitul final și recuperarea incertă continuă verificarea completă.

986 Python PASS/46skip/11subteste și 192 JS PASS după corecție; 155 teste Python
focalizate includ o poartă de rețea blocată în timp ce preview-ul se termină,
serializare și readback diferit de valoarea cerută. 140/140 probe browser R2 PASS:
68 live, 48 recuperare audio și 24 panouri de comenzi, EN/RO × Ink/Noapte.
Cele 20 probe suplimentare confirmă că GET-ul global întârziat/indisponibil nu
blochează următorul preview, iar readbackul invalid oprește coada fără autosalvare.
Nicio eroare de fixture în această rulare; sursa runtime a rămas identică.
Proba nativă R2 de mai jos completează aceste rezultate; fixture-urile nu înlocuiesc
verificarea pe dispozitiv.

## R2 instalat și verificat

Runtime `40e96fcc7f76`, sursă GitHub
`c9ac5e2927f9c77a69f07a6d98d1e79bef01dbde`, precedent `9897df27e389` păstrat.
Toate cele 860 bloburi sursă și modurile neexcluse coincid cu arborele GitHub;
229 hashuri runtime și 29 preferințe verificate la activare. Backupul separat
de pe PC a trecut checksumul și citirea conținutului. Ethernet și gateway-ul
nu au fost modificate. [PR18](https://github.com/Therenthe/PySH/pull/18).

44 verificări native PASS, Chromium real la 800×480, EN/Noapte, pointer și
tastatură sintetizate. Restul matricei EN/RO × Ink/Noapte este acoperit de cele
140 probe browser; această probă nu certifică atingerea fizică a panoului.

| Scenariu | Așteptat și observat | Dovezi private |
|---|---|---|
| Volum în comenzile rapide | Trei niveluri aplicate și procent vizibil cât timp pointerul este ținut; preferința rămâne veche până la eliberare; o singură cerere finală persist=true | `02-main-volume-held.png`, requesturi și gest în `report.json` |
| Luminozitate în comenzile rapide | Trei niveluri reale de backlight, numeric corect înainte de eliberare și salvare finală distinctă | `03-main-brightness-held.png`, gest în raport |
| Meniul extern YouTube | Ambele slidere modifică nivelul real în timpul glisării; preferințele se schimbă la final; worker1.4.2/scalars-v6 observat în profilul existent | `05`–`08-native-*.png`, raport |
| Tastatură și revenire | Pasul de volum se confirmă; focus vizibil; Return autorizat închide fereastra de serviciu și ajunge Acasă | `04`, `08`, `09-native-*.png`, raport |

Stările reale au fost observate prin proiecția proprie `/api/external/controls`,
separat de GET-ul complet folosit pentru verificarea preferințelor. Nouă răspunsuri
POST preview volum măsurate în Chromium: mediană345ms, interval300–1144ms,
cu readback hardware inclus. Este un eșantion diagnostic mic, fără comparație
directă cu R1, fără p95 sau garanție de latență. Timpii pointerului și roundtripurile
instrumentului nu sunt timpi de atingere fizică. Luminozitatea a fost confirmată
înainte de pointerup, fără a pretinde o măsurare fotometrică.

La final au fost restaurate exact preferințele, istoricul, volumul/mute și starea
media inițială. Configurația fără ieșire pregătită a fost păstrată: proba a
selectat temporar numai endpointul analog existent, fără redare sau pairing.
`audioRestored:false` reprezintă indisponibilitatea inițială, iar
`volumeMuteRestored:true` confirmă nivelurile restaurate; nu se declară boxă
funcțională sau acceptare acustică. Fișierele sintetice și ferestrele de test au
fost eliminate, porturile de diagnostic închise, trei servicii active și zero
convertoare/directoare temporare proprii. Stările brute și capturile rămân în
`.runtime/native-live-levels-r2-20261106/`; niciun profil sau cont nu a fost citit.

Rezultat scoped PASS pentru reglaje live și feedback numeric. Nu a rămas un
defect blocant în această probă; cele 30 criterii ale produsului complet rămân OPEN.
Auditul vizual nativ independent R2 a inspectat numai zonele proprii ale meniului:
procente ținute, focus tastatură, fără clipping/suprapuneri, Home la revenire;
nicio regresie vizuală observată. Conținutul conturilor serviciilor a fost exclus.

## Follow-up cu boxa pornită: radio și Antena 1

Cererea utilizatorului: reconectare boxă, verificare sunet radio/TV și stare finală
Antena 1 din favorite la15%. Runtime-ul și codul rămân cele de mai sus; nu s-au
schimbat aplicația, profilurile, rețeaua sau serviciile. Boxa cunoscută, deja
asociată, a fost reconectată prin API-ul existent și selectată ca ieșire Bluetooth.

- România Actualități: mpv playing, semnal pe monitorul ieșirii selectate și
  confirmare explicită a utilizatorului „Da, radioul se aude”.
- Antena 1 din favorite: imagine fullscreen și Chromium audio running, legături
  PipeWire active spre sinkul Bluetooth și semnal pe monitorul acelei ieșiri.
  Utilizatorul confirmă „Da, Antena 1 se aude”.
- S-au citit câte16000eșantioane din monitorul de redare numai în RAM, fără
  microfon sau fișiere audio. Semnalul digital completează confirmarea auditivă;
  nu o înlocuiește și nu este o măsurare acustică a volumului continuu.
- Verificarea finală: volum real/salvat15%, mute=false, boxă conectată/selectată,
  radio idle, trei servicii active, zero dispozitive sintetice rămase și porturi
  debug închise. TV-ul a rămas pornit la cererea utilizatorului. Capturile arată
  Antena 1 și controlul15%; toate artefactele brute rămân private în
  `.runtime/speaker-tv-20261106/`.

Prima încercare TV a rămas la Connecting, cu imagine neagră și fără nod audio
Chromium. Ieșirea din player și redeschiderea aceluiași canal au restabilit imaginea
și sunetul. Clasificare: eșec observat de pornire, cauză nedeterminată; nu există
trasare HLS/decoder pentru a distinge fluxul extern de lifecycle-ul aplicației.
Nu se declară remediată cauza. `TV-START-20261106` rămâne OPEN în planul UI.
