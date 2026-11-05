# PRO TV HD — adaptor MPEG-TS și probă nativă

## Sursă și instalare

Runtime `3ef6f627868a`, cod GitHub
`10ae036022ea21e13268032088878d7fb88abfec`, 227 fișiere. Precedentul
`5131fbbab94a` este păstrat. Backup separat PC: checksum și conținut verificate
înainte de activare; SHA-256
`9d9b4f7fd249b216376cd0831729a7f429d99c5b8af62407d0fc364f29ec5d76`.
227 hashuri și 29 preferințe verificate, Ethernet/gateway neschimbate,
radio reluat. Recorderul inactiv a fost reîncărcat pe noul runtime fără a
întrerupe înregistrări ale utilizatorului.

## Așteptat și observat

Playerul existent trebuie să redea sursa PRO TV HD MPEG-TS continuă fără
alegerea manuală a protocolului și fără schimbarea rezoluției.

| Probă | Observat |
|---|---|
| Module izolate pe Pi | HLS local, H.264 1920×1080/AAC, 30 cadre decodate |
| Ciclu de viață izolat | Închidere, repornire și expirare curăță procesul/directorul |
| Chromium existent, 800×480, EN/Noapte | PRO TV HD real, 1920×1080, 89 cadre observate și avans al poziției |
| Comenzi video | Pauză stabilă, reluare cu avans, revenire la lista TV |
| Înregistrare din UI | Fișier MKV real crește; Oprește și salvează finalizează |
| Redare MKV locală | 1920×1080, 18 cadre efectiv decodate în Chromium |
| Ștergere | Confirmare explicită, numai înregistrarea proprie eliminată |
| Restaurare | Preferințe, volum/mute, radio și istoric exact restaurate; probe proprii și porturi debug eliminate |

27 verificări native PASS. Intrarea pointerului este sintetizată; nu se
revendică o nouă acceptare tactilă sau acustică. Capturile și rapoartele brute
rămân private în dosarul probei `native-ts-20261105`.

Proba separată a recorderului: 10 verificări PASS. Pe același canal PRO TV,
fișierul a crescut cu întregul Hub (browser și backend) oprit; PID-ul
recorderului a rămas identic și după relansarea Hub. Înregistrarea s-a
finalizat automat la sfârșitul salvat. ffprobe real confirmă un MKV cu exact
o pistă H.264 și una AAC. Numai jobul și fișierul propriu au fost eliminate;
preferințele, volumul/mute și radioul inițial au fost restaurate.

Verificarea finală instalată: Hub, recorder și gateway active; runtime-ul
curent și precedentul verificate, zero convertoare proprii rămase, zero
directoare temporare `pysh-ts-*`, porturile debug 9222/9223 închise.

## Regresie și audit

940 teste Python PASS, 46 omise pentru platformă, 11 subteste; 37 teste
specifice adaptorului PASS inclusiv cu avertismente tratate ca erori.
96 teste JavaScript, TypeScript, Vite și structura repository-ului PASS.
80 regresii UI EN/RO × Ink/Noapte PASS: TV, biblioteca locală și proprietatea
transportului media. Audit separat al validării publice, socketurilor,
proceselor, limitelor și concurenței: permite proba nativă.

Prima probă Chromium a eșuat deoarece testul presupunea exact opt favorite,
deși utilizatorul avea favorite suplimentare. Este o limită a testului, corectată
fără modificarea listei; reluarea a trecut. Prima probă ffprobe nu includea
opțiunile versiunii FFmpeg pentru căi opace; după corectarea instrumentului,
același cod a trecut. Tentativele sunt păstrate separat.

## Limite externe și sportive

La două conexiuni simultane spre sursa publică PRO TV, a doua a primit circa
2 MiB apoi s-a întrerupt înainte de primul segment. Închiderea și repornirea
secvențială au trecut. Acest rezultat nu certifică vizionare și înregistrare
simultană pentru această sursă și nu este ascuns printr-un fallback News.

Prima Sport 1 și Digi Sport 1 necesită HD real (minimum 720p) și identitatea
canalului românesc. Candidații publici probați nu au furnizat video verificabil.
Un candidat Digi a răspuns cu manifest, dar segmentul a fost indisponibil,
iar ffprobe nativ a expirat. Celelalte URL-uri Digi/Prima nu au trecut accesul.
Nu au fost salvate drept favorite funcționale și nu au fost folosite conturi,
chei sau ocoliri DRM. Disponibilitatea unui URL poate varia ulterior.

Acceptarea globală a produsului, matricea nativă completă și stabilitatea
îndelungată rămân OPEN.
