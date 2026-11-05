# Digi Sport 1 — player oficial în PySH

Utilizatorul indică pagina oficială și confirmă accesul din rețeaua Digi.
Pagina folosește Shaka/DASH, Widevine și sesiuni DAI emise de furnizor.
Se păstrează playerul oficial; nu se publică tokenuri sau licențe, nu se
ocolește restricția de rețea și nu se pretinde înregistrare IPTV pentru DRM.

- [x] Intrare clară în lista TV, EN/RO, 800×480, ambele teme.
- [ ] Pregătirea Widevine în profilul existent, numai URL-ul oficial permis.
- [ ] Meniu PySH retractabil și revenire reală; worker nou, fără reset conturi.
- [x] Regresii pentru protocoale/hosturi/căi respinse, stări pending și revenire.
- [ ] Publicare, backup, instalare și verificare nativă.
- [ ] Cadre și poziție avansând, rezoluție reală; nu doar deschiderea paginii.

Charter nativ: profilul serviciilor existent pe Pi, radio și preferințe
restaurate după probă. Prima probă a deschis pagina, însă dialogul de
confidențialitate Digi a rămas deasupra playerului și nu s-au decodat cadre.
Nu este PASS pentru redare; se verifică opțiunile de refuz al cookie-urilor
opționale. Intrările pointerului în probe sunt sintetizate.

A doua probă, pe runtime-ul anterior: pagina oficială în browserul existent a
decodat 1280×720, Widevine activ, cadre 532→601 și poziție în avans, fără citirea
conturilor sau a cererilor de licență. Dialogul de preferințe a rămas vizibil;
opțiunea „Respingeți toate” va fi folosită în proba integrării. Deschiderea prin
noua intrare și revenirea sunt încă în așteptarea instalării.

941 Python PASS/46 omise pe platformă/11 subteste, 110 JavaScript, TypeScript,
Vite și 44 regresii TV PASS. Audit separat fără blocaj de sursă; edge-ul
căutării Digi-only a fost corectat și retestat în 8 probe EN/RO × teme.
