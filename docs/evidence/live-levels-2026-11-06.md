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

-983Python PASS,46skip de platformă,11subteste;192JavaScript PASS.
-64regresii TV PASS, inclusiv fullscreen și sesiuni/închidere.
-28probe noi live slider PASS în EN/RO × Ink/Noapte, API mock separat de
  persistență: preview înainte de eliberare, numeric, serializare, polling vechi,
  keyboard/cancel/blur și șapte destinații UI.
-80probe legacy/recuperare PASS:48audio,24command panels și8erori noi. Au fost
  actualizate așteptările vechi commit-only; nu au fost șterse teste.
-Ultima corecție separă închiderea video de indisponibilitate: finalizează
  intenția de volum la ieșire, dar nu auto-repetă preview-ul eșuat.39/40probe
  inițiale au trecut; o probă apăsa Escape înainte de încheierea operației mock.
  Retest16/16 PASS, inclusiv8erori cu pointer încă apăsat;4închideri video cu
  preview pending PASS. Fără eroare de produs rămasă în aceste scenarii.
-Extern:13teste focalizate,4contexte browser,20capturi; numeric și hardware
  mock diferite de valoarea persistentă, final true și recuperare explicită.
-Audit vizual/focus independent:4contexte ×9suprafețe,36capturi și măsurători,
  plus36capturi existente inspectate. Numeric≥14px, input≥48px după derulare,
  focus păstrat și vizibil. Observație neblocantă: sliderul Ecran din Setări
  începe parțial sub fold; derularea/focusul îl dezvăluie integral.

TypeScript/build și verificarea structurii PASS. Fixture-urile nu sunt probe
acustice sau de backlight. Publicarea, instalarea și proba nativă sunt PENDING.
Datele brute rămân private în `.runtime/`; acceptarea globală rămâne OPEN.
