# Android App Control în LAN

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
Pachetele de sistem `openssl` și `avahi-daemon` trebuie să fie instalate.
Gateway-ul folosește `dbus-next` deja fixat în requirements.lock. Supervisorul
alege o interfață IPv4 privată activă, preferând ruta implicită, și publică
`_pysh-control._tcp` cu hubId persistent, protocol=2 și name=PySH. Se leagă de
o singură adresă explicită, fără wildcard sau listener public. La schimbarea
adresei închide listenerul vechi și îl recreează, păstrând certificatul/tokenurile.
Clientul Android acceptă IPv4 privat și portul8766.

```sh
cd /opt/pysh/current
/opt/pysh/venv/bin/python -m services.remote init --host 192.168.1.50
mkdir -p ~/.config/systemd/user
install -m 0644 services/remote/pysh-remote.service ~/.config/systemd/user/pysh-remote.service
systemctl --user daemon-reload
systemctl --user enable --now pysh-remote.service
systemctl --user status pysh-remote.service --no-pager
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

Pe PySH deschideți **Setări → Android App Control** și activați serviciul.
Aplicația caută automat în aceeași rețea Wi-Fi. Alegeți hubul și confirmați
**Da** pe ecranul PySH pentru numele telefonului; **Nu** refuză cererea.
Nu introduceți adresă, certificat sau cod. Cererea expiră după două minute.
Telefoanele asociate se pot elimina din același meniu. Dezactivarea închide
portul LAN; unitatea locală rămâne disponibilă pentru reactivare din meniu.

Identitatea publică inițială este TOFU, fără token sau comenzi. Telefonul trimite
o cheie RSA3072 temporară; aprobarea locală livrează tokenul criptat OAEP SHA256.
Numele telefonului este declarat de client. Acest flux nu oferă verificare
independentă împotriva unui atacator activ la prima asociere. După asociere,
toate citirile/comenzile verifică pinul certificatului DER și identitatea hubului.
O identitate/cheie înlocuită cere asociere nouă. CLI `pair` rămâne compatibil
pentru administratori; nu este fluxul normal al aplicației.

Nu configurați port forwarding, DMZ, reverse proxy public sau tunel internet.
Filtrarea adreselor private nu poate detecta un router care rescrie traficul WAN
în IP privat: izolarea de internet cere și absența acestor configurări în router.
Firewall-ul LAN poate limita suplimentar portul 8766 la subrețeaua telefonului.

## Contract pentru client

| Cerere | Răspuns |
|---|---|
| `GET /remote/health` fără autentificare | Identitatea serviciului |
| `GET /remote/identity` | hubId, name, protocol, enabled, certificateSha256 |
| `POST /remote/pair/request {name,publicKey}` | requestId, requestSecret, expiresIn |
| `POST /remote/pair/status {requestId,requestSecret}` | pending/denied/expired/approved; encryptedResult după aprobare |
| `POST /remote/pair/cancel {requestId,requestSecret}` | Anulează cererea și asocierea emisă pentru ea |
| `POST /remote/pair`, JSON `{"code":"12345678","name":"Telefon"}` | `{"token":"…","deviceId":"UUID","name":"Telefon"}` |
| `POST /remote/revoke-self`, bearer autentificat, JSON `{}` sau corp gol | `{"revoked":true}`; următoarea cerere cu tokenul respectiv primește 401 |
| API permis pe `/api/*` | JSON și codurile de stare ale API-ului PySH |

Telefonul trimite `Authorization: Bearer <token>` pentru fiecare comandă și citire.
Tokenul se emite o singură dată și se păstrează în spațiul privat protejat al
aplicației. Gateway-ul stochează numai hash-ul lui, suportă până la 16 telefoane,
și nu exportă tokenul sesiunii locale. Acțiunea de revocare self poate retrage numai
tokenul telefonului apelant, fără un ID de telefon trimis de client. Dacă telefonul
este offline când utilizatorul îl elimină din aplicație, revocarea se poate face din
meniul local PySH sau CLI pe Pi. `/api/session`, `/api/media/file`, paginile
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
supervisorul urmărește interfața și Android regăsește hubul prin mDNS. Recunoașterea
cere hubId și pin identice celor salvate; nu acceptă automat un certificat nou.
Izolarea clienților sau blocarea multicastului poate împiedica descoperirea.
Pentru înlocuirea certificatului revocați telefoanele și asociați-le din nou.
Protejați datele private în backup separat; actualizările păstrează identitatea.

## Verificare și limite

`python -m pytest tests/test_remote_gateway.py -q` verifică adresele private,
pairing/expirare/persistență/revocare, limitele, contractul HTTPS și separarea
autentificării în fixture-uri temporare. Aceste probe nu certifică instalarea pe
Pi, atingerea pe un telefon, routerul real, redarea sau acțiunile hardware. Turul
real necesită Pi-ul și telefonul conectate în LAN, aprobarea pe ecranul local, citirea stării,
radio/volum/player/Bluetooth/setări, restart și revocare. Nu acordați criterii PASS
hardware din testele acestui gateway.
# Display, standby and active companions (Android 0.1.2)

The phone now shows the current station logo using authenticated
`GET /api/radio/artwork?station=current` (or a known station UUID). PNG/JPEG/GIF/ICO/
WebP responses are limited to256KiB; Android decodes at most512px. The Pi fetches
only known public station metadata; arbitrary URL and private-network fetches
are refused. Up to three redirects each undergo the same DNS validation; known
official homepages provide icon fallback for empty/obsolete favicon metadata. The phone never requests an internet logo URL.

`/api/state` includes `power` and `remote:{connected,count}`. An authenticated
state read renews presence. `POST /remote/heartbeat` renews and `DELETE` withdraws
presence; background/crashed clients expire within15seconds. This shows active
companions rather than saved pairing identities.

`GET /api/power` reports standby, actual/desired brightness, countdown and daily
schedule. `POST /api/power {standby:true|false}` controls recoverable software
standby. `POST /api/power/timer {minutes:0..720}` sets a countdown;0 cancels it.
Preference PATCH keys are `screenBrightness` (1..100), `dailyStandbyEnabled`
and `dailyStandbyTime` (HH:mm). Daily time uses the hub timezone; a manual wake
after that day's event stays awake until a subsequent event or user command.

## Updating an existing independent gateway

Package the five allowlisted source/unit files, including discovery.py. Transfer
the verified archive plus `scripts/update-remote-sidecar.py` to an administrative
private directory. On the appliance:

```sh
sudo python3 update-remote-sidecar.py gateway.tar.gz --sha256 <verified-sha256>
```

This checks old source integrity, new exact inventory/checksum and the unchanged
unit, stages root-owned code, changes the sidecar pointer and checks its TLS
health. It restores the old pointer if startup fails. Private pairing, certificate
and host/port configuration are preserved; previous code remains retained.

An old pre-standby backend rejects the three new preference keys. Before a
voluntary rollback to such a release, stop the hub and make a separate private
copy of current preferences; restore a reviewed copy that removes only these
three keys, preserving all other choices. Do not let an old loader reset to
defaults. Immediate activation recovery uses the independently verified
pre-deployment backup; that backup does not include later user edits.

The local-only `/api/android-control` routes manage enablement, pending requests
and saved devices. They are not forwarded by the gateway. `tests/test_android_control.py`
covers approval/denial/expiry, encrypted delivery, discovery lifecycle and updater
compatibility. See [decision0012](adr/0012-android-discovery-approval.md).
