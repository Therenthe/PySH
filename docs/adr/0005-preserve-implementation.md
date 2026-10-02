# 0005 — Preserve and migrate implementation

Date: 2026-10-02. Status: Accepted.

Context: există cod fără commit-uri și documentație depășită. O structură goală ar pierde progresul.

Decision: import explicit al surselor, cu manifest de hashuri, adaptare de căi și verificări; păstrăm directorul vechi intact. GitHub privat devine sursa canonică după push verificat.

Consequences: app/ și services/ conțin cod real; os/ și hardware/ au responsabilități documentate fără implementări fictive. Datele private și probele brute rămân locale; afirmațiile istorice sunt separate de acceptarea candidatului nou.
