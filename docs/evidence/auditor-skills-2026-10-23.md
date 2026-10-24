# Audit inițial cu skilluri UI/UX — 2026-10-23

Actualizare 24 octombrie: AUD-01/03–09 sunt remediate în domeniul probelor
locale și al retestărilor pe `e1a82fcc1327`, sursă `0c912de`; AUD-02 este păstrat.
[Dovada lotului](ui-polish-2026-10-23.md). Tabelul și stările OPEN de mai jos sunt
constatările inițiale, păstrate ca istoric; nu reprezintă coada curentă.
Acceptarea fizică integrală și conformitatea completă nu sunt deduse din acest lot.

Triage inițial delimitat: **8 defecte de produs și o recomandare APG**, deduplicate;
două priorități P1, șase P2 și una P3. Nu este acceptarea produsului sau o
evaluare completă WCAG. În acest lot se instalează și se aplică auditorii;
defectele erau OPEN; remedierea ulterioară AUD-02 este indicată mai sus.

## Sursă și metodă

Aplicația evaluată este sursa publicată `8cfffd0de81e64f59e1d81c27db0cad3d78a9138`,
corespunzătoare runtime-ului anterior instalat `ca0bbb62a3d8`. Au fost verificate
134 bloburi `app/`: snapshotul înghețat și sursa Git locală coincid. Serverul
de audit folosește numai PC loopback; fiecare auditor are contexte Chromium
separate și API-uri simulate. Nu se schimbă Raspberry, conturile sau datele reale.

Skillurile, reviziile, licențele și rutina sunt în
[AUDITOR_SKILLS.md](../AUDITOR_SKILLS.md). Trei auditori au scris charterul înainte
de probe, au executat interacțiuni și au păstrat dovezi pentru rezultat, nu doar
inspecții ale codului. Root a verificat constatările și a reprodus independent
problema modalelor și tastaturii virtuale.

- **UAT:** patru grupuri de fluxuri × EN/RO × Ink/Noapte = 16 grupuri/context.
  Setări, Radio, Media și Acasă; 92 capturi în rularea finală și două capturi
  suplimentare pentru contrast. Verificările funcționale delimitate trec;
  problema vizuală a etichetei radio este deduplicată în AUD-02.
- **Focus:** 36 stări × patru contexte = 144 capturi. Interacțiuni Tab/Enter,
  focus, închidere, ștergere numai în fixture și aranjare cu săgețile. Cinci
  constatări în schema `a11y-core`, validate; raportul brut este generat cu
  rendererul skillului. Scorul mecanic al acestuia nu este o notă UI/UX.
- **Aspect:** 96 capturi de matrice, zece exploratorii și două de măsurare;
  108 în total, inspectate prin planșe și capturi native. Patru defecte
  confirmate. Măsurătorile sunt la 800×480, DPR1, cu atingere emulată.
- **Detector Impeccable:** context și analiză sursă executate; analiza paginii
  randate prin CDP local a produs două avertismente estetice, analizate mai jos.

Playwright 1.63.0, Chromium 153.0.8010.12, Node 24.19.0. Datele și capturile sunt
sintetice și private. Problemele inițiale de etichete/parametri ale harnessului
au fost corectate înainte de matricea finală și nu sunt raportate ca defecte.

## Coada de remediere

La audit toate rândurile erau OPEN; acum AUD-02 este remediat, restul **OPEN**, responsabil root; auditorul de origine repetă
proba după remediere. P1 se rezolvă înaintea rafinamentelor, apoi P2 și P3.

| ID | Prioritate | Defect / impact observat | Sursă | Rezultat cerut la retest |
|---|---|---|---|---|
| AUD-01 | P1 | Modalul de confirmare și tastatura virtuală lasă focusul în spate; Tab ajunge la alte comenzi, iar închiderea pierde focusul | `app/ui/src/main.tsx:450`, `:452` | Focus inițial în dialog; fundal inert; Tab/Shift+Tab conținute; închidere permisă și revenire la declanșator/succesor, EN/RO × teme |
| AUD-02 | P1 | Eticheta postului și starea semnalului din Acasă restrâns au contrast insuficient peste clădirile orașului | `ambient-home.css:27`, `:117`, `:121`; `AudioVisualizer.tsx:67` | Contrast normal ≥4.5:1 pe fundalul compus, pentru zi/noapte, ambele teme, dimensiuni și poziții mutate; păstrează scena |
| AUD-03 | P2 | Intrarea într-un folder sau ștergerea unui fișier Media pierde focusul; următorul Tab revine la navigarea globală | `main.tsx:289`, `:272` | Focus pe titlu/primul element după navigare și pe vecinul logic după ștergere; inclusiv listă goală |
| AUD-04 | P2 | Redarea Acasă se restrânge după 15s deși Stop are focus, care dispare în BODY | `Home.tsx:31` | Cardul nu se restrânge automat cât timp conține focus; ascunderea explicită mută focusul logic |
| AUD-05 | P2 | Limba, tema și accentul selectate sunt marcate numai prin clase CSS; starea nu apare în arborele accesibil | `main.tsx:417` | Grupuri exclusive cu stare checked/pressed/selected corectă după schimbare și după răspunsul preferințelor |
| AUD-06 | P2 | Eroarea globală ascunde mânerul meniului când bara este retrasă | `canvas-shell.css:15`, `main.tsx:404`, `:409` | Meniul sau o comandă echivalentă rămâne accesibil în timpul erorii, fără pas suplimentar |
| AUD-07 | P2 | Schimbarea secțiunii Setări păstrează scrollul secțiunii anterioare; Vreme se deschide cu titlul și locația ascunse | `main.tsx:414`, `style.css:6` | O secțiune nouă începe logic, ori păstrează intenționat propriul scroll; pollingul nu resetează poziția |
| AUD-08 | P2 | Numele Media cu prefix comun pierd sufixul distinctiv în ellipsis; nu există afișare completă înainte de redare | `Media.tsx:59`, `style.css:5`, `media.css:26`, `:29` | Utilizatorul identifică tactil numele complet fără să pornească fișierul; țintele de 48px rămân |
| AUD-09 | P3 | Opțiunile TouchChoice cu rol radio nu răspund la săgeți conform tiparului APG | `TouchChoice.tsx:29` | Navigare cu săgeți/roving tabindex sau radio nativ; păstrează Tab/Enter/Escape funcționale |

Fișierele fără prefix de director din tabel sunt în `app/ui/src/`.
AUD-09 este recomandare de convenție APG: Tab/Enter permit deja selecția;
nu se declară artificial eșec WCAG Keyboard Accessible. AUD-01 se bazează pe
focusul din fundal și ordinea perturbată, nu doar pe lipsa Escape.
AUD-06 are soluție temporară: Close, vizibil la 48×48, readuce headerul;
nu este o blocare definitivă a utilizatorului.

## Dovezi cheie și pași

**AUD-01:** Setări → Ieși la desktop → Tab: focusul ajunge la „Reia configurarea”
din spatele confirmării. Radio → Caută un post → Tab: focusul ajunge la „Țară”
din spatele tastaturii. Reprodus în toate patru contextele de auditor și separat
de root în RO/Noapte. Sunt dialoguri desktop în fixture, nu o ieșire reală pe Pi.

**AUD-02:** în Ink diurn, după restrângerea redării, 31 poziții din interiorul
literelor numelui radio au raport 1.27–2.41:1, mediană 1.97. Proba independentă
pentru „Semnal audio indisponibil” găsește 203 poziții la 1.17–2.47:1, mediană
1.60. Comparația folosește aceeași scenă înghețată cu/fără text pentru fundalul
de sub literă; capturile cu textul ascuns sunt exclusiv instrumente de măsurare.
Ferestrele luminate pot reduce local și contrastul nocturn. Nu se extrapolează
aceste măsurători la toate scenele.

**AUD-07:** Aspect derulat la 234px → Vreme: panoul rămâne la 117px;
titlul este la y21.59, deasupra panoului care începe la y128.59. Reprodus EN/RO;
matricea arată și ambele teme. **AUD-08:** două fișiere sintetice de 22MB,
cu sufix `integrală 0.mp3` și `integrală 1.mp3`, afișează același prefix;
textul de 582–587px este tăiat într-o zonă de 517px. Căutarea este doar o
soluție temporară dacă utilizatorul cunoaște deja sufixul.

Inventarul privat păstrează charterele, pașii, harnessurile, ledgerele și capturile
sub `auditor-skills-20261023/{uat,focus,visual}`. Manifestul de instalare păstrează
hashurile, iar verificarea root păstrează probe separate. Nu se publică capturi
sau jurnale brute și nu se introduce vreun endpoint public.

## Ce a trecut în domeniul evaluat

- Opțiunile stil/dimensiune vizualizator și timp de repaus rămân deschise peste
  6.5s de ceas/polling; selecția salvează în fixture.
- Radio: filtre, rezultate goale, eroare și retry; normalizare client pentru
  favorite. Fixture-ul nu dovedește aliasurile furnizorului sau redarea reală.
- Media: căutare cu diacritice, cancel/clear, folder gol/revenire și anularea
  ștergerii; ștergerea reușită a fost doar în fixture-ul auditorului de focus.
- Acasă: intrare Arrange cu carduri compacte, cancel, repaus ambiental/wake;
  aranjarea prin săgeți și navigarea retrasă inertă funcționează în probe.
- TouchChoice conține focusul, închide cu Escape și revine la declanșator.
- În cele 96 stări vizuale, țintele primare măsurate sunt ≥48×48, textele
  eșantionate ≥14px, iar documentul are 800×480 fără overflow global. Listele
  derulabile păstrează accesul, fără scrollbar vizibil.
- Cele patru capturi cu reducerea mișcării nu au animații active. Temele și
  identitatea cu stele aerisite/oraș Blender sunt păstrate; fără supereroi.

## Avertismente automate verificate

Detectorul paginii a numit mișcarea metroului „marquee” și lumina cerului
„radial halo”. Sunt false pozitive estetice în raport cu cerințele explicite:
metroul animat și atmosfera cerului sunt parte din scena cerută; metroul se
ascunde la reducerea mișcării. Nu se elimină doar pentru a obține zero avertismente.
Analiza sursei a întors zero constatări: aceasta nu certifică integritatea UI.

Context loaderul a semnalat lipsa schemei proprii de documentație și directorul
Android. Nu se migrează PRODUCT și nu se schimbă platforma hubului pe baza
acestor euristici: Android este clientul separat de telecomandă, iar ținta
auditului este hubul Chromium. Nu au fost instalate hookuri.

## Limite și următorul lot

Nu s-au evaluat fizic touch, contrastul panoului, screen readerul, audio,
rețea/BT reale, conturi/DRM, restart/persistență, toate combinațiile meteo,
performanța Pi sau stabilitatea de opt ore. Nu s-au rerulat inutil toate
testele aplicației pentru schimbări de documentație și skilluri personale.
Inventarul celor 30 criterii de produs rămâne OPEN.

Următorul lot: remediere comună a focusului dialogurilor și contrastului
etichetelor, apoi focus Media/Acasă, starea selecțiilor, navigarea în eroare,
scroll Setări și nume Media. Fiecare remediere repetă proba de mai sus, apoi
verificările afectate și capturi comparabile. Ultimul pas este polish local,
fără schimbarea identității vizuale sau omiterea restanțelor istorice.
