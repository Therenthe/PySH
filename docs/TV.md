# TV în PySH

Deschide **Media → Servicii → TV**. TV rulează în interfața PySH; celelalte
servicii Media își păstrează site-urile oficiale.

## Canale și favorite

Lista pornește cu favoritele solicitate: PRO TV HD (1080p), Antena 1 (Romania),
Bellator MMA, ESPN 2 (United States) HD (720p), ESPN (United States) HD (720p),
NBA TV (720p), NBC Sports NOW (1080p) și PokerGo. Acestea sunt denumirile din
catalog, nu o măsurare sau garanție a rezoluției efective.

Atinge **Favorite** pentru toate canalele, apoi lupa pentru căutare. Căutarea
ignoră majusculele și diacriticele. Selectarea unui rând arată ghidul; **Privește
live** pornește imaginea pe întregul ecran. Steaua adaugă/elimină canalul din
favorite. Un favorit care lipsește din liste este marcat explicit.

TV are o singură bară pentru Canale, Înregistrări și Surse. Triunghiul de lângă
numele canalului pornește vizionarea, cercul pregătește înregistrarea imediată,
iar calendarul de lângă o emisiune programează înregistrarea ei. Atinge titlul
emisiunii sau „Detalii” pentru descriere; o nouă atingere o restrânge. Ghidul
păstrează loc pentru emisiunea curentă și următoarea, fără bara radioului.

**Digi Sport 1 · Player oficial** din lista TV deschide pagina Digi în browserul
protejat al PySH. Accesul este verificat de Digi, inclusiv rețeaua folosită;
eventualul dialog de confidențialitate aparține site-ului. Trage din partea de
sus pentru comenzile PySH; **Canale** revine direct la lista TV. Acesta este playerul oficial cu Widevine,
nu un flux M3U: comenzile de înregistrare IPTV nu se aplică acestei intrări.

Controalele video se retrag după câteva secunde; o atingere le readuce. **Înapoi
la TV** oprește vizionarea și confirmă închiderea sesiunii. Înregistrările
independente continuă. HLS este suportat, inclusiv AES-128 standard. Fluxurile
MPEG-TS directe necriptate sunt transformate local în HLS, fără recodare sau
schimbarea rezoluției; pornirea poate dura câteva secunde. Decodarea depinde
în continuare de codecurile Chromium instalate. DRM, SAMPLE-AES și DASH nu
sunt decodate de acest player.
La indisponibilitatea canalului, folosește Reîncearcă sau Înapoi.

În fullscreen, atingerea imaginii arată comenzile: anterior, redare/pauză,
următor și oprire. Schimbarea canalului folosește ordinea listei filtrate,
închide sesiunea precedentă și păstrează înregistrările independente.
Sliderul de volum și butonul de sunet modifică aceeași ieșire audio ca restul
PySH. Lipsa ieșirii este afișată explicit; nu împiedică imaginea TV.
Comenzile rămân vizibile în timpul reglării și al navigării cu tastatura.
Repausul automat nu întrerupe vizionarea. Un flux fără progres video timp de
aproximativ25secunde primește mesaj de recuperare, nu conectare fără sfârșit;
pauza intenționată nu este tratată ca blocaj.

## Ghid TV și surse

Ghidul afișează emisiunea curentă, programele următoare, orele și descrierile
furnizate. Orele folosesc fusul ales în Setări → Limbă și locație, inclusiv
schimbarea orei de vară. Asocierea preferă ID-ul XMLTV; numele normalizat este
folosit numai când asocierea este neambiguă.

În **Surse**, M3U și XMLTV au liste separate. **Adaugă sursă** acceptă un URL
public HTTP/HTTPS; XMLTV poate fi XML simplu sau gzip. **Actualizează** descarcă
din nou tipul ales, iar butonul din Ghid actualizează programul TV. Listele se
actualizează automat la 24 de ore, ghidul la 6 ore și ambele după pornirea
serviciului. Datele salvate rămân disponibile când sursa nu răspunde, cu stare
explicită; nu sunt transformate în informații actuale inventate.

Sursele inițiale:

- [Free-TV România](https://raw.githubusercontent.com/Free-TV/IPTV/master/playlists/playlist_romania.m3u8)
- [Free-TV complet](https://raw.githubusercontent.com/Free-TV/IPTV/master/playlist.m3u8)
- [iptv-org România](https://iptv-org.github.io/iptv/countries/ro.m3u)
- [iptv-org complet](https://iptv-org.github.io/iptv/index.m3u)
- XMLTV principal: [Open EPG România](https://www.open-epg.com/files/romania1.xml.gz)

PRO TV și Antena 1 primesc completări din [programul oficial PRO TV](https://www.protv.ro/program)
și [programul oficial Antena 1](https://a1.ro/program-tv/), numai când structura,
data și orele pot fi validate. Dacă site-ul se schimbă sau refuză accesul,
XMLTV rămâne disponibil; nu se ghicește programul lipsă.

## Înregistrări

În ghid, **Programează** deschide intervalul emisiunii. Poți ajusta începutul și
sfârșitul cu un minut și adăuga 0–60 de minute înainte/după. **Înregistrează**
de pe canal pregătește o înregistrare imediată, inițial de o oră; durata poate fi
ajustată înainte de salvare. Un interval poate avea cel mult 24 de ore.

Fila **Înregistrări** arată starea reală a serviciului și programărilor:

- **Modifică / Anulează** pentru o programare care nu a pornit.
- **Oprește și salvează** pentru înregistrarea activă.
- **Redă** pentru un fișier salvat și disponibil; redarea folosește biblioteca
  locală și codecurile Chromium instalate.
- **Șterge**, apoi **Șterge definitiv**, pentru fișierul local; **Păstrează**
  renunță la ștergere. Fișierele în curs de înregistrare sunt protejate și din
  biblioteca media generală.

Fișierele MKV sunt în `~/Videos/MediaTool`, cu identificatori unici care previn
suprascrierea. Înregistrarea copiază pistele fără recodare. Pot rula cel mult
două simultan; suprapunerile suplimentare sunt refuzate. Pornirea cere cel puțin
256 MiB liberi; sub 128 MiB înregistrarea este oprită controlat.

Serviciul `pysh-recorder.service` continuă independent de fereastra și serviciul
interfeței. Raspberry trebuie să rămână **pornit, nesuspendat, online și cu
spațiu liber**. Închiderea interfeței nu oprește înregistrarea; oprirea
dispozitivului o întrerupe. După o întrerupere, starea și eventualul fișier
parțial sunt păstrate. Emisiunile pierdute cât dispozitivul era oprit sunt
marcate ca ratate. Programările folosesc intervalul salvat; modificările de
ultim moment ale postului pot necesita ajustare manuală.

Disponibilitatea, calitatea și permisiunea de utilizare depind de sursele
canalelor. Un canal prezent într-o listă nu dovedește că fluxul este accesibil
din rețeaua curentă sau că are ghid complet.

## Orange TV Go

Deschide **Media → Servicii → Orange TV Go**. PySH deschide site-ul oficial
Orange în browserul de servicii, cu profilul existent. Alege pictograma de cont
din dreapta sus, apoi **Sign in / Autentifică-te**. Completează datele direct pe
ecranul Raspberry; parola nu se trimite în chat sau către PySH.

Formularul oficial poate folosi pagina Orange `/accounts/login-user`.
Meniul PySH de sus oferă tastatura și revenirea în Media și pe acea pagină.
Canalele disponibile și drepturile de vizionare depind de contul și abonamentul
Orange. Acest acces web nu instalează un APK Android și nu înlocuiește contul.
