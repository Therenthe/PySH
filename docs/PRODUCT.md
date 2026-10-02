# Pi Smart Hub — definiția produsului

## Scop și stare

Pi Smart Hub este un dispozitiv de uz zilnic pentru Raspberry Pi 4 (4 GB) și ecran tactil DSI de 7 inchi, 800 × 480, în orientare landscape. Reunește ceasul, vremea, comenzile uzuale și accesul la audio/video într-o interfață dedicată, fluentă și ușor de folosit prin atingere. Produsul final trebuie să fie complet, configurabil și recuperabil în utilizare reală; un shell demonstrativ nu îndeplinește definiția.

Acesta este contractul de produs pentru planificare și evaluare. Nu afirmă că funcțiile sunt implementate sau că serviciile externe au fost validate pe Pi. Implementarea locală a fost importată în structura PySH. Starea verificată și restanțele sunt în STATUS.md; această specificație nu certifică funcțiile implementate.

## Utilizator și experiență

- Utilizatorul poate înțelege starea hubului dintr-o privire și poate ajunge la funcțiile principale prin atingeri deliberate, fără precizie de mouse.
- Ecranul principal pune ceasul, vremea și un card principal dinamic în prim-plan; starea rețelei și a redării rămâne vizibilă. Comenzile secundare sunt accesibile fără a aglomera ecranul.
- Toate ecranele, dialogurile, erorile și configurările sunt disponibile în română și engleză. Limba poate fi schimbată din setări și alegerea persistă după repornire.
- Interfața este proiectată întâi pentru 800 × 480, landscape și atingere. Ținta tactilă minimă este 48 × 48 px, cu spațiere între acțiuni riscante. Textul, dialogurile și tastatura virtuală nu se taie la rezoluția țintă.
- Mișcarea și efectele vizuale sunt discrete și nu ascund starea sau comenzile. Contrastul și lizibilitatea au prioritate față de ornament.

## Zone și capabilități

### Acasă și navigare

- Ceas mare, dată localizată, vreme curentă și prognoză utilă, cu oră de actualizare și stare clară pentru date indisponibile sau expirate.
- Card principal dinamic (de exemplu, redarea activă, radio sau un mesaj de stare) și scurtături configurabile spre funcțiile folosite frecvent.
- Bară de stare pentru rețea, Bluetooth și audio; navigare coerentă către Acasă, media și setări.
- Aspect echilibrat, fără suprapuneri, zone moarte disproporționate sau text care cere scroll accidental pe panourile de bază.

### Media și audio

- Radio: listă de posturi configurabilă, redare/opriere, metadate când fluxul le oferă, stări de încărcare și erori inteligibile.
- Player local: navigare în directoarele media aprobate, liste și controale play/pauză, anterior/următor, căutare dacă formatul o permite, progres și volum. Formatele acceptate se publică după validare pe Pi.
- YouTube și Netflix: acces din hub prin integrare permisă și funcțională pe dispozitiv. Dacă nu există o cale suportată care să redea conținutul în condițiile serviciului, produsul trebuie să explice limita și să ofere deschiderea în browserul/sistemul compatibil disponibil; butonul nu poate pretinde că redarea integrată funcționează.
- Muzică: se alege un serviciu după verificarea eligibilității SDK/API, autentificării, licențelor și performanței pe platforma țintă. „Spotify sau alternativă” nu este un angajament că SDK-ul Spotify va fi disponibil.
- Volum accesibil din interfață, cu feedback vizual și integrare verificată cu ieșirea audio activă.
- Bluetooth în aplicație: scanare explicit pornită de utilizator, dispozitive din apropiere, asociere, conectare/deconectare, dispozitiv curent, uitare dispozitiv și mesaje clare pentru refuz, timeout sau indisponibilitate. Aplicația nu se asociază automat cu dispozitive necunoscute. Testul final de compatibilitate audio cere o boxă Bluetooth reală; disponibilitatea actuală a boxei trebuie reconfirmată înaintea testului.

### Configurare și setări

- Prima pornire: întâmpinare, selecția limbii, verificarea rețelei și ghid Wi-Fi/Ethernet cu progres, confirmarea rezultatului și cale de revenire. Configurarea trebuie să poată fi reluată ulterior.
- Setări rapide și pagină dedicată pentru limbă, rețea, audio, teme, mod de noapte, screensaver, sursa/vizualizarea vremii și comportament la pornire.
- Teme: temă întunecată pentru utilizare nocturnă și temă vizuală inspirată de E-Ink pe LCD (paletă predominant alb-negru cu accente limitate; ecranul rămâne LCD). Temele schimbă o paletă și tokenuri comune, nu fragmentează comportamentul UI.
- Preferințele supraviețuiesc repornirii. Datele sensibile de rețea și credențialele de servicii nu sunt afișate în jurnale sau în interfață după salvare.
- În runtime-ul cu desktop, utilizatorul poate părăsi aplicația și reveni la desktop printr-o acțiune vizibilă, protejată de atingere accidentală. În sesiunea dedicată PySH OS, aceeași zonă oferă explicit „Mod de service”: oprește redarea, păstrează diagnosticul accesibil și permite revenirea în hub fără pierderea setărilor. Recuperarea administrativă se validează separat înainte de instalarea OS (ADR-0004 și ADR-0007).

### Pornire, stare și recuperare

- Lansare automată în ecran complet după pornirea sesiunii grafice, splash scurt și trecere controlată la inițializare/acasa.
- O funcție care nu are rețea, permisiuni sau serviciu disponibil explică problema și lasă navigarea și setările accesibile.
- Revenirea aplicației după închiderea neașteptată nu cere ștergerea setărilor. Jurnalele de diagnostic sunt rotite și nu conțin secrete.

## Limite externe și decizii încă deschise

Aceste servicii depind de terți și de mediul real. Documentația oficială YouTube cere respectarea playerului, brandingului, reclamelor și cerințelor API; un player modificat sau ocolirea limitărilor nu este o soluție acceptabilă ([cerințe player YouTube](https://developers.google.com/youtube/terms/required-minimum-functionality), [politici YouTube](https://developers.google.com/youtube/terms/developer-policies-guide)). Netflix precizează că suportul său nu poate depana dispozitive Linux; compatibilitatea exactă cu Pi/browser/DRM trebuie demonstrată pe ținta aleasă, nu presupusă ([cerințe Netflix](https://help.netflix.com/en/node/30081)). Spotify oferă SDK-uri și condiții specifice pentru hardware comercial, iar Web Playback SDK are propriile condiții; eligibilitatea și aprobările trebuie stabilite înainte de a promite integrarea ([hardware Spotify](https://developer.spotify.com/documentation/commercial-hardware), [Web Playback SDK](https://developer.spotify.com/documentation/web-playback-sdk)).

Prin urmare, pentru fiecare serviciu se consemnează soluția permisă, limitările, dependențele de cont/rețea, comportamentul la indisponibilitate și testul pe dispozitiv. Nu se descarcă sau extrage fluxuri protejate, nu se elimină reclamele și nu se prezintă un link extern ca redare integrată.

Implementarea existentă folosește Open-Meteo; decizia și intervalele sunt descrise în DECISIONS.md. Condițiile serviciului se reverifică înainte de release. Starea de rețea poate fi folosită local fără cloud. După auditul dispozitivului din 29 septembrie, arhitectura aleasă este consemnată în [ENVIRONMENT.md](ENVIRONMENT.md): Chromium existent, frontend static React/TypeScript, serviciu Python local, NetworkManager/BlueZ/PipeWire existente și mpv. Probele de mediu nu înlocuiesc acceptarea funcțiilor reale.

## În afara definiției

- Controlul casei inteligente, vocea, cameră/microfon, utilizatori multipli, administrare la distanță și sincronizare cloud.
- Garanția redării unui serviciu terț fără o metodă de acces permisă și verificată pe dispozitivul exact.
- Suport pentru orice codecuri/boxe, orice ecran sau orientare; domeniul hardware de referință este Pi 4 4 GB și DSI 800 × 480.

## Arhitectură și persistență

Preferințele utilizatorului și listele locale rămân disponibile fără internet; sursele externe au adaptoare separate; textul UI este separat de logică pentru EN/RO; setările sunt salvate atomic și fără secrete în loguri. Arhitectura folosește serviciile deja prezente pe Pi; compatibilitatea fiecărui flux se dovedește în bucla DoD, nu se deduce din alegerea frameworkului.
