# UI usability and appearance review

Owner requested two independent auditors, then automatic weather, district search, tolerant radio filters, realistic lunar phase, transparent panels and retractable navigation. Audit was read-only on source1f6a891; follow-up candidate546335e64372 has41 runtime files, native activation pending.

## Remediated findings

- Stable touch settings also suppress the idle screensaver while a choice is open. Failed saves keep the old selection and expose retry/cancel feedback within the dialog. Disabling visualization returns to clock layout; inconsistent old preferences also fall back to clock. Full-screen transport interactions reset the control-hide timer.
- București/Bucharest aliases and case/diacritic variants return the municipality plus sectors1–6. Sector queries return the requested point. Coordinates are representative GeoNames points, not measurements at the home address; attribution is distributed in THIRD_PARTY_NOTICES. [GeoNames source](https://www.geonames.org/search.html?country=RO&q=Bucharest).
- Country variants Romania/romania/ROMÂNIA/RO use standardizedRO; localized language aliases normalize before requests. Other ISO codes are uppercase and country names normalized. Favorites follow visible text/country/language filters. [Radio Browser API](https://docs.radio-browser.info/).
- Weather polling/cache cadence is5minutes, error retry1minute. User-facing weather refresh buttons are removed. The weather action opens location settings; changing location schedules backend refresh. Cached/offline status remains explicit. Faster polling does not imply finer meteorological model resolution.
- Settings icon is a concentric eight-tooth outline. Empty Radio no longer repeats “Nothing playing”; it tells the user to choose a station. Player signal occupies its central space. Night functional boundaries were strengthened.
- Lunar illustration uses low-precision geocentric solar/lunar longitude and latitude to calculate illumination and waxing/waning direction.3October2026 is verified near last quarter, and26October near full moon against [USNO phase data](https://aa.usno.navy.mil/data/api.html). This is an approximate illustration, not exact ephemeris, horizon visibility or telescope orientation.170 stars vary spatially; a small subset twinkles and rare meteor animation is explicitly decorative. Reduced motion disables those effects. No WebGL/3D engine was added. Translucent night panels retain content contrast and reveal the scene beneath.
- A persistent48px top-bar control hides/reopens the navigation rail, releasing its entire107px. Hidden controls are inert and not reachable. Optional hide-after-navigation persists. Width/padding transitions respect reduced motion. A captured clipped title and residual18px padding were fixed before installation.

## Verification and remaining work

275 backend tests passed,22 platform skips and one existing Starlette warning. TypeScript, production build and repository structure passed. Focused settings/recovery10cases passed across EN/RO; the complete176-case browser regression passed. Intermediate full runs correctly failed4new rail-width assertions while residual padding remained; these were defects, not acceptance. Original172other cases passed, then targeted correction passed. Native proof remains pending.

Neither auditor awarded a score. Remaining visual work includes more refined lunar texture, further reduction of duplicated Media/Settings headings, measuring animated rendering on Pi, and physical usability/real-service acceptance. All30 full-product criteria remain OPEN. The candidate is an improvement loop, not a10/10 declaration.
