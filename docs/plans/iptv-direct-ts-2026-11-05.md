# PRO TV HD și surse sportive — redare efectivă

Cererea utilizatorului extinde playerul existent la fluxul MPEG-TS direct al
PRO TV HD; nu schimbă canalul cu un flux News etichetat greșit. Include căutarea
și adăugarea la favorite a Prima Sport1 și Digi Sport1 dacă sursele se verifică,
în HD real (minimum 720p), cu identitatea exactă a canalului românesc.

- [x] Intrare TS publică verificată, normalizare locală în HLS fără recodare,
  păstrând rezoluția și API-ul/playerul existent.
- [x] Destinații publice fixate pe DNS/redirect, date și procese limitate,
  închidere/expirare/schimbare canal fără procese sau fișiere abandonate.
- [ ] Probe sintetice, regresii HLS, recorder independent și audit separat.
- [ ] Sursă GitHub, backup separat PC, instalare și PRO TV HD decodat în UI
  reală 800×480; confirmare Înapoi/Retry și curățare.
- [ ] Surse Prima Sport1/Digi Sport1: identificare exactă, probă video reală,
  favorite salvate; indisponibilitatea/autentificarea se raportează explicit.

Charter: codecurile H.264/AAC confirmate în proba anterioară trebuie să se
decodeze în Chromium printr-o sesiune deținută de backend; ffprobe singur nu
trece acceptarea UI. Userul nu selectează manual protocolul. Fără ocolire DRM,
extragere de conturi sau schimbarea rețelei/audio/profilurilor browser.

Buget: remux FFmpeg copy, fără encodare video, fără dependențe noi. FFmpeg nu
primește URL-ul upstream; adaptorul păstrează validarea și limitele rețelei.
Aceeași clasă este folosită de recorder, cu sesiune și resurse separate.

Verificare PC: 940 teste Python PASS, 46 omise pentru platformă, 11 subteste;
37 teste specifice adaptorului PASS inclusiv cu avertismente tratate ca erori.
TypeScript, build, structura și 96 teste JavaScript PASS; 80 regresii UI
EN/RO × Ink/Noapte PASS. Auditul separat permite proba nativă, nu acordă
acceptare hardware. Proba izolată reală HLS a păstrat 1920×1080 H.264/AAC,
decodat 30 cadre și trecut închidere, repornire și curățare autonomă la expirare.

Limită externă observată: la două conexiuni simultane spre PRO TV, a doua a
primit circa 2 MiB și s-a întrerupt înainte de primul segment. Probele de
concurență internă sunt verzi, dar această sursă nu are încă acceptare de
vizionare și înregistrare simultană. Probe sportive: Digi candidat HLS răspunde
cu manifest, însă video-ul expiră la probă; alte URL-uri Digi/Prima nu oferă
un flux verificabil. Niciun favorit sportiv nou nu este declarat funcțional.
