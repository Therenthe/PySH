# Recuperare și interfață TV — dovezi

## Domeniu și charter

Două cerințe: recuperarea aplicației raportate inutilizabile și refacerea
ecranului TV/ghidului/controalelor fullscreen. [Planul](../plans/tv-recovery-ux-2026-11-06.md)
definește scenariile și limitele. Această probă nu închide acceptarea globală.

## Diagnostic inițial pe dispozitiv

Captură directă Wayland: ceas de repaus cu radio oprit. API și toate cele trei
servicii active, panou800×480. Nu s-au citit profiluri sau conturi. Proba cu
relansare controlată și Chromium existent a recuperat navigarea și a redat
Antena1/PROTV: ambele1920×1080,30/31cadre observate, revenire TV fără eroareJS.
Eșecul inițial nu a fost reprodus, deci cauza lui nu este declarată demonstrată.
Preferințe/istoric/volum/mute/stare player restaurate; fixture propriu eliminat,
porturile debug închise. Ieșirea audio era indisponibilă înainte de probă;
acustica este exclusă conform „Continuă fără boxă”.

## Schimbări urmărite

Un singur toolbar TV; canal/listă în stânga, ghid în dreapta; acțiuni iconice
lângă canal/emisiune, descrieri la cerere. Bara mpv nu ocupă ghidul. Playerul
notifică aplicația despre vizionare, exclude repausul și are termen pentru
lipsa progresului video. Volumul folosește controlul audio comun, cu stare
confirmată și eroare recuperabilă. Schimbarea canalului închide sesiunea veche.

## Verificări intermediare

-941PythonPASS,46skip de platformă,11subteste; TypeScript/Vite/structurăPASS.
-113testeJavaScriptPASS (seturile extensie/navigare/sesiune media).
-RegresieTV inițială36/44; opt eșecuri au indicat ambiguitatea semantică a
  noului element `output` (rol implicitstatus), corectată la text simplu:
  retestare8/8PASS. Au fost păstrate capturile și trasările încercărilor.
-76regresii comune audio/navigare/ownership MediaPASS.
-Detectorul mecanic UI a returnat listă goală; nu certifică accesibilitatea.

Audit separat vizual: 8/8 contexte (EN/RO × Ink/Noapte × navigare deschisă/retrasă),
64 capturi; două emisiuni și acțiunile lor vizibile, radio activ fără footer TV,
editor, surse/căutare/tastatură și fullscreen. Eticheta prematură „În direct”
a fost corectată; retestare 8/8 și 20 capturi pentru conectare/eroare/închidere/
redare/pauză și programare contextuală.

Audit separat tastatură: a găsit focus pierdut la revenire, corectat prin
restaurare după închiderea confirmată; numele programării include emisiunea.
Retestare 12/12 PASS. Indicatorul butonului Play a primit contrast distinct.

20/20 probe noi EN/RO × teme: manifest real HLS cu segmente fără cadre → termen
25s și Retry unic; ramurile simulate acoperă progres/pauză/ended/repaus, API
volum/mute, ordinea închidere→canal nou, ghid selectat, drag și ascundere.
Regresie TV finală 40/44; patru locatoare istorice pentru numele programării
au fost actualizate și retestate 4/4 PASS. Nu s-a schimbat produsul pentru
acele patru eșecuri de harness. Procesele Vite partajate/HMR au invalidat câteva
încercări de audit; rularile independente au folosit porturi loopback proprii.

Runtime pregătit `fda00541134a`, 228 fișiere. Instalarea nouă și verificarea nativă
a acestui candidat sunt încă PENDING.

## Confidențialitate și interpretare

Capturile brute, stările reale și operatorii rămân în directoare private
`.runtime/`. Browserul fixture folosește date sintetice; un ceas media simulat
verifică numai ramuri de control, nu decodare. Nicio probă mock nu se prezintă
ca transmisie reală. Nu s-au schimbat rețeaua, OS-ul, sursele sau favoritele.

## R1 instalat, respins de proba nativă; R2

R1 `fda00541134a`, sursă `6afd5e0ff4be5afa45983d7e53ba12f19e59c56c`:
backup PC verificat, 228 fișiere/29 preferințe, rețea/gateway păstrate și versiunea
precedentă păstrată. Prima probă nativă a găsit însă vechiul TV. Nu este PASS:
locatorul nou a lipsit deoarece pagina randată era veche, nu pentru că noul ghid
ar fi fost validat. Captura și raportul FAIL sunt păstrate. Cleanup complet PASS.

Comparația HTTP directă pe Pi: index servit și index instalat au același hash
`091ddbaefbd958f75a6f0fb6e083621fa88c04a02dbfc867c48c273fac397a36`, cu noul
script `index-nJPmrd8G.js`; Cache-Control absent. Codul StaticFiles permitea
304, iar kiosk deschidea mereu același URL. Aceste probe indică o pagină veche
păstrată de browser; profilurile nu sunt inspectate sau șterse.

R2 `88efb8ce5f6e` servește explicit GET/HEAD `/` și `/index.html` cu no-store,
inclusiv la antete condiționale; URL-ul kiosk folosește hashul conținutului HTML
pentru a evita și cache-ul deja proaspăt. Asseturile cu hash își păstrează cache-ul.
11 teste PASS: corp/antete/HEAD/query, ETag și IMS, fișier nou cu mărime/mtime
identice, index lipsă și identitatea stabilă/schimbată a URL-ului. UI/CSS sunt
identice cu R1 auditat; R2 schimbă backendul și lansatorul. Instalare R2 PENDING.

R2 regresie Python completă: 952 PASS, 46 skip de platformă, 11 subteste.
Fixture Chromium cu profil persistent: rădăcina veche rămâne cache-uită fără
cerere nouă; URL-ul versionat încarcă noul script, apoi no-store revalidează
la reload și relansare în același profil. Nu s-a șters profilul sau cache-ul.
