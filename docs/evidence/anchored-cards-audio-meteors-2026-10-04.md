# Carduri ancorate, dimensiuni audio și meteori — 2026-10-04

## Schimbare

Arrange afișează vremea, prognoza și redarea restrânse. Intrarea în editor închide stările extinse; Done păstrează aceste stări compacte. Cardurile poziționate manual memorează marginea apropiată:anchorX left/right șianchorY top/bottom, cu distanțe normalizate și strat. Creșterea unui card ancorat la dreapta se face spre stânga; cel ancorat jos crește spre sus. Clamp împiedică ieșirea din canvas. Pozițiile istorice fără ancore păstrează interpretarea stânga/sus. Suprapunerea voluntară și selectarea cardului acoperit rămân disponibile.

În editor, cardul compact de redare este disponibil separat pentru poziționare chiar dacă în utilizarea normală este retras în vizualizator. Acțiunile de transport sunt ascunse în editor. Setările Compact/Echilibrat/Mare determină64/88/112px atât cu transportul deschis cât și închis. Transportul deschis folosește un rând superior cu vreme și prognoză separate orizontal, astfel încât semnalul mare și controalele încap la800×480.

Șase geometrii audio distincte sunt bazate pe semnalul real:undă PCM, coloane ascendente, raze orbitale, anvelopă simetrică, linii bilaterale și elipse RMS. Nu reprezintă frecvențe FFT. Fără redare/mute/semnal valid nu există animație audio fictivă. Reduced motion folosește nivelul numeric.

Meteorii decorativi au capul în direcția vitezei și coada în urmă. Traseele coboară spre stânga sau dreapta, cu variații independente și grupuri rare neregulate; nu sunt o predicție astronomică. Visibility/reduced motion opresc și golesc evenimentele.

## Dovezi și limite

- TypeScript și buildVite:PASS;41fișiere împachetate, build94ca6c6baf22.
- Backend:298passed/22Windows skips, un avertisment de depreciereStarlette. Preferințe:23passed, inclusiv persistarea ancorelor, compatibilitatea veche și refuzarea valorilor invalide fără schimbarea discului/memoriei.
- Auditor audio:28probe izolate trecute; integrarea inițială8/8trecută. Proba extinsă necesită90s pentru18combinații/stil×size, nu o limită arbitrară30s. Rerun integrat în curs.
- Auditor ancore:6probe noi+4swap/suprapunere trecute pe snapshot izolat. Auditor meteori:8/8trecute, inclusiv geometria animată reală în Chromium și ambele teme/limbi.
- Prima suită completă integrată:246passed/8failed în4.7min. Patru probe audio au depășit30s; patru probe swap au încărcat versiunea testului cu vechea comparație top-left, schimbată în timpul pregătirii. Rerun proaspăt al fișierelor afectate obligatoriu înainte de instalare.

Rerun proaspăt integrat:18/18probe din audio-sizing-styles,home-free-placement șihome-anchored-placement au trecut în1.3min; cele opt eșecuri inițiale sunt rezolvate în probele actuale. Împreună cu246probe neafectate trecute, acoperă cele254cazuri. Sursele aplicației nu s-au modificat în timpul acestor rulări; fișierele de test actualizate au fost reîncărcate pentru rerun.

Nu este încă dovadă de instalare pe Pi, gest tactil fizic, performanță sau acceptare de produs. Planul complet, inclusiv restanțele mai vechi, este în ../UI_DELIVERY_PLAN.md. Home ambient takeover și erorile Bluetooth/locație rămân pași separați OPEN.
