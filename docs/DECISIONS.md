# Decizii de produs pentru implementare

Acestea completează PRODUCT și sunt deciziile implicite ale proiectului, nu funcții deja implementate.

## Navigare și acasă

Navigare stabilă: Acasă, Radio, Media, Setări. YouTube, Netflix și Spotify apar în zona Servicii din Media. Bara de stare deschide setările rapide pentru rețea, Bluetooth, ieșire audio și volum. Acasă: ceas/data în stânga, vreme în dreapta, un singur card contextual de redare sau reluare, apoi accesul rapid. Niciun carusel automat care schimbă locul butoanelor.

Setup: limbă → conectivitate (cu skip) → oraș meteo (opțional) → boxă Bluetooth (cu skip) → acasă. RO și EN rămân disponibile permanent. Inițial limba este aleasă explicit; nu se deduce din adresa IP. Tastatură tactilă proprie pentru căutări și Wi-Fi, câmpuri de parolă mascate. În lipsa unei boxe: „Conectează o boxă” / „Connect a speaker”, fără indicator fals „audio gata”.

## Meteo

Furnizor ales: [Open-Meteo](https://open-meteo.com/en/docs), geocodare prin API-ul lui. Orașul este selectat în setup; nu se colectează locație precisă implicit. Afișare: temperatură și senzație termică, condiție, minim/maxim, precipitații și prognoză 5 zile. Actualizare la 15 minute, timeout finit și backoff; datele mai vechi de 60 minute sunt marcate explicit. Cache local pentru ultima prognoză și ora actualizării. Celsius și ceas 24h implicit, independente de alegerea limbii; fusul local al dispozitivului, editabil în setări.

Instalația personală folosește API-ul necomercial, cu atribuire; comercializarea ulterioară impune revizuirea [condițiilor furnizorului](https://open-meteo.com/en/terms). Nu este necesar un cont cloud Pi Smart Hub.

## Radio și fișiere

Catalog: [Radio Browser](https://docs.radio-browser.info/), căutare după nume/țară/limbă, favorite persistente, ultima selecție memorată. Respectarea mecanismului de selecție/failover al serverelor și identificarea clientului în cereri. Catalogul și favoritele cache-uite sunt accesibile offline; redarea unui stream cere rețea. mpv gestionează fluxul real; stări idle/connecting/buffering/playing/paused/error, cu retry explicit.

Media locală: folderele Music/Videos ale utilizatorului și volume USB montate de OS, în limita unor rădăcini aprobate. Fără operații de ștergere de fișiere în hub. Formate țintă de validat: MP3, AAC/M4A, FLAC, Ogg/Vorbis, WAV, video MP4 H.264/AAC la 720p; alte formate nu sunt promise fără test. Pentru video full-screen, întoarcerea la hub trebuie să rămână tactil accesibilă. Nu se autoredă media la boot; utilizatorul poate relua.

## Servicii externe

Serviciul muzical ales: Spotify, pe site-ul oficial, cu autentificarea gestionată de serviciu. YouTube și Netflix se deschid tot în context first-party, separat de origin-ul API-ului hubului. Hubul nu colectează parolele conturilor și nu proxifică paginile lor. La plecarea spre un serviciu, redarea internă se oprește/pauzează pentru a evita două surse simultane.

Integrarea este un lansator controlat cu revenire tactilă în hub; nu pretinde că oferă un player Netflix/Spotify propriu. Totuși DoD cere redare efectivă pe acest Pi, nu doar deschiderea URL-ului. Dacă DRM sau serviciul nu funcționează, criteriul rămâne OPEN până la o decizie explicită de schimbare a cerinței. Accesul fără cont poate fi verificat acum; acceptarea redării cu cont aparține etapei aplicației.

## Setări și comportament

Teme: E-Ink (alb/negru cu accent) și Noapte. Accente limitate la trei variante coerente, nu editor de teme. Noapte poate fi manuală sau programată; screensaver ceas după 5 minute, configurabil/oprit, inhibat la video. Prima atingere trezește fără să activeze accidental controlul de dedesubt. Redarea audio poate continua în screensaver. Preferințe salvate atomic și recuperabile.

Bluetooth: buton radio on/off, scanare limitată la 20 secunde, listă fără duplicate, dispozitive salvate, prompts de asociere, conectare/deconectare/uitare și selectarea ieșirii audio. Confirmările de pairing nu sunt acceptate în tăcere. Controlul volumului reflectă ieșirea reală. Când boxa dispare, media este pusă în pauză; nu pornește automat pe o ieșire fizică necunoscută. Reconectarea unei boxe salvate restabilește disponibilitatea, dar nu pornește singură muzica.

Exit către desktop: Setări → Ieșire → confirmare. Autostart se activează numai după probe, ca serviciu/lansator al utilizatorului. Ieșirea intenționată nu este tratată ca un crash și nu trebuie să redeschidă imediat hubul. Update/rollback păstrează preferințele și favoriții.
