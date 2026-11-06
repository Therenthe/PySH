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
