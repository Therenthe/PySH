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
- [x] Regresii actualizate pentru noul contract, audit EN/RO × ambele teme.
- [x] Publicare și identitate verificată, backup separat pe PC, instalare reversibilă.
- [x] Probe native cu slider ținut apăsat, stare reală și persistență la eliberare.
- [x] Restaurare exactă și verificarea serviciilor/resurselor, raport final.

## Charter și limite

Se măsoară numeric draft înainte de pointerup, actual hardware/API în timpul
glisării, salvarea numai la commit, serializarea/coalescerea, stări întârziate,
eșecuri și recuperare, tastatură, cancel/blur/navigare și cele două teme/limbi.
Fixture-urile separă starea hardware de preferințele persistente; nu certifică
acustica sau backlightul real. Capturile și stările brute rămân private.
Proba dispozitivului păstrează rețeaua, preferințele, istoricul și starea media.
Un endpoint analog nu este dovadă că există boxe; volumul sistemului și verificarea
auditivă sunt rezultate distincte. Acceptarea produsului complet rămâne OPEN.

## Iterația R2: latența observată pe dispozitiv

R1 a trecut 44 verificări native cu pointer/tastatură sintetizate, dar timpii
observați includeau mișcarea pointerului și citirea completă a playerului.
R2 elimină o scanare audio duplicată, folosește răspunsul hardware al preview-ului
fără GET complet și mută polling-ul regulat de rețea/BT în afara lockului audio.
Citirea audio rămâne serializată și proaspătă; refreshul explicit are prioritate
față de rezultate vechi. Salvarea și recuperarea incertă păstrează verificările.

- [x] Test determinist: polling de rețea blocat, preview audio terminat înaintea lui.
- [x] Readback real păstrat, fără copierea optimistă a valorii solicitate.
- [x] Repetarea probei native R2 și măsurarea răspunsului preview separat de player.

## Livrare verificată

Runtime `40e96fcc7f76`, cod GitHub `c9ac5e2927f9c77a69f07a6d98d1e79bef01dbde`,
precedent `9897df27e389` păstrat. 140 probe browser și 44 verificări native PASS.
Preferințele, volumul/mute, istoricul și starea media inițială restaurate;
rețeaua/gateway-ul păstrate, trei servicii active, diagnosticul închis și zero
convertoare/directoare temporare proprii. Fără redare audio în probă și fără
acceptare acustică; ieșirea era indisponibilă înainte. Acceptarea este delimitată
la reglaje live, fără a închide criteriile globale ale produsului.
