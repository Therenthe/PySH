# Digi: siglă și Canale; Orange TV Go

Cererea: captura reală, sigla Digi Sport, revenire directă din Digi la Canale;
Orange TV Go în Media → Servicii, cu autentificare pe site-ul oficial.

- [x] Captură de pe runtime-ul actual; Digi are monograma D.
- [x] Verificată sursa oficială Orange și sigla Digi din site-ul oficial.
- [x] Implementare în UI, API, pregătire DRM, extensie și host nativ.
- [x] Regresii și audit complementar EN/RO × Ink/Noapte, 800×480.
- [x] R1 publicat/verificat, backup PC și instalare reversibilă.
- [x] R1 nativ: siglă Digi și revenire Canale; Orange Acasă.
- [x] R2: tastatură/revenire pe pagina oficială de login Orange (TVS-AUTH-01).
- [x] R2: meniu accesibil cu tastatura deschisă (TVS-AUTH-VIS-02).
- [x] R3 nativ: câmpul activ vizibil după micșorarea ferestrei (TVS-AUTH-03).
- [x] Probă nativă: siglă, Digi → Canale, Orange/login/tastatură/revenire.
- [x] Cont Orange real: utilizator autentificat; membrul existent selectat cu acord.
- [ ] Orange playback: FAIL W813 pe Prima Sport 1 și 2, pista video; retry nu rezolvă.
- [x] Diagnostic închis; setările păstrate, trei servicii active, revenire în Media.

Utilizatorul confirmă că Prima Sport 1 funcționează cu același cont pe alt
dispozitiv. Compatibilitatea redării pe Raspberry rămâne de rezolvat; nu este
demonstrată o cauză precisă sau o remediere.
[Dovezi W813](../evidence/orange-w813-2026-11-07.md).

Charter: navigarea este o comandă permisă, nu URL arbitrar; închiderea ferestrei
externe se confirmă. Conturile și profilul existent rămân intacte. Nu se citesc
câmpuri de autentificare sau cookie-uri. Nicio reconfigurare de rețea/audio/OS.
Păstrăm nivelurile găsite înainte de livrare.

Fixture-urile probează numai controalele PySH. Playback-ul Orange din abonament
nu poate fi declarat verificat înainte de autentificarea utilizatorului.
