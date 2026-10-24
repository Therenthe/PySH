# Radio library hierarchy —25October2026

P2 is a verified local-source candidate, not yet installed. Device remains on
P1 runtime34f8210d72fe/public887fc97f. P3/P4/P7 remain planned; proposal6 excluded.

## Behavior

Favorites and Discover are explicit, mutually exclusive collections. Tapping
an already selected collection is a no-op; collection changes retain search,
country and language. Empty Favorites offers Discover, while a filtered saved
collection explains no results and Clear restores it without deleting favorites.

One current player keeps actual station identity, metadata and state together.
Catalog artwork is56px in rows; the player uses64px below a285px outer panel,
96px when wider. A container query follows available content width; paused and
remembered names/track metadata wrap rather than hiding text in a stopped
marquee. Playing text retains the existing marquee. Artwork remains genuine
catalog data with monogram fallback; insecure/IP URLs are not requested.

Mute has a crossed-speaker icon and accent state. The passive selected-row
indicator no longer inherits a34px oval around a20px glyph. Actual transport,
output recovery, favorite ownership, safe artwork handling and callback semantics
are retained. All functional targets remain48px, primary Play64px.

## Reproductions and iteration

Four resolved-stream cases failed: player.url matched catalog url_resolved but
the selected-row test used only the primary url. Both accepted addresses now
identify the row and all four pass.

A private initial28case run had12PASS/16FAIL: four true resolved-selection
failures and12test-harness failures because Apply was looked up under an old
keyboard-actions container. The current keyboard's accessible Apply was present;
only the selector was corrected. No keyboard product defect is claimed.

Independent visual review found six narrow paused title lines beside a centered
96px logo and clipped track text. The compact, top-aligned64px header and wrapped
paused metadata were rendered and inspected in both themes/languages.

Collection backgrounds originally interpolated in opposite directions for140ms
while foreground/state changed immediately. Four immediate post-touch contrast
probes failed, including1:1 at the first frame. Selection colors now change
immediately; press transform feedback and reduced-motion parity remain.
All four negative contrast cases pass after correction. This is a focused
selection-state improvement, not a complete contrast certification.

## Source verification

28focused library cases PASS in EN/RO × Ink/Night at800x480, including decoded
HTTPS artwork, blocked insecure/IP requests, long paused identity and real
transport hit geometry.52favorite ownership/recovery regressions passed during
integration, plus16product/filter/scroll/tour checks. Earlier failed runs and
intermediate visual captures remain private. TypeScript, production build,
repository structure,94extension and701Python checks PASS (32platform-specific
skips). Pinned native delivery is recorded below when complete.

No backend/API/dependency/preference schema or account change is introduced.
Physical touch, audible output, DRM and full product acceptance remain OPEN.
