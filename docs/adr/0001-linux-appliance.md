# 0001 — Linux appliance

Date: 2026-10-02. Status: Accepted as target direction.

Context: conversația de arhitectură și cererea de migrare cer un dispozitiv dedicat și structură pentru sistem, aplicație și hardware. Implementarea locală este o aplicație peste sesiunea desktop.

Decision: PySH evoluează către un appliance Linux, păstrând codul React/Python existent. Nu începem prin rescrierea aplicației sau înlocuirea serviciilor Linux.

Consequences: os/ găzduiește integrarea și viitorul builder. Imaginea, pornirea directă și recuperarea necesită validare separată; runtime-ul actual rămâne utilizabil pe parcursul tranziției.
