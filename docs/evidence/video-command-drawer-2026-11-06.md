# Comenzi rapide în TV și video local

## Problemă și schimbare

Gestul global era dezactivat la video local; TV fullscreen avea un strat și o
izolare de focus care acopereau gestul și meniul. Acum fiecare player are mânerul
central de sus, un buton48×48 și Alt+Shift+P. Se păstrează QuickControls existent,
ca sibling al playerului; numai în modul video, dialogurile proprii și tastatura
sunt deasupra lui. Filmul/sesiunea rămân active la deschiderea sau închiderea
meniului. Sunt afișate canalul sau fișierul real, fără context radio fictiv.

Acasă/Radio/Media/Setări din meniu așteaptă închiderea sesiunii TV cunoscute sau
salvarea/închiderea video local. Eșecul păstrează playerul și recuperarea proprie.
În ramura TV inițială fără ID, se păstrează cleanupul răspunsului sosit târziu;
nu se declară un acknowledgement server înainte de alocarea acelui ID.

Gesturile scurte, orizontale, anulate și pointerul secundar nu deschid meniul;
deplasarea până peste rândul de scurtături nu declanșează navigare accidentală.
Escape aparține numai meniului de deasupra, apoi revine la comanda vizibilă a
playerului. VC-FOCUS-01 a identificat ascunderea HUD-ului după4.5s cât timp meniul
era deschis. Timerul este acum suspendat în acea stare și rearmat la revenire.

## Verificări înainte de instalare

- 986Python PASS,46skip de platformă,11subteste;192JavaScript PASS.
- TypeScript/Vite și structura repository-ului PASS; detectorul mecanic fără constatări.
- Matrice nouă inițială32/32 PASS, apoi108/108 regresii comune/slider/TV și gesturi
  extinse PASS înaintea corecției timerului. Nu certifică atingerea sau codecul real.
- VC-FOCUS-01 a fost reprodus cu meniu deschis6s; aceeași probă a devenit regresie.
  Rulare finală68/68 PASS:36noi,24panouri comune și8TV late-close/failed-close.
  Toate patru probele TV cu meniu deschis6s restaurează focus vizibil și permit
  redeschiderea din tastatură; sursa a rămas identică în timpul rulării.
- Audit vizual independent8TV/local × limbi/teme și8probe focus,72capturi:
  mâner112×10 centrat, colțuri libere, alternativă48px, foaie736×356 fără clipping,
  valori14px, comenzi16px. Contrast eșantionat: Ink≥6.16:1, Noapte≥9.73:1.
  Dialogurile Rețea/BT/Standby și tastatura sunt deasupra video și izolează focusul.
- Retest vizual/focus afectat după timer:4/4 PASS cu meniu deschis6.5s,8capturi
  noi și hashuri actuale verificate. Capturile inițiale rămân baseline istoric.

Un selector vechi de test a fost restrâns la bara transportului pentru a continua
să verifice Play, după adăugarea butonului Quick. Nu a fost eliminată verificarea.
Auditul vizual a separat rotunjirea subpixel, captura în timpul animației și un
helper de test schimbat de defectele produsului; artefactele private păstrează
încercările. Instalarea și probele native sunt consemnate mai jos.

## Instalat și verificat pe Raspberry

Runtime `6314da69ecce`, sursă GitHub
`479361d0af8dc7d64d139122150ace6de2564d17`, precedent `40e96fcc7f76` păstrat.
863bloburi/moduri sursă neexcluse coincid cu GitHub;229hashuri runtime și29preferințe
verificate la activare. Backup separat pe PC verificat prin checksum și citirea
conținutului. Rețeaua/gateway-ul și profilurile au fost păstrate.
[PR19](https://github.com/Therenthe/PySH/pull/19).

Proba folosește sesiunea normală Chromium, 800×480, EN/Noapte, fără browser
diagnostic sau conturi accesate. Atingeri sintetizate printr-un dispozitiv Linux
temporar, eliminat după fiecare gest; calibrarea existentă nu a fost modificată.

| Scenariu | Observat pe dispozitiv | Dovezi private în `native/` |
|---|---|---|
| Tragere peste TV | Quick Controls deasupra Antena1, titlu corect, imagine și legături audio Chromium→Bluetooth active | `pull-1793998337514383900`, `diagnose-1793998423480447100` |
| Reglaje TV cu atingere ținută | Volum9% cu preferință7% și backlight12% cu preferință10% înainte de ridicare; apoi salvare9/12 și restaurare7/10 | `drag-volume-1793998379123699800`, `drag-brightness-1793998384000755000` |
| Închidere/retragere TV | Închiderea meniului păstrează imaginea Live/HUD; redeschidere prin gest; Media revine la ghidul Antena1 | `touch-1793998427314897300`, `pull-1793998431330487200`, `touch-1793998434770681000` |
| Video local real | Clip VP8 propriu320×180,240s, fără audio; Chromium avansează de la0:00.58 la1:12.33, iar starea rămâne Playing după folosirea meniului | `touch-1793998487145189400`, `touch-1793998558794674000` |
| Meniu și reglaje locale | Gestul și butonul48px deschid meniul cu numele real; același preview hardware9/12, persistență la ridicare și restaurare7/10 | `pull-1793998490746863300`, `drag-volume-1793998550632833800`, `drag-brightness-1793998553327245200`, `touch-1793998561991426100` |
| Acasă și cleanup local | Revenire Acasă, închidere sesiune, fișier propriu validat prin hash și șters prin Media API; eliminată numai intrarea lui din istoric | `touch-1793998565533175400`, `fixture-clean-1793998566700078400` |

O secvență de revenire TV a întâlnit modul ambiental Acasă și nu activase meniul
lateral la prima atingere. Verificarea finală a respins starea fără audio TV;
captura arăta Acasă, nu playerul. Clasificare: premisă greșită a automatizării,
corectată prin atingere de wake și navigare observată pas cu pas. Nu s-a modificat
codul și nu este confundată cu TV-START-20261106.

Restaurarea finală este confirmată de `verify-final-1793998821350359800` și
`signal-1793998824882189200`: Antena1fullscreen cu imagine, ieșire Bluetooth
conectată/selectată și semnal digital, luminozitate reală/salvată10%, volum
real/salvat7% (valoarea găsită înaintea probei), fără mute; radio idle. Nivelul7%
era deja salvat înaintea activării/probei și nu a fost suprascris cu indicația
istorică15%. Trei servicii active, precedent păstrat, zero dispozitive touch,
fișiere/istoric de test, directoare transport ori porturi debug rămase.

Auditul nativ vizual independent confirmă contextul TV/local, valorile ținute,
straturile, progresul și revenirea. Capturile brute rămân private. Proba locală
este video-only; nu declară acceptare acustică nouă. Confirmarea auditivă anterioară
a boxei/radio/TV rămâne separată, iar semnalul actual a fost citit numai din
monitorul de redare, în RAM, fără microfon sau fișier audio.

Rezultat scoped PASS. Matricea completă EN/RO×teme, tastatura și erorile injectate
au fost verificate în browser; proba nativă nu înlocuiește gestul fizic pe panou,
testul de stabilitate lung sau acceptarea globală a produsului.

## Limite și stare

Datele brute/capturile rămân în `.runtime/video-command-drawer-20261106/` și
`.runtime/video-command-visual-20261106/`. Nu s-au accesat conturi sau schimbat
extensia, audio, rețeaua ori grafica3D. TV-START-20261106 rămâne OPEN. Acceptarea
globală a produsului și gestul fizic nu sunt acordate din aceste fixture-uri.
