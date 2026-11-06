# Volum și luminozitate în timpul glisării

Cerere: reglajul real și procentul să răspundă în timp ce degetul se mișcă,
fără a aștepta eliberarea sliderului. Toate suprafețele PySH și meniul extern.

- [x] Inventar: Radio, TV, video local, modal/setări audio, comenzi rapide,
  setări/modal ecran și meniul serviciilor externe.
- [x] Draft numeric comun, protejat de polling și confirmări întârziate.
- [x] Un singur request în zbor și ultima valoare în așteptare; preview limitat.
- [x] Preview fără scrieri de preferințe; valoare finală salvată la sfârșit.
- [x] Finalizare la cancel/blur/unmount, fără reluarea automată a scrierii incerte.
- [x] Protocol scalar allowlisted, worker nou, păstrând profilurile și conturile.
- [ ] Regresii actualizate pentru noul contract, audit EN/RO × ambele teme.
- [ ] Publicare și identitate verificată, backup separat pe PC, instalare reversibilă.
- [ ] Probe native cu slider ținut apăsat, stare reală și persistență la eliberare.
- [ ] Restaurare exactă și verificarea serviciilor/resurselor, raport final.

## Charter și limite

Se măsoară numeric draft înainte de pointerup, actual hardware/API în timpul
glisării, salvarea numai la commit, serializarea/coalescerea, stări întârziate,
eșecuri și recuperare, tastatură, cancel/blur/navigare și cele două teme/limbi.
Fixture-urile separă starea hardware de preferințele persistente; nu certifică
acustica sau backlightul real. Capturile și stările brute rămân private.
Proba dispozitivului păstrează rețeaua, preferințele, istoricul și starea media.
Un endpoint analog nu este dovadă că există boxe; volumul sistemului și verificarea
auditivă sunt rezultate distincte. Acceptarea produsului complet rămâne OPEN.
