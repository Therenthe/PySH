# 0004 — Direct UI boot

Date: 2026-10-02. Status: Accepted as target; implementation pending.

Context: produsul nou cere boot direct în UI. Runtime-ul importat pornește după sesiunea grafică și oferă ieșire la desktop conform specificației originale.

Decision: experiența appliance va porni în PySH și va oferi o cale controlată de service/recuperare. Până la validarea ei, păstrăm desktopul și mecanismul de recuperare existent pe Pi.

Consequences: BOOT-01/02 și fluxurile de ieșire trebuie revizuite explicit pentru candidatul appliance. Nu marcăm autostart-ul actual ca boot direct fără desktop și nu eliminăm recuperarea în migrare.
