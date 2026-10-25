# 0011 — Recoverable software standby and LAN companion presence

Accepted 2026-10-13, at the owner's request.

PySH stays running during OFF/standby. The backend pauses playback, closes only
its managed external browser, stops visualization and sets the DSI backlight to
zero when supported. The touchscreen wake surface and authenticated LAN API
remain alive. Wake restores saved brightness without automatically resuming audio.
This never invokes OS shutdown, suspend, reboot or a network change.

Brightness uses the existing sysfs backlight and logind SetBrightness on the
owner's active seated session. No generic root helper or global permission changes
are introduced. Failed hardware writes do not save a misleading brightness value.
The backend restores the desired brightness after startup, including recovery
from a process restart while the panel is off.

Both a cancellable monotonic countdown and a persistent daily HH:mm schedule are
supported. Daily scheduling follows the configured hub timezone, runs at most
once per local date and accounts for daylight-saving transitions. Changing or
restarting the schedule after today's selected time does not unexpectedly undo
a manual wake. Countdown timers are runtime state and reset on service restart.

Foreground authenticated Android heartbeats expire after 15 seconds. A paired
but inactive phone does not produce the header icon. Presence discloses only a
count to the touchscreen; it gives no extra authorization.

Radio artwork is fetched on the Pi from known station metadata, with public
DNS validation on each of at most three redirects and bounded image responses,
then delivered to Android over the
same pinned LAN connection. Android does not fetch logo URLs from the internet.
Known official station homepages provide a fallback icon if stored metadata has
an empty or obsolete URL. Their HTML is parsed only for icon links, bounded to
64KiB; scripts, pages and accounts are never exposed to Android.

Full hardware and product acceptance remain separate from implementation and
automated test results.
