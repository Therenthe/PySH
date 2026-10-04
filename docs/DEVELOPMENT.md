# Dezvoltare

Procedurile appliance sunt în [OPERATIONS](OPERATIONS.md). `scripts/observe-stability.py --output <director-nou-privat>` se rulează pe Pi ca utilizatorul `pysh`, în sesiunea user systemd activă. Implicit observă opt ore la intervale de30s, fără restart sau operații API de modificare. Identitatea runtime-ului este verificată, procesele includ cgroup-ul aplicației și descendenții verificați ai lansatorului (inclusiv Chromium în scope separat), iar răspunsul API este redus la indicatori booleni fără conturi/preferințe. Datele rămân private; nu publica loguri brute. Schimbarea candidatului invalidează observația, iar completarea telemetriei nu acordă automat PASS pentru stabilitatea tactilă/media REL-01.

Din rădăcina repository-ului: Node 24.19.0 și pnpm 11.19.0 (versiunile mediului verificat), Python 3.12 sau 3.13. Dependențele sunt fixate în lockfile-uri. Hardware-ul Linux nu este simulat ca funcțional pe Windows.

```sh
pnpm install --frozen-lockfile
python -m venv .venv
```

Activează venv (`.venv\Scripts\Activate.ps1` pe Windows, `source .venv/bin/activate` pe Linux), apoi:

```sh
python -m pip install -r requirements-dev.lock
python -m pytest tests -q
node node_modules/typescript/bin/tsc -b --pretty false
node node_modules/vite/bin/vite.js build --configLoader native
python scripts/check_repository.py
python scripts/package-release.py
node --test tests/extension-keyboard.test.mjs tests/extension-return.test.mjs tests/extension-return-content.test.mjs
```

În medii unde ensurepip este restricționat se poate folosi `uv venv --python 3.12 .venv`, apoi `uv pip sync --python .venv/Scripts/python.exe requirements-dev.lock` pe Windows. Nu înlocui Python-ul sistemului pe Pi.

Dezvoltare în două terminale, cu venv activ în primul:

```sh
python -m uvicorn services.backend.app:app --host 127.0.0.1 --port 8765 --no-access-log
pnpm dev
```

Configurează `PI_HUB_DATA` spre un director local `.runtime/dev-data` pentru a separa datele de dezvoltare. UI: `http://127.0.0.1:5173`; build static: `dist/`; API: `127.0.0.1:8765`. Vite citește `app/ui/`, backendul servește `dist/`.

`python scripts/check_acceptance.py --phase product` este poarta de release și trebuie să eșueze cât timp criteriile sunt OPEN. Nu este testul CI pentru modificări obișnuite. Poarta preparation rămâne deschisă în copia migrată deoarece probele private istorice nu sunt importate.

Playwright include regresia Wi-Fi în `tests/e2e/`: EN/RO × E-Ink/Noapte, 800×480, atingeri și operații API simulate numai în teste. Rulează `pnpm exec playwright install chromium`, apoi `pnpm test:ui`. Smoke-ul toolchain testează un fixture și nu înlocuiește aceste teste UI. CI verifică Python 3.12/3.13, TypeScript, build, integritatea structurii și testele de browser; nu acceptă hardware-ul.

Unpacked extension background updates require a new manifest worker entry URL and version, followed by existing-profile native verification. Version-only updates can leave stale MV3 code executing; fresh-profile tests are insufficient. Keep the worker implementation shared through importScripts and retain account profiles. See evidence/external-return-2026-10-04.md.
