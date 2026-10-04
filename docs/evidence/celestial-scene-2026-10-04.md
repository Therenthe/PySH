# Natural celestial scene — 2026-10-04

Prepared source only; installed device still52c/source73cc at this checkpoint. No claim of product acceptance or numerical design score.

## Scope

Sun and Moon follow the selected weather coordinates and UTC time, updated once per minute using the existing UI clock. The panorama faces south: east is on the right, south at centre and west on the left. This is a projected scene, not a compass or observational sky chart. Unsupported coordinates hide both bodies. Below-horizon bodies are hidden; an above-horizon Moon can appear by day. Weather visibility and cached/stale handling remain independent. The Moon phase/texture stays on its existing calculation.

The helper uses the [original Schlyter orbital algorithms](https://stjarnhimlen.se/comp/ppcomp.html), lunar perturbations and sea-level topocentric parallax, with [NOAA refraction](https://gml.noaa.gov/grad/solcalc/calcdetails.html). Twelve Sun/Moon points from eight independent [USNO altitude/azimuth requests](https://aa.usno.navy.mil/data/api) are committed as fixtures. Maximum measured fixture errors: altitude0.028786° and azimuth0.068202°, against0.2° test tolerance. These samples do not prove global, all-date accuracy or terrain-specific rise/set.

Night uses a synthetic starfield and city-facade texture masked by the existing roof geometry; they are decorative, not a real catalogue or live city. Attribution and exact generation prompts are in AMBIENT_GRAPHICS.md. Lunar dust follows the actual rendered Moon and stops when it is below the horizon. Preference Retry retains the exact failed key/value and repeats its write; it no longer merely refreshes state.

The owner cancelled all superheroes. NightEncounters, character silhouettes, Bat signal, Batplane, character tests and the superhero preference are absent from the candidate. Private superseded experiments were never published or installed. Only the two natural background assets are included.

## Verification

Canonical TypeScript/Vite build, repository checks and package passed. Initial scoped browser run:100 passed, four failures caused by outdated help-text assertions. Corrected assertions:4/4 passed. The104 cases cover EN/RO, both palettes, celestial placement, daytime Moon, horizon transitions, missing location, ambient preference save/retry/reload, dust target, Home/idle, meteors and rendered solar/language settings. Fixtures cannot establish physical touch, audibility or native performance.

Device publication, exact package hashes, preserved preferences and native screenshot are pending at this source checkpoint. Full30 product criteria remain OPEN. Bluetooth prompt and radio favorite changes are preserved separately in the working tree and require final integration. Current Netflix/YouTube/music, five cold boots/offline, eight-hour interaction, clean image and restore acceptance remain open.
