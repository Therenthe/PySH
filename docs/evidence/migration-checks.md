# Migration checks — 2026-10-02

Scope: new PySH directory, imported source, no device mutation. Python 3.12 from the existing local project environment; Node 24.19.0. The original source was not edited. These checks do not certify a clean install, Linux hardware or final product acceptance.

| Check | Result |
| --- | --- |
| Original document versus imported source | Identical SHA-256; see MIGRATION.md |
| `python -m pytest tests -q --tb=short` | 39 passed in 1.93 s; upstream Starlette/httpx deprecation warning |
| `node node_modules/typescript/bin/tsc -b --pretty false` | Exit 0 |
| `node node_modules/vite/bin/vite.js build --configLoader native` | Exit 0; 15 modules; HTML/CSS/JS emitted |
| `python scripts/check_repository.py` | PASS; full 30-criterion product inventory |
| `python scripts/package-release.py` | Build 5a7b844f486f; 33 runtime files |
| Extracted package inspection | All manifest hashes and archive checksum match; backend imports; static index returns HTTP 200; extension manifest exists |
| `python scripts/check_acceptance.py --phase product` | Expected exit 1; all 30 remain OPEN |

Dependency caveat: copied pnpm dependencies initially failed module resolution. Their local package graph was materialized and checks then passed. At that initial local check, fresh registry installation and GitHub CI had not been observed; subsequent clean CI results are recorded below.

SSH read-only attempt did not return device data: the environment's command returned a wrapper message rather than SSH output. No remote state was established and no device change was made. Use a working authorized SSH execution path for the next live inventory.

Local source audit found an absent browser E2E suite and pre-existing UI defects documented in STATUS. Historical private device evidence remains in the original workspace and is not treated as current release evidence.

Independent static review of the migrated tree found no actionable migration regressions: mapped sources are present and launcher/package/asset paths agree. This review did not execute the app on Pi. A targeted credential-pattern scan found no private-key/GitHub-token patterns in publishable files; it is not a complete security audit.

Follow-up on 2026-10-02: private Therenthe/PySH write access verified via connector. Wired SSH matched the previously trusted host key; batch authentication failed (publickey,password). No live device inventory obtained.

Publication verified: import commit `6ff604b7ebb9c80b11765ea59917971071afba78`, full tree `4a1779e8bf8613c393148e02f080c88b6c09aaa9` matches the local source tree (109 files). The original GitHub commit is retained as parent. Local main/origin/main synchronized using exact, hash-verified Git objects; the earlier local import history is retained on migration-local-history.

Clean GitHub runner checks passed on the import commit: frontend build, backend tests and repository checks under Python 3.12/3.13. [CI run 37030198002](https://github.com/Therenthe/PySH/actions/runs/37030198002). This supersedes the earlier clean-install uncertainty for the application CI paths; hardware acceptance remains OPEN.
