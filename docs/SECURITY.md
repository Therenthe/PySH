# Securitate

- API numai pe loopback; păstrează validarea host/origin și tokenul pentru mutații. Nu publica portul prin router sau LAN.
- Rulează ca utilizator, cu permisiuni minimale; fără endpoint shell generic, sudo global sau dezactivarea politicilor sistemului.
- Parolele Wi-Fi, cheile SSH, tokenurile GitHub, profilurile Chromium și sesiunile serviciilor externe rămân în afara Git și release-urilor.
- Diagnosticele se verifică înainte de publicare. Logurile brute ale dispozitivului, IP-urile, SSID-urile și backupurile private nu sunt probe publice implicite.
- SSH folosește verificarea cheii gazdei; se preferă chei personale protejate. Secretele nu sunt argumente de comandă sau fișiere versionate.
- Păstrează lockfile-urile. Schimbările de dependențe sunt separate și testate. Scanarea simplă locală nu garantează absența tuturor secretelor.
- Serviciile externe gestionează propriile conturi. Nu colectăm parolele lor și nu ocolim DRM.
- Documentația meteo se deschide numai prin identificatorii fixați `open-meteo` și `cc-by`; API-ul refuză URL-uri, căi sau câmpuri suplimentare. Deschiderea documentației nu oprește audio și nu pornește pregătirea DRM.
- Extensia de revenire folosește `nativeMessaging` și `webNavigation`. Observatorul urmărește numai navigările principale ale taburilor de documentație identificate și destinațiile noi pornite din acestea; nu citește conținut, valori introduse sau conturi și nu jurnalizează URL-uri. Scripturile de documentație sunt limitate la originile HTTPS exacte `open-meteo.com` și `creativecommons.org`. Mesajele acceptate cer ID-ul extensiei, cadrul principal și fereastra proprie; pagina de recuperare are originea extensiei și calea exactă `documentation-return.html`.
- Recuperarea unei redirecționări către o destinație neacceptată poate avea loc după inițierea cererii. Observatorul asigură revenirea din fereastra deținută; nu este un firewall și nu blochează toate cererile web.
- Nu s-a efectuat un audit complet de securitate al aplicației în etapa de migrare. NET-02 și celelalte criterii relevante rămân deschise până la probe.
