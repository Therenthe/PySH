# 0014 — MPEG-TS direct în playerul TV existent

Stare: implementare candidat, 5 noiembrie 2026; instalarea și acceptarea nativă
sunt urmărite separat în planul `iptv-direct-ts-2026-11-05.md`.

## Context

Sursa PRO TV HD din catalog livrează MPEG-TS continuu, nu un manifest HLS.
Proba bounded pe Raspberry identifică H.264 1920×1080 și AAC. Playerul HLS
existent nu trebuie înlocuit și utilizatorul nu trebuie să aleagă protocolul.

## Decizie

Fetcherul validează și fixează destinația publică, inclusiv redirecturile.
Recunoaște trei antete TS aliniate, necriptate, apoi transferă aceeași conexiune
unui adaptor limitat. FFmpeg citește numai stdin și copiază pistele în segmente
HLS private. Nu primește URL-uri de rețea și nu encodează video. Proxy-ul
existent rescrie segmentele în identificatori opaci; API-ul și UI rămân aceleași.

Fiecare sesiune își deține procesul și directorul temporar. Închiderea,
schimbarea canalului, eșecul pornirii și expirarea opresc conversia și curăță
resursele. Limite: trei convertoare/proces, maximum 96 MiB/director,
32 MiB/fișier, 24 fișiere, minimum 128 MiB liber, intrare limitată la 8 MiB/s
și durată maximă 24 ore. Recorderul folosește propria instanță independentă.

## Consecințe și validare

Nu apare o dependență nouă: FFmpeg/ffprobe sunt deja cerute de recorder.
Codecurile incompatibile, DRM și sursele indisponibile rămân erori explicite.
Eticheta HD din catalog nu dovedește rezoluția sau identitatea canalului.
Testele cu mock-uri nu certifică redarea nativă; aceasta cere cadre avansând
în Chromium și verificarea proceselor/fișierelor după ieșire.
