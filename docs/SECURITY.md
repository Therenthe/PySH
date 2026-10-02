# Securitate

- API numai pe loopback; păstrează validarea host/origin și tokenul pentru mutații. Nu publica portul prin router sau LAN.
- Rulează ca utilizator, cu permisiuni minimale; fără endpoint shell generic, sudo global sau dezactivarea politicilor sistemului.
- Parolele Wi-Fi, cheile SSH, tokenurile GitHub, profilurile Chromium și sesiunile serviciilor externe rămân în afara Git și release-urilor.
- Diagnosticele se verifică înainte de publicare. Logurile brute ale dispozitivului, IP-urile, SSID-urile și backupurile private nu sunt probe publice implicite.
- SSH folosește verificarea cheii gazdei; se preferă chei personale protejate. Secretele nu sunt argumente de comandă sau fișiere versionate.
- Păstrează lockfile-urile. Schimbările de dependențe sunt separate și testate. Scanarea simplă locală nu garantează absența tuturor secretelor.
- Serviciile externe gestionează propriile conturi. Nu colectăm parolele lor și nu ocolim DRM.
- Nu s-a efectuat un audit complet de securitate al aplicației în etapa de migrare. NET-02 și celelalte criterii relevante rămân deschise până la probe.
