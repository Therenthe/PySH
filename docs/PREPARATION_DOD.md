# Definition of Done — pregătirea proiectului

Etapa solicitată înainte de implementarea aplicației. Candidat: `prep-2026-09-29`. Poarta verificabilă este `scripts/check_acceptance.py --phase preparation`; acceptarea produsului are o poartă separată.

| ID | Condiție | Rezultat |
|---|---|---|
| PREP-01 | Cerințele finale, alegerile implicite, DoD-ul și buclele de lucru sunt documentate; prototipul istoric nu limitează ținta finală. | PASS |
| PREP-02 | Cele trei skill-uri sunt create, instalate, validate și evaluate independent prin scenarii. | PASS |
| PREP-03 | Audit înainte/după, backup verificat off-device și curățare strictă a adaosurilor identificate; fără pierderea datelor personale. | PASS |
| PREP-04 | După modificări, SSH, rețeaua, desktopul, DSI/touch, audio, Bluetooth și APT sunt sănătoase. | PASS |
| PREP-05 | Dependențe locale fixate, compilare reală de fixture frontend, interacțiune browser și server Python local verificate; limitările runnerului Playwright sunt explicite. | PASS |
| PREP-06 | Venv-ul de pe Pi funcționează, D-Bus răspunde, mpv decodifică și primește comenzi IPC; scriptul de pregătire poate fi repetat. | PASS |
| PREP-07 | Proiectul are Git, instrucțiuni de lucru și restaurare, dovezi locale, fără secrete în fișierele versionabile; criteriile de produs rămân deschise. | PASS |

Dovezile fiecărui ID sunt în [acceptance.json](acceptance.json), iar concluziile și limitele sunt în [PREPARATION_REPORT.md](PREPARATION_REPORT.md). PASS aici nu înseamnă UI gata, Bluetooth audio testat pe boxă sau servicii DRM funcționale.
