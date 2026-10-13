# Telecomanda Android în LAN

`services/remote` este un gateway opțional separat. API-ul PySH existent rămâne pe
`127.0.0.1:8765`, cu validarea Host/Origin și tokenul sesiunii intacte. Gateway-ul
folosește HTTPS pe adresa privată explicită a Pi-ului, implicit portul `8766`.
Nu folosește cont, cloud, server intermediar, UPnP sau descoperire pe internet.
Telefonul și Pi-ul trebuie să fie în aceeași rețea locală ori într-o rețea privată
rutată administrată local. Izolarea clienților Wi-Fi poate bloca legătura.

## Instalare pe Pi

Comenzile următoare sunt pentru runtime-ul appliance `/opt/pysh/current` și venv-ul
existent `/opt/pysh/venv`. Se rulează **ca utilizatorul sesiunii PySH**, după livrarea
fișierelor gateway-ului în release. Nu s-au executat prin acest document.
Pachetul de sistem `openssl` trebuie să fie instalat. Gateway-ul nu adaugă
dependențe Python. IP-ul este o adresă RFC1918 IPv4, ULA sau link-local IPv6;
wildcard, loopback, DNS și IP public sunt refuzate. Folosiți o rezervare DHCP.
Aplicația Android livrată folosește numai IPv4 privat și portul fix 8766; configurați
gateway-ul pe această adresă/port. Suportul IPv6 al gateway-ului este disponibil
pentru clienți viitori, dar nu este oferit în formularul acestui client Android.

```sh
cd /opt/pysh/current
/opt/pysh/venv/bin/python -m services.remote init --host 192.168.1.50
mkdir -p ~/.config/systemd/user
install -m 0644 services/remote/pysh-remote.service ~/.config/systemd/user/pysh-remote.service
systemctl --user daemon-reload
systemctl --user enable --now pysh-remote.service
systemctl --user status pysh-remote.service --no-pager
/opt/pysh/venv/bin/python -m services.remote pair
```

Înlocuiți `192.168.1.50` cu IP-ul LAN efectiv. Datele private sunt în
`~/.local/share/pi-smart-hub/remote`, director `0700` și fișiere `0600` pe Linux.
Certificatul și cheia nu intră în Git, APK sau arhiva release. Certificatul se
generează local; nu se trimite cheia privată telefonului. Unitatea presupune
layout-ul appliance; pentru instalarea desktop adaptați numai WorkingDirectory
și calea interpretorului la release-ul și venv-ul existente. Unitatea folosește
UMask, NoNewPrivileges și RestrictAddressFamilies fără sandbox bazat pe mount/user
namespaces; PrivateTmp/ProtectSystem/ProtectHome ar putea împiedica pornirea
serviciului user pe Pi-uri unde user namespaces sunt dezactivate (status 226).
Pentru instalarea separată sidecar, folosiți directorul verificat
`/opt/pysh-remote/<hash>` ca WorkingDirectory și păstrați venv-ul existent în ExecStart;
backendul și runtime-ul PySH curent nu trebuie înlocuite pentru activarea gateway-ului.

În aplicație introduceți IP-ul IPv4 privat și amprenta `Certificate SHA256` afișată
de comanda locală. Amprenta este SHA-256 peste **certificatul X.509 DER complet**,
64 caractere hex lowercase, fără două puncte; nu este hash SPKI. Aplicația trebuie
să verifice această amprentă în handshake TLS înainte de trimiterea codului sau
tokenului. Codul de 8 cifre funcționează 5 minute pentru un telefon, cu maximum
5 încercări; o nouă comandă `pair` înlocuiește codul anterior.

Nu configurați port forwarding, DMZ, reverse proxy public sau tunel internet.
Filtrarea adreselor private nu poate detecta un router care rescrie traficul WAN
în IP privat: izolarea de internet cere și absența acestor configurări în router.
Firewall-ul LAN poate limita suplimentar portul 8766 la subrețeaua telefonului.

## Contract pentru client

| Cerere | Răspuns |
|---|---|
| `GET /remote/health` fără autentificare | `{"service":"pysh-remote","version":1}` |
| `POST /remote/pair`, JSON `{"code":"12345678","name":"Telefon"}` | `{"token":"…","deviceId":"UUID","name":"Telefon"}` |
| `POST /remote/revoke-self`, bearer autentificat, JSON `{}` sau corp gol | `{"revoked":true}`; următoarea cerere cu tokenul respectiv primește 401 |
| API permis pe `/api/*` | JSON și codurile de stare ale API-ului PySH |

Telefonul trimite `Authorization: Bearer <token>` pentru fiecare comandă și citire.
Tokenul se emite o singură dată și se păstrează în spațiul privat protejat al
aplicației. Gateway-ul stochează numai hash-ul lui, suportă până la 16 telefoane,
și nu exportă tokenul sesiunii locale. Acțiunea de revocare self poate retrage numai
tokenul telefonului apelant, fără un ID de telefon trimis de client. Dacă telefonul
este offline când utilizatorul îl elimină din aplicație, revocarea se poate face din
CLI pe Pi. `/api/session`, `/api/media/file`, paginile
web și rapoartele interne DRM nu sunt expuse: telecomanda redă media **pe Pi**.
Codurile de ștergere media întoarse de `/api/media` sunt contractul existent,
distinct de tokenul sesiunii locale.

Lista autoritară metodă/cale este `ROUTES` în `services/remote/gateway.py`.
Sunt permise starea, toate preferințele, audio, Bluetooth inclusiv răspunsurile
PIN/confirmare, rețeaua, vremea/locația, radio/favorite, directoarele media și
ștergerea confirmată, redarea/transportul, deschiderea serviciilor externe și
retry/cancel, ieșirea și revenirea din modul service, diagnosticele redactate.
Query string-urile existente se păstrează. Corpul este JSON, maximum 64 KiB;
răspunsul maximum 2 MiB. Nu se urmează redirect-uri, nu se transmite niciun header
de autentificare al telefonului la backend. HTTPS nu acceptă Origin de browser.

Erorile gateway sunt JSON `{"error":"<cod>"}`: `unauthorized` (401),
`pairing_invalid`/`pairing_expired` (403), `device_limit` (409),
`route_not_allowed` (404), `request_too_large` (413), `rate_limited` (429, Retry-After),
`upstream_unavailable` (503), `upstream_redirect_blocked` (502),
`invalid_request` (400), `forbidden_origin`/`lan_required` (403).
Limite: 120 cereri/minut/IP, 600 global, 5 cereri pairing/minut/IP, 16 conexiuni
concurente, handshake TLS 5 secunde. API-ul local este ținta fixă, independent de
variabile HTTP_PROXY. Tokenul local se recitește automat după restart PySH numai
când API-ul confirmă că o mutație a fost respinsă înainte de execuție.
Cererea mutației nu ține lock-ul tokenului: un pairing Bluetooth în așteptarea
confirmării permite simultan cererea separată `/api/bluetooth/reply`.

## Revocare, oprire și actualizare

```sh
cd /opt/pysh/current
/opt/pysh/venv/bin/python -m services.remote devices
/opt/pysh/venv/bin/python -m services.remote revoke --device-id UUID
systemctl --user disable --now pysh-remote.service
```

Revocarea este efectivă la următoarea cerere, fără restart. Dacă IP-ul se schimbă,
opriți gateway-ul, modificați `host` în fișierul privat `config.json`, reporniți-l
și actualizați IP-ul din aplicație. Pinning-ul verifică identitatea certificatului
independent de IP; nu dezactivați verificarea pinului. Pentru înlocuirea cheii,
folosiți un director privat nou cu `init`, revocați telefoanele vechi și asociați
din nou cu noua amprentă. Protejați datele private în backup separat. Actualizările
codului păstrează datele; păstrați certificatul pentru a evita pairing repetat.

## Verificare și limite

`python -m pytest tests/test_remote_gateway.py -q` verifică adresele private,
pairing/expirare/persistență/revocare, limitele, contractul HTTPS și separarea
autentificării în fixture-uri temporare. Aceste probe nu certifică instalarea pe
Pi, atingerea pe un telefon, routerul real, redarea sau acțiunile hardware. Turul
real necesită Pi-ul și telefonul conectate în LAN, pairing din CLI, citirea stării,
radio/volum/player/Bluetooth/setări, restart și revocare. Nu acordați criterii PASS
hardware din testele acestui gateway.
