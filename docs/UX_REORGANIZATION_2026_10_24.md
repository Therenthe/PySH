# Reorganizarea UX — 24 octombrie 2026

## Scop și probe

Utilizatorul evaluează experiența la 5/10: opțiuni greu de găsit și împărțite
între meniuri fără o legătură clară. Scopul acestui lot este reducerea căutării,
a pașilor inutili și a ambiguității, păstrând funcțiile și preferințele existente.
Un scor declarat de agent nu înlocuiește probele sau aprecierea utilizatorului.

| ID | Livrabil | Stare |
|---|---|---|
| UX-IA-01 | Inventarul complet și două audituri independente, EN/RO × teme, 800×480 | DONE în domeniu: inventar complet și două audituri independente; dovezi în raport |
| UX-IA-02 | Șase categorii orientate către sarcină; fiecare opțiune are o destinație canonică | DONE în domeniul probelor documentate |
| UX-IA-03 | Intrări corect denumite, întoarcere la pagina de origine, legături între asociere și ieșirea audio | DONE în domeniul probelor documentate |
| UX-IA-04 | Recuperare Radio: lipsă boxă și filtre fără rezultate; standby descris corect | DONE în domeniul probelor documentate |
| UX-IA-05 | Reaudit, corecții și regresie pe candidați identificați | DONE în domeniu; eșecurile și retestările fiecărei iterații sunt păstrate |
| UX-IA-06 | Publicare și instalare verificată, preferințe păstrate, tur nativ | DONE: dd9a018bf755 / sursă 38b07da; 107 fișiere, 29 preferințe, 84 capturi native |

## Destinațiile opțiunilor

| Categorie | Secțiuni și conținut |
|---|---|
| Acasă | Carduri și navigare: vizibilitate, aranjare, scurtături, retragerea meniului. Vizualizator: stil și dimensiune comune Acasă/Radio/repaus. Efecte ambientale: aeronave și praf lunar decorative. |
| Ecran și repaus | Temă: paletă, accent, mod manual/solar/programat. Ecran de repaus: întârziere, conținut, previzualizare. Luminozitate și standby: ecran, temporizator, program zilnic. |
| Sunet și boxe | Volum și ieșire; Bluetooth. Asocierea și alegerea boxei au legături reciproce. |
| Internet și telefon | Wi-Fi și cablu; control autorizat de pe telefon. |
| Limbă și locație | Limbă și oră; locație meteo, unitate și proveniența datelor. |
| Sistem | Starea serviciilor, diagnostic, reluarea configurării, mod de service/ieșire confirmată. |

Comenzile rapide sunt explicit separate de pagina completă de Setări. Roata
deschide Setările, indicatorul Rețea deschide Rețeaua, iar Înapoi păstrează pagina
de origine. Setările se salvează automat prin operațiile existente, cu erorile
și protecțiile lor. Nu se introduc preferințe noi și nu se migrează datele.

## Charter de acceptare a lotului

Verificăm găsirea fiecărei opțiuni, absența duplicatelor și a acțiunilor false,
schimbarea/anularea/eroarea, revenirea și păstrarea focusului peste polling.
Fiecare grupă trebuie să fie accesibilă la rezoluția țintă fără derularea meniului
de categorii. Opțiunile lungi rămân accesibile prin derulare tactilă fără bare.
Testele destructive, rețea/audio simulate rămân în fixture; pe Pi păstrăm datele,
profilurile și conexiunea administrativă. Turul automat nu dovedește atingerea
fizică, auzul, DRM sau stabilitatea pe termen lung.

[Dovezi, iterații și limite](evidence/ux-reorganization-2026-10-24.md). Toate cele
30 de criterii complete de produs rămân OPEN; acest lot nu certifică nota 10/10.
