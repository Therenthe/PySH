# PySH — limbajul Media existent

Documentare a implementării existente și a extensiei TV; nu redefinește scena
Blender Acasă sau structura aplicației. Referințe: `style.css`, `media.css`,
`interface-polish.css`, `iptv.css` și probele la 800×480.

## Reguli păstrate

- Manrope pentru titluri și comenzi Media; textul urmează fonturile deja
  găzduite local. Corp 16 px, text secundar în general 14 px.
- Culorile vin din tokenurile temei: `--paper`, `--surface`, `--ink`, `--muted`,
  `--line`, `--line-dark`, `--soft`, `--accent-strong`. Ink și Noapte folosesc
  aceleași componente și comportamente; accentele existente sunt păstrate.
- Comenzi tactile de minimum 48×48 px. Raze în general de 10 px pentru comenzi TV, 16 px
  pentru dialoguri. Stări selectate prin culoare și `aria-pressed`; focusul
  vizibil folosește conturul existent. Nu se bazează pe hover.
- Listele defilează prin atingere; barele de scroll rămân ascunse. Ecranul
  exterior nu defilează. Animațiile respectă reducerea mișcării.
- Iconițe SVG funcționale, greutate coerentă; logo-uri reale opționale, cu
  fallback textual. Nu se inventează artwork, date de ghid sau disponibilitate.

## Extensia TV

Media → Servicii adaugă TV lângă YouTube/Netflix/muzică. Canale/Înregistrări/
Surse sunt destinații distincte. La Canale, lista este în stânga și programul
canalului în dreapta; vizionarea este o alegere explicită, nu efectul selectării
unui rând. Privește live este acțiunea principală.

Playerul video folosește suprafață neagră, fără rame/browser, și o singură bară
inferioară temporară; atingerea readuce comenzile. Închidere, conectare și eroare
au feedback distinct. Dialogurile blochează fundalul și restaurează focusul.
Ștergerea definitivă are confirmare separată; programarea și paddingul rămân
într-un singur dialog, fără lanț de meniuri.

Verificarea finală este delimitată la această extensie; documentul nu afirmă
contrast numeric, acceptare hardware sau scor global 10/10.
