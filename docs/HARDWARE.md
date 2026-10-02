# Hardware de referință

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
