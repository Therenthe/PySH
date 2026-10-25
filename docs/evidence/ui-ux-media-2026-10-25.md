# P4 — real local metadata, artwork and Continue watching

Scoped source candidate; installed P3 remains `7db87b09ea29` until the pinned
publication/deployment/native records below are complete. Full product acceptance
remains OPEN. Proposal6 and saved Home presets remain excluded.

## User-facing change

The existing Files/Services browser is retained. Visible files can show actual
embedded title/artist/duration and an actual extracted image; absent information
keeps the filename/type-icon fallback. Continue watching is within the same scroll
surface, initially showing the newest valid item. Resume, Start over and Remove
from history are separate intents; guarded Delete file remains distinct.

Video progress comes from the mounted Chromium video element, never the radio/mpv
playhead. Resume seeks after metadata before initial play. Serialized final close
persists the actual observation atomically; failed persistence retains the paused
overlay with Retry and explicit Leave without saving. If cleanup cannot be
acknowledged, a separate deliberate local-leave confirmation avoids trapping the
user over optional history. Backend expiry is the fallback, not an immediate
remote-cleanup claim. Back to Media preserves the folder, query and invoking focus.
Explicit replay after end creates a fresh session; Clear/ended observations cannot
resurrect history through the old owner.

## Backend and retained boundaries

One browser session pins an approved read-only regular-file descriptor under the
existing media lock. Names/replacements and current root membership are revalidated;
old session ids cannot affect a replacement. FileResponse retains the pinned
Starlette Range/conditional behavior, with owned cleanup and no deferred pathsend.
An open descriptor does not freeze in-place file writes. Guarded deletion's
original algorithm is unchanged; active browser inode protection is added before
it and cache/history invalidation follows only successful unlink.

History is bounded atomic private JSON,40records/256KiB; only12validated available
items are returned. Missing/unmounted media is hidden without erasing history.
Metadata/JPEG cache is RAM only,64entries/8MiB payload. A separate muted mpv process
uses fixed trusted Lua, one decoder/filter thread, CPU/memory/file/output/time
limits and restricted nested references. It never controls active Player IPC or
audio. No mandatory ffprobe/ffmpeg/dependency/OS/network/profile change is added.
Started threaded operations drain before releasing the media lock, including
cancellation during opening, progress, clear, start and guarded deletion cleanup.

## Findings, iteration and source evidence

The first private native inspector failed parsing a nested filter option. Quoting
the graph option corrected it while retaining the process bounds. Native testing
then exposed a delegated file handle left after disconnect: cancellation interrupted
the library's asynchronous file close. Ordinary controlled unwinding inside a
shielded owned response task now completes that close before releasing the pinned
descriptor. Caller and AnyIO-server cancellation are separately exercised.

Independent review found persistent history-write failure could block all video
exit. The explicit discard/confirmed local-leave recovery was added; before/after
session tests retain9PASS/5expectedFAIL versus14PASS. Browser tests initially
targeted hidden Apply controls; they now use the actual visible keyboard key.
A subsequent broad keyboard-selector rewrite was corrected for Windows text
encoding in the test file only. An old one-button recovery lookup was also made
explicit after the second recovery action was added. Earlier failures are retained
privately and are classified separately from product defects.

755Python tests PASS/44platform skips, plus11subtests;108JavaScript checks PASS,
including14session and94extension checks. TypeScript PASS.44focused browser cases
PASS across EN/RO×Ink/Night, including real decoder fixtures, resume-before-play,
atomic close, stale ownership, explicit replay, search/focus return and persistent
failure recovery. Artwork in browser fixtures is explicitly owned test imagery,
not evidence of extraction from those mocked rows. Broader media/audio regression
and final package/native UI delivery are recorded below when complete.

## Controlled Linux component and API probes

30distinct native component checks PASS on isolated synthetic fixtures: real WAV
duration/title, actual WebM JPEG320×180, restricted playlist nested HTTP not opened,
Range/HEAD/replacement protection, descriptor cleanup, caller/server cancellation,
read-only enforcement and clear/resume history. FD counts7→7, owned fixture handles
empty. No real user's media or active Player was used.

53distinct isolated ASGI composition checks PASS using actual staged API,
Content/LocalMedia, file/procfs/identity guards and original guarded unlink. The
only player is an idle test object; no Device/lifespan/listening server is created.
Real metadata/art endpoint, opaque SID Range/HEAD,12s observation out of the actual
15.911s fixture duration, Continue/reload/resume/clear, stale/replacement ownership,
logical expiry and deletion of one controlled copy pass. The progress here is an
API fixture observation, not a browser playhead. Logical expiry uses a local test
clock; no real/system clock is changed. FD7→7, owned handles empty. The initial
incomplete staging import failure is retained; the completed stage includes the
required existing remote module without launching it.

For both probes the wrapper verified live preferences, actual audio settings,
radio source/state and network unchanged. Raw state, fixtures, screenshots,
operation logs and backups stay private. Physical touch/audible output, all native
language/theme combinations, DRM and full product stability remain unclaimed.

## Broader regression and closing gesture correction

The existing media/audio regression passed227/228; one real close-during-volume-
drag race sent the draft volume after Back began its asynchronous final close.
LocalVideo now gates audio/seek commands synchronously on session ownership and
disables those controls while closing, cancelling the held thumb. The focused
retest passes84/84 (40terminal-audio plus44Media/library/recovery cases), including
all EN/RO×theme close-drag cases. Earlier failure is retained. 52shared command/Radio checks PASS after that correction. TypeScript/build and
repository structure PASS; immutable package/source verification follows before
native UI use.
