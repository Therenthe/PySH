# Radio library hierarchy —25October2026

P2 is installed as runtimef97f14d6b651/code
dc6bee32ac8c69225aef062c2ac2fd539e9c7326. Previous P1 runtime34f8210d72fe
is retained. Scoped native verification passed; full product acceptance is OPEN. P3/P4/P7 remain planned; proposal6 excluded.

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

## Pinned native delivery

Frozen locale7fb88432b2165bbc5fb1aafa95edc3ae9c03225/tree472288ac and public
codedc6bee32/tree3a367d37 were verified across806public source files. Runtime214
files,29preferences, unchanged Ethernet/gateway and a separate PCbackup with
verified contents/checksum were confirmed. ArchiveSHA256:
53133391ec94922b72e4d9b26e58de9b487d71ef3c9a7db003f8fec11d319728.

Current English/night800x480 native verification passed76distinct named checks,
covering pinned loaded assets, one actual player, genuine decoded station logo,
station/track identity, Favorites/Discover without favorite mutation, open/closed
navigation geometry, hidden touch-scroll bars, same-source pause/resume, real mute
and crossed-speaker feedback. No new station/output/network/standby was selected.
All actual control state and original preferences/player were restored.

The first native run passed read-only/transport probes then checked mute while
the preceding operation intentionally still disabled controls. That harness result
is retained; the repeat waits for control availability and passed, including mute.
No product bug is inferred from that premature assertion. Both cleanups confirmed
exact preferences/audio/radio restoration and closed debug ports. Two genuine
auto-hide preference writes were admitted; no unexpected writes or page errors.
A fresh ordinary Wayland frame is inspected after cleanup. Physical-finger,
speaker-audibility, native EN/RO/theme matrix and global stability remain OPEN.
