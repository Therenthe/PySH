# Hardware de referință

Runtime-ul instalat curent și verificările update-ului sunt în [STATUS](../STATUS.md). Un inventar vechi nu certifică acceptarea candidatului nou.

## Ultimul inventar hardware complet — 4 octombrie 2026

Inventarul următor aparține runtime-ului istoric `670c8155227b`, sursă `beab133f81aa3de7d09c4901faef64efb952c0bb`. Colectorul read-only a verificat48 hash-uri, sursa din tranzacția activată, absența unei tranzacții în curs și rădăcina SD. Inventarul este observat pe dispozitiv; nu este o presupunere din imaginea de build. [Dovadă hardware](evidence/hardware-configuration-2026-10-04.md).

| Componentă | Observat pe candidatul inventariat670c |
|---|---|
| Placă | Raspberry Pi 4 Model B Rev 1.5, revizie `c03115` |
| Memorie | Firmware `total_mem=4096`; Linux MemTotal 3,886,824 KiB |
| Arhitectură / kernel | aarch64 / `6.18.50+rpt-rpi-v8` |
| OS | Debian GNU/Linux 13 (trixie), PySH OS pe SD |
| Imagine de bază | source `3ca7e4ef4ec71f84c1510cef20099c73c079baab`, runtime inițial `c8ac9c709acb`, builder `262d4df5a9f9d4133370465399a7958a7c22cdc7` |
| Firmware încărcat | `a86983925695a7e63166327d7c002d64040ed31d`, 2026-09-14 14:49:30 |
| Ieșire video | DSI-1 conectat și activ, 800 × 480 la 60.028999 Hz, transform 180, scale 1, poziție 0,0 |
| Panou | DT `raspberrypi,7inch-dsi`/`simple-panel`, 154 × 86 mm; driver`panel-simple`/modul`panel_simple`, DSI`vc4_dsi`/modul`vc4` |
| Identificare comercială panou | Make/Model/Serial raportate null; nu se atribuie o marcă sau un model comercial neobservat |
| Touch | I²C 10-0038 `edt-ft5506`/`edt,edt-ft5506`, driver/modul`edt_ft5x06`, input`10-0038 generic ft5x06 (00)` |
| Regulator panou | I²C 10-0045 `raspberrypi,7inch-touchscreen-panel-regulator`, driver`rpi_touchscreen_attiny`, modul`rpi_panel_attiny_regulator` |
| Mapare touch | DSI-1, mouseEmulation=no, matrice identitate `1 0 0 0 1 0` |
| Runtime grafic | Chromium `1:154.0.8037.92-1~deb13u1+rpt1`, labwc `0.20.2-1~bpo13+1`, greetd `0.10.3-4`, serviciul utilizatorului `pysh.service` activ |
| Python | pachet OS `3.13.5-1`; 14 distribuții runtime corespund requirements.lock, plus pip 25.1.1 în venv |
| Stocare activă | `/dev/mmcblk0p2`, ext4 |

Captura nouă a compositorului real pe670c este 800 × 480 și afișează o stare PySH în landscape, cu text orientat corect. Maparea și driverul touch sunt configurație observată; nu echivalează cu acceptarea turului tactil. Nici inventarul, nici captura nu acceptă audio/media, stabilitatea, instalarea finală sau produsul complet. Marcajul original EXPERIMENTAL al imaginii de bază este păstrat ca proveniență; nu se confundă cu runtime-ul actual actualizat.

## Referință desktop istorică

Textul de mai jos este păstrat ca istoric și nu descrie instalarea SD actuală:


Referință istorică din 29 septembrie 2026, reconfirmată parțial live pe 2 octombrie: model, arhitectură, OS, kernel, RAM, stocare și adaptoarele active. Display-ul fizic și redarea audio rămân de verificat. Vezi [auditul live](evidence/pi-source-checkout-2026-10-02.md).

| Componentă | Observat |
| --- | --- |
| Placă | Raspberry Pi 4 Model B Rev 1.5, 4 GB |
| Arhitectură | ARM64 |
| Ecran | DSI tactil 7″, 800×480 landscape; edt-ft5506 |
| Stocare | microSD nominal 16 GB |
| OS | Raspberry Pi OS derivat Debian 13.4 trixie; referință pi-gen stage4 |
| Kernel | 6.12.75+rpt-rpi-v8 |
| Python | 3.13.5 |
| Audio | PipeWire/WirePlumber; boxa și sunetul audibil necesită validare |

Conversația ulterioară menționează detectarea unei boxe, dar registrul nu are dovadă completă de asociere și redare. Disponibilitatea curentă a boxei, alimentarea și modelul exact al panoului trebuie reconfirmate. Aplicația nu rulează la auditul din 2 octombrie; pachetul istoric 32d75c593e83 este prezent și hashurile sale sunt verificate. Adresele, parolele și inventarul privat nu intră în repository.
