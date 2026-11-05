# Deplasarea norilor

Cerere: captură actuală și deplasare naturală numai când există nori în date.

- [x] Captură Wayland read-only: cod2, acoperire48%, date actuale. Norii
  Blender existenți se deplasau doar23px în72s, apoi inversau sensul.
- [x] Deplasare continuă a acelorași imagini Blender, viteze pe straturi,
  reluare exclusiv în afara ecranului; fără schimbarea clasificării meteo.
- [x] Browser zi/noapte, sparse/broken/overcast, clear/date lipsă și reducerea
  mișcării; control la limitele ciclului și inspecția capturilor.
- [x] Sursă GitHub verificată, backup PC, instalare și probă nativă în timp real.

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

## Instalare și observație nativă

Runtime `5131fbbab94a`, sursă GitHub `a71660cae35fe6b057f7de1cbd0df5570d556dd4`,
precedent `558fa66b7e13` păstrat. Arhivă SHA-256
`64fcbd23d7719876cdaea718f83c6946719cac40fe4fb4923ae973b897bef60a`;
backup separat PC verificat integral, digest
`f42fed8aea92806f23f18002eb1370e6556f188cc3aaf9a35aa4e1c5274930ca`.
226 hashuri și toate29preferințe corespund; Ethernet/gateway păstrate, radio
reluat. Capturile read-only nu schimbă datele, setările, playerul sau rețeaua.

Două capturi Wayland reale după instalare, la8,446s distanță, arată deplasarea
norilor superior/stânga. Corelarea locală a regiunilor raster, după blur ușor
pentru eliminarea sclipirii stelelor, estimează +21px/+17px. Eroarea potrivirii
este de36/76ori mai mică decât pentru deplasare zero. Perechea anterioară,
la8,430s, arăta +4px/+1px. Perechile au fost inspectate vizual; meteo actuală
neschimbată: cod2, acoperire48%, date neexpirate. Cifrele sunt estimări raster,
nu urmărire 3D sau măsurarea vântului real.

Sursele Blender și numărul maxim de trei imagini sunt păstrate. Mișcarea
folosește exclusiv CSS translate, fără lucru Blender sau buclă JS pe Pi.
Capturile brute rămân private; două cadre nu certifică fluiditate/fps ori
stabilitate de lungă durată. Acceptarea completă rămâne OPEN.
