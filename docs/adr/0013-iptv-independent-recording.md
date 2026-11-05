# 0013 — IPTV HLS și înregistrare independentă

Stare: acceptată pentru implementarea cererii din 5 noiembrie 2026; probele și
starea instalării sunt în planul/evidențele IPTV, fără acceptare globală implicată.

## Context

Media Services trebuie să redea liste M3U, să prezinte XMLTV în ora locală și să
înregistreze MKV chiar cu interfața închisă sau după schimbarea canalului vizionat.
Pi 4 are 4 GB RAM și păstrează Chromium, Python și stiva audio existente.

## Decizie

- Catalogue M3U/XMLTV limitat și persistent în backend; ID-uri și nume
  neambigue pentru asociere, completări oficiale strict datate pentru PRO TV
  și Antena 1. Reîmprospătare în background; stări stale distincte.
- HLS.js 1.7.4, MIT, încărcat la deschiderea vizionării. Chromium decodează un
  singur player TV. Resursele HLS sunt rescrise într-un proxy loopback cu
  identificatori opaci; fiecare destinație și redirect au DNS public verificat,
  socket fixat și limite de dimensiune/concurență. Fără relay public sau DRM.
- Serviciu user systemd separat, `pysh-recorder.service`, fără `PartOf=pysh.service`.
  SQLite serializează comenzile/programările; daemonul este singurul proprietar
  al copiilor FFmpeg. Comenzile de creare au cheie idempotentă.
- FFmpeg remuxează pistele în MKV într-un fișier nou, deschis exclusiv și
  verificat prin descriptor. Fiecare înregistrare are propriul proxy HLS local;
  schimbarea vizionării nu îi schimbă sursa. URL-uri/argumente arbitrare nu
  ajung la o comandă shell. Fișierele active sunt protejate și în Media local.

## Alternative și consecințe

Un timer în React nu supraviețuiește închiderii ferestrei. Integrarea recorderului
în procesul Hub ar opri înregistrarea la restartul UI/backend. Un player extern
adaugă probleme de revenire/focus; păstrăm playerul tactil în Chromium.

Se adaugă o dependență OS explicită, FFmpeg/ffprobe, și un pachet JS fixat.
Înregistrările și baza SQLite sunt date private în afara release-ului. Backupul
lor este separat de backupul runtime; SQLite cere backup tranzacțional, nu
copierea la întâmplare a fișierului WAL activ. Un update ulterior al recorderului
se amână până nu există înregistrări active. Codecurile, disponibilitatea
canalelor și calitatea efectivă se validează separat; lista nu este o garanție.
