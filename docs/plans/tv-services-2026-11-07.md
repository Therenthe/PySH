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

### Compatibilitate Orange pe Raspberry

- [x] Prima Sport 1 reproduce W813 și fără extensii; identificare vizuală și audit separat.
- [x] Observație scalară: trei variante cu codec acceptat, toate marcate nedecodabile.
- [x] Comparație raportată de utilizator: același cont funcționează pe Windows și Android.
- [x] Chrome oficial ARM64 157 verificat prin index Google semnat, pregătit separat.
- [x] Profil separat: tastatură nativă, micșorare pagină și revenire Radio verificate.
- [x] Utilizator autentificat în Chrome; proba Prima Sport 1 executată: FAIL W813, zero cadre.
- [x] Firefox 159 oficial Raspberry Pi, pregătit separat; EME disponibil.
- [x] Utilizator: loginul Firefox dispare, iar videoclipul gratuit dă W813; nu se pretinde autentificare Firefox.
- [x] Control Widevine nativ cu modulul Google nemodificat 4.10.3112: imagine criptată în progres, 68→371 cadre.
- [x] Aceeași configurație Firefox: Kanal D marcat Free în Orange dă W813, cinci observații cu zero cadre.
- [x] Probe închise, port/tunel închis, preferințe păstrate; revenire vizuală la playerul TV PySH.
- [ ] Blocaj de compatibilitate Orange/Linux ARM de rezolvat printr-o cale suportată ori un răspuns tehnic al furnizorului; cauza exactă rămâne nedemonstrată.
- [ ] După o probă reală de succes: integrare persistentă suportată, sursă publicată și retestare prin PySH.

Proba Chrome nu înlocuiește Chromium și nu importă sesiunea existentă. Extensia
încărcată prin DevTools este temporară. Chrome 157 nu a rezolvat redarea; nu este
ales ca browser de producție pe baza acestei probe.

Charter: navigarea este o comandă permisă, nu URL arbitrar; închiderea ferestrei
externe se confirmă. Conturile și profilul existent rămân intacte. Nu se citesc
câmpuri de autentificare sau cookie-uri. Nicio reconfigurare de rețea/audio/OS.
Păstrăm nivelurile găsite înainte de livrare.

Fixture-urile probează numai controalele PySH. Playback-ul Orange din abonament
nu poate fi declarat verificat înainte de autentificarea utilizatorului.
