# Plan urmărit de livrare UI/UX — 2026-10-04

Acest inventar păstrează cerințele din conversație, inclusiv cele vechi. Nu acordă note sau acceptare din descrieri. GitHub este sursa canonică; implementările nepublicate sunt lucru local. Candidatul instalat la începutul acestui tur:43bbb099a8b6/source22e7. Toate cele30criterii de produs rămân OPEN în acceptance.json. O probă veche nu certifică un candidat nou.

Ordine:1vizualizator și aranjare stabilă →2meteori →3repaus Acasă →4defectele auditorilor și tur complet →5acceptare nativă și imagine finală. Cerințele noi se adaugă; nu înlocuiesc restanțele.

| ID | Cerință și rezultat urmărit | Stare / responsabil / dovadă |
|---|---|---|
| UI-01 | Dimensiunea Compact/Echilibrat/Mare schimbă toate stilurile, inclusiv cu redarea extinsă și poziții manuale | Instalat94/sourcec1; matrice audio e2e trecută; proba tactilă/persistență nativă finală OPEN |
| UI-02 | Variante audio distincte, semnal real, logo/nume post, pauză/mute și reduced motion oneste | Instalat94; geometrii/pixeli inspectați, semnal real; tur hardware final OPEN |
| UI-03 | Arrange cu carduri restrânse; aliniere dreapta/jos păstrată la extindere spre spațiul liber; Done/reload persistente | Instalat94;6teste ancore+4swap/suprapunere trecute; gest tactil fizic final OPEN |
| UI-04 | Schimbarea pozițiilor, suprapunere voluntară, selectarea cardului acoperit și ordinea straturilor | Instalate94 și păstratec425; swap/suprapunere regresie trecută; gest fizic final OPEN |
| UI-05 | Meteori descendenți cu cap/coadă corecte, lungimi/unghiuri/viteze și intervale variate | Instalat94;8probe geometrie/browser trecute; tur vizual/performance final OPEN |
| UI-06 | Acasă inactiv: numai ceas, vizualizator și scenă; fără screensaver separat; prima atingere arată cardurile compacte fără comandă accidentală | Instalatc425/source06b5;264cazuri acoperite, audit independent și captură panou; wake fizic/performance final OPEN |
| UI-07 | Spectacol ambiental matur: stele sclipitoare, evenimente rare variate, posibile avioane și praf lunar, fără a simula informații astronomice/live | Instalat7d525/sourcecd1ff; bounded scheduling/reduced motion/settings pending și audit browser trecute; performance/tur fizic OPEN |
| UI-08 | Lună cu fază reală; scenă zi/noapte și condiție meteo coerente, nori vizibili, ploaie/zăpadă peste oraș, lumini urbane și skyline mai înalt | Instalat7d525; textură NASA cu fază calculată, stele/nori/lumini revizuite și captură panou inspectată; tur meteo/performance final OPEN |
| UI-09 | Card vreme se reduce la partea principală; prognoză1↔5zile cu icoane; separare vizuală corectă la extindere | Există implementare; layout nou și ancore necesită regresie |
| UI-10 | Redarea se retrage în vizualizator; atingere o extinde, reatingere/inactivitate o restrânge | Există implementare; Arrange trebuie să permită poziționarea cardului compact |
| UI-11 | Meniu retractabil, mâner aproape de stânga care urmează marginea; header transparent la inactivitate, solid la utilizare | Instalat24b268: contrast mâner Ink/open/idle corectat;16stări randate și18regresii Home trecute; tur fizic final OPEN |
| UI-12 | Fără scrollbar vizibil; swipe tactil funcțional; fără scroll accidental Acasă | Regresie completă și probă tactilă nouă OPEN |
| UI-13 | Personalizare carduri Acasă, dimensiuni/stiluri vizualizator, screensaver numai vizualizator pe întregul ecran | Există setări; fiecare combinație/persistență verificată din nou |
| UI-14 | Fără salut fictiv, duplicări de ceas/redare/text; pictogramă settings corectă, logo pentru posturile care au | Există corecții; tur vizual/inventar OPEN |
| UI-15 | Căutare București și sectoarele1–6; normalizare radio romania/Romania/diacritice | Există corecții; backend și e2e/nativ regresie OPEN |
| UI-16 | Meteo actualizat automat, recuperare automată, fără refresh manual | Există refresh5min/retry1min; online/offline/stale nativ OPEN |
| UI-17 | Temă nocturnă după apus/răsărit la locație; ambele teme logice și lizibile EN/RO | Există implementare solară; noile geometrii/layout necesită revizie |
| UI-18 | Dropdownuri stabile, tastatură apare când trebuie și dispare după utilizare | Probe existente; tur toate controalele/nativ OPEN |
| UI-19 | Netflix imersiv, fără rame/scroll; întoarcere la hub recuperabilă dar discretă | Implementare existentă; film DRM real/resoluție/audio încă OPEN |
| UI-20 | Bluetooth: pending/eroare/retry în dialogul activ, fără eroare ascunsă în spate | Instalat98385/source9e91;52probe recovery+316regresie browser; hardware final OPEN |
| UI-21 | Salvare locație eșuată păstrează rezultatele și permite retry | Instalat98385/source9e91;52probe recovery+316regresie browser; hardware final OPEN |
| UI-22 | Animații/microanimații explică acțiunile, aspect matur apropiat de referințe, fără ornament care ascunde UI | Revizie continuă pe800×480; fără autoevaluare10/10 |
| UI-23 | Atribuire meteo cu link sursă/licență lângă date, revenire la hub fără întreruperea radioului | Instalat d56dd/sourceee423;338inițiale apoi146afectate și30extensie;28probe native/208eșantioane radio trecute; profil conturi/physical/full acceptance OPEN |
| UI-24 | Media: după eșecul deschiderii unui folder sau al revenirii, retry repetă exact destinația; răspunsurile vechi nu înlocuiesc navigarea nouă | Instalat d56dd/sourceee423;20probe noi incluse în146regresii afectate trecute; Media native error tour OPEN |
| UI-25 | Prima intrare Arrange fără poziții salvate: toate cardurile și mânerele compacte încap, fără suprapunere accidentală, la fiecare dimensiune audio | Instalat d56dd/sourceee423;22regresii existente și12probe inițiale;36native edge/persistence și12first-entry trecute; preferințe restaurate; physical touch OPEN |
| UI-26 | În Arrange, numele București · Sector 5 complet vizibil fără padding redundant; sursa și mânerul rămân independente | Instalat48561/source9eb5;26probe afectate și12native full-text/bounds trecute; preferințe restaurate/porturi închise; physical touch OPEN |
| UI-27 | O singură selecție media în pending; navigarea/folderul nou abandonează overlay/retry vechi; lansarea serviciilor nu intră în conflict cu fișierul local | Corecție locală integrată în942427;60probe selecție/navigare și24probe serviciu↔fișier trecute; 438regresii înainte de ajustarea feedbackului,192afectate și8suplimentare după; instalare/hardware acceptare OPEN |
| UI-28 | Dimensiuni de fișiere cu unități B/KB/MB/GB, zero vizibil și valori necunoscute omise; rânduri lizibile EN/RO | Corecție locală integrată;4probe randate EN/RO×teme,21valori fiecare, trecute; 192probe afectate trecute; publicare/instalare încă OPEN |
| UI-30 | Feedback lansare serviciu înlocuiește explicația și nu împinge comenzile în afara panoului; acces tactil înainte/după | Corecție locală942427;8contexte EN/RO×teme×radio și192afectate trecute; tur nativ OPEN |
| UI-29 | Eroarea redării locale explică recuperarea fără a inventa o cauză de codec sau a expune loguri | Auditor a identificat mesajul generic pentru stream_failed; remediere și verificare încă OPEN |
| INTEGRATION-01 | Radio Browser: semnal best-effort numai la porniri explicite cu UUID catalog valid | Instalat24b268/source152f;327backend și110browser teste trecute; actual upstream counter reply not claimed |
| QA-01 | Auditor uzabilitate execută fiecare comandă, inclusiv eșec/retry/cancel | Raport user-ui-audit-2026-10-04:232existente+12probe+4lifecycle; fixture≠hardware |
| QA-02 | Auditor aspect inspectează capturi EN/RO×Ink/Noapte și stări expand/collapse/idle | Raport visual-ui-audit-2026-10-04:72combinații+4Arrange; retest nou candidat OPEN |
| QA-03 | Vizualizare întregului panou exclusiv privată, prin PC loopback/SSH; fără publicare sau înregistrare | Există viewer privat; nu expunem API/viewer în internet |
| OS-01 | Flasher SSH cu progres în consolă, identificare disc, backup înainte de scriere, verificare și recuperare | Migrare SD făcută anterior; final UI nu cere reflash la fiecare corecție; release final OPEN |
| OS-02 | GitHub canonic, repo agent-friendly, documente/ADR/source/teste/manifest/CI și rollback | Structură existentă; sincronizare și CI pentru fiecare candidat |
| PERF-01 | Memorie întregului arbore incl.Chromium separat;5lansări, latență tactilă,8ore pe același candidat | Collector corectat22e7;931b8:5relansări aplicație4.701–5.089s și idle complet598.951MiB laHome+120s; coldboot/latency/media/8h OPEN; vechile sume cgroup-only invalide pentru total |
| DELIVERY-01 | Toate30DoD:hardware,Wi-Fi/offline,radio/local media,BT,streaming,boot,recovery,secrete,licențe și imagine finală bootată | OPEN; acceptance.json rămâne inventarul obligatoriu, nu se substituie cu teste UI |

Pentru fiecare remediere se consemnează: sursă/candidat, test executat, rezultat real, captură inspectată, publicare și instalare. Utilizatorul primește o actualizare când remedierea este verificată; nu numim implementarea locală drept instalată. Preferințele și aranjarea utilizatorului se păstrează. Auditorii nu schimbă dispozitivul sau conturile pentru a produce un PASS.

Verificarea sursei152/fc4 și build-ul OS nu au pornit runner-ele GitHub din cauza setărilor de plăți/limită ale contului. [Dovada și poarta rămasă](evidence/actions-runner-not-started-2026-10-04.md). Nu se substituie CI/imaginea actuală cu rezultatele verzi ale surseicd1ff. Testele locale și native independente continuă.
