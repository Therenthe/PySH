# Auditori UI/UX pentru PySH

Instalați și verificați la 2026-10-23. Skillurile sunt instrucțiuni de lucru,
nu o certificare a aplicației. Contractul produsului, cerințele utilizatorului
și dovezile de pe dispozitiv au prioritate față de recomandările generale.

## Surse fixate

| Rol | Skill / sursă | Revizie | Licență |
|---|---|---|---|
| Audit tehnic UI, teme, mișcare, lizibilitate | [Impeccable](https://github.com/pbakaus/impeccable/tree/7e51b1e1aa61c0ca60e9d7a510b77c57029f7d98/.agents/skills/impeccable) | `7e51b1e1aa61c0ca60e9d7a510b77c57029f7d98` | Apache-2.0 |
| Fluxuri cap-coadă și analiză a rezultatului vizibil | [Browser UAT Analyst](https://github.com/microsoft/cat-agent-skills/tree/5c8cad25a6f1f01fd9bc922080fb8aae5bb420be/submissions/browser-uat-analyst) | `5c8cad25a6f1f01fd9bc922080fb8aae5bb420be` | MIT |
| Focus, tastatură, meniuri și dialoguri | [Keyboard Navigator](https://github.com/Community-Access/accessibility-agents/tree/decf6bac7f086c19afb242797b4974671ceff597/skills/keyboard-navigator) | `decf6bac7f086c19afb242797b4974671ceff597` | MIT |
| Contract și schemă pentru constatările de accesibilitate | [a11y-core](https://github.com/Community-Access/accessibility-agents/tree/decf6bac7f086c19afb242797b4974671ceff597/skills/a11y-core) | aceeași revizie | MIT |

Instalarea folosește helperul `skill-installer`, în directorul personal de
skilluri Codex. `SKILL.md` instalat este identic cu sursa fixată; licența upstream
și `UPSTREAM.json` păstrează proveniența și hashurile. Nu se copiază întregi
colecții sau skilluri terțe în sursa ori pachetul runtime PySH.

Impeccable engine `0.1.16` a fost verificat cu SHA-256 publicat lângă binarul
release-ului oficial. Contextul și detectorul au fost rulate explicit; nu s-au
instalat hookuri sau modificări ale configurației globale de execuție.

## Rutina de audit

1. Citește `STATUS.md`, `PRODUCT.md`, `DEFINITION_OF_DONE.md` și planul UI.
   Identifică sursa, candidatul și limitele probei înainte de verdict.
2. Scrie un charter: sarcina utilizatorului, starea inițială, datele de test,
   rezultatul așteptat, scenariile de eșec și ceea ce rămâne netestat.
3. Auditori separați verifică uzabilitatea, aspectul și accesibilitatea. Fiecare
   folosește propriul context de browser pe aceeași sursă înghețată, fără editări
   concurente care ar invalida măsurătorile.
4. La 800×480, EN/RO și Ink/Noapte: execută comenzile, observă rezultatul și
   capturează stările relevante. Include pending, eroare, retry, cancel, date
   lipsă/lungi și revenirea din flux. Gesturile sintetizate se declară ca atare.
5. Pentru fiecare defect: ID stabil, severitate, pași, așteptat/observat, dovadă,
   fișier/linie, remediere și probă de retestare. Separă defectul produsului de
   limita fixture-ului sau a instrumentului. Recomandările estetice sunt
   distincte de defectele măsurate.
6. Responsabilul reproduce și deduplică constatările, apoi le urmărește în
   `UI_DELIVERY_PLAN.md`. Remedierea se verifică prin repetarea aceleiași probe.

## Limite și confidențialitate

- Numai servere locale loopback pentru aceste audituri. Fără tunel public,
  încărcări de capturi în cloud sau citirea profilurilor cu conturi reale.
- Fixture-urile nu schimbă datele, rețeaua, audio sau preferințele Raspberry.
  Orice probă nativă urmează separat procedura din `OPERATIONS.md`.
- Ținta PySH este 48×48 px; aceasta este o cerință de produs, nu pragul generic
  WCAG 2.2 AA de 24×24 px cu excepțiile sale.
- Contrastul se verifică pe fundalul efectiv compus. O culoare CSS sau un
  avertisment al detectorului nu dovedește singur contrastul randat.
- Lipsa unui `DESIGN.md` sau prezența clientului `android/` nu schimbă ținta:
  aici se evaluează hubul Chromium, nu se migrează documentele și platforma.
- O recomandare prea strictă a unui skill nu devine automat încălcare WCAG.
  Lipsa erorilor automate nu dovedește conformitate sau acceptare fizică.
- Capturile, trasările și jurnalele brute rămân private. În Git intră numai
  sinteza redactată, fără conturi, tokenuri, preferințe sau detalii operaționale.
- Nu se acordă nota globală 10/10 dintr-o inspecție parțială. Criteriile de
  hardware, DRM, performanță și stabilitate se închid numai cu probele lor.

## Prima aplicare

Auditul inițial este urmărit în
[raportul din 23 octombrie](evidence/auditor-skills-2026-10-23.md).
