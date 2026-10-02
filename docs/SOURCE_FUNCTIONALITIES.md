# Pi Smart Hub — Funcționalități

## Scop

Pi Smart Hub este o aplicație pentru Raspberry Pi cu ecran tactil, care combină un centru multimedia cu un afișaj inteligent pentru utilizarea zilnică. Interfața trebuie să ofere experiența unui dispozitiv dedicat: atractivă, fluentă și ușor de folosit prin atingere.

Acest document descrie funcționalitățile planificate în documentul de context din 9 martie 2026. Enumerarea lor nu înseamnă că sunt deja implementate.

## 1. Ecran principal

- Ceas mare, ușor de citit.
- Zonă meteo cu prezentare vizuală bogată.
- Card principal dinamic, cu rol central în compoziția ecranului.
- Carduri pentru acces rapid la funcțiile multimedia.
- Bară superioară cu informații de stare, inclusiv conectivitatea.
- Zonă pentru utilitare și comenzi rapide.
- Compoziție echilibrată, fără aglomerare și fără spații nejustificat de goale.
- Afișare în orientare landscape.

## 2. Funcții multimedia

| Funcționalitate | Comportament planificat |
| --- | --- |
| Radio | Acces la posturi radio și redare audio. |
| YouTube | Acces rapid la serviciu din interfața hubului. |
| Netflix | Acces rapid la serviciu din interfața hubului. |
| Player local | Redarea fișierelor multimedia locale. |
| Spotify sau alternativă | Acces la un serviciu de muzică; serviciul final nu este încă stabilit. |
| Volum | Controlul volumului din interfața tactilă. |
| Audio Bluetooth | Posibilitatea utilizării dispozitivelor audio Bluetooth. |

Metoda de integrare pentru YouTube, Netflix și serviciul de muzică urmează să fie stabilită și verificată. Documentul de context nu confirmă încă redarea funcțională a acestor servicii pe dispozitiv.

## 3. Ceas și vreme

- Afișarea ceasului direct pe ecranul principal.
- Afișarea informațiilor meteo într-o zonă dedicată.
- Integrarea vizuală a informațiilor în tema activă.

Sursa datelor meteo și detaliile prognozei nu sunt încă stabilite.

## 4. Conectivitate și configurare inițială

- Ecran de întâmpinare la configurarea inițială.
- Verificarea conectivității.
- Asistent de configurare pentru Wi-Fi și Ethernet.
- Afișarea stării Wi-Fi / rețelei în interfață.
- Acces la setările de conectivitate.

## 5. Setări și personalizare

- Panou de setări rapide.
- Pagină dedicată setărilor aplicației.
- Control al volumului.
- Mod de noapte.
- Screensaver.
- Selectarea temei și a accentelor vizuale.

### Teme planificate

| Temă | Direcție vizuală |
| --- | --- |
| E-Ink | Alb - negru dar cu "pete" de culoare. |
| modului de noapte | 

## 6. Experiență vizuală și tactilă

- Aspect modern și futurist, cu identitate vizuală premium.
- Efecte discrete de lumină și reflexii.
- Butoane și controale mari, potrivite pentru atingere.
- Tranziții fluide între ecrane.
- Stil unitar între ecranul principal, setări și funcțiile multimedia.
- Utilizare principală pe întregul ecran.

## 7. Pornire și ieșire

- Pornirea automată a aplicației la pornirea Raspberry Pi.
- Ecran de pornire — splash screen.
- Acces la ecranul principal după fluxul de inițializare.
- Posibilitatea de a închide aplicația și de a reveni la desktopul Raspberry Pi.

## 8. Prima versiune: Premium Shell Prototype

Prima etapă se concentrează pe interfața de bază și navigare.

Include:

- Aplicație în mod full-screen.
- Splash screen.
- Ecran de întâmpinare și verificarea conectivității.
- Asistent pentru configurarea Wi-Fi / Ethernet.
- Ecran principal premium.
- Sistem de teme.
- Panou de setări rapide.
- Pagină de setări.
- Ieșire către desktop.
- Organizare modulară pentru adăugarea funcțiilor multimedia.

Prima versiune trebuie să demonstreze că aplicația pornește, interfața și navigarea funcționează, temele pot fi schimbate, configurarea conectivității este accesibilă și utilizatorul poate reveni la desktop. Integrările multimedia complete sunt dezvoltate ulterior, iterativ.
