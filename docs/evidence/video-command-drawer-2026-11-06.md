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
încercările. Publicarea, instalarea și proba nativă sunt PENDING.

## Limite și stare

Datele brute/capturile rămân în `.runtime/video-command-drawer-20261106/` și
`.runtime/video-command-visual-20261106/`. Nu s-au accesat conturi sau schimbat
extensia, audio, rețeaua ori grafica3D. TV-START-20261106 rămâne OPEN. Acceptarea
globală a produsului și gestul fizic nu sunt acordate din aceste fixture-uri.
