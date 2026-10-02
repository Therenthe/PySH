# Workflow

Starea curentă este în [STATUS](../STATUS.md). Proiectul a depășit pregătirea și are implementare; produsul nu este acceptat.

GitHub păstrează codul, deciziile, criteriile și rezultatele. Pentru fiecare schimbare: branch din main actualizat → implementare delimitată → verificările DEVELOPMENT → actualizare documente/acceptance → commit → push → pull request → CI/review. Nu se dezvoltă în fișierele Project sincronizate.

Pe Pi se livrează un candidat identificat și verificat, nu fișiere ad-hoc fără istoric. Codul modificat acolo se recuperează și se compară înainte de a înlocui orice release.

Bucla de produs: criteriu OPEN/FAIL → modificare → teste automate → probă reală → rezultat și dovadă → remediere. PASS cere dovadă pe candidatul relevant; modificările invalidează probele afectate. Toate criteriile obligatorii trebuie să treacă pe același candidat pentru release.

Comenzile remote se arată înainte și rezultatele după. Nu se salvează credențiale. Hardware-ul sau conturile absente rămân blocaje explicite. Preferințele utilizatorului nu se șterg pentru a face testele să treacă.
