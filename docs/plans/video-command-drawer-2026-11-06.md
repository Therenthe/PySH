# Meniul tras de sus în timpul redării video

Cerere: gestul existent trebuie să funcționeze și peste TV fullscreen și video
local. Luminozitatea a fost aplicată întâi la25%, apoi la10% conform noii cereri;
ultima valoare10% se păstrează la livrare. Volumul este restaurat la nivelul
observat înaintea probei native, pentru a păstra setarea mai recentă de pe dispozitiv.
TV final: Antena1 favorite.

- [x] Cauză identificată: video local exclus, TV acoperă gestul/meniul și izolează focusul.
- [x] Gest în fiecare player, alternativă tactilă48px și tastatură.
- [x] Meniul și dialogurile proprii deasupra playerului, fără întreruperea redării.
- [x] Contextul video corect, revenire focus/Escape, navigare după cleanup confirmat pentru sesiuni cunoscute.
- [x] Regresii EN/RO × Ink/Noapte, erori, cancel și audit complementar.
- [x] Publicare verificată, backup PC și instalare reversibilă.
- [x] Probe native, restaurare Antena1/niveluri inițiale/luminozitate10 și raport final.

Se păstrează meniul și designul existente; nu se schimbă serviciile externe.
Mockurile nu certifică redarea reală sau atingerea fizică. Problema separată
TV-START-20261106 rămâne OPEN; această schimbare nu pretinde remedierea ei.

Instalat runtime `6314da69ecce`, sursă GitHub
`479361d0af8dc7d64d139122150ace6de2564d17`, precedent `40e96fcc7f76` păstrat.
Probe native TV și clip local propriu PASS; nivelurile reale se schimbă în timpul
atingerii, persistă la ridicare, meniul se închide/reintră și navigarea funcționează.
Clipul/istoricul propriu eliminate prin API după validarea hashului, trei servicii
active și zero dispozitive touch/porturi de diagnostic rămase. Gesturile native
au fost sintetizate prin intrarea Linux; nu este o certificare a gestului fizic.
