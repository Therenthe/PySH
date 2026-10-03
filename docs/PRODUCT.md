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
- Microanimațiile explică acțiunile și tranzițiile: atingere, schimbarea paginii, încărcare, asociere și schimbarea redării. Respectă reducerea mișcării și bugetele de performanță pe Pi.

## Zone și capabilități

### Acasă și navigare

- Un singur ceas și o singură dată în bara de sus, fără salut/profil fictiv. Ambient Canvas urmărește condiția reală și zi/noapte; datele expirate folosesc o scenă neutră. Prognoza cuprinde cinci coloane vizibile cu icoana condiției și maximă/minimă, fără scroll. Umiditatea, presiunea, vântul și UV provin din date reale; valorile absente rămân indisponibile.
- Card principal dinamic (de exemplu, redarea activă, radio sau un mesaj de stare) și scurtături configurabile spre funcțiile folosite frecvent.
- Bară de stare pentru rețea, Bluetooth și audio; navigare coerentă către Acasă, media și setări.
- Aspect echilibrat, fără suprapuneri, zone moarte disproporționate sau text care cere scroll accidental pe panourile de bază.
- Navigarea laterală se poate retrage și redeschide printr-o comandă tactilă permanent accesibilă; opțional se retrage după schimbarea paginii. Fundalul rămâne vizibil prin panouri discrete, fără a compromite lizibilitatea. Luna reflectă faza calculată pentru moment; efectele de stele sunt decorative și respectă reducerea mișcării.
- Barele de scroll nu sunt vizibile în nicio zonă PySH; conținutul derulabil rămâne accesibil prin atingere. Aceasta include liste, setări, dialoguri și serviciile externe gestionate de hub.
- Acasă prezintă o singură zonă principală pentru redarea curentă, fără repetarea acelorași informații într-un card și o bară. La radio, numele postului rămâne clar, separat de artist/melodie și stările de flux.
- Pictograma meteo corespunde codului condiției reale și etichetei localizate: senin folosește simbolul de soare, iar stările fără date au un simbol distinct.

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
- Vremea se actualizează automat, cu reluare după indisponibilitate; utilizatorul nu face refresh manual. Căutarea locației include București și sectoarele1–6, fără a confunda orașul cu Bucureștii Noi. Filtrele radio acceptă diferențe de majuscule/minuscule și aliasurile localizate suportate.
- Screensaverul păstrează controale tactile pentru redare/pauză și anterior/următor când radioul este activ; la radio acestea aleg posturile, iar la fișiere locale piesele. Sunt disponibile stiluri de vizualizare audio configurabile; vizualizarea de nivel/undă trebuie să reflecte semnalul real, iar o animație decorativă să fie prezentată explicit astfel.
- Teme: temă întunecată pentru utilizare nocturnă și temă vizuală inspirată de E-Ink pe LCD (paletă predominant alb-negru cu accente limitate; ecranul rămâne LCD). Temele schimbă o paletă și tokenuri comune, nu fragmentează comportamentul UI.
- Preferințele supraviețuiesc repornirii. Datele sensibile de rețea și credențialele de servicii nu sunt afișate în jurnale sau în interfață după salvare.
- Modul de noapte poate urma apusul/răsăritul locației meteo, un program orar sau selecția manuală. Lipsa orelor solare pentru ziua curentă este explicată și păstrează tema aleasă. Screensaverul poate afișa ceas/redare cu semnal între ele sau numai vizualizatorul ales pe întregul ecran; atingerea dezvăluie temporar comenzi și revenire. Listele de setări rămân deschise peste actualizările periodice ale stării și ceasului.
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

Pe Acasă, comenzile se retrag pentru a lăsa scena ambientală vizibilă. Controlul de navigare urmează marginea barei și ajunge la4px de marginea ecranului când bara este închisă. După15secunde fără folosirea cardului, vremea ascunde coloana cu vânt/umiditate/presiune/UV și ajunge la jumătate din lățime; prognoza păstrează prima zi și se extinde/restrânge la atingere. Cu vizualizarea activată, cardul de redare se retrage în vizualizatorul mărit; atingerea vizualizatorului readuce cardul, iar reatingerea îl retrage. Fiecare card are temporizator independent. Pictograma postului folosește artwork-ul disponibil din catalog, cu monogramă de rezervă când lipsește. Scena combină luna în faza aproximativă cu norii pentru condiții nocturne parțial senine; precipitațiile discrete trec peste silueta orașului înaltă de170px. Datele meteo lipsă/expirate nu declanșează efecte prezentate ca actuale. Mișcarea redusă dezactivează animațiile.

Preferințele utilizatorului și listele locale rămân disponibile fără internet; sursele externe au adaptoare separate; textul UI este separat de logică pentru EN/RO; setările sunt salvate atomic și fără secrete în loguri. Arhitectura folosește serviciile deja prezente pe Pi; compatibilitatea fiecărui flux se dovedește în bucla DoD, nu se deduce din alegerea frameworkului.
## Personalizarea scenei Acasă

După 10 secunde fără atingere sau tastare, bara de sus devine transparentă; ceasul și controlul meniului rămân vizibile și accesibile. O interacțiune readuce imediat fundalul solid. Textul se adaptează scenei nocturne și temei; animațiile respectă mișcarea redusă.

Setări → Acasă permite alegerea cardurilor Vreme, Prognoză și Redare. „Aranjează Acasă” deschide un mod explicit în care mânerele tactile mută separat fiecare card și vizualizatorul, fără a declanșa comenzile lor. Gata salvează pozițiile proporțional cu spațiul disponibil; Anulează păstrează aranjarea salvată, iar Resetează revine la pozițiile implicite după salvare. Pozițiile sunt limitate la ecran când navigarea sau dimensiunile se schimbă. Utilizatorul poate suprapune deliberat carduri; nu există rearanjare automată a alegerilor sale.

Vizualizatorul are dimensiuni Compact, Echilibrat și Mare, plus stilurile Undă, Bare, Orbită, Panglică, Oglindă și Inele. Stilurile folosesc semnalul real de ieșire, fără microfon; cu mișcare redusă arată nivelul numeric. Scenele nocturne includ ferestre luminate, nori cu contururi distincte și stele căzătoare decorative în grupuri cu intervale și poziții variabile. Aceste efecte nu sunt previziuni astronomice.

În modul Aranjează Acasă, coordonatele sunt raportate la întreaga scenă, nu la rândurile aspectului implicit. Lista „Selectează cardul” aduce în față un card inclusiv când este acoperit; stratul de suprapunere se salvează împreună cu poziția. Limitele păstrează cardul integral pe suprafața Acasă.
