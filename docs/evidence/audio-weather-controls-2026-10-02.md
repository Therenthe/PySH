# Audio transport, persistence and weather races â€” 2026-10-02

Source review found local audio directory queue existed but the UI exposed only pause/stop, active radio pause reloaded a stream, saved audio settings were persisted but not reapplied, and old weather requests could overwrite a new selected city's results.

Repairs expose queue availability, previous/next, progress and touch seek; use pause/resume for the same radio URL; restore saved available output/volume/mute once per availability cycle; and discard stale weather results using request generation plus location identity. Audio snapshots retain actual device values and hardware errors do not become success. No automatic unknown Bluetooth pairing is introduced. Supervisor recovery now logs role and exit code without process arguments or credentials.

Automated asynchronous cases delay the old city request, replace/remove the location, and finish the old request last. Audio tests restore saved values from another default, avoid repeating writes on each poll, pause on device loss and restore on return; preference bytes survive a new store. Queue boundaries are returned for local sources only. Device acceptance remains pending on the candidate produced after these changes.

Local checks: 49 Python tests passed, five Linux cases skipped on Windows; TypeScript and production build passed. Full browser suite: 52 passed, zero skipped/flaky/unexpected, 56.042s. New tests cover EN/RO/themes, local queue boundaries, seek/pause/replay after EOF/error, and same-title/different-URL radio identity. These synthetic checks do not prove device acceptance.
