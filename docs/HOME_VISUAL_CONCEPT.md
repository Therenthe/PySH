# Conceptul vizual Home PySH

## Scop și format

Home este o dioramă ambientală interactivă pentru un dispozitiv de uz zilnic,
cu ecran tactil LCD de 7 inci, 800 × 480, în orientare landscape. Informațiile și
comenzile trebuie să fie ușor de găsit când sunt necesare, apoi să lase scena
vizibilă. Ecranul de bază nu trebuie să necesite derulare sau mouse.

## Direcția artistică

Referința cerută este Gotham din Batman: The Animated Series, interpretat prin
Dark Deco: arhitectură monumentală, volume unghiulare, retrageri asimetrice,
umbre ample și accente industriale. Paleta folosește cărbune, gri-albăstrui,
cărămidă închisă și ferestre cu lumină caldă. Identitatea clădirilor vine din
volume și siluete distincte, nu din repetarea aceleiași fațade cu alte ferestre.
Modelele sunt originale; scenele cu supereroi au fost abandonate.

Orașul ocupă partea inferioară, într-un strat de 208 px la rezoluția nativă.
Cerul oferă spațiu negativ și mișcare discretă. Lumina și atmosfera trebuie să
creeze profunzime fără să ascundă funcțiile sau să transforme scena într-un
fundal fotorealist încărcat. Referința de stil nu presupune copierea unei imagini
din serial și nici o schimbare arbitrară a vremii reale.

## Informație și compoziție

Ceasul este reperul principal din bara de sus. Data, conexiunea activă și accesul
la comenzi sunt secundare. Bara poate deveni transparentă după inactivitate,
iar navigația din stânga este retractabilă.

Cardul meteo prezintă localitatea, temperatura și simbolul condiției reale;
detaliile despre vânt, umiditate și presiune apar la extindere. Prognoza se
prezintă orizontal, cu pictograme și temperaturi pentru cinci zile, și se poate
restrânge la o zi. Cardurile folosesc suprafețe discrete, fără rame dominante.
Transparența nu trebuie să compromită citirea textului.

Redarea are un singur context coerent: numele postului sau fișierului, metadate
și comenzi tactile. Pe Home, modul Undă al radioului îmbracă fațada clădirii radio
cu neon. Atingerea clădirii readuce playerul. Celelalte stiluri păstrează
vizualizarea separată și dimensiunea aleasă de utilizator.

## Scena ca indicator al dispozitivului

Bluetooth are un semn 3D montat pe o clădire; emisia animată diferențiază
conectarea de simpla alimentare. Clădirea Wi-Fi reflectă starea conexiunii și
ruta activă. Antena radio emite în timpul redării, iar neonul fațadei urmărește
semnalul audio măsurat și se stinge la pauză, mute sau lipsă de semnal.

Luminile funcționale sunt deasupra vălului atmosferic din prim-plan, pentru a
rămâne lizibile în ceață. Sunt în continuare parte a scenei, sub cardurile
interactive. O poziție aleasă de utilizator pentru un card le poate acoperi;
această relație trebuie analizată ca problemă de descoperire și compoziție.

## Ritmul interacțiunii

Utilizatorul poate selecta cardurile vizibile și le poate muta. Aranjarea se
face cu ele restrânse. Cardurile ancorate la dreapta sau jos păstrează marginea
aleasă și se extind spre spațiul disponibil. Dimensiunea vizualizatorului se
alege separat; montajul pe clădire are dimensiunea arhitecturii.

După inactivitate, cardurile se restrâng, apoi Home păstrează scena, ceasul și
vizualizarea audio. Prima atingere readuce comenzile, fără să execute accidental
o acțiune. Tranzițiile trebuie să explice schimbarea de stare; pulsațiile nu
trebuie să simuleze o conectare sau o redare care nu există.

## Cer, vreme și teme

Soarele și luna urmăresc ora și locația; faza lunară este calculată. Ziua nu
afișează luna, iar noaptea nu afișează soarele. Norii, precipitațiile și ceața
reflectă datele meteo. Pe cerul nocturn eligibil există 170 de stele rare și meteori
decorativi cu traiectorii și intervale variate. Ceața densă și norii pot elimina
eligibilitatea cerului senin. Previzualizările cu vreme controlată se etichetează.

Temele E-Ink și Noapte folosesc suprafețe și contraste adaptate; E-Ink este o
temă pe LCD. Comutarea solară folosește apusul și răsăritul. Alegerea manuală a
unei teme întunecate poate întuneca o scenă diurnă. Mișcarea redusă păstrează
indicii statice de stare și oprește efectele decorative incompatibile.

## Criterii pentru analiza specialistului

- Ierarhie clară între informație, comenzi și decor, fără duplicări inutile.
- Identitate Dark Deco coerentă și clădiri distincte la dimensiunea fizică.
- Descoperirea navigației, playerului și cardurilor retractate prin atingere.
- Lizibilitate pe fundalul efectiv compus, în ambele teme și în atmosferă densă.
- Comenzi de minimum 48 × 48 px; țintă tipografică 16 px corp și 14 px text secundar.
- Formulare EN/RO, fără hover obligatoriu, clipping sau scroll accidental.
- Echilibru între personalizare, suprapuneri și păstrarea reperelor funcționale.
- Animații cu sens, fără orbire, zgomot continuu sau cost excesiv pe Raspberry.

Geometria este creată în Blender și randată în straturi ușoare; Raspberry nu
rulează un motor 3D continuu pentru oraș. Bugetul tehnic trebuie evaluat împreună
cu lizibilitatea și răspunsul tactil. Criteriile de mai sus sunt obiective de
analiză, nu o certificare globală 10/10. Verificările și limitele curente sunt în
[dovezile orașului](evidence/city-v3-2026-10-24.md) și
[vizibilitatea cerului](evidence/night-sky-visibility-2026-10-24.md).
