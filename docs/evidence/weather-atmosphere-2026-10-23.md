# Weather-driven atmosphere

## Problem and data boundary

The previous scene treated every WMO45/48 condition as dense ground fog and a
fully overcast sky. A diagnostic found code45 alongside about8km visibility;
the large opaque veil overstated what that estimate supported. The current
Open-Meteo response is model output, not a sensor observation at the user's home.

The fix separates two measurements from the **same current provider timestamp**:
`visibility_m` controls ground haze and `cloud_cover_pct` controls Blender cloud
coverage. Missing, invalid or expired values never become measured clear sky.
The provider condition label/code remains unchanged. Existing cached responses
without the new keys are refreshed once; failures preserve stale cached data.
No hourly-neighbour substitution, forced clear weather or location change occurs.

## Sources and presentation choices

- [Open-Meteo API documentation](https://open-meteo.com/en/docs): current conditions
  are model data; hourly variables are also available in current conditions;
  visibility is in metres and total cloud cover is a percentage.
- [WMO aviation guidance](https://community.wmo.int/site/knowledge-hub/programmes-and-initiatives/aviation/aviation-hazards-low-visibility-and-low-cloud):
  fog reduces horizontal visibility below1000m. This does not imply a measured
  local condition or an alert, and horizontal visibility does not measure sky cover.

The opacity curve is an artistic presentation mapping: none at8km or more,
gradually weak down to1km, progressively stronger below1km. Cloud cover is
independent. Day/night gates, astronomical body positions and actual lunar phase
are preserved. The same sparse Blender stars, descending meteor renders and
five aircraft models remain integrated; no photographic star field is added.

## Implemented and independently reviewed

633Python cases passed with32platform skips;132affected browser cases passed in
EN/RO. Independent actualApp800×480review covered24atmosphere scenarios and4new
day/night precipitation scenes. At8km/86% the city remains visible while Blender
clouds honestly retain overcast sky; at8km/14% the sparse stars and real phase can
appear at night. Dense fog, unknown/missing/invalid/stale data and precipitation
retain conservative celestial gating. Measurement-only polls do not move cards.

The review also found faint daytime precipitation. Two daytime-only CSS rules
darken the existing Blender raindrop render and add soft relief to its snowflake
render. Particle geometry, quantity, alpha and timing are unchanged; night filters
remain untouched. Eight dedicated EN/RO screenshot comparisons passed, measuring
stronger daytime contrast and identical night appearance against the control.
No new assets, procedural substitute particles or photorealistic star fields ship.

Frozen-candidate verification, canonical publication and native rollout remain
pending. Full product acceptance remains OPEN.
