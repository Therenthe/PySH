# Deplasarea norilor

Cerere: captură actuală și deplasare naturală numai când există nori în date.

- [x] Captură Wayland read-only: cod2, acoperire48%, date actuale. Norii
  Blender existenți se deplasau doar23px în72s, apoi inversau sensul.
- [x] Deplasare continuă a acelorași imagini Blender, viteze pe straturi,
  reluare exclusiv în afara ecranului; fără schimbarea clasificării meteo.
- [x] Browser zi/noapte, sparse/broken/overcast, clear/date lipsă și reducerea
  mișcării; control la limitele ciclului și inspecția capturilor.
- [ ] Sursă GitHub verificată, backup PC, instalare și probă nativă în timp real.

Mișcarea este una de prezentare, nu o măsurare a vântului la altitudinea norilor.
Buget: zero texturi noi, zero timer sau buclă JavaScript de animație; maximum
cele trei imagini deja existente. Compoziția statică rămâne pentru reduced motion.
Probele native păstrează vremea, preferințele, audio/radio și datele utilizatorului.

96 probe cer/atmosferă PASS; 12 retestări PASS după corectarea capturilor care
sincronizau artificial straturile la același procent al ciclului. Capturile finale
păstrează fazele naturale și includ cer acoperit la +0/+120/+300s. 903 Python
PASS/46 platform skip/11 subteste și 108 JavaScript PASS; TS/structură PASS.
Limitele: nu este o simulare a vântului la altitudine, nu este acceptarea globală.

Audit independent read-only: zece PNG-uri zi/noapte și faze de cer acoperit,
fără probleme vizuale materiale; verdict scoped ship. Mișcarea și ritmul pe Pi
necesită observația nativă, nu sunt deduse din capturi de browser.
